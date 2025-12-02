#!/usr/bin/env python3
"""
Phase 3: Complete Live Prediction Pipeline

Integrates all Phase 1-3 components into a unified real-time betting system:
  1. Headless parser → Live match stats extraction
  2. Feature extractor → 23 ML-ready features
  3. ML model → Danger score calculation
  4. Penalty detection → Market suspension
  5. TTL manager → Freshness decay
  6. Error handler → Auto-recovery
  7. Output → Betting decision signals

Architecture: Streaming pipeline (match snapshots → danger scores)

Usage:
  pipeline = LivePredictionPipeline()
  pipeline.initialize()
  
  while True:
    live_stats = parser.capture_snapshot()
    decision = pipeline.process_snapshot(live_stats)
    if decision['should_bet']:
      emit_telegram_alert(decision)
"""

import json
import logging
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BettingDecision:
    """Final betting decision output."""
    should_bet: bool
    reason: str
    danger_score: float  # 0-100
    confidence: float  # 0-1 (after freshness decay)
    freshness_factor: float  # e^(-t/TTL)
    market_suspended: bool
    penalty_ttl_seconds: int
    signal_age_seconds: float
    interval: Tuple[int, int]
    match_id: str
    minute: int
    home_team: str
    away_team: str
    score: str
    timestamp: float
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        d['interval'] = list(d['interval'])
        return d


class LivePredictionPipeline:
    """
    Complete Phase 3 live prediction pipeline.
    
    Processes live match data → decision signals.
    """
    
    def __init__(self, model_path: str = 'models/au_moins_1_but_model.pkl',
                 scaler_path: str = 'models/scaler.pkl',
                 confidence_threshold: float = 0.35,
                 danger_score_threshold: float = 40.0):
        """Initialize pipeline with pre-trained models."""
        self.model = None
        self.scaler = None
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.confidence_threshold = confidence_threshold
        self.danger_score_threshold = danger_score_threshold
        
        # Import components
        from signal_ttl_manager import SignalTTLManager, DynamicTTLManager
        self.ttl_manager = SignalTTLManager(ttl_seconds=300, confidence_threshold=0.3)
        self.dynamic_ttl = DynamicTTLManager(base_ttl=300)
        
        # Penalty state machine
        self.penalty_state = "NORMAL"
        self.penalty_suspension_until = None
        
        # Statistics
        self.decisions_history = []
        self.bets_triggered = 0
        self.bets_filtered = 0
    
    def initialize(self) -> bool:
        """Load pre-trained models."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"✅ Pipeline initialized")
            logger.info(f"   Model: {self.model_path}")
            logger.info(f"   Scaler: {self.scaler_path}")
            logger.info(f"   Confidence threshold: {self.confidence_threshold:.2f}")
            logger.info(f"   Danger score threshold: {self.danger_score_threshold:.1f}%")
            return True
        except FileNotFoundError as e:
            logger.error(f"❌ Failed to initialize pipeline: {e}")
            return False
    
    def calculate_danger_score(self, features: Dict) -> Dict:
        """Calculate raw danger score from features."""
        if not self.model or not self.scaler:
            return {'danger_score': 0.0, 'probability': 0.0, 'error': 'Model not loaded'}
        
        feature_cols = [
            'minute', 'minute_bucket', 'score_home', 'score_away', 'goal_diff',
            'poss_home', 'poss_away', 'shots_home', 'shots_away', 'sot_home', 'sot_away',
            'shot_accuracy', 'sot_ratio', 'shot_delta_5m', 'sot_delta_5m', 'corner_delta_5m',
            'red_cards', 'yellow_cards', 'elo_home', 'elo_away', 'elo_diff',
            'recent_goal_count_5m', 'saturation_score'
        ]
        
        try:
            X = np.array([[features.get(col, 0.0) for col in feature_cols]])
            X_scaled = self.scaler.transform(X)
            probability = self.model.predict_proba(X_scaled)[0][1]
            danger_score = probability * 100
            
            return {
                'danger_score': float(danger_score),
                'probability': float(probability),
            }
        except Exception as e:
            logger.error(f"❌ Error calculating danger score: {e}")
            return {'danger_score': 0.0, 'probability': 0.0, 'error': str(e)}
    
    def check_penalty_suspension(self, current_time: float) -> Tuple[bool, int]:
        """Check if market is suspended due to penalty."""
        if self.penalty_suspension_until is None:
            return False, 0
        
        if current_time >= self.penalty_suspension_until:
            self.penalty_state = "NORMAL"
            self.penalty_suspension_until = None
            return False, 0
        
        ttl = int(self.penalty_suspension_until - current_time)
        return True, max(0, ttl)
    
    def process_snapshot(self, live_stats: Dict, current_time: Optional[float] = None) -> Optional[BettingDecision]:
        """
        Process a live match snapshot and produce betting decision.
        
        Input: Live stats from headless parser
        Output: BettingDecision or None if filtered
        """
        if current_time is None:
            current_time = datetime.now().timestamp()
        
        # Extract basic match info
        match_id = live_stats.get('match_id', 'UNKNOWN')
        minute = live_stats.get('minute', 0)
        home_team = live_stats.get('home_team', 'HOME')
        away_team = live_stats.get('away_team', 'AWAY')
        home_score = live_stats.get('home_score', 0)
        away_score = live_stats.get('away_score', 0)
        score_str = f"{home_score}-{away_score}"
        
        # Determine active interval
        if 30 <= minute <= 45:
            interval = (30, 45)
        elif 75 <= minute <= 90:
            interval = (75, 90)
        else:
            logger.debug(f"⏩ Minute {minute} outside target intervals")
            return None
        
        # Calculate raw danger score
        raw_danger = self.calculate_danger_score(live_stats.get('features', {}))
        if raw_danger.get('error'):
            logger.error(f"❌ {raw_danger['error']}")
            return None
        
        danger_score_raw = raw_danger['danger_score']
        confidence_raw = raw_danger['probability']
        
        # Check penalty suspension
        market_suspended, penalty_ttl = self.check_penalty_suspension(current_time)
        
        # Apply penalties to confidence if market suspended
        confidence_adjusted = confidence_raw * 0.5 if market_suspended else confidence_raw
        danger_adjusted = danger_score_raw * 0.5 if market_suspended else danger_score_raw
        
        # Apply TTL freshness decay (if signal has age)
        signal_age = live_stats.get('signal_age_seconds', 0.0)
        freshness_factor = self.ttl_manager.calculate_freshness_factor(signal_age)
        
        confidence_fresh = confidence_adjusted * freshness_factor
        danger_score_fresh = danger_adjusted * freshness_factor
        
        # Determine if should bet
        reason = ""
        should_bet = False
        
        if market_suspended:
            reason = f"MARKET_SUSPENDED (TTL: {penalty_ttl}s)"
        elif signal_age > 300:
            reason = f"SIGNAL_STALE ({signal_age:.0f}s > 300s TTL)"
        elif confidence_fresh < self.confidence_threshold:
            reason = f"LOW_CONFIDENCE ({confidence_fresh:.2f} < {self.confidence_threshold:.2f})"
            self.bets_filtered += 1
        elif danger_score_fresh < self.danger_score_threshold:
            reason = f"LOW_DANGER ({danger_score_fresh:.1f}% < {self.danger_score_threshold:.1f}%)"
            self.bets_filtered += 1
        else:
            should_bet = True
            reason = "BETTING_SIGNAL_ACTIVE"
            self.bets_triggered += 1
        
        # Create decision
        decision = BettingDecision(
            should_bet=should_bet,
            reason=reason,
            danger_score=float(danger_score_fresh),
            confidence=float(confidence_fresh),
            freshness_factor=float(freshness_factor),
            market_suspended=market_suspended,
            penalty_ttl_seconds=penalty_ttl,
            signal_age_seconds=float(signal_age),
            interval=interval,
            match_id=match_id,
            minute=minute,
            home_team=home_team,
            away_team=away_team,
            score=score_str,
            timestamp=current_time,
        )
        
        self.decisions_history.append(decision)
        
        # Log decision
        status = "🎯 BET" if should_bet else "⏭️ SKIP"
        logger.info(f"{status}: {match_id} {minute}' {score_str} | "
                   f"danger={danger_score_fresh:.1f}% conf={confidence_fresh:.2f} "
                   f"reason={reason}")
        
        return decision
    
    def process_match_sequence(self, snapshots: List[Dict]) -> List[BettingDecision]:
        """Process a sequence of snapshots (simulated live match)."""
        base_time = datetime.now().timestamp()
        decisions = []
        
        for i, snapshot in enumerate(snapshots):
            current_time = base_time + (i * 45)  # 45s between snapshots
            snapshot['signal_age_seconds'] = 0.0  # Fresh signals in simulation
            
            decision = self.process_snapshot(snapshot, current_time)
            if decision:
                decisions.append(decision)
        
        return decisions
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics."""
        return {
            'total_decisions': len(self.decisions_history),
            'bets_triggered': self.bets_triggered,
            'bets_filtered': self.bets_filtered,
            'trigger_rate': self.bets_triggered / len(self.decisions_history) if self.decisions_history else 0.0,
            'confidence_threshold': self.confidence_threshold,
            'danger_score_threshold': self.danger_score_threshold,
        }


def demo_phase3_pipeline():
    """Demo: Complete Phase 3 pipeline."""
    
    print("\n" + "=" * 70)
    print("🚀 PHASE 3: LIVE PREDICTION PIPELINE DEMO")
    print("=" * 70 + "\n")
    
    # Initialize pipeline
    pipeline = LivePredictionPipeline(
        confidence_threshold=0.35,
        danger_score_threshold=40.0
    )
    
    if not pipeline.initialize():
        logger.error("Failed to initialize pipeline")
        return
    
    # Simulate live match snapshots
    print("📊 SIMULATING LIVE MATCH [30-45] INTERVAL")
    print("-" * 70 + "\n")
    
    base_time = datetime.now().timestamp()
    snapshots = [
        {
            'match_id': 'MATCH_001',
            'minute': 32,
            'home_team': 'Test Home',
            'away_team': 'Test Away',
            'home_score': 0,
            'away_score': 0,
            'features': {
                'minute': 32,
                'minute_bucket': 30,
                'score_home': 0,
                'score_away': 0,
                'goal_diff': 0,
                'poss_home': 55.0,
                'poss_away': 45.0,
                'shots_home': 3,
                'shots_away': 2,
                'sot_home': 1,
                'sot_away': 0,
                'shot_accuracy': 33.3,
                'sot_ratio': 1.0,
                'shot_delta_5m': 0,
                'sot_delta_5m': 0,
                'corner_delta_5m': 1,
                'red_cards': 0,
                'yellow_cards': 1,
                'elo_home': 1600.0,
                'elo_away': 1550.0,
                'elo_diff': 50.0,
                'recent_goal_count_5m': 0,
                'saturation_score': 0.3,
            },
        },
        {
            'match_id': 'MATCH_001',
            'minute': 35,
            'home_team': 'Test Home',
            'away_team': 'Test Away',
            'home_score': 1,
            'away_score': 0,
            'features': {
                'minute': 35,
                'minute_bucket': 30,
                'score_home': 1,
                'score_away': 0,
                'goal_diff': 1,
                'poss_home': 58.0,
                'poss_away': 42.0,
                'shots_home': 5,
                'shots_away': 2,
                'sot_home': 2,
                'sot_away': 0,
                'shot_accuracy': 40.0,
                'sot_ratio': 1.0,
                'shot_delta_5m': 2,
                'sot_delta_5m': 1,
                'corner_delta_5m': 2,
                'red_cards': 0,
                'yellow_cards': 2,
                'elo_home': 1600.0,
                'elo_away': 1550.0,
                'elo_diff': 50.0,
                'recent_goal_count_5m': 1,
                'saturation_score': 0.6,
            },
        },
        {
            'match_id': 'MATCH_001',
            'minute': 40,
            'home_team': 'Test Home',
            'away_team': 'Test Away',
            'home_score': 1,
            'away_score': 1,
            'features': {
                'minute': 40,
                'minute_bucket': 30,
                'score_home': 1,
                'score_away': 1,
                'goal_diff': 0,
                'poss_home': 50.0,
                'poss_away': 50.0,
                'shots_home': 7,
                'shots_away': 5,
                'sot_home': 3,
                'sot_away': 2,
                'shot_accuracy': 42.9,
                'sot_ratio': 0.6,
                'shot_delta_5m': 1,
                'sot_delta_5m': 1,
                'corner_delta_5m': 1,
                'red_cards': 0,
                'yellow_cards': 3,
                'elo_home': 1600.0,
                'elo_away': 1550.0,
                'elo_diff': 50.0,
                'recent_goal_count_5m': 1,
                'saturation_score': 0.7,
            },
        },
    ]
    
    # Process snapshots
    decisions = pipeline.process_match_sequence(snapshots)
    
    # Display decisions
    print("\n" + "=" * 70)
    print("📋 DECISIONS SUMMARY")
    print("=" * 70)
    print(f"{'Min':<5} {'Score':<8} {'Danger':<10} {'Conf':<8} {'Decision':<12} {'Reason':<20}")
    print("-" * 70)
    
    for d in decisions:
        decision_text = "🎯 BET" if d.should_bet else "⏭️ SKIP"
        print(f"{d.minute:<5} {d.score:<8} {d.danger_score:<10.1f}% "
              f"{d.confidence:<8.2f} {decision_text:<12} {d.reason:<20}")
    
    # Statistics
    print("\n" + "=" * 70)
    print("📊 PIPELINE STATISTICS")
    print("=" * 70)
    stats = pipeline.get_statistics()
    print(f"Total decisions: {stats['total_decisions']}")
    print(f"Bets triggered: {stats['bets_triggered']}")
    print(f"Bets filtered: {stats['bets_filtered']}")
    print(f"Trigger rate: {stats['trigger_rate']:.1%}")
    print(f"Confidence threshold: {stats['confidence_threshold']:.2f}")
    print(f"Danger score threshold: {stats['danger_score_threshold']:.1f}%")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_phase3_pipeline()
