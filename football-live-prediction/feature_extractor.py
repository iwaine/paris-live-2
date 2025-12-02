"""
Feature extraction pipeline for ML model.
Converts live match stats into feature vectors for danger score prediction.

Features:
  - minute, minute_bucket (30-35, 35-40, etc.)
  - score_home, score_away, goal_diff
  - possession_home, possession_away
  - shots_home/away, sot_home/away
  - shot_deltas (last 5 min)
  - corners_home/away, red_cards, yellow_cards
  - team_elo_home, team_elo_away
  - recent_goal_count (last 10 min)
  - home_advantage (bool)
  - saturation_score (goals + shots in last X min)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """Feature vector for ML model."""
    minute: int
    minute_bucket: str  # "30-35", "75-80", etc.
    score_home: int
    score_away: int
    goal_diff: int  # home - away
    possession_home: float  # 0.0 - 1.0
    possession_away: float
    shots_home: int
    shots_away: int
    sot_home: int
    sot_away: int
    shot_sot_ratio_home: float  # sot / shots (capped at 1.0)
    shot_sot_ratio_away: float
    shots_delta_5m_home: int  # shots in last 5 min
    shots_delta_5m_away: int
    sot_delta_5m_home: int
    sot_delta_5m_away: int
    corners_home: int
    corners_away: int
    corners_delta_5m_home: int
    corners_delta_5m_away: int
    red_cards_home: int
    red_cards_away: int
    yellow_cards_home: int
    yellow_cards_away: int
    team_elo_home: float  # Elo rating ~1500
    team_elo_away: float
    elo_diff: float  # home - away
    home_advantage: float  # 0 or 1
    recent_goal_count_5m: int  # goals in last 5 min
    saturation_score: float  # (goals + shots_on_target) in last 10 min
    
    def to_dict(self) -> Dict:
        """Convert to dict for model input."""
        return {
            'minute': self.minute,
            'score_home': self.score_home,
            'score_away': self.score_away,
            'goal_diff': self.goal_diff,
            'possession_home': self.possession_home,
            'possession_away': self.possession_away,
            'shots_home': self.shots_home,
            'shots_away': self.shots_away,
            'sot_home': self.sot_home,
            'sot_away': self.sot_away,
            'shot_sot_ratio_home': self.shot_sot_ratio_home,
            'shot_sot_ratio_away': self.shot_sot_ratio_away,
            'shots_delta_5m_home': self.shots_delta_5m_home,
            'shots_delta_5m_away': self.shots_delta_5m_away,
            'sot_delta_5m_home': self.sot_delta_5m_home,
            'sot_delta_5m_away': self.sot_delta_5m_away,
            'corners_home': self.corners_home,
            'corners_away': self.corners_away,
            'corners_delta_5m_home': self.corners_delta_5m_home,
            'corners_delta_5m_away': self.corners_delta_5m_away,
            'red_cards_home': self.red_cards_home,
            'red_cards_away': self.red_cards_away,
            'yellow_cards_home': self.yellow_cards_home,
            'yellow_cards_away': self.yellow_cards_away,
            'team_elo_home': self.team_elo_home,
            'team_elo_away': self.team_elo_away,
            'elo_diff': self.elo_diff,
            'home_advantage': self.home_advantage,
            'recent_goal_count_5m': self.recent_goal_count_5m,
            'saturation_score': self.saturation_score,
        }


class FeatureExtractor:
    """
    Extract feature vectors from match snapshots and historical cache.
    """
    
    def __init__(self, team_elo_map: Optional[Dict[str, float]] = None):
        """
        Args:
            team_elo_map: Dict mapping team names to Elo ratings.
                         If None, defaults all teams to 1500.
        """
        self.team_elo_map = team_elo_map or {}
    
    @staticmethod
    def get_minute_bucket(minute: int) -> str:
        """Bucket minute into 5-min windows."""
        if minute < 45:
            # 1st half: 0-5, 5-10, ..., 40-45
            bucket_start = (minute // 5) * 5
            return f"{bucket_start}-{bucket_start + 5}"
        else:
            # 2nd half: 45-50, 50-55, ..., 85-90
            adjusted = minute - 45
            bucket_start = (adjusted // 5) * 5
            return f"{45 + bucket_start}-{45 + bucket_start + 5}"
    
    @staticmethod
    def safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safely compute ratio, cap at 1.0."""
        if denominator == 0:
            return default
        ratio = numerator / denominator
        return min(1.0, ratio)
    
    def get_team_elo(self, team_name: str) -> float:
        """Get Elo for team, default 1500."""
        return self.team_elo_map.get(team_name, 1500.0)
    
    def extract_deltas(
        self,
        snapshots: List,  # from SnapshotCache.snapshots
        window_sec: float = 300  # 5 minutes
    ) -> Dict:
        """
        Calculate deltas (changes) over a time window.
        
        Returns dict with keys like:
          shots_delta_home, sot_delta_home, corners_delta_home, etc.
        """
        if len(snapshots) < 2:
            return {
                'shots_delta_home': 0, 'shots_delta_away': 0,
                'sot_delta_home': 0, 'sot_delta_away': 0,
                'corners_delta_home': 0, 'corners_delta_away': 0,
                'goal_count': 0,
            }
        
        import time
        now = time.time()
        recent = [s for s in snapshots if now - s.timestamp <= window_sec]
        
        if len(recent) < 2:
            return {
                'shots_delta_home': 0, 'shots_delta_away': 0,
                'sot_delta_home': 0, 'sot_delta_away': 0,
                'corners_delta_home': 0, 'corners_delta_away': 0,
                'goal_count': 0,
            }
        
        first, last = recent[0], recent[-1]
        
        return {
            'shots_delta_home': (last.shots_home or 0) - (first.shots_home or 0),
            'shots_delta_away': (last.shots_away or 0) - (first.shots_away or 0),
            'sot_delta_home': (last.sot_home or 0) - (first.sot_home or 0),
            'sot_delta_away': (last.sot_away or 0) - (first.sot_away or 0),
            'corners_delta_home': (last.corners_home or 0) - (first.corners_home or 0),
            'corners_delta_away': (last.corners_away or 0) - (first.corners_away or 0),
            'goal_count': (last.score_home or 0) + (last.score_away or 0) - (first.score_home or 0) - (first.score_away or 0),
        }
    
    def extract_saturation_score(
        self,
        snapshots: List,
        window_sec: float = 600  # 10 minutes
    ) -> float:
        """
        Saturation = measure of recent activity (goals + shots on target).
        Helps detect if match is "open" (high saturation) or "defensive" (low).
        
        Returns: float 0-100 (rough score)
        """
        if len(snapshots) < 2:
            return 0.0
        
        import time
        now = time.time()
        recent = [s for s in snapshots if now - s.timestamp <= window_sec]
        
        if not recent:
            return 0.0
        
        first, last = recent[0], recent[-1]
        
        # Goal count in window
        goals_in_window = (last.score_home or 0) + (last.score_away or 0) - (first.score_home or 0) - (first.score_away or 0)
        
        # Total shots on target in window
        sot_in_window = (last.sot_home or 0) + (last.sot_away or 0) - (first.sot_home or 0) - (first.sot_away or 0)
        
        # Simple formula: (goals * 10) + (sot / 2)
        saturation = (goals_in_window * 10) + (sot_in_window / 2)
        
        return min(100, saturation)
    
    def extract_features(
        self,
        current_stats,  # MatchStats object
        snapshots: List,  # from SnapshotCache
        home_team: str,
        away_team: str,
    ) -> FeatureVector:
        """
        Extract full feature vector from current match state.
        
        Args:
            current_stats: MatchStats object (current snapshot)
            snapshots: List of historical MatchStats snapshots
            home_team: Home team name (for Elo lookup)
            away_team: Away team name (for Elo lookup)
        
        Returns:
            FeatureVector
        """
        
        # Deltas over 5 min window
        deltas_5m = self.extract_deltas(snapshots, window_sec=300)
        
        # Saturation over 10 min window
        saturation = self.extract_saturation_score(snapshots, window_sec=600)
        
        # Extract scalar features
        minute = current_stats.minute or 0
        score_home = current_stats.score_home or 0
        score_away = current_stats.score_away or 0
        possession_home = current_stats.possession_home or 0.5
        possession_away = current_stats.possession_away or 0.5
        shots_home = current_stats.shots_home or 0
        shots_away = current_stats.shots_away or 0
        sot_home = current_stats.sot_home or 0
        sot_away = current_stats.sot_away or 0
        corners_home = current_stats.corners_home or 0
        corners_away = current_stats.corners_away or 0
        red_cards_home = current_stats.red_cards_home or 0
        red_cards_away = current_stats.red_cards_away or 0
        yellow_cards_home = current_stats.yellow_cards_home or 0
        yellow_cards_away = current_stats.yellow_cards_away or 0
        
        # Build feature vector
        features = FeatureVector(
            minute=minute,
            minute_bucket=self.get_minute_bucket(minute),
            score_home=score_home,
            score_away=score_away,
            goal_diff=score_home - score_away,
            possession_home=possession_home,
            possession_away=possession_away,
            shots_home=shots_home,
            shots_away=shots_away,
            sot_home=sot_home,
            sot_away=sot_away,
            shot_sot_ratio_home=self.safe_ratio(sot_home, shots_home),
            shot_sot_ratio_away=self.safe_ratio(sot_away, shots_away),
            shots_delta_5m_home=deltas_5m.get('shots_delta_home', 0),
            shots_delta_5m_away=deltas_5m.get('shots_delta_away', 0),
            sot_delta_5m_home=deltas_5m.get('sot_delta_home', 0),
            sot_delta_5m_away=deltas_5m.get('sot_delta_away', 0),
            corners_home=corners_home,
            corners_away=corners_away,
            corners_delta_5m_home=deltas_5m.get('corners_delta_home', 0),
            corners_delta_5m_away=deltas_5m.get('corners_delta_away', 0),
            red_cards_home=red_cards_home,
            red_cards_away=red_cards_away,
            yellow_cards_home=yellow_cards_home,
            yellow_cards_away=yellow_cards_away,
            team_elo_home=self.get_team_elo(home_team),
            team_elo_away=self.get_team_elo(away_team),
            elo_diff=self.get_team_elo(home_team) - self.get_team_elo(away_team),
            home_advantage=1.0,  # Always true by definition
            recent_goal_count_5m=deltas_5m.get('goal_count', 0),
            saturation_score=saturation,
        )
        
        logger.debug(f"Features extracted: minute={features.minute}, "
                    f"score={features.score_home}-{features.score_away}, "
                    f"possession={features.possession_home:.1%}-{features.possession_away:.1%}, "
                    f"saturation={features.saturation_score:.1f}")
        
        return features


# Test: example usage
if __name__ == "__main__":
    from headless_parser_prototype import MatchStats
    
    # Create mock snapshots
    stats_1 = MatchStats(
        timestamp=1000,
        minute=30,
        score_home=0, score_away=0,
        possession_home=0.55, possession_away=0.45,
        shots_home=2, shots_away=1,
        sot_home=1, sot_away=0,
        corners_home=1, corners_away=0,
        red_cards_home=0, red_cards_away=0,
        yellow_cards_home=0, yellow_cards_away=0,
    )
    
    stats_2 = MatchStats(
        timestamp=1150,  # +150 sec
        minute=32,
        score_home=1, score_away=0,
        possession_home=0.58, possession_away=0.42,
        shots_home=5, shots_away=1,
        sot_home=2, sot_away=0,
        corners_home=2, corners_away=0,
        red_cards_home=0, red_cards_away=0,
        yellow_cards_home=0, yellow_cards_away=0,
    )
    
    snapshots = [stats_1, stats_2]
    
    # Extract features
    extractor = FeatureExtractor(team_elo_map={'Arsenal': 1620, 'Chelsea': 1580})
    
    features = extractor.extract_features(
        current_stats=stats_2,
        snapshots=snapshots,
        home_team='Arsenal',
        away_team='Chelsea',
    )
    
    print("=" * 80)
    print("FEATURE VECTOR EXAMPLE")
    print("=" * 80)
    print(f"Minute: {features.minute} (bucket: {features.minute_bucket})")
    print(f"Score: {features.score_home}-{features.score_away} (diff: {features.goal_diff})")
    print(f"Possession: {features.possession_home:.1%} - {features.possession_away:.1%}")
    print(f"Shots: {features.shots_home} vs {features.shots_away} "
          f"(SOT: {features.sot_home} vs {features.sot_away})")
    print(f"Shot ratios: {features.shot_sot_ratio_home:.2f} vs {features.shot_sot_ratio_away:.2f}")
    print(f"Deltas (5m): shots +{features.shots_delta_5m_home} vs +{features.shots_delta_5m_away}, "
          f"SOT +{features.sot_delta_5m_home} vs +{features.sot_delta_5m_away}")
    print(f"Corners: {features.corners_home} vs {features.corners_away} "
          f"(delta: +{features.corners_delta_5m_home} vs +{features.corners_delta_5m_away})")
    print(f"Red cards: {features.red_cards_home} vs {features.red_cards_away}")
    print(f"Elo: {features.team_elo_home:.0f} vs {features.team_elo_away:.0f} (diff: {features.elo_diff:+.0f})")
    print(f"Recent goals (5m): {features.recent_goal_count_5m}")
    print(f"Saturation score (10m): {features.saturation_score:.1f}")
    print("\nFeature dict (for ML):")
    import json
    print(json.dumps(features.to_dict(), indent=2))
