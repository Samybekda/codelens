"""
Configuration de l'application CodeLens.
Projet universitaire L3 MIAGE / MIASHS - Université Toulouse III Paul Sabatier.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Chargement du fichier .env s'il existe
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Paramètres globaux et facilement configurables de CodeLens."""
    
    # Sécurité Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "codelens-default-secret-key-l3miage")
    
    # Token d'authentification GitHub (optionnel pour augmenter le quota de 60 à 5000 req/h)
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
    
    # Base de données SQLite
    DB_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "codelens.db"))
    
    # Seuils de détection de complexité (facilement modifiables pour la soutenance)
    LINE_THRESHOLD = int(os.getenv("LINE_THRESHOLD", 200))        # Plus de 200 lignes -> fichier long
    FUNCTION_THRESHOLD = int(os.getenv("FUNCTION_THRESHOLD", 10))  # Plus de 10 fonctions -> beaucoup de fonctions
    CLASS_THRESHOLD = int(os.getenv("CLASS_THRESHOLD", 5))        # Plus de 5 classes -> beaucoup de classes
    MAX_INSPECT_FILES = 12                                        # Nombre maximal de fichiers prioritaires analysés en détail
    
    # Dictionnaire d'associations extensions -> langages de programmation
    LANGUAGE_EXTENSIONS = {
        # Python
        ".py": "Python",
        ".pyw": "Python",
        # JavaScript / TypeScript / Web
        ".js": "JavaScript",
        ".mjs": "JavaScript",
        ".jsx": "JavaScript (React)",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "Sass",
        ".less": "Less",
        # Java & JVM
        ".java": "Java",
        ".kt": "Kotlin",
        ".scala": "Scala",
        # C / C++ / C#
        ".c": "C",
        ".h": "C/C++ Header",
        ".cpp": "C++",
        ".cc": "C++",
        ".hpp": "C++ Header",
        ".cs": "C#",
        # Systèmes & Autres
        ".go": "Go",
        ".rs": "Rust",
        ".php": "PHP",
        ".rb": "Ruby",
        ".swift": "Swift",
        ".sh": "Shell",
        ".bash": "Shell",
        ".sql": "SQL",
        ".r": "R",
        # Configuration & Données
        ".json": "JSON",
        ".xml": "XML",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".md": "Markdown",
        ".txt": "Text"
    }
