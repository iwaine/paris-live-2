#!/usr/bin/env python3
"""
Prédicteur live v2 - Optimisé avec métriques any_goal, récurrence_last_5 et confidence_level.
Prédit la probabilité qu'AU MOINS 1 BUT soit marqué dans l'intervalle critique.
"""

import sqlite3
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LiveMatchContext:
    """Contexte d'un match en cours."""
    home_team: str
    away_team: str
    current_minute: int
    home_score: int
    away_score: int
    country: str = "Bulgaria"
    league: str = "bulgaria"
    
    # Stats live (optionnelles)
    possession_home: Optional[float] = None
    possession_away: Optional[float] = None
    corners_home: Optional[int] = None
    corners_away: Optional[int] = None
    shots_home: Optional[int] = None
    shots_away: Optional[int] = None
    shots_on_target_home: Optional[int] = None
    shots_on_target_away: Optional[int] = None
    shots_inside_box_home: Optional[int] = None
    shots_inside_box_away: Optional[int] = None
    shots_outside_box_home: Optional[int] = None
    shots_outside_box_away: Optional[int] = None
    attacks_home: Optional[int] = None
    attacks_away: Optional[int] = None
    dangerous_attacks_home: Optional[int] = None
    dangerous_attacks_away: Optional[int] = None


@dataclass
class IntervalPrediction:
    """Prédiction pour un intervalle critique."""
    interval_name: str
    probability: float  # Probabilité qu'au moins 1 but soit marqué
    confidence_level: str  # EXCELLENT, TRES_BON, BON, MOYEN, FAIBLE
    
    # Détails pattern
    freq_any_goal: float
    recurrence_last_5: Optional[float]
    total_matches: int
    matches_with_goal: int
    
    # Détails buts marqués/encaissés
    goals_scored: int
    freq_scored: float
    goals_conceded: int
    freq_conceded: float
    
    # Timing
    avg_minute: Optional[float]
    std_minute: Optional[float]
    
    # Analyse
    reasoning: str
    is_active: bool  # True si on est dans l'intervalle


class LivePredictorV2:
    """
    Prédicteur optimisé pour intervalles critiques.
    Focus: Prédire si AU MOINS 1 BUT sera marqué dans 31-45 ou 75-90.
    """
    
    INTERVAL_1 = (31, 45, "31-45+")
    INTERVAL_2 = (75, 90, "75-90+")
    
    def __init__(self, db_path='data/predictions.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Fermer connexion DB."""
        self.conn.close()
    
    def _get_active_interval(self, minute: int) -> Optional[Tuple[int, int, str]]:
        """Déterminer l'intervalle actif."""
        if self.INTERVAL_1[0] <= minute <= self.INTERVAL_1[1]:
            return self.INTERVAL_1
        elif self.INTERVAL_2[0] <= minute <= self.INTERVAL_2[1]:
            return self.INTERVAL_2
        return None
    
    def _get_next_interval(self, minute: int) -> Optional[Tuple[int, int, str]]:
        """Déterminer le prochain intervalle critique."""
        if minute < self.INTERVAL_1[0]:
            return self.INTERVAL_1
        elif self.INTERVAL_1[1] < minute < self.INTERVAL_2[0]:
            return self.INTERVAL_2
        return None
    
    def _load_pattern(self, team: str, is_home: bool, interval_name: str, 
                     country: str = "Bulgaria") -> Optional[Dict]:
        """Charger pattern pour équipe + contexte."""
        self.cursor.execute('''
            SELECT 
                team_name, is_home, interval_name,
                goals_scored, matches_with_goals_scored, freq_goals_scored,
                avg_minute_scored, std_minute_scored,
                goals_conceded, matches_with_goals_conceded, freq_goals_conceded,
                avg_minute_conceded, std_minute_conceded,
                any_goal_total, matches_with_any_goal, freq_any_goal,
                recurrence_last_5, confidence_level,
                avg_goals_full_match, avg_goals_first_half, avg_goals_second_half,
                total_matches
            FROM team_critical_intervals
            WHERE country = ? AND team_name = ? AND is_home = ? AND interval_name = ?
        ''', (country, team, is_home, interval_name))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return {
            'team_name': row[0],
            'is_home': row[1],
            'interval_name': row[2],
            'goals_scored': row[3],
            'matches_scored': row[4],
            'freq_scored': row[5],
            'avg_minute_scored': row[6],
            'std_minute_scored': row[7],
            'goals_conceded': row[8],
            'matches_conceded': row[9],
            'freq_conceded': row[10],
            'avg_minute_conceded': row[11],
            'std_minute_conceded': row[12],
            'any_goal_total': row[13],
            'matches_any_goal': row[14],
            'freq_any_goal': row[15],
            'recurrence_last_5': row[16],
            'confidence_level': row[17],
            'avg_goals_full_match': row[18],
            'avg_goals_first_half': row[19],
            'avg_goals_second_half': row[20],
            'total_matches': row[21]
        }
    
    def _build_prediction(self, pattern: Optional[Dict], interval: Tuple[int, int, str],
                         team: str, is_home: bool, is_active: bool,
                         context: LiveMatchContext,
                         pattern_home: Optional[Dict] = None,
                         pattern_away: Optional[Dict] = None) -> IntervalPrediction:
        """Construire prédiction depuis pattern + momentum live + saturation."""
        
        interval_name = interval[2]
        
        if pattern is None:
            # Pas de données historiques
            return IntervalPrediction(
                interval_name=interval_name,
                probability=0.15,
                confidence_level="INSUFFICIENT_DATA",
                freq_any_goal=0.0,
                recurrence_last_5=None,
                total_matches=0,
                matches_with_goal=0,
                goals_scored=0,
                freq_scored=0.0,
                goals_conceded=0,
                freq_conceded=0.0,
                avg_minute=None,
                std_minute=None,
                reasoning=f"Aucune donnée historique pour {team} ({'HOME' if is_home else 'AWAY'}) {interval_name}",
                is_active=is_active
            )
        
        # Pattern trouvé - Analyser confiance
        confidence = pattern['confidence_level']
        freq_any = pattern['freq_any_goal']
        rec5 = pattern['recurrence_last_5']
        total = pattern['total_matches']
        
        # Calculer momentum live
        momentum_score = self._calculate_momentum(context, is_home)
        
        # Calculer ajustement de saturation (si patterns disponibles)
        saturation_adj = 0.0
        if pattern_home and pattern_away:
            saturation_adj = self._calculate_saturation_adjustment(
                context, pattern_home, pattern_away, interval_name
            )
        
        # Calculer probabilité ajustée (80% pattern + 20% momentum + saturation)
        probability = self._calculate_probability(
            freq_any, rec5, confidence, is_active, momentum_score, saturation_adj
        )
        
        # Calculer minute moyenne (mixte scored + conceded)
        avg_scored = pattern['avg_minute_scored']
        avg_conceded = pattern['avg_minute_conceded']
        
        if avg_scored and avg_conceded:
            avg_minute = (avg_scored + avg_conceded) / 2
        elif avg_scored:
            avg_minute = avg_scored
        elif avg_conceded:
            avg_minute = avg_conceded
        else:
            avg_minute = None
        
        # Construire reasoning
        reasoning = self._build_reasoning(pattern, is_active, momentum_score)
        
        return IntervalPrediction(
            interval_name=interval_name,
            probability=probability,
            confidence_level=confidence,
            freq_any_goal=freq_any,
            recurrence_last_5=rec5,
            total_matches=total,
            matches_with_goal=pattern['matches_any_goal'],
            goals_scored=pattern['goals_scored'],
            freq_scored=pattern['freq_scored'],
            goals_conceded=pattern['goals_conceded'],
            freq_conceded=pattern['freq_conceded'],
            avg_minute=avg_minute,
            std_minute=pattern['std_minute_scored'],
            reasoning=reasoning,
            is_active=is_active
        )
    
    def _calculate_probability(self, freq_any: float, rec5: Optional[float], 
                              confidence: str, is_active: bool,
                              momentum_score: Optional[float] = None,
                              saturation_adjustment: float = 0.0) -> float:
        """
        Calculer probabilité ajustée - SYSTÈME HYBRIDE.
        
        🔥 80% Pattern historique + 20% Momentum live + Ajustement saturation
        
        Pattern historique (80%):
        - Base: freq_any_goal (fréquence historique globale)
        - Ajustements récurrence récente (rec5) : +/- 15%
        - Ajustements niveau de confiance : +/- 10%
        - Boost intervalle actif : +20% (urgence)
        
        Momentum live (20%):
        - Calculé depuis stats live du match (possession, shots, attacks, etc.)
        - Score entre 0 et 1
        
        Saturation:
        - Ajustement négatif si nombre de buts actuels ≥ moyenne attendue
        - Logique: Si déjà beaucoup de buts → Moins probable d'en avoir plus
        """
        # PARTIE 1: PATTERN HISTORIQUE (80%)
        historical_prob = freq_any
        
        # Ajustement récurrence récente
        if rec5 is not None:
            if rec5 >= 0.8:
                historical_prob += 0.15  # Très forte récurrence récente
            elif rec5 >= 0.6:
                historical_prob += 0.10
            elif rec5 >= 0.4:
                historical_prob += 0.05
            elif rec5 <= 0.2:
                historical_prob -= 0.15  # Faible récurrence récente = danger
            elif rec5 <= 0.4:
                historical_prob -= 0.10
        
        # Ajustement confiance
        if confidence == "EXCELLENT":
            historical_prob += 0.10
        elif confidence == "TRES_BON":
            historical_prob += 0.05
        elif confidence == "FAIBLE":
            historical_prob -= 0.10
        
        # Boost si intervalle actif (urgence)
        if is_active:
            historical_prob += 0.20
        
        # AJUSTEMENT SATURATION (appliqué AVANT momentum)
        historical_prob += saturation_adjustment
        
        # Limiter entre 0 et 1
        historical_prob = max(0.0, min(1.0, historical_prob))
        
        # PARTIE 2: MOMENTUM LIVE (20%)
        if momentum_score is None:
            # Pas de stats live → 100% pattern historique
            return historical_prob
        
        # Combiner: 80% historique + 20% momentum
        final_probability = 0.80 * historical_prob + 0.20 * momentum_score
        
        return max(0.0, min(1.0, final_probability))
    
    def _calculate_saturation_adjustment(self, context: LiveMatchContext, 
                                        pattern_home: Optional[Dict], 
                                        pattern_away: Optional[Dict],
                                        interval_name: str) -> float:
        """
        Calculer ajustement de saturation basé sur le nombre de buts actuels vs moyenne attendue.
        
        Logique:
        - Moyenne attendue = (moyenne_home_config + moyenne_away_config) / 2
        - Si buts_actuels >= moyenne_attendue → Ajustement NÉGATIF (saturation)
        - Si buts_actuels < moyenne_attendue → Pas d'ajustement (ou léger positif)
        
        Args:
            context: Contexte match live avec scores actuels
            pattern_home: Pattern équipe domicile
            pattern_away: Pattern équipe extérieur
            interval_name: "31-45+" ou "75-90+"
        
        Returns:
            Ajustement entre -0.20 et +0.05
        """
        if not pattern_home or not pattern_away:
            return 0.0
        
        current_goals = context.home_score + context.away_score
        
        # Déterminer quelle moyenne utiliser selon l'intervalle et la minute
        if interval_name == "31-45+":
            # 1ère mi-temps en cours
            avg_home = pattern_home.get('avg_goals_first_half', 0.0) or 0.0
            avg_away = pattern_away.get('avg_goals_first_half', 0.0) or 0.0
        else:  # 75-90+
            # 2nde mi-temps ou match complet
            # Si minute < 46 → utiliser moyenne full match
            # Si minute >= 46 → utiliser moyenne 2nde mi-temps + buts déjà marqués en 1ère
            if context.current_minute < 46:
                avg_home = pattern_home.get('avg_goals_full_match', 0.0) or 0.0
                avg_away = pattern_away.get('avg_goals_full_match', 0.0) or 0.0
            else:
                # On est en 2nde mi-temps : moyenne = buts_actuels + moyenne_2nde_mi_temps
                avg_second_home = pattern_home.get('avg_goals_second_half', 0.0) or 0.0
                avg_second_away = pattern_away.get('avg_goals_second_half', 0.0) or 0.0
                # La moyenne pour le reste du match = moyenne 2nde mi-temps
                avg_home = avg_second_home
                avg_away = avg_second_away
        
        # Moyenne combinée attendue
        expected_avg = (avg_home + avg_away) / 2.0
        
        if expected_avg == 0:
            return 0.0
        
        # Ratio saturation
        saturation_ratio = current_goals / expected_avg
        
        # Ajustement progressif
        if saturation_ratio >= 1.5:
            # 150%+ de la moyenne → Forte saturation
            return -0.20
        elif saturation_ratio >= 1.25:
            # 125-149% → Saturation modérée
            return -0.15
        elif saturation_ratio >= 1.0:
            # 100-124% → Légère saturation
            return -0.10
        elif saturation_ratio >= 0.75:
            # 75-99% → Proche de la moyenne, neutre
            return -0.05
        else:
            # < 75% → Sous la moyenne, léger boost
            return 0.05
    
    def _calculate_momentum(self, context: LiveMatchContext, is_home: bool) -> Optional[float]:
        """
        Calculer le score de momentum live pour une équipe.
        
        Formule avec shots inside/outside box (si disponibles):
        - 20% possession
        - 15% shots ratio
        - 15% shots on target ratio
        - 10% shots inside box ratio (si disponible)
        - 5% shots outside box ratio (si disponible)
        - 15% dangerous attacks ratio
        - 10% attacks ratio
        - 10% corners ratio
        
        Si shots inside/outside box non disponibles, redistribution:
        - 25% possession
        - 20% shots
        - 20% shots on target
        - 15% dangerous attacks
        - 10% attacks
        - 10% corners
        
        Returns:
            Score entre 0 et 1, ou None si pas de stats live
        """
        # Vérifier si on a des stats live
        if context.possession_home is None and context.shots_home is None:
            return None
        
        momentum = 0.0
        weights_used = 0.0
        
        # Déterminer si on a shots inside/outside box
        has_box_stats = (context.shots_inside_box_home is not None and 
                        context.shots_inside_box_away is not None and
                        context.shots_outside_box_home is not None and 
                        context.shots_outside_box_away is not None)
        
        # 1. POSSESSION (20% ou 25%)
        poss_weight = 0.20 if has_box_stats else 0.25
        if context.possession_home is not None and context.possession_away is not None:
            total_poss = context.possession_home + context.possession_away
            if total_poss > 0:
                ratio = context.possession_home / total_poss if is_home else context.possession_away / total_poss
                momentum += poss_weight * ratio
                weights_used += poss_weight
        
        # 2. SHOTS (15% ou 20%)
        shots_weight = 0.15 if has_box_stats else 0.20
        if context.shots_home is not None and context.shots_away is not None:
            total_shots = context.shots_home + context.shots_away
            if total_shots > 0:
                ratio = context.shots_home / total_shots if is_home else context.shots_away / total_shots
                momentum += shots_weight * ratio
                weights_used += shots_weight
        
        # 3. SHOTS ON TARGET (15% ou 20%)
        sot_weight = 0.15 if has_box_stats else 0.20
        if context.shots_on_target_home is not None and context.shots_on_target_away is not None:
            total_sot = context.shots_on_target_home + context.shots_on_target_away
            if total_sot > 0:
                ratio = context.shots_on_target_home / total_sot if is_home else context.shots_on_target_away / total_sot
                momentum += sot_weight * ratio
                weights_used += sot_weight
        
        # 4. SHOTS INSIDE BOX (10% si disponible)
        if has_box_stats:
            total_sib = context.shots_inside_box_home + context.shots_inside_box_away
            if total_sib > 0:
                ratio = context.shots_inside_box_home / total_sib if is_home else context.shots_inside_box_away / total_sib
                momentum += 0.10 * ratio
                weights_used += 0.10
        
        # 5. SHOTS OUTSIDE BOX (5% si disponible)
        if has_box_stats:
            total_sob = context.shots_outside_box_home + context.shots_outside_box_away
            if total_sob > 0:
                ratio = context.shots_outside_box_home / total_sob if is_home else context.shots_outside_box_away / total_sob
                momentum += 0.05 * ratio
                weights_used += 0.05
        
        # 6. DANGEROUS ATTACKS (15%)
        if context.dangerous_attacks_home is not None and context.dangerous_attacks_away is not None:
            total_da = context.dangerous_attacks_home + context.dangerous_attacks_away
            if total_da > 0:
                ratio = context.dangerous_attacks_home / total_da if is_home else context.dangerous_attacks_away / total_da
                momentum += 0.15 * ratio
                weights_used += 0.15
        
        # 7. ATTACKS (10%)
        if context.attacks_home is not None and context.attacks_away is not None:
            total_att = context.attacks_home + context.attacks_away
            if total_att > 0:
                ratio = context.attacks_home / total_att if is_home else context.attacks_away / total_att
                momentum += 0.10 * ratio
                weights_used += 0.10
        
        # 8. CORNERS (10%)
        if context.corners_home is not None and context.corners_away is not None:
            total_corners = context.corners_home + context.corners_away
            if total_corners > 0:
                ratio = context.corners_home / total_corners if is_home else context.corners_away / total_corners
                momentum += 0.10 * ratio
                weights_used += 0.10
        
        # Normaliser si on n'a pas toutes les stats
        if weights_used > 0:
            return momentum / weights_used
        
        return None
    
    def _build_reasoning(self, pattern: Dict, is_active: bool, momentum_score: Optional[float] = None) -> str:
        """Construire explication textuelle."""
        team = pattern['team_name']
        loc = "HOME" if pattern['is_home'] else "AWAY"
        interval = pattern['interval_name']
        confidence = pattern['confidence_level']
        freq = pattern['freq_any_goal']
        rec5 = pattern['recurrence_last_5']
        matches = pattern['matches_any_goal']
        total = pattern['total_matches']
        
        # Base
        reason = f"{team} {loc} {interval}: {matches}/{total} matches avec but ({freq*100:.0f}%). "
        
        # Récurrence récente
        if rec5 is not None:
            reason += f"Récurrence 5 derniers: {rec5*100:.0f}%. "
        
        # Détail buts
        scored = pattern['goals_scored']
        conceded = pattern['goals_conceded']
        reason += f"Buts marqués: {scored}, encaissés: {conceded}. "
        
        # Confiance
        reason += f"Confiance: {confidence}."
        
        # Momentum live
        if momentum_score is not None:
            reason += f" Momentum live: {momentum_score*100:.0f}%."
        
        if is_active:
            reason += " ⚠️ INTERVALLE ACTIF MAINTENANT!"
        
        return reason
    
    def predict(self, match: LiveMatchContext) -> Dict[str, IntervalPrediction]:
        """
        Prédire probabilités pour le match en cours.
        
        Retourne dict avec:
        - 'home_active': Prédiction HOME pour intervalle actif (si applicable)
        - 'away_active': Prédiction AWAY pour intervalle actif (si applicable)
        - 'home_next': Prédiction HOME pour prochain intervalle
        - 'away_next': Prédiction AWAY pour prochain intervalle
        - 'combined_active': Probabilité qu'au moins 1 des 2 équipes marque (intervalle actif)
        - 'combined_next': Probabilité qu'au moins 1 des 2 équipes marque (prochain intervalle)
        """
        predictions = {}
        
        # Déterminer intervalles
        active_interval = self._get_active_interval(match.current_minute)
        next_interval = self._get_next_interval(match.current_minute)
        
        # INTERVALLE ACTIF
        if active_interval:
            home_pattern = self._load_pattern(match.home_team, True, active_interval[2], match.country)
            away_pattern = self._load_pattern(match.away_team, False, active_interval[2], match.country)
            
            predictions['home_active'] = self._build_prediction(
                home_pattern, active_interval, match.home_team, True, is_active=True, 
                context=match, pattern_home=home_pattern, pattern_away=away_pattern
            )
            predictions['away_active'] = self._build_prediction(
                away_pattern, active_interval, match.away_team, False, is_active=True, 
                context=match, pattern_home=home_pattern, pattern_away=away_pattern
            )
            
            # Probabilité combinée (au moins 1 des 2 marque)
            # P(A ou B) = P(A) + P(B) - P(A et B)
            # Approximation: P(A et B) ≈ P(A) * P(B) (indépendance)
            p_home = predictions['home_active'].probability
            p_away = predictions['away_active'].probability
            p_combined = p_home + p_away - (p_home * p_away)
            
            predictions['combined_active'] = {
                'probability': p_combined,
                'interval': active_interval[2],
                'reasoning': f"Probabilité qu'au moins 1 des 2 équipes marque dans {active_interval[2]}"
            }
        
        # PROCHAIN INTERVALLE
        if next_interval:
            home_pattern = self._load_pattern(match.home_team, True, next_interval[2], match.country)
            away_pattern = self._load_pattern(match.away_team, False, next_interval[2], match.country)
            
            predictions['home_next'] = self._build_prediction(
                home_pattern, next_interval, match.home_team, True, is_active=False, 
                context=match, pattern_home=home_pattern, pattern_away=away_pattern
            )
            predictions['away_next'] = self._build_prediction(
                away_pattern, next_interval, match.away_team, False, is_active=False, 
                context=match, pattern_home=home_pattern, pattern_away=away_pattern
            )
            
            # Probabilité combinée
            p_home = predictions['home_next'].probability
            p_away = predictions['away_next'].probability
            p_combined = p_home + p_away - (p_home * p_away)
            
            predictions['combined_next'] = {
                'probability': p_combined,
                'interval': next_interval[2],
                'reasoning': f"Probabilité qu'au moins 1 des 2 équipes marque dans {next_interval[2]}"
            }
        
        return predictions
    
    def display_predictions(self, match: LiveMatchContext, predictions: Dict):
        """Afficher prédictions formatées."""
        print("=" * 80)
        print(f"�� PRÉDICTION LIVE - {match.home_team} vs {match.away_team}")
        print(f"⏱️  Minute {match.current_minute} | Score: {match.home_score}-{match.away_score}")
        print("=" * 80)
        
        # Intervalle actif
        if 'home_active' in predictions:
            print("\n⚡ INTERVALLE ACTIF MAINTENANT:")
            home = predictions['home_active']
            away = predictions['away_active']
            combined = predictions['combined_active']
            
            print(f"\n  {match.home_team} (HOME):")
            print(f"    Probabilité: {home.probability*100:.1f}%")
            print(f"    Confiance: {home.confidence_level}")
            print(f"    Fréquence historique: {home.freq_any_goal*100:.0f}% ({home.matches_with_goal}/{home.total_matches} matches)")
            if home.recurrence_last_5:
                print(f"    Récurrence 5 derniers: {home.recurrence_last_5*100:.0f}%")
            print(f"    Détails: {home.goals_scored} marqués, {home.goals_conceded} encaissés")
            if home.avg_minute:
                print(f"    ⏰ Timing: Minute moyenne {home.avg_minute:.1f}", end="")
                if home.std_minute:
                    min_range = max(home.avg_minute - home.std_minute, 31 if '31-45' in home.interval_name else 75)
                    max_range = min(home.avg_minute + home.std_minute, 45 if '31-45' in home.interval_name else 90)
                    print(f" (±{home.std_minute:.1f}) → Buts entre {min_range:.0f}-{max_range:.0f}min")
                else:
                    print()
            
            print(f"\n  {match.away_team} (AWAY):")
            print(f"    Probabilité: {away.probability*100:.1f}%")
            print(f"    Confiance: {away.confidence_level}")
            print(f"    Fréquence historique: {away.freq_any_goal*100:.0f}% ({away.matches_with_goal}/{away.total_matches} matches)")
            if away.recurrence_last_5:
                print(f"    Récurrence 5 derniers: {away.recurrence_last_5*100:.0f}%")
            print(f"    Détails: {away.goals_scored} marqués, {away.goals_conceded} encaissés")
            if away.avg_minute:
                print(f"    ⏰ Timing: Minute moyenne {away.avg_minute:.1f}", end="")
                if away.std_minute:
                    min_range = max(away.avg_minute - away.std_minute, 31 if '31-45' in away.interval_name else 75)
                    max_range = min(away.avg_minute + away.std_minute, 45 if '31-45' in away.interval_name else 90)
                    print(f" (±{away.std_minute:.1f}) → Buts entre {min_range:.0f}-{max_range:.0f}min")
                else:
                    print()
            
            print(f"\n  🎯 PROBABILITÉ COMBINÉE: {combined['probability']*100:.1f}%")
            print(f"     (Au moins 1 but marqué par l'une des 2 équipes)")
        
        # Prochain intervalle
        if 'home_next' in predictions:
            print(f"\n📅 PROCHAIN INTERVALLE ({predictions['home_next'].interval_name}):")
            home = predictions['home_next']
            away = predictions['away_next']
            combined = predictions['combined_next']
            
            print(f"\n  {match.home_team} (HOME): {home.probability*100:.1f}% | {home.confidence_level}")
            if home.avg_minute:
                timing_info = f"    ⏰ Minute moyenne: {home.avg_minute:.1f}"
                if home.std_minute:
                    timing_info += f" (±{home.std_minute:.1f})"
                print(timing_info)
            
            print(f"  {match.away_team} (AWAY): {away.probability*100:.1f}% | {away.confidence_level}")
            if away.avg_minute:
                timing_info = f"    ⏰ Minute moyenne: {away.avg_minute:.1f}"
                if away.std_minute:
                    timing_info += f" (±{away.std_minute:.1f})"
                print(timing_info)
            
            print(f"\n  🎯 PROBABILITÉ COMBINÉE: {combined['probability']*100:.1f}%")
        
        print("\n" + "=" * 80)


# ============================================================================
# DEMO
# ============================================================================

def demo_bulgaria():
    """Démonstration avec match bulgare."""
    predictor = LivePredictorV2()
    
    # Simulation match: Spartak Varna vs Slavia Sofia, minute 32
    match = LiveMatchContext(
        home_team="Spartak Varna",
        away_team="Slavia Sofia",
        current_minute=32,
        home_score=0,
        away_score=0,
        country="Bulgaria",
        league="bulgaria"
    )
    
    predictions = predictor.predict(match)
    predictor.display_predictions(match, predictions)
    
    print("\n" + "=" * 80)
    print("SCÉNARIO 2: Minute 78 (intervalle 75-90 actif)")
    print("=" * 80)
    
    match2 = LiveMatchContext(
        home_team="Spartak Varna",
        away_team="Slavia Sofia",
        current_minute=78,
        home_score=1,
        away_score=1,
        country="Bulgaria",
        league="bulgaria"
    )
    
    predictions2 = predictor.predict(match2)
    predictor.display_predictions(match2, predictions2)
    
    predictor.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prédicteur live pour n'importe quel match")
    parser.add_argument('--home', type=str, required=True, help='Nom de l’équipe à domicile')
    parser.add_argument('--away', type=str, required=True, help='Nom de l’équipe à l’extérieur')
    parser.add_argument('--minute', type=int, required=True, help='Minute actuelle du match')
    parser.add_argument('--score', type=str, required=True, help='Score actuel sous forme X-Y')
    parser.add_argument('--league', type=str, default='england', help='Nom de la ligue')
    parser.add_argument('--country', type=str, default='England', help='Pays')
    args = parser.parse_args()

    try:
        home_score, away_score = map(int, args.score.split('-'))
    except Exception:
        print("Format du score invalide. Utilisez X-Y.")
        exit(1)

    match = LiveMatchContext(
        home_team=args.home,
        away_team=args.away,
        current_minute=args.minute,
        home_score=home_score,
        away_score=away_score,
        country=args.country,
        league=args.league
    )
    predictor = LivePredictorV2()
    predictions = predictor.predict(match)
    predictor.display_predictions(match, predictions)
    predictor.close()
