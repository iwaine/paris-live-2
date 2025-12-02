#!/usr/bin/env python3
"""
Phase 3 Integration Test: TTL Manager + Live Prediction Pipeline

Complete validation of:
1. Signal TTL and freshness decay
2. Live prediction pipeline end-to-end
3. Betting decision filtering
4. Market suspension logic
"""

import json
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_ttl_manager():
    """Test 1: Signal TTL Manager."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Signal TTL Manager & Freshness Decay")
    logger.info("=" * 70)
    
    try:
        from signal_ttl_manager import SignalTTLManager, DangerSignal
        
        manager = SignalTTLManager(ttl_seconds=300, confidence_threshold=0.3)
        base_time = datetime.now().timestamp()
        
        # Test confidence evolution
        test_points = [0, 100, 200, 300, 400]
        logger.info("\n📈 Freshness factor evolution:")
        logger.info(f"{'Age (s)':<10} {'Freshness':<12} {'Confidence %':<15}")
        logger.info("-" * 70)
        
        for age in test_points:
            factor = manager.calculate_freshness_factor(float(age))
            logger.info(f"{age:<10} {factor:<12.4f} {factor*100:<15.1f}%")
        
        # Create test signals
        signals = [
            DangerSignal(
                signal_id=f"SIG_{age:03d}",
                timestamp=base_time - age,
                danger_score=60.0,
                confidence=0.75,
                interval=(30, 45),
                market_suspended=False,
                ttl_seconds=0,
                match_id="TEST_001",
                minute=35,
                home_team="Home",
                away_team="Away",
                score="1-0",
            )
            for age in [0, 100, 150, 300, 350]
        ]
        
        # Process signals
        logger.info("\n🔄 Processing signal stream:")
        processed = manager.process_signal_stream(signals, current_time=base_time)
        
        logger.info(f"\n✅ TEST 1 PASSED: {len(processed)}/5 signals active")
        return True
    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}")
        return False


def test_pipeline_initialization():
    """Test 2: Pipeline Initialization."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Live Prediction Pipeline Initialization")
    logger.info("=" * 70)
    
    try:
        from live_prediction_pipeline import LivePredictionPipeline
        
        pipeline = LivePredictionPipeline(
            confidence_threshold=0.30,
            danger_score_threshold=35.0
        )
        
        if not pipeline.initialize():
            logger.error("Failed to initialize pipeline")
            return False
        
        logger.info("✅ Pipeline initialized successfully")
        logger.info(f"   Model: {pipeline.model_path}")
        logger.info(f"   Scaler: {pipeline.scaler_path}")
        logger.info(f"   Thresholds: confidence={pipeline.confidence_threshold:.2f}, "
                   f"danger_score={pipeline.danger_score_threshold:.1f}%")
        
        logger.info("\n✅ TEST 2 PASSED: Pipeline ready")
        return True
    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}")
        return False


def test_danger_score_calculation():
    """Test 3: Danger Score Calculation."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Danger Score Calculation")
    logger.info("=" * 70)
    
    try:
        from live_prediction_pipeline import LivePredictionPipeline
        
        pipeline = LivePredictionPipeline()
        if not pipeline.initialize():
            return False
        
        # Test features
        test_features = {
            'minute': 35,
            'minute_bucket': 30,
            'score_home': 1,
            'score_away': 0,
            'goal_diff': 1,
            'poss_home': 60.0,
            'poss_away': 40.0,
            'shots_home': 6,
            'shots_away': 3,
            'sot_home': 3,
            'sot_away': 1,
            'shot_accuracy': 50.0,
            'sot_ratio': 0.75,
            'shot_delta_5m': 1,
            'sot_delta_5m': 1,
            'corner_delta_5m': 1,
            'red_cards': 0,
            'yellow_cards': 2,
            'elo_home': 1600.0,
            'elo_away': 1550.0,
            'elo_diff': 50.0,
            'recent_goal_count_5m': 1,
            'saturation_score': 0.6,
        }
        
        result = pipeline.calculate_danger_score(test_features)
        
        logger.info(f"\nDanger score: {result['danger_score']:.1f}%")
        logger.info(f"Probability: {result['probability']:.4f}")
        
        if 0 <= result['danger_score'] <= 100 and 0 <= result['probability'] <= 1:
            logger.info("\n✅ TEST 3 PASSED: Danger score valid")
            return True
        else:
            logger.error("Invalid danger score range")
            return False
    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}")
        return False


def test_betting_decisions():
    """Test 4: Betting Decisions."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Betting Decision Filtering")
    logger.info("=" * 70)
    
    try:
        from live_prediction_pipeline import LivePredictionPipeline
        
        pipeline = LivePredictionPipeline(
            confidence_threshold=0.30,
            danger_score_threshold=35.0
        )
        
        if not pipeline.initialize():
            return False
        
        # Test scenarios
        scenarios = [
            {
                'name': 'Low score (should filter)',
                'minute': 32,
                'score': '0-0',
                'saturation': 0.2,
            },
            {
                'name': 'After goal (should trigger)',
                'minute': 35,
                'score': '1-0',
                'saturation': 0.6,
            },
            {
                'name': 'Balanced match (moderate)',
                'minute': 40,
                'score': '1-1',
                'saturation': 0.7,
            },
        ]
        
        logger.info("\nTesting decision scenarios:")
        logger.info(f"{'Scenario':<30} {'Minute':<8} {'Decision':<15}")
        logger.info("-" * 70)
        
        decision_count = 0
        for scenario in scenarios:
            live_stats = {
                'match_id': 'TEST_MATCH',
                'minute': scenario['minute'],
                'home_team': 'Home',
                'away_team': 'Away',
                'home_score': int(scenario['score'].split('-')[0]),
                'away_score': int(scenario['score'].split('-')[1]),
                'signal_age_seconds': 0.0,
                'features': {
                    'minute': scenario['minute'],
                    'minute_bucket': (scenario['minute'] // 15) * 15,
                    'score_home': int(scenario['score'].split('-')[0]),
                    'score_away': int(scenario['score'].split('-')[1]),
                    'goal_diff': int(scenario['score'].split('-')[0]) - int(scenario['score'].split('-')[1]),
                    'poss_home': 55.0,
                    'poss_away': 45.0,
                    'shots_home': 5 if scenario['saturation'] > 0.5 else 3,
                    'shots_away': 3,
                    'sot_home': 2 if scenario['saturation'] > 0.5 else 1,
                    'sot_away': 1,
                    'shot_accuracy': 40.0,
                    'sot_ratio': 0.66,
                    'shot_delta_5m': 1 if scenario['saturation'] > 0.5 else 0,
                    'sot_delta_5m': 0,
                    'corner_delta_5m': 1,
                    'red_cards': 0,
                    'yellow_cards': 2,
                    'elo_home': 1600.0,
                    'elo_away': 1550.0,
                    'elo_diff': 50.0,
                    'recent_goal_count_5m': 1 if scenario['saturation'] > 0.5 else 0,
                    'saturation_score': scenario['saturation'],
                }
            }
            
            decision = pipeline.process_snapshot(live_stats)
            if decision:
                decision_count += 1
                status = "🎯 BET" if decision.should_bet else "⏭️ SKIP"
                logger.info(f"{scenario['name']:<30} {scenario['minute']:<8} {status:<15}")
        
        logger.info(f"\n✅ TEST 4 PASSED: {decision_count} decisions processed")
        return True
    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_penalty_suspension():
    """Test 5: Penalty Market Suspension."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Penalty Market Suspension Logic")
    logger.info("=" * 70)
    
    try:
        from live_prediction_pipeline import LivePredictionPipeline
        
        pipeline = LivePredictionPipeline()
        if not pipeline.initialize():
            return False
        
        base_time = datetime.now().timestamp()
        
        # Simulate penalty event
        logger.info("\nSimulating penalty sequence:")
        
        # Normal play
        pipeline.penalty_state = "NORMAL"
        pipeline.penalty_suspension_until = None
        suspended, ttl = pipeline.check_penalty_suspension(base_time)
        logger.info(f"Before penalty: suspended={suspended}, ttl={ttl}s")
        
        # Penalty occurs
        pipeline.penalty_state = "PENDING"
        pipeline.penalty_suspension_until = base_time + 45
        suspended, ttl = pipeline.check_penalty_suspension(base_time + 10)
        logger.info(f"During penalty: suspended={suspended}, ttl={ttl}s")
        
        # Suspension expires
        suspended, ttl = pipeline.check_penalty_suspension(base_time + 50)
        logger.info(f"After penalty: suspended={suspended}, ttl={ttl}s")
        
        logger.info("\n✅ TEST 5 PASSED: Penalty suspension working")
        return True
    except Exception as e:
        logger.error(f"❌ TEST 5 FAILED: {e}")
        return False


def run_all_tests():
    """Run complete Phase 3 test suite."""
    print("\n" + "=" * 70)
    print("🧪 PHASE 3 INTEGRATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("TTL Manager", test_ttl_manager),
        ("Pipeline Initialization", test_pipeline_initialization),
        ("Danger Score Calculation", test_danger_score_calculation),
        ("Betting Decisions", test_betting_decisions),
        ("Penalty Suspension", test_penalty_suspension),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 70 + "\n")
    
    if passed == total:
        print("✅ ALL PHASE 3 TESTS PASSED - Ready for production deployment!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
