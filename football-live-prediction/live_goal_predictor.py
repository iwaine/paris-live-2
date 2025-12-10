#!/usr/bin/env python3
"""
Live Goal Predictor with Recurrence Integration
Combines live match data with historical recurrence patterns
to predict goal probability in critical intervals.
"""

import sqlite3
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import math

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RecurrenceData:
    """Recurrence statistics for a team in a specific context."""
    team_name: str
    is_home: bool
    interval_name: str
    
    # Goals scored
    goals_scored: int
    matches_with_goals_scored: int
    freq_goals_scored: float
    avg_minute_scored: Optional[float]
    std_minute_scored: Optional[float]
    
    # Goals conceded
    goals_conceded: int
    matches_with_goals_conceded: int
    freq_goals_conceded: float
    avg_minute_conceded: Optional[float]
    std_minute_conceded: Optional[float]
    
    total_matches: int


@dataclass
class GlobalStats:
    """Global team statistics (all matches)."""
    team_name: str
    is_home: bool
    total_matches: int
    goals_frequency: float
    avg_goals_per_match: float


@dataclass
class RecentForm:
    """Recent form statistics (last 4 matches)."""
    team_name: str
    is_home: bool
    interval_name: str
    recent_matches: int
    recent_goals: int
    recent_frequency: float


@dataclass
class LiveMatchStats:
    """Current live match statistics."""
    minute: int
    score_home: int
    score_away: int
    possession_home: float
    possession_away: float
    shots_home: int
    shots_away: int
    sot_home: int
    sot_away: int
    dangerous_attacks_home: int
    dangerous_attacks_away: int


@dataclass
class GoalPrediction:
    """Goal prediction result."""
    team: str
    probability: float
    confidence: str  # LOW, MEDIUM, HIGH, CRITICAL
    reasoning: str
    recurrence_match: bool
    time_to_critical_minute: Optional[int]


class LiveGoalPredictor:
    """Predict goals using live stats + historical recurrence."""
    
    # Intervalles critiques (incluant temps additionnel)
    INTERVAL_1 = (31, 47, "31-45+")  # 31-45 + ~2min stoppage time
    INTERVAL_2 = (75, 95, "75-90+")  # 75-90 + ~5min stoppage time
    
    def __init__(self, db_path='data/predictions.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def _get_current_interval(self, minute: int) -> Optional[Tuple[int, int, str]]:
        """Get current critical interval if in one."""
        if self.INTERVAL_1[0] <= minute <= self.INTERVAL_1[1]:
            return self.INTERVAL_1
        elif self.INTERVAL_2[0] <= minute <= self.INTERVAL_2[1]:
            return self.INTERVAL_2
        return None
    
    def _load_recurrence(self, team_name: str, is_home: bool, interval_name: str) -> Optional[RecurrenceData]:
        """Load recurrence data for team in specific context."""
        self.cursor.execute('''
            SELECT 
                team_name, is_home, interval_name,
                goals_scored, matches_with_goals_scored, freq_goals_scored, 
                avg_minute_scored, std_minute_scored,
                goals_conceded, matches_with_goals_conceded, freq_goals_conceded, 
                avg_minute_conceded, std_minute_conceded,
                total_matches
            FROM team_critical_intervals
            WHERE team_name = ? AND is_home = ? AND interval_name = ?
        ''', (team_name, is_home, interval_name))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return RecurrenceData(*row)
    
    def _load_global_stats(self, team_name: str, is_home: bool) -> Optional[GlobalStats]:
        """Load global team statistics."""
        self.cursor.execute('''
            SELECT team_name, is_home, total_matches, goals_frequency, avg_goals_per_match
            FROM team_global_stats
            WHERE team_name = ? AND is_home = ?
        ''', (team_name, is_home))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return GlobalStats(*row)
    
    def _load_recent_form(self, team_name: str, is_home: bool, interval_name: str) -> Optional[RecentForm]:
        """Load recent form statistics."""
        self.cursor.execute('''
            SELECT team_name, is_home, interval_name, recent_matches, 
                   recent_goals, recent_frequency
            FROM team_recent_form
            WHERE team_name = ? AND is_home = ? AND interval_name = ?
        ''', (team_name, is_home, interval_name))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return RecentForm(*row)
    
    def _calculate_proximity_score(self, current_minute: int, avg_minute: Optional[float], 
                                   std_minute: Optional[float]) -> float:
        """
        Calculate how close we are to the typical goal minute.
        Returns 0.0 to 1.0 (1.0 = exactly at avg minute)
        """
        if avg_minute is None or std_minute is None:
            return 0.5  # neutral if no data
        
        # Distance from average in standard deviations
        distance = abs(current_minute - avg_minute)
        
        if std_minute == 0:
            # All goals at exact same minute
            return 1.0 if distance == 0 else 0.3
        
        # Gaussian-like decay
        # Within 1 std: high score
        # Beyond 2 std: low score
        normalized_distance = distance / std_minute
        proximity = math.exp(-0.5 * normalized_distance ** 2)
        
        return proximity
    
    def _calculate_live_momentum(self, live_stats: LiveMatchStats, for_home: bool) -> float:
        """
        Calculate current momentum based on live stats.
        Returns 0.0 to 1.0
        """
        if for_home:
            possession = live_stats.possession_home
            shots = live_stats.shots_home
            sot = live_stats.sot_home
            attacks = live_stats.dangerous_attacks_home
            
            opp_possession = live_stats.possession_away
            opp_shots = live_stats.shots_away
        else:
            possession = live_stats.possession_away
            shots = live_stats.shots_away
            sot = live_stats.sot_away
            attacks = live_stats.dangerous_attacks_away
            
            opp_possession = live_stats.possession_home
            opp_shots = live_stats.shots_home
        
        # Weighted momentum score
        momentum = 0.0
        
        # Possession (30%)
        momentum += 0.3 * possession
        
        # Shot dominance (40%)
        total_shots = shots + opp_shots
        if total_shots > 0:
            shot_ratio = shots / total_shots
            momentum += 0.4 * shot_ratio
        
        # Shots on target quality (20%)
        if shots > 0:
            sot_ratio = sot / shots
            momentum += 0.2 * sot_ratio
        
        # Dangerous attacks (10%)
        if attacks > 0:
            momentum += 0.1 * min(attacks / 5, 1.0)  # cap at 5 attacks
        
        return min(momentum, 1.0)
    
    def predict_goal(self, home_team: str, away_team: str, 
                    live_stats: LiveMatchStats) -> Dict[str, GoalPrediction]:
        """
        Predict goal probability for both teams.
        Returns dict with 'home' and 'away' predictions.
        """
        current_interval = self._get_current_interval(live_stats.minute)
        
        predictions = {}
        
        # Predict for home team
        predictions['home'] = self._predict_for_team(
            team_name=home_team,
            is_home=True,
            live_stats=live_stats,
            current_interval=current_interval
        )
        
        # Predict for away team
        predictions['away'] = self._predict_for_team(
            team_name=away_team,
            is_home=False,
            live_stats=live_stats,
            current_interval=current_interval
        )
        
        return predictions
    
    def _predict_for_team(self, team_name: str, is_home: bool, 
                         live_stats: LiveMatchStats,
                         current_interval: Optional[Tuple]) -> GoalPrediction:
        """Predict goal for specific team."""
        
        if current_interval is None:
            # Not in critical interval
            return GoalPrediction(
                team=team_name,
                probability=0.1,
                confidence="LOW",
                reasoning="Not in critical interval (31-45 or 76-90)",
                recurrence_match=False,
                time_to_critical_minute=None
            )
        
        interval_min, interval_max, interval_name = current_interval
        
        # Load recurrence data
        recurrence = self._load_recurrence(team_name, is_home, interval_name)
        
        # CRITICAL: Need at least 3 DIFFERENT matches with goals for valid recurrence
        if recurrence is None or recurrence.total_matches < 3 or recurrence.matches_with_goals_scored < 3:
            # Insufficient historical data or no real recurrence pattern
            reason = "Insufficient historical data"
            if recurrence and recurrence.matches_with_goals_scored < 3:
                reason = f"No recurrence: only {recurrence.matches_with_goals_scored} matches with goals (need ≥3)"
            
            return GoalPrediction(
                team=team_name,
                probability=0.2,
                confidence="LOW",
                reasoning=f"{reason} for {team_name} ({'home' if is_home else 'away'}) in {interval_name}",
                recurrence_match=False,
                time_to_critical_minute=None
            )
        
        # Load additional stats
        global_stats = self._load_global_stats(team_name, is_home)
        recent_form = self._load_recent_form(team_name, is_home, interval_name)
        
        # Calculate components with new weights:
        # 20% Global baseline
        # 40% Historical interval pattern
        # 25% Recent form (last 4 matches)
        # 15% Live momentum
        
        # 1. Global baseline (20% weight)
        global_score = global_stats.goals_frequency if global_stats else 0.5
        
        # 2. Historical interval frequency (40% weight)
        interval_score = recurrence.freq_goals_scored
        
        # 3. Recent form (25% weight)
        recent_score = recent_form.recent_frequency if recent_form and recent_form.recent_matches >= 3 else interval_score
        
        # 4. Proximity to typical goal minute (boost factor, not direct weight)
        proximity = self._calculate_proximity_score(
            live_stats.minute,
            recurrence.avg_minute_scored,
            recurrence.std_minute_scored
        )
        
        # 5. Current live momentum (15% weight)
        momentum = self._calculate_live_momentum(live_stats, is_home)
        
        # Combined probability
        base_probability = (0.20 * global_score) + (0.40 * interval_score) + \
                          (0.25 * recent_score) + (0.15 * momentum)
        
        # Apply proximity boost (multiply by 0.7 to 1.3 based on proximity)
        proximity_multiplier = 0.7 + (0.6 * proximity)
        probability = base_probability * proximity_multiplier
        probability = min(probability, 0.95)  # cap at 95%
        
        # Confidence level
        if probability >= 0.7:
            confidence = "CRITICAL"
        elif probability >= 0.5:
            confidence = "HIGH"
        elif probability >= 0.3:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # Time to critical minute
        time_to_critical = None
        if recurrence.avg_minute_scored:
            time_to_critical = int(recurrence.avg_minute_scored - live_stats.minute)
        
        # Reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Global: {global_score:.2f}")
        reasoning_parts.append(f"Interval: {recurrence.goals_scored} goals in {recurrence.total_matches} matches (freq={interval_score:.2f})")
        
        if recent_form and recent_form.recent_matches >= 3:
            reasoning_parts.append(f"Recent: {recent_form.recent_goals} in last {recent_form.recent_matches} (freq={recent_score:.2f})")
        
        if recurrence.avg_minute_scored:
            reasoning_parts.append(f"Typical: {recurrence.avg_minute_scored:.1f}±{recurrence.std_minute_scored:.1f}min")
            reasoning_parts.append(f"Proximity: {proximity:.2f}")
        
        reasoning_parts.append(f"Momentum: {momentum:.2f}")
        reasoning_parts.append(f"Final: {probability:.2f}")
        
        reasoning = " | ".join(reasoning_parts)
        
        return GoalPrediction(
            team=team_name,
            probability=probability,
            confidence=confidence,
            reasoning=reasoning,
            recurrence_match=True,
            time_to_critical_minute=time_to_critical
        )


def demo_prediction():
    """Demo prediction with sample data."""
    
    predictor = LiveGoalPredictor()
    
    print("\n" + "="*80)
    print("🎯 DEMO: LIVE GOAL PREDICTION WITH RECURRENCE")
    print("="*80)
    
    # Scenario 1: Angers vs Marseille, minute 80, Angers dominating
    print("\n📊 SCENARIO 1: Angers (home) vs Marseille, minute 80")
    print("-" * 80)
    
    live_stats = LiveMatchStats(
        minute=80,
        score_home=1,
        score_away=1,
        possession_home=0.58,
        possession_away=0.42,
        shots_home=12,
        shots_away=7,
        sot_home=5,
        sot_away=2,
        dangerous_attacks_home=8,
        dangerous_attacks_away=3
    )
    
    predictions = predictor.predict_goal("Angers", "Marseille", live_stats)
    
    for team_type, pred in predictions.items():
        print(f"\n{team_type.upper()}: {pred.team}")
        print(f"  Probability: {pred.probability:.1%}")
        print(f"  Confidence: {pred.confidence}")
        print(f"  Time to critical: {pred.time_to_critical_minute} min" if pred.time_to_critical_minute else "  N/A")
        print(f"  Reasoning: {pred.reasoning}")
    
    # Scenario 2: PSG away, minute 40
    print("\n" + "="*80)
    print("📊 SCENARIO 2: Lyon (home) vs PSG (away), minute 40")
    print("-" * 80)
    
    live_stats2 = LiveMatchStats(
        minute=40,
        score_home=0,
        score_away=1,
        possession_home=0.45,
        possession_away=0.55,
        shots_home=5,
        shots_away=8,
        sot_home=2,
        sot_away=4,
        dangerous_attacks_home=3,
        dangerous_attacks_away=6
    )
    
    predictions2 = predictor.predict_goal("Lyon", "PSG", live_stats2)
    
    for team_type, pred in predictions2.items():
        print(f"\n{team_type.upper()}: {pred.team}")
        print(f"  Probability: {pred.probability:.1%}")
        print(f"  Confidence: {pred.confidence}")
        print(f"  Time to critical: {pred.time_to_critical_minute} min" if pred.time_to_critical_minute else "  N/A")
        print(f"  Reasoning: {pred.reasoning}")
    
    predictor.close()
    
    print("\n" + "="*80)
    print("✅ Demo complete!")
    print("="*80)


if __name__ == "__main__":
    demo_prediction()
