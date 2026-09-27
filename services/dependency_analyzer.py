"""
Module d'analyse des dépendances logicielles.
Identifie et extrait les bibliothèques et paquets déclarés dans les fichiers manifestes
(requirements.txt, package.json, pom.xml, composer.json...) sans rien installer.
"""
import re
import json

class DependencyAnalyzer:
    """Analyseur de manifestes de dépendances."""

    @staticmethod
    def identify_dependency_files(tree):
        """
        Scanne l'arborescence pour trouver les fichiers manifestes de dépendances connus.
        Retourne une liste de dictionnaires avec le type, le nom et le chemin.
        """
        known_manifests = {
            "requirements.txt": "python",
            "Pipfile": "python",
            "setup.py": "python",
            "pyproject.toml": "python",
            "package.json": "javascript",
            "pom.xml": "java",
            "build.gradle": "java",
            "composer.json": "php",
            "Gemfile": "ruby",
            "go.mod": "go"
        }

        found = []
        for item in tree:
            if item.get("type") == "blob":
                filename = item.get("path", "").split("/")[-1]
                if filename in known_manifests:
                    found.append({
                        "name": filename,
                        "path": item.get("path"),
                        "ecosystem": known_manifests[filename]
                    })
        return found

    @staticmethod
    def parse_python_requirements(content):
        """
        Parse le contenu d'un fichier requirements.txt standard.
        Extrait les noms de bibliothèques propres sans numéros de version.
        """
        if not content:
            return []

        packages = []
        for line in content.splitlines():
            line = line.strip()
            # Ignorer les commentaires et lignes vides ou options pip (-r, -i, etc.)
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Supprimer les commentaires en bout de ligne
            line = line.split("#")[0].strip()

            # Nettoyer les comparateurs de version (==, >=, <=, ~=, !=, <, >)
            pkg_name = re.split(r"[><=~!]+", line)[0].strip()

            # Nettoyer les extras de dépendances ex: "celery[redis]" -> "celery"
            pkg_name = re.sub(r"\[.*?\]", "", pkg_name).strip()

            if pkg_name and pkg_name not in packages:
                packages.append(pkg_name)

        return packages

    @staticmethod
    def parse_package_json(content):
        """
        Parse un fichier package.json JavaScript / Node.js
        Extrait les 'dependencies' et 'devDependencies'.
        """
        if not content:
            return []

        packages = []
        try:
            data = json.loads(content)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})

            for name in list(deps.keys()) + list(dev_deps.keys()):
                if name not in packages:
                    packages.append(name)
        except Exception:
            # En cas de JSON malformé, repli sur regex
            matches = re.findall(r'"([@a-zA-Z0-9_\-\.\/]+)"\s*:\s*"[^"]+"', content)
            for m in matches:
                if m not in ["name", "version", "description", "main", "scripts", "author", "license"] and m not in packages:
                    packages.append(m)

        return packages

    @staticmethod
    def parse_pom_xml(content):
        """
        Parse un fichier Maven pom.xml.
        Extrait les balises <artifactId>...</artifactId>.
        """
        if not content:
            return []

        packages = []
        matches = re.findall(r"<artifactId>\s*([a-zA-Z0-9_\-\.]+)\s*</artifactId>", content)
        for m in matches:
            if m not in packages:
                packages.append(m)
        return packages

    @staticmethod
    def parse_composer_json(content):
        """
        Parse un fichier PHP composer.json.
        Extrait les paquets de la section 'require'.
        """
        if not content:
            return []

        packages = []
        try:
            data = json.loads(content)
            reqs = data.get("require", {})
            for name in reqs.keys():
                if name not in ["php"] and name not in packages:
                    packages.append(name)
        except Exception:
            pass
        return packages

    @classmethod
    def parse_file(cls, filename, content):
        """
        Routeur de parsing en fonction du nom du fichier de dépendances.
        """
        lower = filename.lower()
        if "requirements" in lower or lower.endswith(".txt"):
            return {
                "ecosystem": "Python",
                "filename": filename,
                "packages": cls.parse_python_requirements(content)
            }
        elif lower == "package.json":
            return {
                "ecosystem": "JavaScript / TypeScript",
                "filename": filename,
                "packages": cls.parse_package_json(content)
            }
        elif lower == "pom.xml":
            return {
                "ecosystem": "Java (Maven)",
                "filename": filename,
                "packages": cls.parse_pom_xml(content)
            }
        elif lower == "composer.json":
            return {
                "ecosystem": "PHP (Composer)",
                "filename": filename,
                "packages": cls.parse_composer_json(content)
            }
        return {
            "ecosystem": "Autre",
            "filename": filename,
            "packages": []
        }
