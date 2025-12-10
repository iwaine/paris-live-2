"""
Pattern Analyzer - Version compatible avec structure Overall
"""
from typing import Dict, List
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger


class PatternAnalyzer:
    def __init__(self):
        self.logger = get_logger()
        self.logger.info("PatternAnalyzer initialized")
        self.DANGER_THRESHOLD = 0.5
        self.HIGH_DANGER_THRESHOLD = 0.7
    
    def analyze_team_profile(self, team_stats: Dict) -> Dict:
        team_name = team_stats.get('team', 'Unknown')
        self.logger.info(f"Analyzing profile for {team_name}")
        
        gp = int(team_stats.get('gp', 0))
        goals_by_interval = team_stats.get('goals_by_interval', {})
        first_half = team_stats.get('first_half', {})
        second_half = team_stats.get('second_half', {})
        
        danger_zones = self._identify_danger_zones(goals_by_interval, gp)
        play_style = self._analyze_play_style(goals_by_interval, first_half, second_half, gp)
        
        total_scored = sum(interval['scored'] for interval in goals_by_interval.values())
        total_conceded = sum(interval['conceded'] for interval in goals_by_interval.values())
        
        profile = {
            'team': team_name,
            'league': 'Unknown',
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
        
        return profile
    
    def _identify_danger_zones(self, goals_by_interval: Dict, gp: int) -> List[Dict]:
        danger_zones = []
        for interval, stats in goals_by_interval.items():
            total_goals = stats.get('scored', 0) + stats.get('conceded', 0)
            goals_per_game = total_goals / gp if gp > 0 else 0
            
            if goals_per_game >= self.HIGH_DANGER_THRESHOLD:
                intensity = 'high'
            elif goals_per_game >= self.DANGER_THRESHOLD:
                intensity = 'medium'
            else:
                continue
            
            danger_zones.append({
                'interval': interval,
                'total_goals': total_goals,
                'goals_per_game': round(goals_per_game, 2),
                'intensity': intensity
            })
        
        danger_zones.sort(key=lambda x: x['total_goals'], reverse=True)
        return danger_zones
    
    def _analyze_play_style(self, goals_by_interval: Dict, first_half: Dict, second_half: Dict, gp: int) -> Dict:
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
        
        return {'characteristics': characteristics, 'summary': ', '.join(characteristics)}
    
    def save_team_profile(self, profile: Dict, output_dir: str = None) -> str:
        if output_dir is None:
            from utils.config_loader import get_config
            config = get_config()
            output_dir = config.get_data_directory('team_profiles')
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        team_name = profile['team'].lower().replace(' ', '_')
        filename = f"{team_name}_profile.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        self.logger.success(f"Profile saved: {filepath}")
        return str(filepath)
    
    def load_team_profile(self, team_name: str, profiles_dir: str = None) -> Dict:
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
