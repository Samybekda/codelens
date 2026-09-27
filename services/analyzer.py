"""
Module d'analyse de structure, langages, complexité et documentation README.
Algorithmes clairs, déterministes et facilement explicables pour une soutenance L3.
"""
import os
import re
from config import Config

class RepoAnalyzer:
    """Analyseur principal du contenu et de la composition d'un dépôt."""

    @staticmethod
    def analyze_structure(tree):
        """
        Calcule les métriques structurelles du dépôt à partir de l'arbre Git :
        - Nombre total de fichiers
        - Nombre total de dossiers
        - Profondeur maximale de l'arborescence
        - Représentation textuelle de l'arborescence
        """
        files = [item for item in tree if item.get("type") == "blob"]
        folders = [item for item in tree if item.get("type") == "tree"]

        file_count = len(files)
        folder_count = len(folders)

        # Calcul de la profondeur maximale (nombre de '/' dans les chemins)
        max_depth = 1
        for item in tree:
            depth = item.get("path", "").count("/") + 1
            if depth > max_depth:
                max_depth = depth

        # Génération d'une arborescence textuelle compacte (jusqu'à 3 niveaux de profondeur)
        tree_text = RepoAnalyzer._build_ascii_tree(tree, max_depth_display=3)

        return {
            "file_count": file_count,
            "folder_count": folder_count,
            "max_depth": max_depth,
            "tree_representation": tree_text,
            "raw_files": files
        }

    @staticmethod
    def _build_ascii_tree(tree, max_depth_display=3):
        """
        Construit une représentation visuelle de l'arborescence (style 'tree').
        Limite la profondeur pour garder un rendu lisible et élégant.
        """
        # Organiser les chemins dans une structure hiérarchique simple (dictionnaire imbriqué)
        root = {}
        for item in tree:
            parts = item.get("path", "").split("/")
            if len(parts) > max_depth_display:
                # Tronquer pour ne pas surcharger
                parts = parts[:max_depth_display]
            
            curr = root
            for p in parts[:-1]:
                curr = curr.setdefault(p, {})
            # Dernier élément (fichier ou dossier)
            curr.setdefault(parts[-1], None if item.get("type") == "blob" else {})

        lines = ["repository/"]

        def render_level(node, prefix=""):
            items = list(node.items())
            # Afficher les dossiers en premier, puis les fichiers
            items.sort(key=lambda x: (x[1] is None, x[0].lower()))
            # Limiter à 15 entrées par niveau pour éviter les arbres infinis
            displayed_items = items[:15]
            for i, (name, subtree) in enumerate(displayed_items):
                is_last = (i == len(displayed_items) - 1)
                connector = "└── " if is_last else "├── "
                sub_prefix = "    " if is_last else "│   "
                
                if subtree is None:
                    # Fichier
                    lines.append(f"{prefix}{connector}{name}")
                else:
                    # Dossier
                    lines.append(f"{prefix}{connector}{name}/")
                    render_level(subtree, prefix + sub_prefix)
            if len(items) > 15:
                lines.append(f"{prefix}└── ... ({len(items) - 15} autres éléments)")

        render_level(root)
        return "\n".join(lines[:60])  # Maximum 60 lignes pour une clarté optimale

    @staticmethod
    def analyze_languages(files):
        """
        Détermine la répartition des langages de programmation en se basant sur les extensions de fichiers.
        Retourne une liste triée avec le nom, le nombre de fichiers, le volume en octets et le pourcentage.
        """
        lang_counts = {}
        lang_bytes = {}
        total_code_files = 0
        total_bytes = 0

        # Extensions à ignorer pour l'analyse des langages principaux (ex: markdown, texte brut)
        excluded_exts = {".md", ".txt", ".gitignore", ".gitattributes", ".lock"}

        for f in files:
            path = f.get("path", "")
            size = f.get("size", 0)
            _, ext = os.path.splitext(path)
            ext = ext.lower()

            if ext in excluded_exts or not ext:
                continue

            lang_name = Config.LANGUAGE_EXTENSIONS.get(ext)
            if lang_name:
                lang_counts[lang_name] = lang_counts.get(lang_name, 0) + 1
                lang_bytes[lang_name] = lang_bytes.get(lang_name, 0) + size
                total_code_files += 1
                total_bytes += size

        if total_code_files == 0:
            # Si aucun langage spécifique n'a été reconnu
            return []

        results = []
        for lang, count in lang_counts.items():
            pct = round((count / total_code_files) * 100, 1)
            results.append({
                "name": lang,
                "count": count,
                "size_bytes": lang_bytes.get(lang, 0),
                "percentage": pct
            })

        # Trier par pourcentage décroissant
        results.sort(key=lambda x: x["percentage"], reverse=True)
        return results

    @staticmethod
    def inspect_file_complexity(content, filename):
        """
        Analyse le contenu d'un fichier source et compte :
        - Nombre de lignes
        - Nombre de fonctions
        - Nombre de classes
        """
        if not content:
            return None

        lines = content.splitlines()
        line_count = len(lines)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        function_count = 0
        class_count = 0

        if ext in [".py", ".pyw"]:
            # Détection en Python
            function_count = len(re.findall(r"^\s*def\s+([a-zA-Z0-9_]+)\s*\(", content, re.MULTILINE))
            class_count = len(re.findall(r"^\s*class\s+([a-zA-Z0-9_]+)", content, re.MULTILINE))
        elif ext in [".js", ".mjs", ".ts"]:
            # Détection en JS / TS
            func_classic = len(re.findall(r"(?:function\s+[a-zA-Z0-9_]+|(?:const|let|var)\s+[a-zA-Z0-9_]+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)", content))
            function_count = func_classic
            class_count = len(re.findall(r"class\s+[a-zA-Z0-9_]+", content))
        elif ext in [".java", ".cpp", ".c", ".cs", ".php"]:
            # Détection générique C-like
            class_count = len(re.findall(r"\bclass\s+[a-zA-Z0-9_]+", content))
            # Heuristique simple pour les signatures de méthodes
            function_count = len(re.findall(r"(?:public|private|protected|static|\bfunction\b)\s+[\w<>\[\]]+\s+([a-zA-Z0-9_]+)\s*\(", content))

        reasons = []
        if line_count > Config.LINE_THRESHOLD:
            reasons.append(f"{line_count} lignes (seuil : > {Config.LINE_THRESHOLD})")
        if function_count > Config.FUNCTION_THRESHOLD:
            reasons.append(f"{function_count} fonctions (seuil : > {Config.FUNCTION_THRESHOLD})")
        if class_count > Config.CLASS_THRESHOLD:
            reasons.append(f"{class_count} classes (seuil : > {Config.CLASS_THRESHOLD})")

        is_complex = len(reasons) > 0

        return {
            "filename": filename,
            "line_count": line_count,
            "function_count": function_count,
            "class_count": class_count,
            "is_complex": is_complex,
            "reasons": reasons
        }

    @staticmethod
    def analyze_readme(readme_content):
        """
        Analyse la documentation README :
        - Détection de la présence
        - Nombre de lignes
        - Détection des sections : Installation, Utilisation, Contribution
        """
        if not readme_content:
            return {
                "present": False,
                "line_count": 0,
                "has_installation": False,
                "has_usage": False,
                "has_contributing": False,
                "score_feedback": "Aucun fichier README trouvé à la racine du dépôt."
            }

        lines = readme_content.splitlines()
        line_count = len(lines)

        # Motifs de recherche insensibles à la casse pour les sections
        install_pattern = r"(?i)(?:#+\s*|===+|\b)(?:installation|install|setup|mise en place|pr[ée]requis)\b"
        usage_pattern = r"(?i)(?:#+\s*|===+|\b)(?:utilisation|usage|how to use|quick start|d[ée]marrage|fonctionnement)\b"
        contrib_pattern = r"(?i)(?:#+\s*|===+|\b)(?:contribution|contributing|contribuer|d[ée]veloppement|participer)\b"

        has_installation = bool(re.search(install_pattern, readme_content))
        has_usage = bool(re.search(usage_pattern, readme_content))
        has_contributing = bool(re.search(contrib_pattern, readme_content))

        return {
            "present": True,
            "line_count": line_count,
            "has_installation": has_installation,
            "has_usage": has_usage,
            "has_contributing": has_contributing
        }

    @staticmethod
    def generate_report(stats, languages, complex_files, readme_audit, dependencies_count, git_stats):
        """
        Génère un rapport global, factuel et structuré ('Rapport CodeLens').
        Ne donne pas de note subjective. Met en avant les faits mesurés.
        """
        points = []

        # Point sur les fichiers
        file_count = stats.get("file_count", 0)
        points.append(f"Le projet est composé de {file_count} fichiers répartis dans {stats.get('folder_count', 0)} dossiers.")

        # Point sur le langage dominant
        if languages:
            top_lang = languages[0]
            points.append(f"{top_lang['name']} est le langage principal avec {top_lang['percentage']} % des fichiers de code.")
        else:
            points.append("Aucun langage de programmation majeur n'a été prédominant parmi les extensions analysées.")

        # Point sur les fichiers complexes
        nb_complex = len(complex_files)
        if nb_complex > 0:
            points.append(f"{nb_complex} fichier(s) dépassent les seuils de complexité définis (plus de {Config.LINE_THRESHOLD} lignes ou {Config.FUNCTION_THRESHOLD} fonctions).")
        else:
            points.append("Aucun fichier ne dépasse les seuils de complexité fixés.")

        # Point sur la communauté et l'activité Git
        commits_nb = git_stats.get("commit_count", 0)
        contribs_nb = git_stats.get("contributor_count", 0)
        points.append(f"Le dépôt compte {contribs_nb} contributeur(s) et environ {commits_nb} commit(s).")

        # Point sur la documentation README
        if readme_audit.get("present"):
            sections = []
            if readme_audit.get("has_installation"):
                sections.append("Installation")
            if readme_audit.get("has_usage"):
                sections.append("Utilisation")
            if readme_audit.get("has_contributing"):
                sections.append("Contribution")
            
            if sections:
                points.append(f"Un fichier README ({readme_audit.get('line_count')} lignes) est présent avec les sections : {', '.join(sections)}.")
            else:
                points.append(f"Un fichier README ({readme_audit.get('line_count')} lignes) est présent mais sans sections standards identifiées.")
        else:
            points.append("Le dépôt ne comporte pas de documentation README détectable à la racine.")

        # Point sur les dépendances
        if dependencies_count > 0:
            points.append(f"{dependencies_count} paquet(s) et bibliothèque(s) externe(s) ont été répertoriés dans les manifestes du projet.")

        return {
            "status_title": "Analyse du dépôt terminée avec succès.",
            "checklist": [
                {"label": "Structure détectée", "ok": True},
                {"label": "Langages analysés", "ok": len(languages) > 0},
                {"label": "Dépendances détectées", "ok": dependencies_count > 0},
                {"label": "Statistiques Git récupérées", "ok": commits_nb > 0},
                {"label": "Documentation README auditée", "ok": readme_audit.get("present", False)}
            ],
            "points": points
        }
