#  CodeLens — Analyseur de Dépôts GitHub

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-orange.svg)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/Tests-pytest%20(16%2F16%20passed)-brightgreen.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)



## 1. Présentation de CodeLens

**CodeLens** est une application web conçue en Python avec le microframework Flask. Elle permet à un utilisateur de renseigner l'URL d'un dépôt GitHub public afin d'obtenir automatiquement une analyse complète, structurée et visuelle du projet.

Contrairement aux outils d'analyse statique complexes et opaques (SonarQube, Coveralls...), CodeLens a été pensé pour être **100% transparent, déterministe et pédagogique**. Il extrait et synthétise des informations factuelles sur l'architecture, la composition technologique, la communauté et l'activité du projet sans jamais prétendre attribuer une note arbitraire au code.

---

## 2. Objectifs Pédagogiques

Ce projet valide les compétences fondamentales attendues d'un étudiant en fin de cycle de Licence 3 MIAGE / MIASHS :
* **Développement Web Backend & Frontend :** Maîtrise de l'architecture MVC avec Flask, Jinja2, HTML5 sémantique, CSS3 responsive et JavaScript Vanilla (sans dépendance à un framework lourd comme React).
* **Consommation d'API REST :** Interrogation de l'API publique GitHub avec `requests`, gestion de la pagination via les en-têtes HTTP `Link`, gestion du Rate Limiting et authentification par token.
* **Algorithmique & Manipulation de Données :** Détection d'extensions, calculs de pourcentages, reconstruction d'arborescences de fichiers, détection déterministe de la complexité logicielle selon des seuils configurables.
* **Bases de Données Relationnelles :** Modélisation relationnelle avec SQLite, requêtes SQL paramétrées sécurisées contre les injections SQL, et persistance d'un historique complet.
* **Visualisation de Données :** Conception de graphiques dynamiques et interactifs avec Chart.js.
* **Qualité & Tests Logiciels :** Rédaction d'une suite de tests automatisés avec `pytest`.

---

## 3. Fonctionnalités de l'Application

###  1. Informations Générales
* Nom du dépôt, propriétaire, avatar et description.
* Métriques de popularité : nombre d'étoiles (stars), forks, watchers.
* Métadonnées Git : branche principale par défaut, visibilité (public/privé), licence logicielle déclarée, dates de création et de dernière mise à jour.

###  2. Structure du Dépôt
* Récupération de l'arborescence complète en un appel HTTP unique grâce à l'API Git Trees récursive (`git/trees/{branch}?recursive=1`).
* Calcul du nombre total de fichiers et de dossiers.
* Mesure de la profondeur maximale de l'arborescence.
* Rendu textuel élégant de l'arborescence (style commande système `tree`).

###  3. Langages Utilisés
* Classification déterministe par extensions de fichiers (`.py`, `.js`, `.ts`, `.html`, `.css`, `.java`, `.cpp`, `.php`, etc.).
* Calcul de la part relative de chaque langage (% du total des fichiers sources et volume en octets).
* Graphique interactif en anneau (Doughnut Chart) propulsé par **Chart.js**.

###  4. Dépendances Logicielles
* Détection automatique des fichiers manifestes standards :
  * **Python :** `requirements.txt`, `Pipfile`, `setup.py`
  * **JavaScript / Node.js :** `package.json` (`dependencies` et `devDependencies`)
  * **Java :** `pom.xml` (balises `<artifactId>`)
  * **PHP :** `composer.json` (section `require`)
* Extraction et affichage propre des paquets sans nécessiter d'installation locale.

###  5. Statistiques & Activité Git
* Dernier commit : auteur, date formatée, message et empreinte SHA courte.
* Volume global estimé de commits, nombre de branches et contributeurs.
* Graphique en barres Chart.js illustrant la dynamique temporelle des commits récents par période.
* Cartes des contributeurs principaux avec liens vers leurs profils GitHub.

###  6. Fichiers Nécessitant une Attention Particulière (Complexité)
Détection de fichiers potentiellement complexes selon des seuils clairs et ajustables :
* **Fichiers longs :** plus de **200 lignes**.
* **Fichiers à forte densité de fonctions :** plus de **10 fonctions** déclarées.
* **Fichiers à forte densité de classes :** plus de **5 classes** déclarées.

###  7. Audit de la Documentation README
* Vérification de la présence d'un fichier `README.md` à la racine.
* Décompte du nombre de lignes.
* Détection automatique des sections clés grâce à des expressions régulières bilingues (FR/EN) :
  * Section **Installation** (Instructions de configuration).
  * Section **Utilisation** (Guide de démarrage et exemples).
  * Section **Contribution** (Directives de développement collaboratif).

###  8. Rapport CodeLens Factuel
* Liste de contrôle récapitulative (structure, langages, dépendances, statistiques Git, documentation).
* Synthèse factuelle générée dynamiquement sous forme de puces informatives.
* **Aucune notation arbitraire :** respect strict d'une démarche scientifique d'analyse de données.

###  9. Historique Persistant SQLite
* Enregistrement automatique de chaque analyse réussie dans la base SQLite locale `codelens.db`.
* Page dédiée `/history` avec recherche et filtrage en direct en JavaScript Vanilla.
* Rechargement instantané d'une analyse passée sans nouvel appel à l'API GitHub.
* Suppression d'une entrée d'historique en un clic.

---

## 4. Technologies Utilisées

| Composant | Technologie | Justification pour le niveau L3 |
| :--- | :--- | :--- |
| **Backend** | Python 3.12 & Flask | Syntaxe claire, framework léger, idéal pour comprendre le routage et le cycle requête/réponse HTTP. |
| **Base de Données** | SQLite 3 | Base relationnelle intégrée nativement à Python, sans configuration de serveur externe. |
| **API Web** | GitHub REST API v3 | Standard de l'industrie, documentation exhaustive, format JSON propre. |
| **Requêtes HTTP** | `requests` | Bibliothèque Python de référence pour les appels HTTP, fiable et expressive. |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Code accessible, maintenable sans bundler complexe (évite la complexité de React/Webpack). |
| **Visualisation** | Chart.js 4.4 | Bibliothèque de graphiques vectoriels sur canvas HTML5, responsive et personnalisable. |
| **Tests** | `pytest` | Standard Python moderne pour les tests unitaires et fonctionnels. |

---

## 5. Architecture du Projet

```text
codelens/
│
├── app.py                      # Contrôleur principal Flask et définition des routes
├── config.py                   # Configuration centralisée (seuils, extensions, chemins)
├── requirements.txt            # Liste des dépendances Python
├── .env.example                # Modèle de configuration des variables d'environnement
├── .gitignore                  # Exclusion des fichiers temporaires, caches et secrets
├── README.md                   # Documentation complète du projet
│
├── services/                   # Couche logique métier et services externes
│   ├── __init__.py
│   ├── github_service.py       # Client API GitHub (appels HTTP, en-têtes Link, pagination, erreurs)
│   ├── analyzer.py             # Algorithmes de structure, détection de langages, complexité, README
│   ├── dependency_analyzer.py  # Analyse et extraction des manifestes de dépendances
│   └── git_analyzer.py         # Traitement statistique des commits et activité temporelle
│
├── database/                   # Couche d'accès aux données (DAL)
│   ├── __init__.py
│   ├── database.py             # Fonctions CRUD SQLite (init_db, save, get_recent, delete)
│   └── codelens.db             # Base SQLite locale créée automatiquement
│
├── templates/                  # Vues HTML5 rendues par le moteur Jinja2
│   ├── base.html               # Layout commun (navbar, messages flash, footer, scripts)
│   ├── index.html              # Accueil avec champ de recherche et suggestions rapides
│   ├── analysis.html           # Tableau de bord complet de restitution de l'analyse
│   ├── history.html            # Tableau d'historique avec recherche dynamique
│   └── about.html              # Page de présentation académique et argumentaire
│
├── static/                     # Fichiers statiques servis au client
│   ├── css/
│   │   └── style.css           # Feuille de style moderne, responsive et soignée
│   └── js/
│       ├── main.js             # Interactions Vanilla JS (alertes, loaders)
│       └── charts.js           # Configuration et rendu des graphiques Chart.js
│
└── tests/                      # Tests automatisés
    ├── __init__.py
    ├── test_analyzer.py        # 10 tests unitaires sur les règles d'analyse et algorithmes
    └── test_routes.py          # 6 tests fonctionnels sur les routes Flask et SQLite
```

---

## 6. Installation

### Prérequis
* **Python 3.10 ou supérieur** installé sur votre machine.
* `git` pour cloner le projet.

### Procédure pas à pas

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/votre-compte/codelens.git
   cd codelens
   ```

2. **Créer et activer un environnement virtuel :**
   * **Sous Windows (PowerShell) :**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   * **Sous Linux / macOS :**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optionnel mais conseillé) Configurer un token GitHub :**
   Pour augmenter la limite de requêtes de l'API GitHub de 60 requêtes/h à 5 000 requêtes/h :
   ```bash
   cp .env.example .env
   ```
   Éditez `.env` et renseignez votre token personnel GitHub :
   ```env
   GITHUB_TOKEN=ghp_votreTokenGitHubPersonnel
   ```

---

## 7. Lancement du Projet

Démarrez le serveur de développement Flask avec :

```bash
python app.py
```

Rendez-vous ensuite dans votre navigateur web à l'adresse suivante :
 **http://127.0.0.1:5000**

---

## 8. Utilisation

1. Sur la page d'accueil, saisissez l'URL d'un dépôt GitHub public.  
   *Exemples valides :*
   * `https://github.com/pallets/flask`
   * `https://github.com/psf/requests`
   * `expressjs/express`
   * Ou cliquez directement sur l'une des **suggestions de démonstration** proposées.
2. Cliquez sur **Analyser le dépôt**.
3. Consultez les différentes cartes :
   * **Rapport CodeLens :** bilan factuel et points d'attention.
   * **Langages :** visualisation en anneau Chart.js et tableau des proportions.
   * **Arborescence :** exploration de la structure des dossiers.
   * **Activité Git :** commits récents et contributeurs majeurs.
   * **Fichiers complexes :** alerte sur les fichiers dépassant 200 lignes ou 10 fonctions.
   * **Dépendances & README :** audit des bibliothèques et de la documentation.
4. Rendez-vous dans l'onglet **Historique** pour revoir à tout moment les dépôts déjà analysés.

---

## 9. Tests Automatisés

Le projet intègre une suite de tests unitaires et fonctionnels avec `pytest`.

Pour lancer les tests :

```bash
pytest tests/ -v
```

### Couverture des tests réalisés :
* ✅ Extraction et validation des formats d'URL GitHub (URL complète, avec `.git`, slug court).
* ✅ Détection des extensions et calcul précis des pourcentages de langages.
* ✅ Algorithme de détection des fichiers complexes (lignes, fonctions, classes).
* ✅ Parsing des fichiers `requirements.txt` (Python), `package.json` (JavaScript), `pom.xml` (Java) et `composer.json` (PHP).
* ✅ Détection des sections bilingues dans le README (Installation, Utilisation, Contribution).
* ✅ Calcul de la profondeur d'arborescence et génération de l'arbre ASCII.
* ✅ Traitement de l'historique des commits et regroupement chronologique mensuel.
* ✅ Cohérence factuelle du rapport CodeLens.
* ✅ Codes HTTP 200 sur les routes `/`, `/about`, `/history`.
* ✅ Gestion des redirections et erreurs d'URL invalides.
* ✅ Persistance SQLite de bout en bout (insertion, lecture, mise à jour, suppression).

---



---



