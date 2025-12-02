"""
Interval Predictor - Prédit la probabilité d'un but dans l'intervalle ACTUEL
"""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from loguru import logger


class IntervalPredictor:
    def __init__(self, profiles_dir: str = "data/team_profiles"):
        self.profiles_dir = Path(profiles_dir)
        logger.info("IntervalPredictor initialized")
    
    def load_team_profile(self, team_name: str) -> Optional[Dict]:
        normalized_name = team_name.lower().replace(' ', '_').replace('.', '')
        profile_path = self.profiles_dir / f"{normalized_name}_profile.json"
        
        if not profile_path.exists():
            logger.warning(f"Profile not found: {profile_path}")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            logger.info(f"Profile loaded: {team_name}")
            return profile
        except Exception as e:
            logger.error(f"Error loading profile {team_name}: {e}")
            return None
    
    def determine_current_interval(self, current_minute: int) -> str:
        """Détermine l'intervalle ACTUEL de 15min (où on est maintenant)"""
        if 0 <= current_minute <= 15:
            return "0-15"
        elif 16 <= current_minute <= 30:
            return "16-30"
        elif 31 <= current_minute <= 45:
            return "31-45"
        elif 46 <= current_minute <= 60:
            return "46-60"
        elif 61 <= current_minute <= 75:
            return "61-75"
        elif 76 <= current_minute <= 90:
            return "76-90"
        else:
            return None
    
    def calculate_danger_score(self, home_profile: Dict, away_profile: Dict, interval: str,
                               current_score: Tuple[int, int] = (0, 0), current_minute: int = 0):
        """
        Calcule le danger score AMÉLIORÉ avec :
        - Attaque équipe + Défense adverse (pondérés 60/40)
        - Forme récente (boost jusqu'à +25%)
        - Saturation du match (réduction si beaucoup de buts)
        """
        try:
            home_venue = home_profile.get('home', {})
            home_intervals = home_venue.get('goals_by_interval', {})
            away_venue = away_profile.get('away', {})
            away_intervals = away_venue.get('goals_by_interval', {})
            
            home_interval_data = home_intervals.get(interval, {})
            away_interval_data = away_intervals.get(interval, {})
            
            # Récupérer les stats
            home_gp = home_venue.get('games_played', 1)
            away_gp = away_venue.get('games_played', 1)
            
            home_scored = home_interval_data.get('scored', 0)
            home_conceded = home_interval_data.get('conceded', 0)
            away_scored = away_interval_data.get('scored', 0)
            away_conceded = away_interval_data.get('conceded', 0)
            
            # 1. CALCUL BASE (Attaque 60% + Défense adverse 40%)
            home_attack_rate = home_scored / max(home_gp, 1)
            away_defense_weakness = away_conceded / max(away_gp, 1)
            home_base = (home_attack_rate * 0.6) + (away_defense_weakness * 0.4)
            
            away_attack_rate = away_scored / max(away_gp, 1)
            home_defense_weakness = home_conceded / max(home_gp, 1)
            away_base = (away_attack_rate * 0.6) + (home_defense_weakness * 0.4)
            
            # 2. FORME RÉCENTE (si disponible)
            # La méthode _calculate_form_boost prend désormais l'intervalle courant
            home_form_boost = self._calculate_form_boost(home_venue, interval)
            away_form_boost = self._calculate_form_boost(away_venue, interval)
            
            # 3. SATURATION (ajustement si beaucoup de buts déjà)
            saturation_factor = self._calculate_saturation(current_score, current_minute)
            
            # 4. CALCUL FINAL
            home_danger = home_base * home_form_boost * saturation_factor
            away_danger = away_base * away_form_boost * saturation_factor
            
            # Normalisation en score 0-100
            home_score = min(100, home_danger * 40)
            away_score = min(100, away_danger * 40)
            
            # Score global (pour compatibilité ancien code)
            danger_score = (home_score + away_score) / 20  # Ramené à échelle ~0-10
            
            details = {
                'interval': interval,
                'home_team': home_profile.get('team'),
                'away_team': away_profile.get('team'),
                'home_score': round(home_score, 1),
                'away_score': round(away_score, 1),
                'home_attack_rate': round(home_attack_rate, 2),
                'away_defense_weakness': round(away_defense_weakness, 2),
                'away_attack_rate': round(away_attack_rate, 2),
                'home_defense_weakness': round(home_defense_weakness, 2),
                'home_form_boost': round(home_form_boost, 2),
                'away_form_boost': round(away_form_boost, 2),
                'saturation_factor': round(saturation_factor, 2),
                'danger_score': round(danger_score, 2)
            }
            
            return danger_score, details
        except Exception as e:
            logger.error(f"Error: {e}")
            return 0.0, {}
    
    def predict_match(self, home_team: str, away_team: str, current_minute: int, live_stats=None):
        logger.info(f"Analyzing CURRENT interval: {home_team} vs {away_team} @ {current_minute}'")
        
        home_profile = self.load_team_profile(home_team)
        away_profile = self.load_team_profile(away_team)
        
        if not home_profile or not away_profile:
            return {'success': False, 'error': 'Team profiles not found'}
        
        current_interval = self.determine_current_interval(current_minute)
        if not current_interval:
            return {'success': False, 'error': 'Match too advanced'}
        
        # Récupérer le score actuel depuis live_stats
        current_score = (0, 0)
        if live_stats and 'score' in live_stats:
            try:
                score_parts = live_stats['score'].split('-')
                current_score = (int(score_parts[0]), int(score_parts[1]))
            except:
                current_score = (0, 0)
        
        # Calculer danger score avec nouveaux paramètres
        danger_score, details = self.calculate_danger_score(
            home_profile, 
            away_profile, 
            current_interval,
            current_score,
            current_minute
        )
        
        interpretation = self._interpret_danger_score(danger_score)
        bet = self._generate_bet_recommendation(danger_score, details, interpretation, current_minute)
        
        return {
            'success': True,
            'current_minute': current_minute,
            'current_interval': current_interval,
            'current_score': f"{current_score[0]}-{current_score[1]}",
            'danger_score': danger_score,
            'interpretation': interpretation,
            'details': details,
            'bet_recommendation': bet
        }
    
    
    def _calculate_form_boost(self, venue_data: Dict, interval: str) -> float:
        """
        Calcule le boost basé sur la forme récente PAR INTERVALLE
        
        Args:
            venue_data: Données du venue (home/away)
            interval: Intervalle actuel (ex: '61-75')
        """
        # Vérifier si on a recent_form_by_interval
        recent_form_interval = venue_data.get('recent_form_by_interval', {})
        
        if recent_form_interval and interval in recent_form_interval:
            # Forme PAR INTERVALLE disponible ✅
            interval_data = recent_form_interval[interval]
            avg_scored_recent = interval_data.get('scored_avg', 0)
            matches_count = interval_data.get('matches', 0)
            
            # Récupérer aussi l'historique pour cet intervalle
            goals_by_interval = venue_data.get('goals_by_interval', {})
            if interval in goals_by_interval:
                hist_scored = goals_by_interval[interval].get('scored', 0)
                hist_games = venue_data.get('games_played', 1)
                avg_scored_hist = hist_scored / max(hist_games, 1)
                
                # Comparer forme récente vs historique
                if avg_scored_hist > 0:
                    trend = avg_scored_recent / avg_scored_hist
                    
                    # Boost selon la tendance
                    if trend > 1.5:
                        return 1.30  # Forme en forte hausse
                    elif trend > 1.2:
                        return 1.20  # Bonne hausse
                    elif trend > 1.0:
                        return 1.10  # Légère hausse
                    elif trend < 0.5:
                        return 0.75  # Forte baisse
                    elif trend < 0.8:
                        return 0.85  # Légère baisse
                
                # Boost basé sur moyenne récente si pas de tendance claire
                if avg_scored_recent > 1.5:
                    return 1.20  # Très bon
                elif avg_scored_recent > 1.0:
                    return 1.10  # Bon
                elif avg_scored_recent > 0.5:
                    return 1.00  # Neutre
                elif avg_scored_recent > 0.25:
                    return 0.90  # Faible
                else:
                    return 0.80  # Très faible
        
        # Fallback: Utiliser recent_form globale (ancienne méthode)
        recent_form = venue_data.get('recent_form', {})
        avg_scored = recent_form.get('avg_goals_scored', 0)
        
        if avg_scored == 0:
            # Utiliser stats globales
            total_scored = venue_data.get('total_scored', 0)
            games_played = venue_data.get('games_played', 1)
            avg_scored_season = total_scored / max(games_played, 1)
            
            if avg_scored_season > 2.0:
                return 1.10
            elif avg_scored_season > 1.5:
                return 1.05
            elif avg_scored_season < 0.8:
                return 0.90
            else:
                return 1.0
        
        # Boost basé sur forme globale
        total_scored = venue_data.get('total_scored', 0)
        games_played = venue_data.get('games_played', 1)
        avg_scored_season = total_scored / max(games_played, 1)
        
        if avg_scored_season > 0:
            trend = avg_scored / avg_scored_season
            
            if trend > 1.3:
                return 1.25
            elif trend > 1.1:
                return 1.15
            elif trend > 0.9:
                return 1.05
            elif trend < 0.7:
                return 0.85
            else:
                return 0.95
        
        return 1.0  # Neutre par défaut
    def _calculate_saturation(self, current_score: Tuple[int, int], current_minute: int) -> float:
        """
        Calcule la saturation du match
        Plus il y a de buts, moins il y en aura (généralement)
        """
        total_goals = sum(current_score)
        
        # Buts attendus à cette minute (estimation : ~2.7 buts par match)
        expected_goals = (current_minute / 90) * 2.7
        
        # Différence
        goal_diff = total_goals - expected_goals
        
        # Facteur de saturation (max -30%)
        if goal_diff > 2:
            return 0.70  # Beaucoup trop de buts déjà
        elif goal_diff > 1:
            return 0.85  # Pas mal de buts
        elif goal_diff > 0:
            return 0.95  # Légèrement plus que prévu
        else:
            return 1.0   # Normal ou peu de buts
    
    def _interpret_danger_score(self, score):
        if score >= 4.5:
            return "ULTRA-DANGEREUX"
        elif score >= 3.5:
            return "DANGEREUX"
        elif score >= 2.5:
            return "MODERE"
        else:
            return "FAIBLE"
    
    def _generate_bet_recommendation(self, score, details, interp, current_minute):
        interval = details.get('interval', 'N/A')
        interval_end = int(interval.split('-')[1])
        minutes_left = interval_end - current_minute
        
        if score >= 4.0:
            action = f"PARIER MAINTENANT: But dans les {minutes_left} prochaines minutes (intervalle {interval})"
            confidence = "TRES HAUTE"
        elif score >= 3.0:
            action = f"PARIER: But probable dans les {minutes_left} prochaines minutes (intervalle {interval})"
            confidence = "HAUTE"
        else:
            action = f"EVITER: Peu probable dans cet intervalle {interval}"
            confidence = "FAIBLE"
        
        home_prob = details.get('home_goal_probability', 0)
        away_prob = details.get('away_goal_probability', 0)
        
        if home_prob > away_prob * 1.5:
            scorer = f"Domicile ({details.get('home_team')})"
        elif away_prob > home_prob * 1.5:
            scorer = f"Exterieur ({details.get('away_team')})"
        else:
            scorer = "Indetermine"
        
        return {
            'confidence': confidence,
            'action': action,
            'over_under': 'Over 0.5 buts',
            'likely_scorer': scorer,
            'home_goal_prob': f"{home_prob * 20:.0f}%",
            'away_goal_prob': f"{away_prob * 20:.0f}%",
            'minutes_left_in_interval': minutes_left
        }
