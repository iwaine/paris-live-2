#!/usr/bin/env python3
"""
Préditeur de probabilité de but EN DIRECT
Prédit si "il y aura un but" (peu importe qui marque) basé sur les données historiques + live
"""

import statistics
from typing import Dict, Optional, Tuple
from datetime import datetime


class LiveGoalProbabilityPredictor:
    """Prédit la probabilité qu'un but soit marqué dans les prochaines minutes"""

    def __init__(self, db_manager):
        """
        Args:
            db_manager: Instance de DatabaseManager avec goal_stats
        """
        self.db = db_manager

    def predict_goal_probability(
        self,
        home_team: str,
        away_team: str,
        current_minute: int,
        home_possession: Optional[float],
        away_possession: Optional[float],
        home_attacks: Optional[int],
        away_attacks: Optional[int],
        home_dangerous_attacks: Optional[int],
        away_dangerous_attacks: Optional[int],
        home_shots_on_target: Optional[int],
        away_shots_on_target: Optional[int],
        home_red_cards: int = 0,
        away_red_cards: int = 0,
        score_home: int = 0,
        score_away: int = 0,
        last_5_min_events: Optional[Dict] = None,  # {'buts': N, 'tirs': N}
    ) -> Dict:
        """
        Prédit la probabilité qu'un but soit marqué.

        Args:
            home_team: Équipe à domicile
            away_team: Équipe à l'extérieur
            current_minute: Minute courante du match
            home_possession: Possession % domicile
            away_possession: Possession % extérieur
            home_attacks: Attaques domicile
            away_attacks: Attaques extérieur
            home_dangerous_attacks: Attaques dangereuses domicile
            away_dangerous_attacks: Attaques dangereuses extérieur
            home_shots_on_target: Tirs cadrés domicile
            away_shots_on_target: Tirs cadrés extérieur
            home_red_cards: Cartons rouges domicile
            away_red_cards: Cartons rouges extérieur
            score_home: Score courant domicile
            score_away: Score courant extérieur
            last_5_min_events: Dict avec 'buts' et 'tirs' des 5 dernières minutes

        Returns:
            Dict avec:
                - goal_probability: float (0-100%) probabilité de but
                - danger_level: str ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
                - details: dict avec breakdowns
        """

        # 1. BASE RATE: moyenne historique de buts à cette minute
        interval_name = self._get_interval_name(current_minute)
        base_rate = self._calculate_base_rate(interval_name)

        # 2. FACTEUR POSSESSION
        possession_factor = self._calculate_possession_factor(home_possession, away_possession)

        # 3. FACTEUR ATTAQUES DANGEREUSES
        dangerous_attacks_ratio_home = self._safe_ratio(home_dangerous_attacks, home_attacks)
        dangerous_attacks_ratio_away = self._safe_ratio(away_dangerous_attacks, away_attacks)
        dangerous_attacks_factor = max(dangerous_attacks_ratio_home, dangerous_attacks_ratio_away)
        dangerous_attacks_factor = min(1.5, dangerous_attacks_factor * 2)  # capper à 1.5

        # 4. FACTEUR TIRS CADRÉS
        shots_on_target_factor = self._calculate_shots_on_target_factor(
            home_shots_on_target, away_shots_on_target
        )

        # 5. FACTEUR MOMENTUM (dernières 5 minutes)
        momentum_factor = self._calculate_momentum_factor(last_5_min_events)

        # 6. FACTEUR CARTE ROUGE (réduction si rouge)
        red_card_factor = self._calculate_red_card_factor(home_red_cards, away_red_cards)

        # 7. FACTEUR SATURATION (si déjà beaucoup de buts)
        saturation_factor = self._calculate_saturation_factor(score_home, score_away, interval_name)

        # 8. FACTEUR SCORE DIFFERENTIAL (menée = plus d'urgence offensive)
        score_diff_factor = self._calculate_score_differential_factor(score_home, score_away)

        # FORMULE FINALE
        goal_probability = (
            base_rate
            * possession_factor
            * dangerous_attacks_factor
            * shots_on_target_factor
            * momentum_factor
            * red_card_factor
            * saturation_factor
            * score_diff_factor
        )

        # Capper à 95% max (jamais 100%)
        goal_probability = min(0.95, max(0.05, goal_probability))

        # Déterminer le niveau de danger
        danger_level = self._get_danger_level(goal_probability)

        return {
            "goal_probability": goal_probability * 100,  # en %
            "danger_level": danger_level,
            "details": {
                "base_rate": base_rate,
                "possession_factor": possession_factor,
                "dangerous_attacks_factor": dangerous_attacks_factor,
                "shots_on_target_factor": shots_on_target_factor,
                "momentum_factor": momentum_factor,
                "red_card_factor": red_card_factor,
                "saturation_factor": saturation_factor,
                "score_differential_factor": score_diff_factor,
                "interval": interval_name,
                "current_minute": current_minute,
                "timestamp": datetime.now().isoformat(),
            },
        }

    def _get_interval_name(self, minute: int) -> str:
        """Retourne l'intervalle du match (ex: '31-45', '76-90')"""
        if 1 <= minute <= 15:
            return "1-15"
        elif 16 <= minute <= 30:
            return "16-30"
        elif 31 <= minute <= 45:
            return "31-45"
        elif 46 <= minute <= 60:
            return "46-60"
        elif 61 <= minute <= 75:
            return "61-75"
        elif 76 <= minute <= 90:
            return "76-90"
        elif 91 <= minute <= 120:
            return "91-120"
        else:
            return "unknown"

    def _calculate_base_rate(self, interval_name: str) -> float:
        """Calcule la base rate historique de but pour cet intervalle"""
        try:
            # Récupérer la moyenne historique de buts par minute dans cet intervalle
            # Simplifié: retourner une base rate par intervalle
            base_rates = {
                "1-15": 0.15,  # 15% de chance de but par minute (low)
                "16-30": 0.20,  # 20%
                "31-45": 0.35,  # 35% (fin 1ère mi-temps, plus de buts)
                "46-60": 0.18,  # 18% (début 2e mi-temps, adaptation)
                "61-75": 0.22,  # 22%
                "76-90": 0.38,  # 38% (fin de match, urgence accrue)
                "91-120": 0.30,  # 30% (prolongations)
            }
            return base_rates.get(interval_name, 0.20)
        except Exception as e:
            return 0.20

    def _calculate_possession_factor(
        self, home_possession: Optional[float], away_possession: Optional[float]
    ) -> float:
        """
        Facteur possession: plus la possession est concentrée, plus haute la chance de but
        Possession équilibrée (45-55%) = 1.0x
        Possession déséquilibrée (>60% ou <40%) = 1.2x
        """
        if home_possession is None or away_possession is None:
            return 1.0

        # Vérifier si l'une des équipes domine (>60% ou <40%)
        if home_possession > 60 or home_possession < 40:
            return 1.2
        return 1.0

    def _calculate_dangerous_attacks_factor(
        self, dangerous_attacks_home: Optional[int], dangerous_attacks_away: Optional[int]
    ) -> float:
        """Facteur attaques dangereuses: ratio > 35% = très boost"""
        if dangerous_attacks_home is None or dangerous_attacks_away is None:
            return 1.0

        total = (dangerous_attacks_home or 0) + (dangerous_attacks_away or 0)
        if total == 0:
            return 1.0

        dangerous_ratio = total / max(1, (dangerous_attacks_home + dangerous_attacks_away) * 0.5)
        if dangerous_ratio > 0.35:
            return 1.4
        elif dangerous_ratio > 0.20:
            return 1.2
        return 1.0

    def _calculate_shots_on_target_factor(
        self, home_sot: Optional[int], away_sot: Optional[int]
    ) -> float:
        """Facteur tirs cadrés: plus il y en a, plus de chance de but"""
        if home_sot is None or away_sot is None:
            return 1.0

        total_sot = (home_sot or 0) + (away_sot or 0)
        if total_sot >= 4:
            return 1.3
        elif total_sot >= 2:
            return 1.1
        return 1.0

    def _calculate_momentum_factor(self, last_5_min_events: Optional[Dict]) -> float:
        """Facteur momentum: buts/tirs rapides augmentent la probabilité"""
        if last_5_min_events is None:
            return 1.0

        events = last_5_min_events.get("buts", 0) + last_5_min_events.get("tirs", 0) // 2
        if events >= 3:
            return 1.5
        elif events >= 1:
            return 1.2
        return 1.0

    def _calculate_red_card_factor(self, home_red: int, away_red: int) -> float:
        """Facteur carte rouge: réduction si rouge (10 vs 11)"""
        total_reds = (home_red or 0) + (away_red or 0)
        if total_reds >= 2:
            return 0.4  # 2 rouges = très peu de buts
        elif total_reds == 1:
            return 0.7  # 1 rouge = réduction 30%
        return 1.0

    def _calculate_saturation_factor(
        self, score_home: int, score_away: int, interval_name: str
    ) -> float:
        """Facteur saturation: si déjà beaucoup de buts, réduire"""
        total_goals = (score_home or 0) + (score_away or 0)

        # Expected goals par intervalle
        expected_goals_by_interval = {
            "1-15": 0.3,
            "16-30": 0.5,
            "31-45": 1.0,
            "46-60": 0.5,
            "61-75": 0.6,
            "76-90": 1.2,
            "91-120": 0.8,
        }
        expected = expected_goals_by_interval.get(interval_name, 0.7)

        if total_goals > expected * 1.5:
            return 0.5  # Saturation: réduction 50%
        elif total_goals > expected:
            return 0.75  # Légère saturation
        return 1.0

    def _calculate_score_differential_factor(self, score_home: int, score_away: int) -> float:
        """Facteur score differential: menée = plus d'attaques = plus de buts potentiels"""
        diff = abs(score_home - score_away)
        if diff == 0:
            return 1.0  # Équilibré
        elif diff == 1:
            return 1.1  # Légèrement avantagé
        else:
            return 1.15  # Significativement derrière

    def _safe_ratio(self, numerator: Optional[int], denominator: Optional[int]) -> float:
        """Ratio safe (évite division par zéro)"""
        if denominator is None or denominator == 0:
            return 0
        if numerator is None:
            return 0
        return numerator / denominator

    def _get_danger_level(self, probability: float) -> str:
        """Retourne le niveau de danger basé sur la probabilité"""
        if probability < 0.30:
            return "LOW"
        elif probability < 0.50:
            return "MEDIUM"
        elif probability < 0.70:
            return "HIGH"
        else:
            return "CRITICAL"


def predict_goal(
    db_manager, home_team: str, away_team: str, live_data: Dict
) -> Dict:
    """
    Fonction wrapper simple pour prédire un but avec les données live

    Args:
        db_manager: Instance de DatabaseManager
        home_team: Équipe à domicile
        away_team: Équipe à l'extérieur
        live_data: Dict de LiveMatchData.to_dict()

    Returns:
        Dict avec goal_probability, danger_level, details
    """
    predictor = LiveGoalProbabilityPredictor(db_manager)

    return predictor.predict_goal_probability(
        home_team=home_team,
        away_team=away_team,
        current_minute=live_data.get("minute", 0),
        home_possession=live_data.get("possession_home"),
        away_possession=live_data.get("possession_away"),
        home_attacks=live_data.get("attacks_home"),
        away_attacks=live_data.get("attacks_away"),
        home_dangerous_attacks=live_data.get("dangerous_attacks_home"),
        away_dangerous_attacks=live_data.get("dangerous_attacks_away"),
        home_shots_on_target=live_data.get("shots_on_target_home"),
        away_shots_on_target=live_data.get("shots_on_target_away"),
        home_red_cards=live_data.get("red_cards_home", 0),
        away_red_cards=live_data.get("red_cards_away", 0),
        score_home=live_data.get("score_home", 0),
        score_away=live_data.get("score_away", 0),
    )
