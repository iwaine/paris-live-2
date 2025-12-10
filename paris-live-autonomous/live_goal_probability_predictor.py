#!/usr/bin/env python3
"""
Préditeur de probabilité de but EN DIRECT
Prédit si "il y aura un but" (peu importe qui marque) basé sur les données historiques + live
"""

import statistics
import sqlite3
import json
from typing import Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class LiveGoalProbabilityPredictor:
    """Prédit la probabilité qu'un but soit marqué dans les prochaines minutes"""

    def __init__(self, db_manager=None, db_path='/workspaces/paris-live/football-live-prediction/data/predictions.db'):
        """
        Args:
            db_manager: Instance de DatabaseManager avec goal_stats (legacy)
            db_path: Chemin vers la base de données soccerstats_scraped_matches
        """
        self.db = db_manager
        self.db_path = db_path
        self._patterns_cache = {}  # Cache pour les patterns historiques

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
        league: str = None,  # NOUVEAU: code ligue pour patterns historiques
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
            league: Code ligue (ex: 'germany2', 'france') pour patterns historiques

        Returns:
            Dict avec:
                - goal_probability: float (0-100%) probabilité de but
                - danger_level: str ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
                - details: dict avec breakdowns
        """

        # 1. BASE RATE: moyenne historique RÉELLE de buts à cette minute
        interval_name = self._get_interval_name(current_minute)
        base_rate = self._calculate_base_rate(interval_name, home_team, away_team, league)

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

        # FORMULE FINALE - 80% HISTORIQUE + 20% LIVE
        # Composante historique (base_rate pure)
        historical_component = base_rate
        
        # Composante live (tous les facteurs dynamiques)
        live_multiplier = (
            possession_factor
            * dangerous_attacks_factor
            * shots_on_target_factor
            * momentum_factor
            * red_card_factor
            * saturation_factor
            * score_diff_factor
        )
        
        # Si live_multiplier > 1, cela booste la proba
        # Si live_multiplier < 1, cela réduit la proba
        # On applique seulement 20% de l'impact live
        live_adjustment = (live_multiplier - 1.0) * 0.20
        
        # Formule finale: 80% base historique + 20% ajustement live
        goal_probability = historical_component * (1.0 + live_adjustment)
        
        # Capper à 95% max (jamais 100%)
        goal_probability = min(0.95, max(0.05, goal_probability))

        # Déterminer le niveau de danger
        danger_level = self._get_danger_level(goal_probability)

        return {
            "goal_probability": goal_probability * 100,  # en %
            "danger_level": danger_level,
            "details": {
                "base_rate": base_rate,
                "historical_component": historical_component,
                "live_multiplier": live_multiplier,
                "live_adjustment": live_adjustment,
                "final_probability": goal_probability,
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
                "weighting": "80% historique + 20% live",
            },
        }

    def _get_interval_name(self, minute: int) -> str:
        """Retourne l'intervalle du match - UNIQUEMENT intervalles clés 31-45+ et 76-90+"""
        # INTERVALLES CLÉS : Fin de mi-temps avec temps additionnel
        if 31 <= minute <= 50:  # 31-45 + temps additionnel (~5 min)
            return "31-45"
        elif 76 <= minute <= 120:  # 76-90 + temps additionnel + prolongations
            return "76-90"
        else:
            # Hors des intervalles clés - pas de signal
            return "outside_key_intervals"

    def _calculate_base_rate(self, interval_name: str, home_team: str = None, away_team: str = None, league: str = None) -> float:
        """
        Calcule la base rate historique RÉELLE pour cet intervalle
        UNIQUEMENT pour les intervalles clés 31-45+ et 76-90+
        
        Args:
            interval_name: Intervalle (ex: '31-45', '76-90')
            home_team: Équipe à domicile (optionnel)
            away_team: Équipe à l'extérieur (optionnel)
            league: Code ligue (ex: 'germany2', 'france')
        
        Returns:
            Probabilité de but basée sur récurrence historique
        """
        # Hors des intervalles clés → probabilité très faible (pas de signal)
        if interval_name == "outside_key_intervals":
            return 0.05  # 5% seulement (bruit de fond)
        
        try:
            # Si on a les équipes, calculer base_rate spécifique
            if home_team and away_team and league:
                home_rate = self._get_team_recurrence(home_team, league, interval_name, is_home=True)
                away_rate = self._get_team_recurrence(away_team, league, interval_name, is_home=False)
                
                if home_rate is not None and away_rate is not None:
                    # Prendre le MAX des deux récurrences (pattern le plus fort domine)
                    combined_rate = max(home_rate, away_rate) / 100
                    return combined_rate
            
            # Fallback: base rates pour intervalles clés uniquement
            base_rates = {
                "31-45": 0.35,  # 35% (fin 1ère mi-temps, plus de buts)
                "76-90": 0.38,  # 38% (fin de match, urgence accrue)
            }
            return base_rates.get(interval_name, 0.05)  # Défaut très bas
        except Exception as e:
            print(f"⚠️ Erreur calcul base_rate: {e}")
            return 0.05
    
    def _get_team_recurrence(self, team: str, league: str, interval_name: str, is_home: bool) -> Optional[float]:
        """
        Récupère la récurrence historique d'une équipe pour un intervalle
        
        Args:
            team: Nom de l'équipe
            league: Code ligue
            interval_name: Intervalle (ex: '31-45')
            is_home: True si domicile, False si extérieur
        
        Returns:
            Récurrence en % ou None si pas de données
        """
        cache_key = f"{league}_{team}_{interval_name}_{'HOME' if is_home else 'AWAY'}"
        # Vérifier le cache
        if cache_key in self._patterns_cache:
            return self._patterns_cache[cache_key]
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Récupérer tous les matchs de cette équipe
            cursor.execute("""
                SELECT goal_times, goal_times_conceded, date, opponent
                FROM soccerstats_scraped_matches
                WHERE league = ? AND team = ? AND is_home = ?
            """, (league, team, 1 if is_home else 0))
            matches = cursor.fetchall()
            conn.close()
            if not matches or len(matches) == 0:
                # Pas de données historiques, retourner une valeur faible et logguer
                print(f"⚠️ Aucun match historique pour {team} ({'HOME' if is_home else 'AWAY'}) dans {league} intervalle {interval_name}")
                self._patterns_cache[cache_key] = 5.0  # 5% par défaut
                return 5.0
            # Déterminer l'intervalle en minutes
            if interval_name == "1-15":
                min_start, min_end = 1, 15
            elif interval_name == "16-30":
                min_start, min_end = 16, 30
            elif interval_name == "31-45":
                min_start, min_end = 31, 45
            elif interval_name == "46-60":
                min_start, min_end = 46, 60
            elif interval_name == "61-75":
                min_start, min_end = 61, 75
            elif interval_name == "76-90":
                min_start, min_end = 76, 90
            else:
                return None
            # Compter matchs avec but dans l'intervalle
            matches_with_goal = set()
            for row in matches:
                goals_scored = json.loads(row[0])
                goals_conceded = json.loads(row[1])
                match_id = f"{row[2]}_{row[3]}"
                # Vérifier si au moins 1 but (marqué OU encaissé) dans l'intervalle
                for minute in goals_scored + goals_conceded:
                    if min_start <= minute <= min_end:
                        matches_with_goal.add(match_id)
                        break
            # Calculer récurrence en toute sécurité
            total_matches = len(matches)
            if total_matches == 0:
                print(f"⚠️ Aucun match historique pour {team} ({'HOME' if is_home else 'AWAY'}) dans {league} intervalle {interval_name}")
                self._patterns_cache[cache_key] = 5.0
                return 5.0
            recurrence = (len(matches_with_goal) / total_matches) * 100
            # Si la récurrence est nulle, retourner une valeur faible
            if recurrence == 0:
                print(f"⚠️ Récurrence nulle pour {team} ({'HOME' if is_home else 'AWAY'}) dans {league} intervalle {interval_name}")
                self._patterns_cache[cache_key] = 5.0
                return 5.0
            # Mettre en cache
            self._patterns_cache[cache_key] = recurrence
            return recurrence
        except Exception as e:
            print(f"⚠️ Erreur récupération patterns {team}: {e}")
            self._patterns_cache[cache_key] = 5.0
            return 5.0

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
    
    # Détecter la ligue depuis l'URL du match si disponible
    league = None
    match_url = live_data.get('url', '')
    if 'league=' in match_url:
        import re
        match = re.search(r'league=([a-z0-9]+)', match_url)
        if match:
            league = match.group(1)

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
        league=league,  # Passer la ligue pour patterns historiques
    )
