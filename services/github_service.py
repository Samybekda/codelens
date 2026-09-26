"""
Service d'interaction avec l'API REST publique de GitHub.
Gère l'authentification optionnelle, les requêtes HTTP (requests),
la pagination et les erreurs de réseau / quotas.
"""
import re
import base64
import requests
from config import Config

class GitHubServiceError(Exception):
    """Exception personnalisée pour les erreurs de l'API GitHub."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class GitHubService:
    """Classe encapsulant les appels à l'API REST de GitHub."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token=None):
        self.token = token or Config.GITHUB_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeLens-L3-MIAGE-Toulouse"
        })
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"

    @staticmethod
    def parse_repo_url(url_or_slug):
        """
        Extrait le couple (propriétaire, nom_du_dépôt) à partir d'une URL GitHub ou d'un slug.
        Exemples acceptés :
          - https://github.com/pallets/flask
          - https://github.com/pallets/flask.git
          - github.com/pallets/flask/
          - pallets/flask
        
        :return: (owner, repo) ou (None, None) si format invalide
        """
        if not url_or_slug:
            return None, None

        cleaned = url_or_slug.strip()
        # Supprimer le .git éventuel à la fin
        if cleaned.endswith(".git"):
            cleaned = cleaned[:-4]

        # Expression régulière pour capturer owner et repo
        pattern = r"^(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)/?$"
        match = re.match(pattern, cleaned)
        if match:
            return match.group(1), match.group(2)

        # Format slug direct : "owner/repo"
        slug_pattern = r"^([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)$"
        slug_match = re.match(slug_pattern, cleaned)
        if slug_match:
            return slug_match.group(1), slug_match.group(2)

        return None, None

    def _make_request(self, endpoint, params=None, headers=None, raw=False):
        """
        Effectue une requête GET sécurisée vers l'API GitHub avec gestion d'erreurs.
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        req_headers = {}
        if headers:
            req_headers.update(headers)
        if raw:
            req_headers["Accept"] = "application/vnd.github.v3.raw"

        try:
            response = self.session.get(url, params=params, headers=req_headers, timeout=12)
            
            # Gestion des erreurs de statut HTTP
            if response.status_code == 404:
                raise GitHubServiceError("Dépôt introuvable ou privé. Vérifiez l'orthographe de l'URL.", status_code=404)
            elif response.status_code == 403:
                # Quota GitHub dépassé
                rate_limit_reset = response.headers.get("X-RateLimit-Reset")
                msg = "Quota de l'API GitHub dépassé (60 requêtes/heure pour les appels non-authentifiés)."
                if not self.token:
                    msg += " Astuce : configurez un GITHUB_TOKEN dans le fichier .env pour bénéficier de 5000 requêtes/heure."
                raise GitHubServiceError(msg, status_code=403)
            elif response.status_code >= 400:
                raise GitHubServiceError(f"Erreur API GitHub ({response.status_code}) : {response.reason}", status_code=response.status_code)

            if raw:
                return response.text
            return response.json(), response.headers

        except requests.exceptions.Timeout:
            raise GitHubServiceError("Délai d'attente dépassé lors de la connexion à GitHub.")
        except requests.exceptions.ConnectionError:
            raise GitHubServiceError("Erreur de connexion : impossible de joindre les serveurs GitHub.")
        except requests.exceptions.RequestException as e:
            raise GitHubServiceError(f"Erreur réseau inattendue : {str(e)}")

    def get_repo_details(self, owner, repo):
        """
        Récupère les informations générales du dépôt :
        nom, description, étoiles, forks, dates, branche par défaut...
        """
        data, _ = self._make_request(f"repos/{owner}/{repo}")
        return {
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "owner": data.get("owner", {}).get("login"),
            "owner_avatar": data.get("owner", {}).get("avatar_url"),
            "owner_url": data.get("owner", {}).get("html_url"),
            "description": data.get("description") or "Aucune description fournie.",
            "html_url": data.get("html_url"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "pushed_at": data.get("pushed_at"),
            "stars_count": data.get("stargazers_count", 0),
            "forks_count": data.get("forks_count", 0),
            "watchers_count": data.get("subscribers_count", data.get("watchers_count", 0)),
            "open_issues_count": data.get("open_issues_count", 0),
            "default_branch": data.get("default_branch", "main"),
            "visibility": "Public" if not data.get("private") else "Privé",
            "size_kb": data.get("size", 0),
            "license": data.get("license", {}).get("name") if data.get("license") else "Non spécifiée"
        }

    def get_git_tree(self, owner, repo, branch="main"):
        """
        Récupère l'arborescence complète du dépôt via l'endpoint Git Trees (récursif).
        Permet d'obtenir tous les fichiers et dossiers en une seule requête HTTP.
        """
        try:
            data, _ = self._make_request(f"repos/{owner}/{repo}/git/trees/{branch}", params={"recursive": "1"})
            return data.get("tree", []), data.get("truncated", False)
        except GitHubServiceError as e:
            # Si la branche principale n'a pas pu être trouvée avec 'main', tester 'master'
            if e.status_code == 404 and branch == "main":
                data, _ = self._make_request(f"repos/{owner}/{repo}/git/trees/master", params={"recursive": "1"})
                return data.get("tree", []), data.get("truncated", False)
            raise

    def get_commits_info(self, owner, repo):
        """
        Récupère les commits récents et estime le nombre total de commits
        en utilisant l'en-tête de pagination 'Link'.
        """
        try:
            commits, headers = self._make_request(f"repos/{owner}/{repo}/commits", params={"per_page": 30})
            
            # Détection du nombre total via Link header (ex: rel="last")
            total_commits = len(commits)
            link_header = headers.get("Link", "")
            if link_header and 'rel="last"' in link_header:
                # Extraire le numéro de la dernière page
                match = re.search(r'[?&]page=(\d+)[^>]*>;\s*rel="last"', link_header)
                if match:
                    last_page = int(match.group(1))
                    # Estimation : (dernière page - 1) * 30 + éléments de la dernière page
                    # Pour être exact sans faire d'appel supplémentaire : au moins last_page * 30
                    total_commits = last_page * 30

            return commits, total_commits
        except Exception:
            return [], 0

    def get_contributors_info(self, owner, repo):
        """
        Récupère la liste des principaux contributeurs et le décompte total.
        """
        try:
            contributors, headers = self._make_request(f"repos/{owner}/{repo}/contributors", params={"per_page": 10})
            total_contributors = len(contributors)
            link_header = headers.get("Link", "")
            if link_header and 'rel="last"' in link_header:
                match = re.search(r'[?&]page=(\d+)[^>]*>;\s*rel="last"', link_header)
                if match:
                    total_contributors = int(match.group(1)) * 10
            return contributors, total_contributors
        except Exception:
            return [], 0

    def get_branches_info(self, owner, repo):
        """
        Récupère les branches et leur nombre total.
        """
        try:
            branches, headers = self._make_request(f"repos/{owner}/{repo}/branches", params={"per_page": 10})
            total_branches = len(branches)
            link_header = headers.get("Link", "")
            if link_header and 'rel="last"' in link_header:
                match = re.search(r'[?&]page=(\d+)[^>]*>;\s*rel="last"', link_header)
                if match:
                    total_branches = int(match.group(1)) * 10
            return [b.get("name") for b in branches], total_branches
        except Exception:
            return [], 0

    def get_file_content(self, owner, repo, path):
        """
        Récupère le contenu brut textuel d'un fichier du dépôt.
        """
        try:
            content = self._make_request(f"repos/{owner}/{repo}/contents/{path}", raw=True)
            return content
        except Exception:
            return None
