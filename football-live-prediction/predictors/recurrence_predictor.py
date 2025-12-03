"""
RecurrencePredictor - Couple données live + données historiques
Prédit le danger score avec minutage précis basé sur la récurrence
"""

import json
import math
from typing import Dict, Optional, Tuple
from loguru import logger
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.database_manager import DatabaseManager


class RecurrencePredictor:
    """Prédit le danger score en couplant live data + historique"""

    def __init__(self, db_path: str = "data/predictions.db"):
        self.db = DatabaseManager(db_path)
        self.logger = logger
        logger.info("RecurrencePredictor initialized")

    def predict_at_minute(
        self,
        home_team: str,
        away_team: str,
        current_minute: int,
        home_possession: Optional[float] = None,  # 0.0-1.0
        away_possession: Optional[float] = None,
        home_shots: Optional[int] = None,
        away_shots: Optional[int] = None,
        home_sot: Optional[int] = None,
        away_sot: Optional[int] = None,
    ) -> Dict:
        """
        Prédit le danger score à une minute donnée

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur
            current_minute: Minute actuelle (ex: 38)
            home_possession, away_possession: Stats live possession
            home_shots, away_shots: Stats live tirs
            home_sot, away_sot: Stats live tirs cadrés

        Returns:
        {
            "current_minute": 38,
            "interval": "31-45",
            "danger_score_percentage": 67.3,
            "home_goal_probability": 0.45,
            "away_goal_probability": 0.22,
            "optimal_minute_range": "31-42",
            "data_summary": {
                "home_matches": 42,
                "home_recent": 4,
                "away_matches": 35,
                "away_recent": 4
            },
            "details": {...}
        }
        """

        # 1. Déterminer l'intervalle
        interval = self._get_interval(current_minute)
        if not interval:
            return {
                "error": f"Minute {current_minute} is not in priority intervals [31-45] or [76-90]",
                "current_minute": current_minute
            }

        # 2. Récupérer stats historiques
        home_stats = self.db.get_goal_stats(home_team, "home", interval)
        away_stats = self.db.get_goal_stats(away_team, "away", interval)

        if not home_stats or not away_stats:
            return {
                "error": f"Missing historical data for {home_team} (home) or {away_team} (away) in {interval}",
                "current_minute": current_minute,
                "interval": interval
            }

        # 3. Calculer probabilités
        home_goal_prob = self._calculate_goal_probability(
            current_minute, home_stats, home_possession or 0.5
        )
        away_goal_prob = self._calculate_goal_probability(
            current_minute, away_stats, away_possession or 0.5
        )

        # 4. Danger score combiné (70/30 rule)
        danger_score = (home_goal_prob * 0.70) + (away_goal_prob * 0.30)
        danger_percentage = round(danger_score * 100, 1)

        # 5. Déterminer fenêtre optimale (avg ± std_dev)
        optimal_range = self._get_optimal_minute_range(home_stats, away_stats)

        # 6. Compiler résultat
        result = {
            "current_minute": current_minute,
            "interval": interval,
            "danger_score_percentage": danger_percentage,
            "home_goal_probability": round(home_goal_prob * 100, 1),
            "away_goal_probability": round(away_goal_prob * 100, 1),
            "optimal_minute_range": optimal_range,
            "data_summary": {
                "home_team": home_team,
                "home_matches_total": home_stats.get('total_matches'),
                "home_matches_recent": home_stats.get('recent_matches'),
                "away_team": away_team,
                "away_matches_total": away_stats.get('total_matches'),
                "away_matches_recent": away_stats.get('recent_matches'),
            },
            "details": {
                "home": self._format_stats(home_stats),
                "away": self._format_stats(away_stats),
            }
        }

        return result

    def _get_interval(self, minute: int) -> Optional[str]:
        """Détermine l'intervalle d'une minute"""
        if 31 <= minute <= 45:
            return "31-45"
        elif 76 <= minute <= 90:
            return "76-90"
        return None

    def _calculate_goal_probability(
        self,
        current_minute: int,
        stats: Dict,
        possession: float
    ) -> float:
        """
        Calcule probabilité de but basé sur:
        1. Base rate (buts/match historique)
        2. Minute factor (timing - distribution exacte)
        3. Possession factor (live data)
        4. Récence boost
        """

        # 1. Base rate (buts par match en cette période)
        base_rate = stats['goals_scored'] / max(stats['total_matches'], 1)

        # 2. Minute factor (fenêtre ±σ)
        avg_minute = stats.get('avg_minute')
        std_dev = stats.get('std_dev', 0)

        if avg_minute is None:
            minute_factor = 0.1  # Très faible si aucune donnée
        else:
            # Fenêtre: avg ± std_dev
            window_min = max(31, avg_minute - std_dev)
            window_max = min(90, avg_minute + std_dev)

            if window_min <= current_minute <= window_max:
                # On est dans la fenêtre optimale
                # Chercher le ratio de buts à cette minute exacte
                minute_dist = json.loads(stats.get('minute_distribution', '{}'))
                buts_this_minute = int(minute_dist.get(str(current_minute), 0))
                total_buts = stats['goals_scored']

                if total_buts > 0:
                    exact_minute_ratio = buts_this_minute / total_buts
                    minute_factor = 0.5 + (exact_minute_ratio * 0.5)  # 0.5-1.0
                else:
                    minute_factor = 0.7  # Dans la fenêtre mais pas de données
            else:
                # En dehors de la fenêtre
                # Distance à la fenêtre
                if current_minute < window_min:
                    distance = window_min - current_minute
                else:
                    distance = current_minute - window_max

                # Décroissance rapide (exponentielle)
                minute_factor = math.exp(-distance / 5)  # Moitié tous les 3.5 min

        # 3. Possession factor (boost si possession élevée)
        possession_factor = 0.7 + (possession * 0.3)  # 0.7-1.0

        # 4. Récence boost
        recent_buts = stats.get('recent_goals', 0)
        recent_matches = stats.get('recent_matches', 1)
        recent_rate = recent_buts / max(recent_matches, 1)

        if recent_rate > base_rate * 1.2:
            recency_boost = 1.2  # En forme
        elif recent_rate > base_rate:
            recency_boost = 1.1
        else:
            recency_boost = 1.0

        # Combinaison finale
        final_prob = base_rate * minute_factor * possession_factor * recency_boost

        # Clamp entre 0 et 1
        return min(1.0, max(0.0, final_prob))

    def _get_optimal_minute_range(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> str:
        """Détermine la fenêtre optimale [avg ± σ]"""
        # Moyenne des deux équipes
        home_avg = home_stats.get('avg_minute')
        home_std = home_stats.get('std_dev', 0)
        away_avg = away_stats.get('avg_minute')
        away_std = away_stats.get('std_dev', 0)

        if home_avg is None or away_avg is None:
            return "N/A"

        avg = (home_avg + away_avg) / 2
        std = (home_std + away_std) / 2

        window_min = max(31, int(avg - std))
        window_max = min(90, int(avg + std))

        return f"{window_min}-{window_max}"

    def _format_stats(self, stats: Dict) -> Dict:
        """Formate les stats pour affichage"""
        minute_dist = json.loads(stats.get('minute_distribution', '{}'))
        recent_dist = json.loads(stats.get('recent_minute_distribution', '{}'))

        return {
            "goals_scored": stats['goals_scored'],
            "goals_conceded": stats['goals_conceded'],
            "avg_minute": stats.get('avg_minute'),
            "std_dev": stats.get('std_dev'),
            "total_matches": stats['total_matches'],
            "recent_matches": stats['recent_matches'],
            "recent_goals": stats['recent_goals'],
            "minute_distribution": minute_dist,
            "recent_minute_distribution": recent_dist,
        }


if __name__ == "__main__":
    predictor = RecurrencePredictor()

    # Test: Arsenal (home) vs Chelsea (away) @ minute 38
    print("\n🎯 Test Prediction:")
    prediction = predictor.predict_at_minute(
        home_team="Arsenal",
        away_team="Chelsea",
        current_minute=38,
        home_possession=0.62,
        away_possession=0.38,
        home_shots=3,
        away_shots=1
    )

    if "error" not in prediction:
        print(f"\nDanger Score: {prediction['danger_score_percentage']}%")
        print(f"Home Goal: {prediction['home_goal_probability']}%")
        print(f"Away Goal: {prediction['away_goal_probability']}%")
        print(f"Optimal Range: {prediction['optimal_minute_range']}")
        print(f"Data: {prediction['data_summary']}")
    else:
        print(f"❌ Error: {prediction['error']}")
