"""
Tests unitaires pour les services d'analyse de CodeLens.
Couvre : parsing d'URL, détection d'extensions, calcul des pourcentages,
complexité de fichiers, analyse de dépendances et audit README.
"""
import pytest
from services.github_service import GitHubService
from services.analyzer import RepoAnalyzer
from services.dependency_analyzer import DependencyAnalyzer
from config import Config

def test_parse_github_url():
    """Vérifie l'extraction robuste du propriétaire et du nom de dépôt."""
    # URLs valides
    assert GitHubService.parse_repo_url("https://github.com/pallets/flask") == ("pallets", "flask")
    assert GitHubService.parse_repo_url("https://github.com/psf/requests.git") == ("psf", "requests")
    assert GitHubService.parse_repo_url("http://github.com/expressjs/express/") == ("expressjs", "express")
    assert GitHubService.parse_repo_url("github.com/vuejs/core") == ("vuejs", "core")
    assert GitHubService.parse_repo_url("torvalds/linux") == ("torvalds", "linux")

    # URLs invalides
    assert GitHubService.parse_repo_url("") == (None, None)
    assert GitHubService.parse_repo_url("https://google.com/foo/bar") == (None, None)
    assert GitHubService.parse_repo_url("just_a_word") == (None, None)

def test_analyze_languages_and_percentages():
    """Vérifie le calcul correct de la répartition des langages."""
    fake_files = [
        {"path": "app.py", "size": 1000},
        {"path": "models.py", "size": 1500},
        {"path": "utils.py", "size": 500},
        {"path": "static/main.js", "size": 2000},
        {"path": "templates/index.html", "size": 1000},
        {"path": "README.md", "size": 800},         # Doit être ignoré dans les langages de code
        {"path": ".gitignore", "size": 50}          # Doit être ignoré
    ]
    # Total fichiers de code reconnus = 3 (Python) + 1 (JS) + 1 (HTML) = 5
    languages = RepoAnalyzer.analyze_languages(fake_files)
    assert len(languages) == 3

    # Python doit être premier avec 3/5 = 60.0%
    assert languages[0]["name"] == "Python"
    assert languages[0]["count"] == 3
    assert languages[0]["percentage"] == 60.0

    # Les autres ont 1/5 = 20.0%
    assert languages[1]["percentage"] == 20.0
    assert languages[2]["percentage"] == 20.0

def test_file_complexity_detection():
    """Vérifie la détection des fichiers complexes dépassant les seuils."""
    # Fichier court et simple
    simple_python = "def hello():\n    return 'world'\n"
    res_simple = RepoAnalyzer.inspect_file_complexity(simple_python, "hello.py")
    assert res_simple["is_complex"] is False
    assert res_simple["line_count"] == 2
    assert res_simple["function_count"] == 1
    assert res_simple["class_count"] == 0

    # Fichier long (> 200 lignes)
    long_content = "\n".join([f"# ligne {i}" for i in range(250)])
    res_long = RepoAnalyzer.inspect_file_complexity(long_content, "big_script.py")
    assert res_long["is_complex"] is True
    assert any("250 lignes" in r for r in res_long["reasons"])

    # Fichier avec beaucoup de fonctions (> 10 fonctions)
    many_functions = "\n".join([f"def func_{i}(): pass" for i in range(15)])
    res_funcs = RepoAnalyzer.inspect_file_complexity(many_functions, "api.py")
    assert res_funcs["is_complex"] is True
    assert res_funcs["function_count"] == 15
    assert any("15 fonctions" in r for r in res_funcs["reasons"])

def test_dependency_analyzer_python():
    """Vérifie l'extraction propre des dépendances dans un requirements.txt."""
    req_content = """
    # Dépendances principales
    Flask>=3.0.0
    requests==2.31.0
    pandas~=2.1.0
    numpy
    -r other-requirements.txt
    pytest
    celery[redis]>=5.2
    """
    pkgs = DependencyAnalyzer.parse_python_requirements(req_content)
    assert "Flask" in pkgs
    assert "requests" in pkgs
    assert "pandas" in pkgs
    assert "numpy" in pkgs
    assert "pytest" in pkgs
    assert "celery" in pkgs
    # Pas de flags ou options
    assert "-r" not in pkgs

def test_dependency_analyzer_javascript():
    """Vérifie l'extraction des paquets dans un package.json."""
    pkg_json = """{
        "name": "mon-projet",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.18.2",
            "cors": "^2.8.5"
        },
        "devDependencies": {
            "jest": "^29.5.0"
        }
    }"""
    pkgs = DependencyAnalyzer.parse_package_json(pkg_json)
    assert "express" in pkgs
    assert "cors" in pkgs
    assert "jest" in pkgs

def test_readme_audit():
    """Vérifie la détection des sections clés du README."""
    sample_readme = """
    # Mon Super Projet

    Ceci est un projet académique.

    ## Installation
    Pour installer le projet, lancez :
    ```bash
    pip install -r requirements.txt
    ```

    ## Utilisation
    Exécutez `python app.py` puis ouvrez votre navigateur.

    ## Guide de Contribution
    Les pull requests sont les bienvenues !
    """
    audit = RepoAnalyzer.analyze_readme(sample_readme)
    assert audit["present"] is True
    assert audit["line_count"] > 10
    assert audit["has_installation"] is True
    assert audit["has_usage"] is True
    assert audit["has_contributing"] is True

def test_dependency_analyzer_pom_and_composer():
    """Vérifie l'analyse de pom.xml (Java) et composer.json (PHP)."""
    pom_xml = """<project>
        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-web</artifactId>
            </dependency>
            <dependency>
                <groupId>junit</groupId>
                <artifactId>junit</artifactId>
            </dependency>
        </dependencies>
    </project>"""
    java_deps = DependencyAnalyzer.parse_pom_xml(pom_xml)
    assert "spring-boot-starter-web" in java_deps
    assert "junit" in java_deps

    composer_json = """{
        "require": {
            "php": ">=8.1",
            "laravel/framework": "^10.0",
            "guzzlehttp/guzzle": "^7.2"
        }
    }"""
    php_deps = DependencyAnalyzer.parse_composer_json(composer_json)
    assert "laravel/framework" in php_deps
    assert "guzzlehttp/guzzle" in php_deps
    assert "php" not in php_deps

def test_analyze_structure_and_depth():
    """Vérifie le calcul de profondeur et la génération de l'arbre ASCII."""
    fake_tree = [
        {"path": "src", "type": "tree"},
        {"path": "src/controllers", "type": "tree"},
        {"path": "src/controllers/home.py", "type": "blob", "size": 500},
        {"path": "README.md", "type": "blob", "size": 120}
    ]
    res = RepoAnalyzer.analyze_structure(fake_tree)
    assert res["file_count"] == 2
    assert res["folder_count"] == 2
    assert res["max_depth"] == 3  # "src/controllers/home.py" -> 3 niveaux
    assert "repository/" in res["tree_representation"]
    assert "src/" in res["tree_representation"]
    assert "README.md" in res["tree_representation"]

def test_git_analyzer_process_commits():
    """Vérifie le traitement des commits et le groupement temporel."""
    from services.git_analyzer import GitAnalyzer
    fake_commits = [
        {
            "sha": "abc1234567",
            "commit": {
                "author": {"name": "Alice", "date": "2026-09-20T14:30:00Z"},
                "message": "Feat: add analysis feature\n\nMore details..."
            }
        },
        {
            "sha": "def8901234",
            "commit": {
                "author": {"name": "Bob", "date": "2026-08-15T10:00:00Z"},
                "message": "Fix: typo in README"
            }
        }
    ]
    res = GitAnalyzer.process_commits(fake_commits, total_commits_estimate=150)
    assert res["commit_count"] == 150
    assert res["latest_commit"]["author_name"] == "Alice"
    assert res["latest_commit"]["sha"] == "abc1234"
    assert res["latest_commit"]["message"] == "Feat: add analysis feature"
    assert len(res["monthly_activity"]["labels"]) >= 2
    assert len(res["recent_commits_list"]) == 2

def test_generate_report_factual():
    """Vérifie que le rapport CodeLens est factuel et respecte la structure attendue."""
    stats = {"file_count": 84, "folder_count": 8}
    languages = [{"name": "Python", "percentage": 65.0}]
    complex_files = [{"filename": "main.py"}, {"filename": "app.py"}, {"filename": "db.py"}]
    readme_audit = {"present": True, "line_count": 120, "has_installation": True, "has_usage": True, "has_contributing": True}
    git_stats = {"commit_count": 120, "contributor_count": 4}

    report = RepoAnalyzer.generate_report(stats, languages, complex_files, readme_audit, 15, git_stats)
    assert report["checklist"][0]["label"] == "Structure détectée"
    assert report["checklist"][0]["ok"] is True
    assert any("84 fichiers" in p for p in report["points"])
    assert any("Python est le langage principal avec 65.0 %" in p for p in report["points"])
    assert any("3 fichier(s) dépassent" in p for p in report["points"])
    assert any("4 contributeur(s)" in p for p in report["points"])
    assert any("Installation, Utilisation, Contribution" in p for p in report["points"])

