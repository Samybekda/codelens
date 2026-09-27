"""
Module d'accès aux données SQLite pour CodeLens.
Gère l'initialisation de la table 'analyses', l'insertion d'analyses,
la consultation de l'historique et la suppression.
"""
import sqlite3
import json
import os
from datetime import datetime
from config import Config

def get_db_connection():
    """Établit une connexion avec la base de données SQLite."""
    # S'assurer que le dossier parent existe
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
    return conn

def init_db():
    """Initialise le schéma de la base de données si elle n'existe pas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repository_url TEXT NOT NULL,
            repository_name TEXT NOT NULL,
            owner TEXT,
            analysis_date TEXT NOT NULL,
            languages TEXT,
            file_count INTEGER DEFAULT 0,
            folder_count INTEGER DEFAULT 0,
            commit_count INTEGER DEFAULT 0,
            contributor_count INTEGER DEFAULT 0,
            details_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_analysis(repo_info, stats, languages, report, raw_details=None):
    """
    Enregistre le résultat d'une analyse dans la table 'analyses'.
    
    :param repo_info: Données générales du dépôt (nom, propriétaire, URL...)
    :param stats: Statistiques globales (fichiers, dossiers, commits, contributeurs...)
    :param languages: Dictionnaire des langages détectés avec pourcentages
    :param report: Rapport synthétique de l'analyse
    :param raw_details: Dictionnaire complet des résultats pour relecture ultérieure
    :return: id de la nouvelle ligne insérée
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Formater les langages sous forme d'une chaîne lisible (ex: "Python (65%), JavaScript (20%)")
    lang_str = ", ".join([f"{l['name']} ({l['percentage']}%)" for l in languages[:4]]) if languages else "Non spécifié"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Sérialiser l'analyse complète au format JSON
    full_payload = {
        "repo_info": repo_info,
        "stats": stats,
        "languages": languages,
        "report": report,
        "details": raw_details or {}
    }
    
    cursor.execute("""
        INSERT INTO analyses (
            repository_url,
            repository_name,
            owner,
            analysis_date,
            languages,
            file_count,
            folder_count,
            commit_count,
            contributor_count,
            details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        repo_info.get("html_url", ""),
        repo_info.get("name", "Inconnu"),
        repo_info.get("owner", "Inconnu"),
        now_str,
        lang_str,
        stats.get("file_count", 0),
        stats.get("folder_count", 0),
        stats.get("commit_count", 0),
        stats.get("contributor_count", 0),
        json.dumps(full_payload, ensure_ascii=False)
    ))
    
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def get_recent_analyses(limit=50):
    """Récupère les dernières analyses triées par date décroissante."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, repository_url, repository_name, owner, analysis_date,
               languages, file_count, folder_count, commit_count, contributor_count
        FROM analyses
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_analysis_by_id(analysis_id):
    """Récupère une analyse complète par son identifiant unique."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM analyses WHERE id = ?
    """, (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    data = dict(row)
    if data.get("details_json"):
        try:
            data["full_data"] = json.loads(data["details_json"])
        except Exception:
            data["full_data"] = None
    return data

def delete_analysis(analysis_id):
    """Supprime une entrée de l'historique."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    conn.close()
