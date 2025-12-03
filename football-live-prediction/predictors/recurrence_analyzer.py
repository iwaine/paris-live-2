"""
RecurrenceAnalyzer - Analyse les données historiques match par match
Calcule: distribution par minute, écart-type, récence, etc.
"""

import json
import statistics
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from loguru import logger
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.database_manager import DatabaseManager


class RecurrenceAnalyzer:
    """Analyse la récurrence des buts par minute exacte"""

    def __init__(self, db_path: str = "data/predictions.db"):
        self.db = DatabaseManager(db_path)
        self.recent_window = 4  # Derniers 4 matchs = "récent"
        logger.info("RecurrenceAnalyzer initialized")

    def get_interval_from_minute(self, minute: int) -> Optional[str]:
        """Convertit une minute en intervalle 15-min"""
        if 31 <= minute <= 45:
            return "31-45"
        elif 76 <= minute <= 90:
            return "76-90"
        else:
            return None

    def analyze_team_venue_interval(
        self,
        team_name: str,
        venue: str,  # "home" ou "away"
        interval_name: str,  # "31-45" ou "76-90"
    ) -> Dict:
        """
        Analyse complète d'une équipe dans un contexte spécifique

        Returns:
        {
            "team_name": "Arsenal",
            "venue": "home",
            "interval_name": "31-45",
            "overall": {
                "total_matches": 42,
                "goals_scored": 28,
                "goals_conceded": 8,
                "avg_minute": 37.2,
                "std_dev": 5.3,
                "min_minute": 31,
                "max_minute": 45,
                "minute_distribution": {"31": 0, "32": 1, ..., "45": 0}
            },
            "recent": {
                "matches": 4,
                "goals_scored": 3,
                "goals_conceded": 1,
                "avg_minute": 36.8,
                "std_dev": 4.1,
                "minute_distribution": {"35": 1, "38": 1, "40": 1}
            }
        }
        """

        # 1. Récupérer tous les matchs pertinents
        if venue == "home":
            matches = self.db.get_match_history(home_team=team_name)
        else:  # away
            matches = self.db.get_match_history(away_team=team_name)

        if not matches:
            logger.warning(f"No matches found for {team_name} ({venue})")
            return None

        # 2. Extraire les buts dans cet intervalle
        goals_scored = []  # Minutes where team scored
        goals_conceded = []  # Minutes where team conceded

        for match in matches:
            match_id = match['id']
            goals_data = self.db.get_goals_for_match(match_id)

            for goal in goals_data:
                goal_minute = goal['minute']

                # Vérifier que le but est dans cet intervalle
                if self.get_interval_from_minute(goal_minute) != interval_name:
                    continue

                # Déterminer qui a marqué et qui a encaissé
                if venue == "home":
                    if goal['team'] == "home":
                        goals_scored.append(goal_minute)
                    else:
                        goals_conceded.append(goal_minute)
                else:  # away
                    if goal['team'] == "away":
                        goals_scored.append(goal_minute)
                    else:
                        goals_conceded.append(goal_minute)

        # 3. Calculer stats globales
        overall_stats = self._calculate_stats(goals_scored, goals_conceded, len(matches))

        # 4. Calculer stats récentes (derniers 4 matchs)
        recent_matches = matches[:self.recent_window]
        recent_goals_scored = []
        recent_goals_conceded = []

        for match in recent_matches:
            match_id = match['id']
            goals_data = self.db.get_goals_for_match(match_id)

            for goal in goals_data:
                goal_minute = goal['minute']

                if self.get_interval_from_minute(goal_minute) != interval_name:
                    continue

                if venue == "home":
                    if goal['team'] == "home":
                        recent_goals_scored.append(goal_minute)
                    else:
                        recent_goals_conceded.append(goal_minute)
                else:  # away
                    if goal['team'] == "away":
                        recent_goals_scored.append(goal_minute)
                    else:
                        recent_goals_conceded.append(goal_minute)

        recent_stats = self._calculate_stats(recent_goals_scored, recent_goals_conceded, len(recent_matches))

        # 5. Compiler le résultat
        result = {
            "team_name": team_name,
            "venue": venue,
            "interval_name": interval_name,
            "overall": overall_stats,
            "recent": recent_stats
        }

        return result

    def _calculate_stats(
        self,
        goals_scored: List[int],
        goals_conceded: List[int],
        total_matches: int
    ) -> Dict:
        """Calcule les stats pour une liste de minutes"""

        # Distribution par minute
        minute_distribution = self._build_minute_distribution(goals_scored)

        # Statistiques
        stats = {
            "total_matches": total_matches,
            "goals_scored": len(goals_scored),
            "goals_conceded": len(goals_conceded),
            "minute_distribution": minute_distribution,
        }

        # Moyenne et écart-type (si buts marqués)
        if goals_scored:
            stats["avg_minute"] = round(statistics.mean(goals_scored), 2)
            stats["min_minute"] = min(goals_scored)
            stats["max_minute"] = max(goals_scored)

            if len(goals_scored) > 1:
                stats["std_dev"] = round(statistics.stdev(goals_scored), 2)
            else:
                stats["std_dev"] = 0.0
        else:
            stats["avg_minute"] = None
            stats["std_dev"] = None
            stats["min_minute"] = None
            stats["max_minute"] = None

        return stats

    def _build_minute_distribution(self, minutes: List[int]) -> Dict[str, int]:
        """Crée une distribution {minute: count}"""
        distribution = defaultdict(int)

        for minute in minutes:
            distribution[str(minute)] += 1

        return dict(distribution)

    def save_analysis_to_db(self, analysis: Dict) -> bool:
        """Sauvegarde l'analyse dans goal_stats"""
        if not analysis:
            return False

        overall = analysis["overall"]
        recent = analysis["recent"]

        stats_data = {
            "team_name": analysis["team_name"],
            "venue": analysis["venue"],
            "interval_name": analysis["interval_name"],

            # Overall
            "total_matches": overall["total_matches"],
            "goals_scored": overall["goals_scored"],
            "goals_conceded": overall["goals_conceded"],
            "avg_minute": overall.get("avg_minute"),
            "std_dev": overall.get("std_dev"),
            "min_minute": overall.get("min_minute"),
            "max_minute": overall.get("max_minute"),

            # Recent
            "recent_matches": recent["total_matches"],
            "recent_goals": recent["goals_scored"],
            "recent_avg_minute": recent.get("avg_minute"),
            "recent_std_dev": recent.get("std_dev"),

            # JSON distributions
            "minute_distribution": json.dumps(overall["minute_distribution"]),
            "recent_minute_distribution": json.dumps(recent["minute_distribution"])
        }

        return self.db.upsert_goal_stats(stats_data)

    def analyze_and_save_all(self, teams: List[str], intervals: List[str] = None) -> Dict:
        """
        Analyse et sauvegarde les stats pour toutes les combinaisons

        Args:
            teams: Liste des équipes
            intervals: ["31-45", "76-90"] par défaut
        """
        if intervals is None:
            intervals = ["31-45", "76-90"]

        results = {}

        for team in teams:
            for venue in ["home", "away"]:
                for interval in intervals:
                    logger.info(f"Analyzing {team} ({venue}) [{interval}]...")

                    analysis = self.analyze_team_venue_interval(team, venue, interval)

                    if analysis:
                        self.save_analysis_to_db(analysis)
                        key = f"{team}_{venue}_{interval}"
                        results[key] = analysis
                    else:
                        logger.warning(f"No data for {team} ({venue}) [{interval}]")

        logger.success(f"✓ Analysis complete: {len(results)} configurations saved")
        return results

    def get_analysis(self, team_name: str, venue: str, interval_name: str) -> Dict:
        """Récupère l'analyse stockée en BD"""
        return self.db.get_goal_stats(team_name, venue, interval_name)


if __name__ == "__main__":
    analyzer = RecurrenceAnalyzer()

    # Test avec Arsenal home [31-45]
    print("\n📊 Test Analysis:")
    analysis = analyzer.analyze_team_venue_interval("Arsenal", "home", "31-45")

    if analysis:
        print(json.dumps(analysis, indent=2))

        # Sauvegarder en BD
        if analyzer.save_analysis_to_db(analysis):
            print("\n✅ Analysis saved to database")
