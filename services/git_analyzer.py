"""
Module d'analyse des métriques Git.
Extrait les données de commits, l'activité temporelle récente,
les informations d'auteurs et prépare les séries pour Chart.js.
"""
from datetime import datetime
from collections import Counter

class GitAnalyzer:
    """Analyseur de métriques et d'activité Git."""

    @staticmethod
    def process_commits(commits, total_commits_estimate=0):
        """
        Traite la liste des commits récents récupérés depuis l'API GitHub.
        Extrait :
        - Les infos du dernier commit (auteur, date, message)
        - La répartition mensuelle de l'activité pour Chart.js
        - La liste formatée des derniers commits
        """
        if not commits:
            return {
                "latest_commit": None,
                "commit_count": total_commits_estimate or 0,
                "monthly_activity": {"labels": [], "data": []},
                "recent_commits_list": []
            }

        latest_raw = commits[0]
        commit_obj = latest_raw.get("commit", {})
        author_obj = commit_obj.get("author", {})
        
        # Date du dernier commit
        raw_date = author_obj.get("date", "")
        formatted_date = ""
        if raw_date:
            try:
                dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%d/%m/%Y à %H:%M")
            except Exception:
                formatted_date = raw_date

        latest_commit = {
            "author_name": author_obj.get("name", "Inconnu"),
            "author_email": author_obj.get("email", ""),
            "author_avatar": latest_raw.get("author", {}).get("avatar_url") if latest_raw.get("author") else None,
            "date": formatted_date,
            "raw_date": raw_date,
            "message": commit_obj.get("message", "").split("\n")[0],  # Première ligne
            "sha": latest_raw.get("sha", "")[:7],
            "html_url": latest_raw.get("html_url", "")
        }

        # Calcul de l'activité temporelle (commits par mois / période)
        # Ex: "2026-09", "2026-08", etc.
        months_counter = Counter()
        recent_commits_list = []

        for c in commits:
            c_author = c.get("commit", {}).get("author", {})
            c_date_raw = c_author.get("date", "")
            if c_date_raw:
                try:
                    month_key = c_date_raw[:7]  # AAAA-MM
                    months_counter[month_key] += 1
                except Exception:
                    pass

            recent_commits_list.append({
                "sha": c.get("sha", "")[:7],
                "author": c_author.get("name", "Inconnu"),
                "date": c_date_raw[:10] if len(c_date_raw) >= 10 else "",
                "message": c.get("commit", {}).get("message", "").split("\n")[0]
            })

        # Trier les mois par ordre chronologique
        sorted_months = sorted(months_counter.keys())
        monthly_labels = []
        monthly_values = []
        for m in sorted_months:
            try:
                dt = datetime.strptime(m, "%Y-%m")
                # Format plus lisible ex: "Sept. 2026"
                mois_fr = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]
                label = f"{mois_fr[dt.month - 1]} {dt.year}"
            except Exception:
                label = m
            monthly_labels.append(label)
            monthly_values.append(months_counter[m])

        return {
            "latest_commit": latest_commit,
            "commit_count": max(total_commits_estimate, len(commits)),
            "monthly_activity": {
                "labels": monthly_labels,
                "data": monthly_values
            },
            "recent_commits_list": recent_commits_list[:8]
        }
