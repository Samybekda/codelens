"""
Application principale Flask pour CodeLens.
Analyseur de dépôts GitHub - Projet universitaire L3 MIAGE / MIASHS.
Université Toulouse III - Paul Sabatier.
"""
import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Ajout du répertoire courant au PYTHONPATH pour les imports locaux
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database.database import (
    init_db,
    save_analysis,
    get_recent_analyses,
    get_analysis_by_id,
    delete_analysis
)
from services.github_service import GitHubService, GitHubServiceError
from services.analyzer import RepoAnalyzer
from services.dependency_analyzer import DependencyAnalyzer
from services.git_analyzer import GitAnalyzer

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

# Initialisation de la base de données SQLite au démarrage
with app.app_context():
    init_db()

# Filtre Jinja pour formater les tailles d'octets de façon lisible
@app.template_filter("filesize_format")
def filesize_format(bytes_val):
    try:
        val = float(bytes_val)
        for unit in ["o", "Ko", "Mo", "Go"]:
            if val < 1024.0:
                return f"{val:.1f} {unit}"
            val /= 1024.0
        return f"{val:.1f} To"
    except (ValueError, TypeError):
        return "0 o"

# Exemples de dépôts populaires pour faciliter la démo lors de la soutenance
DEMO_REPOSITORIES = [
    {"name": "Flask", "url": "https://github.com/pallets/flask", "desc": "Microframework web Python"},
    {"name": "Requests", "url": "https://github.com/psf/requests", "desc": "Client HTTP Python élégant"},
    {"name": "Express", "url": "https://github.com/expressjs/express", "desc": "Framework web minimaliste Node.js"},
    {"name": "Chart.js", "url": "https://github.com/chartjs/Chart.js", "desc": "Bibliothèque de graphiques JS"},
]

@app.route("/")
def index():
    """Page d'accueil avec champ de recherche et suggestions."""
    recent = get_recent_analyses(limit=5)
    return render_template("index.html", demo_repos=DEMO_REPOSITORIES, recent=recent)

@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    """
    Route de lancement d'une analyse.
    Accepte l'URL via formulaire POST ou paramètre GET (?url=...).
    """
    if request.method == "POST":
        repo_url = request.form.get("repo_url", "").strip()
    else:
        repo_url = request.args.get("url", "").strip()

    if not repo_url:
        flash("Veuillez saisir l'URL d'un dépôt GitHub public.", "warning")
        return redirect(url_for("index"))

    owner, repo = GitHubService.parse_repo_url(repo_url)
    if not owner or not repo:
        flash("Format d'URL invalide. Exemple attendu : https://github.com/proprietaire/nom-du-depot", "danger")
        return redirect(url_for("index"))

    github = GitHubService()

    try:
        # 1. Informations générales du dépôt
        repo_info = github.get_repo_details(owner, repo)

        # 2. Arborescence Git complète
        tree, is_truncated = github.get_git_tree(owner, repo, branch=repo_info["default_branch"])
        structure_data = RepoAnalyzer.analyze_structure(tree)
        raw_files = structure_data.pop("raw_files")

        # 3. Répartition des langages
        languages = RepoAnalyzer.analyze_languages(raw_files)

        # 4. Analyse des fichiers de dépendances
        manifest_files = DependencyAnalyzer.identify_dependency_files(tree)
        parsed_dependencies = []
        # On inspecte les premiers manifestes trouvés (max 4 pour limiter les appels API)
        for manifest in manifest_files[:4]:
            content = github.get_file_content(owner, repo, manifest["path"])
            if content:
                dep_data = DependencyAnalyzer.parse_file(manifest["name"], content)
                parsed_dependencies.append(dep_data)

        # Total cumulé des paquets
        total_dependencies_count = sum(len(d["packages"]) for d in parsed_dependencies)

        # 5. Statistiques Git (Commits, Contributeurs, Branches)
        commits_raw, total_commits = github.get_commits_info(owner, repo)
        git_commits_data = GitAnalyzer.process_commits(commits_raw, total_commits)

        contributors_list, total_contribs = github.get_contributors_info(owner, repo)
        branches_list, total_branches = github.get_branches_info(owner, repo)

        git_stats = {
            "commit_count": git_commits_data["commit_count"],
            "contributor_count": max(total_contribs, len(contributors_list)),
            "branch_count": max(total_branches, len(branches_list)),
            "latest_commit": git_commits_data["latest_commit"],
            "monthly_activity": git_commits_data["monthly_activity"],
            "recent_commits_list": git_commits_data["recent_commits_list"],
            "top_contributors": contributors_list[:6],
            "branches": branches_list[:6]
        }

        # 6. Analyse des fichiers complexes
        # On sélectionne les fichiers de code candidats parmi les plus volumineux
        code_exts = tuple(Config.LANGUAGE_EXTENSIONS.keys())
        code_files = [f for f in raw_files if f.get("path", "").endswith(code_exts)]
        # Trier par taille décroissante
        code_files.sort(key=lambda x: x.get("size", 0), reverse=True)

        complex_files = []
        files_to_check = code_files[:Config.MAX_INSPECT_FILES]
        for f in files_to_check:
            # Ne récupérer le contenu que pour les fichiers dépassant une taille minimale (> 3 Ko) ou premiers
            if f.get("size", 0) > 2000 or len(files_to_check) <= 5:
                content = github.get_file_content(owner, repo, f.get("path"))
                if content:
                    analysis = RepoAnalyzer.inspect_file_complexity(content, f.get("path"))
                    if analysis and analysis["is_complex"]:
                        complex_files.append(analysis)

        # 7. Audit du README
        readme_file = next((item for item in tree if item.get("path", "").lower() in ["readme.md", "readme.txt", "readme"]), None)
        readme_content = None
        if readme_file:
            readme_content = github.get_file_content(owner, repo, readme_file.get("path"))
        readme_audit = RepoAnalyzer.analyze_readme(readme_content)

        # 8. Rapport global factuel CodeLens
        global_stats = {
            "file_count": structure_data["file_count"],
            "folder_count": structure_data["folder_count"],
            "max_depth": structure_data["max_depth"],
            "size_kb": repo_info["size_kb"],
            "commit_count": git_stats["commit_count"],
            "contributor_count": git_stats["contributor_count"]
        }
        report = RepoAnalyzer.generate_report(
            stats=global_stats,
            languages=languages,
            complex_files=complex_files,
            readme_audit=readme_audit,
            dependencies_count=total_dependencies_count,
            git_stats=git_stats
        )

        # 9. Sauvegarde dans SQLite
        raw_details = {
            "structure": structure_data,
            "dependencies": parsed_dependencies,
            "git_stats": git_stats,
            "complex_files": complex_files,
            "readme_audit": readme_audit,
            "is_truncated": is_truncated,
            "thresholds": {
                "line": Config.LINE_THRESHOLD,
                "function": Config.FUNCTION_THRESHOLD,
                "class": Config.CLASS_THRESHOLD
            }
        }
        saved_id = save_analysis(repo_info, global_stats, languages, report, raw_details)

        return redirect(url_for("view_analysis", analysis_id=saved_id))

    except GitHubServiceError as e:
        flash(str(e), "danger")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Une erreur imprévue est survenue : {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/analysis/<int:analysis_id>")
def view_analysis(analysis_id):
    """Affiche les détails complets d'une analyse enregistrée."""
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        flash("Analyse introuvable dans la base de données.", "warning")
        return redirect(url_for("history"))

    full_data = analysis.get("full_data", {})
    repo_info = full_data.get("repo_info", {})
    stats = full_data.get("stats", {})
    languages = full_data.get("languages", [])
    report = full_data.get("report", {})
    details = full_data.get("details", {})

    return render_template(
        "analysis.html",
        analysis_id=analysis_id,
        analysis_date=analysis.get("analysis_date"),
        repo_info=repo_info,
        stats=stats,
        languages=languages,
        report=report,
        structure=details.get("structure", {}),
        dependencies=details.get("dependencies", []),
        git_stats=details.get("git_stats", {}),
        complex_files=details.get("complex_files", []),
        readme_audit=details.get("readme_audit", {}),
        is_truncated=details.get("is_truncated", False),
        thresholds=details.get("thresholds", {
            "line": Config.LINE_THRESHOLD,
            "function": Config.FUNCTION_THRESHOLD,
            "class": Config.CLASS_THRESHOLD
        })
    )

@app.route("/history")
def history():
    """Page listant l'ensemble des analyses passées enregistrées dans SQLite."""
    analyses_list = get_recent_analyses(limit=100)
    return render_template("history.html", analyses=analyses_list)

@app.route("/history/delete/<int:analysis_id>", methods=["POST"])
def delete_history_item(analysis_id):
    """Supprime une analyse de la base de données."""
    delete_analysis(analysis_id)
    flash("L'analyse a été supprimée de l'historique.", "info")
    return redirect(url_for("history"))

@app.route("/about")
def about():
    """Page de présentation du projet universitaire CodeLens."""
    thresholds = {
        "line": Config.LINE_THRESHOLD,
        "function": Config.FUNCTION_THRESHOLD,
        "class": Config.CLASS_THRESHOLD
    }
    return render_template("about.html", thresholds=thresholds)

if __name__ == "__main__":
    # Lancement du serveur de développement Flask
    print("=" * 60)
    print(" CodeLens — Analyseur de dépôts GitHub (L3 MIAGE / MIASHS)")
    print(" Université Toulouse III – Paul Sabatier")
    print(" Serveur disponible sur : http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)
