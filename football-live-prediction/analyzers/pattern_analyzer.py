"""
Pattern Analyzer - Version Home/Away/Overall
Analyse les patterns de buts avec distinction domicile/extérieur
"""
from typing import Dict, List
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger


class PatternAnalyzer:
    """Analyseur de patterns avec support Home/Away"""
    
    def __init__(self):
        self.logger = get_logger()
        self.logger.info("PatternAnalyzer initialized (Home/Away version)")
        self.DANGER_THRESHOLD = 0.5
        self.HIGH_DANGER_THRESHOLD = 0.7
    
    def analyze_team_profile(self, team_stats: Dict) -> Dict:
        """
        Analyse le profil complet d'une équipe (Overall + Home + Away)
        
        Args:
            team_stats: Stats avec 'overall', 'home', 'away'
            
        Returns:
            Profil analysé complet
        """
        team_name = team_stats.get('team', 'Unknown')
        self.logger.info(f"Analyzing profile for {team_name}")
        
        profile = {
            'team': team_name,
            'league': team_stats.get('league', 'Unknown'),
            'overall': None,
            'home': None,
            'away': None
        }
        
        # Analyser chaque venue
        for venue in ['overall', 'home', 'away']:
            if venue in team_stats:
                venue_data = team_stats[venue]
                profile[venue] = self._analyze_venue_stats(venue_data, venue)
        
        self.logger.success(f"Analysis complete for {team_name}")
        
        return profile
    
    def _analyze_venue_stats(self, venue_data: Dict, venue_name: str) -> Dict:
        """Analyse les stats d'un venue spécifique"""
        gp = int(venue_data.get('gp', 0))
        goals_by_interval = venue_data.get('goals_by_interval', {})
        first_half = venue_data.get('first_half', {})
        second_half = venue_data.get('second_half', {})
        
        # Identifier les zones de danger
        danger_zones = self._identify_danger_zones(goals_by_interval, gp)
        
        # Analyser le style de jeu
        play_style = self._analyze_play_style(goals_by_interval, first_half, second_half, gp)
        
        # Calculer les totaux
        total_scored = sum(interval.get('scored', 0) for interval in goals_by_interval.values())
        total_conceded = sum(interval.get('conceded', 0) for interval in goals_by_interval.values())
        
        return {
            'venue': venue_name,
            'games_played': gp,
            'total_scored': total_scored,
            'total_conceded': total_conceded,
            'goal_difference': total_scored - total_conceded,
            'goals_by_interval': goals_by_interval,
            'first_half_stats': first_half,
            'second_half_stats': second_half,
            'danger_zones': danger_zones,
            'play_style': play_style
        }
    
    def _identify_danger_zones(self, goals_by_interval: Dict, gp: int) -> List[Dict]:
        """Identifie les zones de danger"""
        danger_zones = []
        
        for interval, stats in goals_by_interval.items():
            scored = stats.get('scored', 0)
            conceded = stats.get('conceded', 0)
            total_goals = scored + conceded
            
            goals_per_game = total_goals / gp if gp > 0 else 0
            
            if goals_per_game >= self.HIGH_DANGER_THRESHOLD:
                intensity = 'high'
            elif goals_per_game >= self.DANGER_THRESHOLD:
                intensity = 'medium'
            else:
                continue
            
            danger_zones.append({
                'interval': interval,
                'goals_scored': scored,
                'goals_conceded': conceded,
                'total_goals': total_goals,
                'goals_per_game': round(goals_per_game, 2),
                'intensity': intensity
            })
        
        danger_zones.sort(key=lambda x: x['total_goals'], reverse=True)
        return danger_zones
    
    def _analyze_play_style(self, goals_by_interval: Dict, first_half: Dict, second_half: Dict, gp: int) -> Dict:
        """Analyse le style de jeu"""
        fh_scored = first_half.get('scored', 0)
        sh_scored = second_half.get('scored', 0)
        total_scored = fh_scored + sh_scored
        total_conceded = first_half.get('conceded', 0) + second_half.get('conceded', 0)
        
        characteristics = []
        
        if total_scored > total_conceded * 1.5:
            characteristics.append('offensive')
        elif total_conceded > total_scored * 1.5:
            characteristics.append('defensive')
        else:
            characteristics.append('balanced')
        
        fh_avg = fh_scored / gp if gp > 0 else 0
        sh_avg = sh_scored / gp if gp > 0 else 0
        
        if fh_avg > sh_avg * 1.3:
            characteristics.append('strong first half')
        elif sh_avg > fh_avg * 1.3:
            characteristics.append('strong second half')
        else:
            characteristics.append('consistent')
        
        return {
            'characteristics': characteristics,
            'summary': ', '.join(characteristics),
            'first_half_avg': round(fh_avg, 2),
            'second_half_avg': round(sh_avg, 2)
        }
    
    def save_team_profile(self, profile: Dict, output_dir: str = None) -> str:
        """Sauvegarde le profil complet (avec Home/Away)"""
        if output_dir is None:
            from utils.config_loader import get_config
            config = get_config()
            output_dir = config.get_data_directory('team_profiles')
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        team_name = profile['team'].lower().replace(' ', '_')
        filename = f"{team_name}_profile.json"
        filepath = output_path / filename
        
        # Ajouter date d'analyse
        from datetime import datetime
        profile['analysis_date'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        self.logger.success(f"Profile saved: {filepath}")
        return str(filepath)
    
    def load_team_profile(self, team_name: str, profiles_dir: str = None) -> Dict:
        """Charge le profil d'une équipe"""
        if profiles_dir is None:
            from utils.config_loader import get_config
            config = get_config()
            profiles_dir = config.get_data_directory('team_profiles')
        
        filename = f"{team_name.lower().replace(' ', '_')}_profile.json"
        filepath = Path(profiles_dir) / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        self.logger.info(f"Profile loaded: {team_name}")
        return profile
    
    def calculate_match_danger_score(
        self, 
        home_team_profile: Dict, 
        away_team_profile: Dict,
        interval: str
    ) -> Dict:
        """
        Calcule le score de danger pour un match spécifique
        Utilise les stats HOME de l'équipe à domicile et AWAY de l'équipe extérieure
        
        Args:
            home_team_profile: Profil de l'équipe à domicile
            away_team_profile: Profil de l'équipe à l'extérieur
            interval: Intervalle de temps (ex: "31-40")
            
        Returns:
            Dict avec les scores de danger
        """
        result = {
            'interval': interval,
            'home_team': home_team_profile['team'],
            'away_team': away_team_profile['team'],
            'home_attack_strength': 0,
            'away_defense_weakness': 0,
            'away_attack_strength': 0,
            'home_defense_weakness': 0,
            'home_goal_probability': 0,
            'away_goal_probability': 0,
            'total_goals_probability': 0
        }
        
        # Extraire les stats HOME de l'équipe à domicile
        if 'home' in home_team_profile and home_team_profile['home']:
            home_stats = home_team_profile['home']['goals_by_interval'].get(interval, {})
            result['home_attack_strength'] = home_stats.get('scored', 0)
            result['home_defense_weakness'] = home_stats.get('conceded', 0)
        
        # Extraire les stats AWAY de l'équipe extérieure
        if 'away' in away_team_profile and away_team_profile['away']:
            away_stats = away_team_profile['away']['goals_by_interval'].get(interval, {})
            result['away_attack_strength'] = away_stats.get('scored', 0)
            result['away_defense_weakness'] = away_stats.get('conceded', 0)
        
        # Calculer les probabilités de but
        # But de l'équipe à domicile = force attaque home + faiblesse défense away
        result['home_goal_probability'] = (
            result['home_attack_strength'] + result['away_defense_weakness']
        ) / 2
        
        # But de l'équipe extérieure = force attaque away + faiblesse défense home
        result['away_goal_probability'] = (
            result['away_attack_strength'] + result['home_defense_weakness']
        ) / 2
        
        # Probabilité totale de buts
        result['total_goals_probability'] = (
            result['home_goal_probability'] + result['away_goal_probability']
        )
        
        return result
