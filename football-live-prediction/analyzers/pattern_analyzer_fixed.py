"""
Pattern Analyzer - Version compatible avec structure Overall
Analyse les patterns de buts par intervalle de temps
"""
from typing import Dict, List
from pathlib import Path
import json

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


class PatternAnalyzer:
    """Analyseur de patterns de buts"""
    
    def __init__(self):
        """Initialise l'analyseur"""
        self.logger = get_logger()
        self.logger.info("PatternAnalyzer initialized")
        
        # Seuils pour déterminer les zones de danger
        self.DANGER_THRESHOLD = 0.5  # 50% des matchs avec but
        self.HIGH_DANGER_THRESHOLD = 0.7  # 70% des matchs avec but
    
    def analyze_team_profile(self, team_stats: Dict) -> Dict:
        """
        Analyse le profil d'une équipe
        
        Args:
            team_stats: Stats de l'équipe (format Overall)
            
        Returns:
            Profil analysé avec zones de danger
        """
        team_name = team_stats.get('team', 'Unknown')
        self.logger.info(f"Analyzing profile for {team_name}")
        
        # Extraire les données
        gp = int(team_stats.get('gp', 0))
        goals_by_interval = team_stats.get('goals_by_interval', {})
        first_half = team_stats.get('first_half', {})
        second_half = team_stats.get('second_half', {})
        
        # Identifier les zones de danger
        danger_zones = self._identify_danger_zones(goals_by_interval, gp)
        
        # Analyser le style de jeu
        play_style = self._analyze_play_style(
            goals_by_interval, 
            first_half, 
            second_half, 
            gp
        )
        
        # Calculer les totaux
        total_scored = sum(interval['scored'] for interval in goals_by_interval.values())
        total_conceded = sum(interval['conceded'] for interval in goals_by_interval.values())
        
        # Construire le profil
        profile = {
            'team': team_name,
            'league': 'Unknown',  # Sera rempli par setup_profiles
            'games_played': gp,
            'total_scored': total_scored,
            'total_conceded': total_conceded,
            'goal_difference': total_scored - total_conceded,
            'goals_by_interval': goals_by_interval,
            'first_half_stats': first_half,
            'second_half_stats': second_half,
            'danger_zones': danger_zones,
            'play_style': play_style,
            'analysis_date': None  # Sera rempli lors de la sauvegarde
        }
        
        self.logger.info(f"Analysis complete: {len(danger_zones)} danger zones identified")
        
        return profile
    
    def _identify_danger_zones(self, goals_by_interval: Dict, gp: int) -> List[Dict]:
        """
        Identifie les zones de danger (intervalles avec beaucoup de buts)
        
        Args:
            goals_by_interval: Buts par intervalle
            gp: Nombre de matchs joués
            
        Returns:
            Liste des zones de danger
        """
        danger_zones = []
        
        for interval, stats in goals_by_interval.items():
            scored = stats.get('scored', 0)
            conceded = stats.get('conceded', 0)
            total_goals = scored + conceded
            
            # Calculer le taux de buts par match
            goals_per_game = total_goals / gp if gp > 0 else 0
            
            # Déterminer l'intensité
            if goals_per_game >= self.HIGH_DANGER_THRESHOLD:
                intensity = 'high'
            elif goals_per_game >= self.DANGER_THRESHOLD:
                intensity = 'medium'
            else:
                continue  # Pas une zone de danger
            
            danger_zones.append({
                'interval': interval,
                'goals_scored': scored,
                'goals_conceded': conceded,
                'total_goals': total_goals,
                'goals_per_game': round(goals_per_game, 2),
                'intensity': intensity
            })
        
        # Trier par intensité et nombre de buts
        danger_zones.sort(key=lambda x: (x['intensity'] == 'high', x['total_goals']), reverse=True)
        
        self.logger.info(f"Identified {len(danger_zones)} danger zones")
        
        return danger_zones
    
    def _analyze_play_style(
        self, 
        goals_by_interval: Dict, 
        first_half: Dict, 
        second_half: Dict,
        gp: int
    ) -> Dict:
        """
        Analyse le style de jeu de l'équipe
        
        Args:
            goals_by_interval: Buts par intervalle
            first_half: Stats première mi-temps
            second_half: Stats deuxième mi-temps
            gp: Nombre de matchs
            
        Returns:
            Analyse du style de jeu
        """
        # Calculer moyennes par mi-temps
        fh_scored = first_half.get('scored', 0)
        fh_conceded = first_half.get('conceded', 0)
        sh_scored = second_half.get('scored', 0)
        sh_conceded = second_half.get('conceded', 0)
        
        fh_avg = fh_scored / gp if gp > 0 else 0
        sh_avg = sh_scored / gp if gp > 0 else 0
        
        # Déterminer les caractéristiques
        characteristics = []
        
        # Offensive vs Défensive
        total_scored = fh_scored + sh_scored
        total_conceded = fh_conceded + sh_conceded
        
        if total_scored > total_conceded * 1.5:
            characteristics.append('offensive')
        elif total_conceded > total_scored * 1.5:
            characteristics.append('defensive')
        else:
            characteristics.append('balanced')
        
        # Forte première ou deuxième mi-temps
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
    
    def calculate_goal_probability(
        self, 
        team_stats: Dict, 
        interval: str, 
        venue: str = 'overall'
    ) -> float:
        """
        Calcule la probabilité de but dans un intervalle
        
        Args:
            team_stats: Stats de l'équipe
            interval: Intervalle (ex: "31-40")
            venue: overall/home/away
            
        Returns:
            Probabilité (0-1)
        """
        goals_by_interval = team_stats.get('goals_by_interval', {})
        gp = int(team_stats.get('gp', 0))
        
        if interval not in goals_by_interval or gp == 0:
            return 0.0
        
        stats = goals_by_interval[interval]
        total_goals = stats.get('scored', 0) + stats.get('conceded', 0)
        
        # Probabilité = nombre de matchs avec but / nombre total de matchs
        probability = min(total_goals / gp, 1.0)
        
        return round(probability, 3)
    
    def save_team_profile(self, profile: Dict, output_dir: str = None) -> str:
        """
        Sauvegarde le profil d'une équipe en JSON
        
        Args:
            profile: Profil à sauvegarder
            output_dir: Répertoire de sortie
            
        Returns:
            Chemin du fichier sauvegardé
        """
        if output_dir is None:
            from utils.config_loader import get_config
            config = get_config()
            output_dir = config.get_data_directory('team_profiles')
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Nom du fichier
        team_name = profile['team'].lower().replace(' ', '_')
        filename = f"{team_name}_profile.json"
        filepath = output_path / filename
        
        # Ajouter date d'analyse
        from datetime import datetime
        profile['analysis_date'] = datetime.now().isoformat()
        
        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        self.logger.success(f"Profile saved: {filepath}")
        
        return str(filepath)
    
    def load_team_profile(self, team_name: str, profiles_dir: str = None) -> Dict:
        """
        Charge le profil d'une équipe depuis JSON
        
        Args:
            team_name: Nom de l'équipe
            profiles_dir: Répertoire des profils
            
        Returns:
            Profil de l'équipe
        """
        if profiles_dir is None:
            from utils.config_loader import get_config
            config = get_config()
            profiles_dir = config.get_data_directory('team_profiles')
        
        # Nom du fichier
        filename = f"{team_name.lower().replace(' ', '_')}_profile.json"
        filepath = Path(profiles_dir) / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Profile not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        self.logger.info(f"Profile loaded: {team_name}")
        
        return profile
