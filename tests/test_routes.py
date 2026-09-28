"""
Tests fonctionnels pour l'application Flask CodeLens et la base SQLite.
Vérifie le bon fonctionnement des routes HTTP et la persistance.
"""
import pytest
import os
import tempfile
import sys
from pathlib import Path

# Configurer le chemin d'import
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import app
from database.database import init_db, save_analysis, get_recent_analyses, get_analysis_by_id, delete_analysis
from config import Config

@pytest.fixture
def client(tmp_path):
    """Fixture créant un client de test Flask et une base de données temporaire."""
    test_db = str(tmp_path / "test_codelens.db")
    Config.DB_PATH = test_db
    app.config["TESTING"] = True
    
    with app.app_context():
        init_db()

    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Vérifie que la page d'accueil répond avec le code 200 et le titre."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"CodeLens" in response.data
    assert b"Analyser le d" in response.data  # "Analyser le dépôt"

def test_about_page(client):
    """Vérifie que la page À propos répond avec le code 200 et les infos L3."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"MIAGE" in response.data
    assert b"Paul Sabatier" in response.data

def test_history_page(client):
    """Vérifie que la page Historique se charge sans erreur."""
    response = client.get("/history")
    assert response.status_code == 200
    assert b"Historique des analyses" in response.data

def test_analyze_empty_url_redirect(client):
    """Vérifie qu'une URL vide redirige vers l'accueil avec un avertissement."""
    response = client.post("/analyze", data={"repo_url": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Veuillez saisir l" in response.data

def test_analyze_invalid_url_redirect(client):
    """Vérifie qu'une URL invalide redirige vers l'accueil avec un message d'erreur."""
    response = client.post("/analyze", data={"repo_url": "https://not-github.com/foo/bar"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Format d" in response.data

def test_sqlite_persistence_flow(client):
    """Vérifie le cycle complet de sauvegarde, consultation et suppression SQLite."""
    repo_info = {
        "name": "flask",
        "owner": "pallets",
        "html_url": "https://github.com/pallets/flask",
        "description": "A simple framework"
    }
    stats = {
        "file_count": 42,
        "folder_count": 5,
        "commit_count": 350,
        "contributor_count": 12
    }
    languages = [
        {"name": "Python", "percentage": 85.0, "count": 35, "size_bytes": 50000},
        {"name": "HTML", "percentage": 15.0, "count": 7, "size_bytes": 10000}
    ]
    report = {
        "status_title": "Analyse terminée.",
        "checklist": [],
        "points": ["Point 1"]
    }
    details = {"structure": {}, "dependencies": []}

    # Insertion
    analysis_id = save_analysis(repo_info, stats, languages, report, details)
    assert analysis_id is not None
    assert analysis_id > 0

    # Consultation par ID
    saved = get_analysis_by_id(analysis_id)
    assert saved is not None
    assert saved["repository_name"] == "flask"
    assert saved["file_count"] == 42
    assert "Python (85.0%)" in saved["languages"]

    # Consultation de la liste récente
    recent = get_recent_analyses(limit=10)
    assert len(recent) >= 1
    assert recent[0]["repository_name"] == "flask"

    # Affichage de la page de consultation
    resp = client.get(f"/analysis/{analysis_id}")
    assert resp.status_code == 200
    assert b"flask" in resp.data

    # Suppression
    resp_del = client.post(f"/history/delete/{analysis_id}", follow_redirects=True)
    assert resp_del.status_code == 200
    assert get_analysis_by_id(analysis_id) is None
