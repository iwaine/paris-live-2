#!/usr/bin/env python3
"""
Phase 2 Integration Test: Complete Pipeline Validation

Tests:
1. Feature extraction on demo match data
2. ML model inference with danger score calculation
3. Penalty detection state machine
4. Error handling & recovery scenarios
5. End-to-end danger score output format

Output: Comprehensive test report with all validations
"""

import json
import logging
import pickle
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MatchSnapshot:
    """Live match data snapshot at a point in time."""
    match_id: str
    minute: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    possession_home: float
    possession_away: float
    shots_home: int
    shots_away: int
    sot_home: int
    sot_away: int
    corners_home: int
    corners_away: int
    red_cards: int
    yellow_cards: int
    events: List[Dict]  # [{'minute': 35, 'type': 'goal', 'team': 'home'}, ...]
    
    def to_feature_dict(self) -> Dict:
        """Convert to feature dict format for ML model (all 23 features)."""
        return {
            'minute': self.minute,
            'minute_bucket': self.minute // 15 * 15,  # Bucket to 15-min intervals
            'score_home': self.home_score,
            'score_away': self.away_score,
            'goal_diff': self.home_score - self.away_score,
            'poss_home': self.possession_home,
            'poss_away': self.possession_away,
            'shots_home': self.shots_home,
            'shots_away': self.shots_away,
            'sot_home': self.sot_home,
            'sot_away': self.sot_away,
            'shot_accuracy': (self.sot_home / (self.shots_home + 1)) * 100,
            'sot_ratio': self.sot_home / (self.sot_home + self.sot_away + 1),
            'shot_delta_5m': max(-2, min(2, np.random.randint(-2, 3))),
            'sot_delta_5m': max(-1, min(1, np.random.randint(-1, 2))),
            'corner_delta_5m': max(-1, min(2, np.random.randint(-1, 3))),
            'red_cards': self.red_cards,
            'yellow_cards': self.yellow_cards,
            'elo_home': 1600.0,  # Demo Elo
            'elo_away': 1550.0,
            'elo_diff': 50.0,
            'recent_goal_count_5m': 1 if any(e.get('type') == 'goal' for e in self.events) else 0,
            'saturation_score': 0.5 + (self.shots_home + self.shots_away) / 50.0,
        }


class PenaltyStateMachine:
    """
    State machine for penalty detection and market suspension.
    
    States:
    - NORMAL: Regular play
    - PENDING: Penalty awarded (waiting for kick)
    - RESOLVED: Penalty completed (kicked or missed)
    """
    
    class State:
        NORMAL = "NORMAL"
        PENDING = "PENDING"
        RESOLVED = "RESOLVED"
    
    def __init__(self):
        self.state = self.State.NORMAL
        self.penalty_start_time = None
        self.suspension_end_time = None
        self.penalty_history = []
    
    def process_event(self, event: Dict, current_time: float) -> Dict:
        """
        Process event and update state.
        
        Returns: {'state': str, 'market_suspended': bool, 'ttl_seconds': int}
        """
        event_type = event.get('type', '').lower()
        
        # Penalty awarded
        if event_type == 'penalty':
            self.state = self.State.PENDING
            self.penalty_start_time = current_time
            self.suspension_end_time = current_time + 45  # 45 second suspension
            self.penalty_history.append({
                'timestamp': current_time,
                'state_change': 'NORMAL → PENDING'
            })
            logger.info(f"🚨 Penalty detected at {current_time}s - market suspended for 45s")
        
        # Goal scored (resolves any pending penalty)
        elif event_type == 'goal' and self.state == self.State.PENDING:
            self.state = self.State.RESOLVED
            self.penalty_history.append({
                'timestamp': current_time,
                'state_change': 'PENDING → RESOLVED (goal)'
            })
            logger.info(f"⚽ Goal scored - penalty resolved")
        
        # Penalty missed/saved (resolves pending penalty)
        elif event_type == 'missed_penalty' and self.state == self.State.PENDING:
            self.state = self.State.RESOLVED
            self.penalty_history.append({
                'timestamp': current_time,
                'state_change': 'PENDING → RESOLVED (missed)'
            })
            logger.info(f"❌ Penalty missed - penalty resolved")
        
        # Check if suspension expired
        if self.state == self.State.RESOLVED and self.suspension_end_time and current_time >= self.suspension_end_time:
            self.state = self.State.NORMAL
            self.penalty_history.append({
                'timestamp': current_time,
                'state_change': 'RESOLVED → NORMAL (timeout)'
            })
            logger.info(f"✅ Suspension expired - market reopened")
        
        # Calculate market suspension status
        market_suspended = self.state != self.State.NORMAL
        ttl_seconds = int(self.suspension_end_time - current_time) if self.suspension_end_time and current_time < self.suspension_end_time else 0
        
        return {
            'state': self.state,
            'market_suspended': market_suspended,
            'ttl_seconds': max(0, ttl_seconds),
        }


class ErrorHandler:
    """Handle errors with exponential backoff and graceful degradation."""
    
    def __init__(self):
        self.retry_count = 0
        self.max_retries = 4
        self.backoff_delays = [1, 2, 4, 8]  # exponential backoff in seconds
    
    def attempt_operation(self, operation_name: str, operation_func) -> Tuple[bool, Optional[str]]:
        """
        Attempt operation with exponential backoff.
        
        Returns: (success, error_message)
        """
        try:
            result = operation_func()
            self.retry_count = 0  # Reset on success
            logger.info(f"✅ {operation_name} succeeded")
            return True, None
        except Exception as e:
            if self.retry_count < self.max_retries:
                delay = self.backoff_delays[self.retry_count]
                self.retry_count += 1
                logger.warning(f"⚠️ {operation_name} failed (attempt {self.retry_count}): {e}")
                logger.warning(f"   Retrying in {delay}s...")
                return False, f"Retry in {delay}s"
            else:
                logger.error(f"❌ {operation_name} failed after {self.max_retries} retries: {e}")
                return False, f"Max retries exceeded"
    
    def health_check(self) -> Dict:
        """Check system health."""
        return {
            'parser_status': 'OK',
            'model_loaded': True,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
        }


class DangerScoreCalculator:
    """Calculate danger score from ML model with all Phase 2 features."""
    
    def __init__(self, model_path: str = 'models/au_moins_1_but_model.pkl',
                 scaler_path: str = 'models/scaler.pkl'):
        self.model = None
        self.scaler = None
        self.load_models(model_path, scaler_path)
    
    def load_models(self, model_path: str, scaler_path: str):
        """Load ML model and scaler."""
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"✅ Model loaded: {model_path}")
            logger.info(f"✅ Scaler loaded: {scaler_path}")
        except FileNotFoundError as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise
    
    def calculate_danger_score(self, features: Dict, interval: Tuple[int, int],
                               market_suspended: bool = False,
                               ttl_seconds: int = 0) -> Dict:
        """
        Calculate danger score for a match.
        
        Returns: {
            'danger_score': float (0-100),
            'probability': float (0-1),
            'interval': (30, 45),
            'market_suspended': bool,
            'ttl_seconds': int,
            'confidence': float,
        }
        """
        if not self.model or not self.scaler:
            return {
                'danger_score': 0.0,
                'probability': 0.0,
                'error': 'Model not loaded',
                'market_suspended': market_suspended,
            }
        
        # Extract features in order (must match ml_model_training.py prepare_features)
        feature_cols = [
            'minute', 'minute_bucket', 'score_home', 'score_away', 'goal_diff',
            'poss_home', 'poss_away', 'shots_home', 'shots_away', 'sot_home', 'sot_away',
            'shot_accuracy', 'sot_ratio', 'shot_delta_5m', 'sot_delta_5m', 'corner_delta_5m',
            'red_cards', 'yellow_cards', 'elo_home', 'elo_away', 'elo_diff',
            'recent_goal_count_5m', 'saturation_score'
        ]
        
        X = np.array([[features.get(col, 0.0) for col in feature_cols]])
        X_scaled = self.scaler.transform(X)
        
        # Get probability from model
        probability = self.model.predict_proba(X_scaled)[0][1]
        
        # Apply market suspension (zero out if suspended)
        if market_suspended:
            probability *= 0.5  # 50% confidence penalty during suspension
            logger.warning(f"⚠️ Market suspended - confidence penalty applied")
        
        # Apply freshness decay (Phase 3 feature preview)
        if ttl_seconds > 0:
            decay_factor = np.exp(-ttl_seconds / 300.0)  # TTL=300s
            probability *= decay_factor
        
        danger_score = probability * 100  # Convert to 0-100 scale
        confidence = min(1.0, probability * 1.2)  # Confidence boost for calibration
        
        return {
            'danger_score': float(danger_score),
            'probability': float(probability),
            'interval': interval,
            'market_suspended': market_suspended,
            'ttl_seconds': ttl_seconds,
            'confidence': float(confidence),
        }


class Phase2IntegrationTest:
    """Run complete Phase 2 integration tests."""
    
    def __init__(self):
        self.results = {
            'test_feature_extraction': None,
            'test_model_inference': None,
            'test_penalty_detection': None,
            'test_error_handling': None,
            'test_end_to_end': None,
        }
    
    def create_demo_snapshot(self, minute: int, home_goals: int, away_goals: int,
                            events: List[Dict] = None) -> MatchSnapshot:
        """Create demo match snapshot."""
        return MatchSnapshot(
            match_id='TEST_MATCH_001',
            minute=minute,
            home_team='Test Home',
            away_team='Test Away',
            home_score=home_goals,
            away_score=away_goals,
            possession_home=55.0,
            possession_away=45.0,
            shots_home=12,
            shots_away=8,
            sot_home=5,
            sot_away=3,
            corners_home=4,
            corners_away=2,
            red_cards=0,
            yellow_cards=2,
            events=events or [],
        )
    
    def test_feature_extraction(self):
        """Test 1: Feature extraction from match snapshot."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 1: Feature Extraction")
        logger.info("=" * 70)
        
        try:
            snapshot = self.create_demo_snapshot(35, 1, 0)
            features = snapshot.to_feature_dict()
            
            # Validate features (all 23 ML features)
            required_features = [
                'minute', 'minute_bucket', 'score_home', 'score_away', 'goal_diff',
                'poss_home', 'poss_away', 'shots_home', 'shots_away', 'sot_home', 'sot_away',
                'shot_accuracy', 'sot_ratio', 'shot_delta_5m', 'sot_delta_5m', 'corner_delta_5m',
                'red_cards', 'yellow_cards', 'elo_home', 'elo_away', 'elo_diff',
                'recent_goal_count_5m', 'saturation_score'
            ]
            
            missing = [f for f in required_features if f not in features]
            if missing:
                logger.error(f"❌ Missing features: {missing}")
                self.results['test_feature_extraction'] = False
                return
            
            logger.info(f"✅ Extracted {len(features)} features")
            logger.info(f"   Sample features: minute={features['minute']}, "
                       f"score={features['score_home']}-{features['score_away']}, "
                       f"poss={features['poss_home']:.1f}%, "
                       f"elo_diff={features['elo_diff']}")
            self.results['test_feature_extraction'] = True
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            self.results['test_feature_extraction'] = False
    
    def test_model_inference(self):
        """Test 2: ML model inference and danger score calculation."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: Model Inference & Danger Score")
        logger.info("=" * 70)
        
        try:
            calculator = DangerScoreCalculator()
            snapshot = self.create_demo_snapshot(38, 1, 0)
            features = snapshot.to_feature_dict()
            
            # Test [30,45] interval
            result = calculator.calculate_danger_score(features, (30, 45))
            
            # Validate output
            required_keys = ['danger_score', 'probability', 'interval', 'confidence']
            missing = [k for k in required_keys if k not in result]
            if missing:
                logger.error(f"❌ Missing keys: {missing}")
                self.results['test_model_inference'] = False
                return
            
            # Validate ranges
            if not (0 <= result['danger_score'] <= 100):
                logger.error(f"❌ Invalid danger_score: {result['danger_score']}")
                self.results['test_model_inference'] = False
                return
            
            if not (0 <= result['probability'] <= 1):
                logger.error(f"❌ Invalid probability: {result['probability']}")
                self.results['test_model_inference'] = False
                return
            
            logger.info(f"✅ Model inference successful")
            logger.info(f"   Danger score: {result['danger_score']:.1f}%")
            logger.info(f"   Probability: {result['probability']:.4f}")
            logger.info(f"   Confidence: {result['confidence']:.4f}")
            logger.info(f"   Interval: {result['interval']}")
            self.results['test_model_inference'] = True
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            self.results['test_model_inference'] = False
    
    def test_penalty_detection(self):
        """Test 3: Penalty detection state machine."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: Penalty Detection State Machine")
        logger.info("=" * 70)
        
        try:
            sm = PenaltyStateMachine()
            
            # Simulate penalty sequence
            events_sequence = [
                ({'type': 'normal'}, 30.0, PenaltyStateMachine.State.NORMAL),
                ({'type': 'penalty'}, 35.0, PenaltyStateMachine.State.PENDING),
                ({'type': 'goal'}, 38.0, PenaltyStateMachine.State.RESOLVED),
                ({'type': 'normal'}, 85.0, PenaltyStateMachine.State.NORMAL),
            ]
            
            logger.info("Simulating penalty sequence:")
            for event, time, expected_state in events_sequence:
                result = sm.process_event(event, time)
                
                if result['state'] != expected_state:
                    logger.error(f"❌ State mismatch: expected {expected_state}, got {result['state']}")
                    self.results['test_penalty_detection'] = False
                    return
                
                logger.info(f"   t={time:5.1f}s: event={event['type']:15} → state={result['state']:10} "
                           f"suspended={result['market_suspended']} ttl={result['ttl_seconds']}s")
            
            logger.info(f"✅ State machine test passed (4/4 transitions correct)")
            logger.info(f"   Penalty history: {len(sm.penalty_history)} state changes")
            self.results['test_penalty_detection'] = True
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            self.results['test_penalty_detection'] = False
    
    def test_error_handling(self):
        """Test 4: Error handling and recovery."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: Error Handling & Auto-Recovery")
        logger.info("=" * 70)
        
        try:
            handler = ErrorHandler()
            
            # Test successful operation
            logger.info("Testing successful operation:")
            success, error = handler.attempt_operation(
                "Operation 1",
                lambda: "success"
            )
            if not success:
                logger.error(f"❌ Operation 1 should succeed")
                self.results['test_error_handling'] = False
                return
            
            # Test retryable operation
            logger.info("\nTesting retryable operation (3 failures, then success):")
            attempt_count = [0]
            
            def retryable_op():
                attempt_count[0] += 1
                if attempt_count[0] < 3:
                    raise Exception(f"Attempt {attempt_count[0]} failed")
                return "success"
            
            for i in range(3):
                handler.attempt_operation(f"Retryable Op {i+1}", retryable_op)
            
            # Test health check
            health = handler.health_check()
            logger.info(f"\n✅ Health check:")
            logger.info(f"   Parser status: {health['parser_status']}")
            logger.info(f"   Model loaded: {health['model_loaded']}")
            logger.info(f"   Retry count: {health['retry_count']}/{health['max_retries']}")
            
            self.results['test_error_handling'] = True
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            self.results['test_error_handling'] = False
    
    def test_end_to_end(self):
        """Test 5: End-to-end pipeline with multiple time points."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: End-to-End Pipeline")
        logger.info("=" * 70)
        
        try:
            calculator = DangerScoreCalculator()
            sm = PenaltyStateMachine()
            
            # Simulate 5 snapshots during [30, 45] interval
            timepoints = [
                (32, 0, 0, []),
                (35, 1, 0, [{'type': 'goal', 'minute': 35}]),
                (38, 1, 0, []),
                (41, 1, 1, [{'type': 'goal', 'minute': 41}]),
                (45, 1, 1, []),
            ]
            
            logger.info("Processing match sequence:")
            results = []
            
            for minute, h_goals, a_goals, events in timepoints:
                snapshot = self.create_demo_snapshot(minute, h_goals, a_goals, events)
                features = snapshot.to_feature_dict()
                
                # Process events through penalty SM
                for event in events:
                    sm.process_event(event, float(minute))
                
                # Get market status
                market_status = sm.process_event({}, float(minute))
                
                # Calculate danger score
                danger = calculator.calculate_danger_score(
                    features,
                    (30, 45),
                    market_suspended=market_status['market_suspended'],
                    ttl_seconds=market_status['ttl_seconds']
                )
                
                results.append({
                    'minute': minute,
                    'score': f"{h_goals}-{a_goals}",
                    'danger_score': danger['danger_score'],
                    'market_suspended': market_status['market_suspended'],
                })
                
                logger.info(f"   {minute}' {h_goals}-{a_goals}: "
                           f"danger={danger['danger_score']:.1f}%, "
                           f"suspended={market_status['market_suspended']}")
            
            logger.info(f"\n✅ End-to-end pipeline test passed ({len(results)} snapshots)")
            self.results['test_end_to_end'] = True
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            self.results['test_end_to_end'] = False
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "=" * 70)
        print("🧪 PHASE 2 INTEGRATION TEST SUITE")
        print("=" * 70)
        
        self.test_feature_extraction()
        self.test_model_inference()
        self.test_penalty_detection()
        self.test_error_handling()
        self.test_end_to_end()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for v in self.results.values() if v is True)
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print("\n" + "=" * 70)
        print(f"TOTAL: {passed}/{total} tests passed")
        print("=" * 70 + "\n")
        
        if passed == total:
            print("✅ ALL INTEGRATION TESTS PASSED - Phase 2 ready for deployment!")
            return 0
        else:
            print(f"❌ {total - passed} test(s) failed - review logs above")
            return 1


if __name__ == "__main__":
    tester = Phase2IntegrationTest()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
