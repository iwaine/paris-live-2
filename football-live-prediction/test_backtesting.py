#!/usr/bin/env python3
"""
Backtesting Integration Tests

Tests cover:
1. Backtesting engine initialization
2. Decision generation on sample data
3. Metrics calculation accuracy
4. Analyzer functionality
5. Export functionality
"""

import pytest
import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from datetime import datetime
from backtesting_engine import BacktestingEngine, BacktestDecision, BacktestMetrics
from backtesting_analyzer import BacktestingAnalyzer, StrategyComparison


class TestBacktestingEngine:
    """Tests for BacktestingEngine"""

    def test_1_engine_initialization(self):
        """Test engine initializes with valid model and data"""
        print("\n✅ TEST 1: Engine Initialization")
        
        try:
            engine = BacktestingEngine()
            
            # Verify models loaded
            assert engine.model is not None, "Model not loaded"
            assert engine.scaler is not None, "Scaler not loaded"
            assert engine.data is not None, "Data not loaded"
            
            # Verify data shape
            assert len(engine.data) > 0, "Data is empty"
            
            print(f"   ✓ Model loaded: {type(engine.model).__name__}")
            print(f"   ✓ Scaler loaded: {type(engine.scaler).__name__}")
            print(f"   ✓ Data loaded: {len(engine.data)} records")
            
            assert True
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise

    def test_2_danger_score_calculation(self):
        """Test danger score calculation returns valid values"""
        print("\n✅ TEST 2: Danger Score Calculation")
        
        try:
            engine = BacktestingEngine()
            
            # Create dummy features (23 features)
            features = np.random.randn(23)
            
            # Calculate danger score
            danger_score, probability = engine.calculate_danger_score(features)
            
            # Verify output ranges
            assert 0 <= danger_score <= 100, f"Danger score out of range: {danger_score}"
            assert 0 <= probability <= 1, f"Probability out of range: {probability}"
            assert danger_score == probability * 100, "Danger score not correctly calculated"
            
            print(f"   ✓ Danger score: {danger_score:.2f}%")
            print(f"   ✓ Probability: {probability:.4f}")
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise

    def test_3_freshness_decay(self):
        """Test TTL freshness decay calculation"""
        print("\n✅ TEST 3: Freshness Decay (TTL)")
        
        try:
            engine = BacktestingEngine()
            
            initial_confidence = 1.0
            ttl = 300  # 5 minutes
            
            # Test at different ages
            times = [0, 150, 300, 450]
            expected_factors = [1.0, np.exp(-150/300), np.exp(-300/300), np.exp(-450/300)]
            
            for age, expected in zip(times, expected_factors):
                decayed = engine.apply_freshness_decay(initial_confidence, age, ttl)
                assert abs(decayed - expected) < 0.001, f"Decay incorrect at t={age}s"
                print(f"   ✓ Age {age:3d}s: confidence {decayed:.3f} (expected {expected:.3f})")
            
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise

    def test_4_interval_decision_generation(self):
        """Test decision generation for intervals"""
        print("\n✅ TEST 4: Interval Decision Generation")
        
        try:
            engine = BacktestingEngine()
            
            # Get first match from data
            if len(engine.data) == 0:
                pytest.skip("No data available")
            
            match_data = engine.data.iloc[0]
            
            # Generate decisions for 30-45 interval
            decisions = engine.simulate_interval_decisions(match_data, interval="30-45")
            
            # Verify decisions structure
            assert len(decisions) > 0, "No decisions generated"
            
            for decision in decisions:
                assert isinstance(decision, BacktestDecision)
                assert decision.interval == "30-45"
                assert 0 <= decision.danger_score <= 100
                assert 0 <= decision.confidence <= 1
                assert decision.reason != ""
                
            print(f"   ✓ Generated {len(decisions)} decisions for interval 30-45")
            print(f"   ✓ First decision: {decisions[0].reason}")
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise

    def test_5_full_backtesting_pipeline(self):
        """Test full backtesting pipeline"""
        print("\n✅ TEST 5: Full Backtesting Pipeline")
        
        try:
            engine = BacktestingEngine(
                confidence_threshold=0.30,
                danger_threshold=0.35
            )
            
            # Run backtesting on subset (first 10 matches)
            print(f"   Testing on first 10 matches...")
            
            all_decisions = []
            for idx in range(min(10, len(engine.data))):
                match_data = engine.data.iloc[idx]
                
                for interval in ["30-45", "75-90"]:
                    decisions = engine.simulate_interval_decisions(match_data, interval)
                    all_decisions.extend(decisions)
            
            engine.decisions = all_decisions
            
            # Verify decisions
            assert len(all_decisions) > 0, "No decisions generated"
            
            # Calculate metrics
            metrics = engine.calculate_metrics()
            
            assert isinstance(metrics, BacktestMetrics)
            assert metrics.total_decisions == len(all_decisions)
            assert 0 <= metrics.win_rate <= 100
            assert 0 <= metrics.precision <= 1
            
            print(f"   ✓ Generated {len(all_decisions)} decisions")
            print(f"   ✓ Bets triggered: {metrics.total_bets_triggered}")
            print(f"   ✓ Win rate: {metrics.win_rate:.1f}%")
            print(f"   ✓ Precision: {metrics.precision:.2%}")
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise


class TestBacktestingAnalyzer:
    """Tests for BacktestingAnalyzer"""

    def test_6_analyzer_initialization(self):
        """Test analyzer initialization"""
        print("\n✅ TEST 6: Analyzer Initialization")
        
        try:
            # First generate some decisions
            engine = BacktestingEngine()
            all_decisions = []
            for idx in range(min(5, len(engine.data))):
                match_data = engine.data.iloc[idx]
                for interval in ["30-45", "75-90"]:
                    decisions = engine.simulate_interval_decisions(match_data, interval)
                    all_decisions.extend(decisions)
            
            engine.decisions = all_decisions
            engine.export_decisions_csv("test_backtesting_decisions.csv")
            
            # Initialize analyzer
            analyzer = BacktestingAnalyzer("test_backtesting_decisions.csv")
            
            assert analyzer.df is not None
            assert len(analyzer.df) == len(all_decisions)
            
            print(f"   ✓ Analyzer initialized")
            print(f"   ✓ Loaded {len(analyzer.df)} decisions")
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise

    def test_7_interval_analysis(self):
        """Test interval analysis"""
        print("\n✅ TEST 7: Interval Analysis")
        
        try:
            engine = BacktestingEngine()
            all_decisions = []
            for idx in range(min(10, len(engine.data))):
                match_data = engine.data.iloc[idx]
                for interval in ["30-45", "75-90"]:
                    decisions = engine.simulate_interval_decisions(match_data, interval)
                    all_decisions.extend(decisions)
            
            engine.decisions = all_decisions
            engine.export_decisions_csv("test_backtesting_decisions.csv")
            
            analyzer = BacktestingAnalyzer("test_backtesting_decisions.csv")
            interval_metrics = analyzer.analyze_by_interval()
            
            assert len(interval_metrics) > 0
            
            for interval, metrics in interval_metrics.items():
                assert interval in ["30-45", "75-90"]
                assert metrics.decisions > 0
                assert 0 <= metrics.win_rate <= 100
                print(f"   ✓ {interval}: {metrics.decisions} decisions, {metrics.win_rate:.1f}% win rate")
            
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise

    def test_8_strategy_comparison(self):
        """Test strategy variation analysis"""
        print("\n✅ TEST 8: Strategy Comparison")
        
        try:
            engine = BacktestingEngine()
            all_decisions = []
            for idx in range(min(10, len(engine.data))):
                match_data = engine.data.iloc[idx]
                for interval in ["30-45", "75-90"]:
                    decisions = engine.simulate_interval_decisions(match_data, interval)
                    all_decisions.extend(decisions)
            
            engine.decisions = all_decisions
            engine.export_decisions_csv("test_backtesting_decisions.csv")
            
            analyzer = BacktestingAnalyzer("test_backtesting_decisions.csv")
            strategies = analyzer.analyze_strategy_variations()
            
            assert len(strategies) > 0
            
            print(f"\n   Strategy Comparison ({len(strategies)} strategies tested):")
            for strat in strategies:
                assert isinstance(strat, StrategyComparison)
                assert 0 <= strat.precision <= 1
                print(f"   ✓ {strat.strategy_name}: {strat.total_bets} bets, {strat.win_rate:.1f}% WR")
            
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise

    def test_9_export_functionality(self):
        """Test export functionality"""
        print("\n✅ TEST 9: Export Functionality")
        
        try:
            engine = BacktestingEngine()
            all_decisions = []
            for idx in range(min(5, len(engine.data))):
                match_data = engine.data.iloc[idx]
                for interval in ["30-45", "75-90"]:
                    decisions = engine.simulate_interval_decisions(match_data, interval)
                    all_decisions.extend(decisions)
            
            engine.decisions = all_decisions
            engine.export_decisions_csv("test_backtesting_decisions.csv")
            
            analyzer = BacktestingAnalyzer("test_backtesting_decisions.csv")
            files = analyzer.export_analysis("test_analysis_output")
            
            assert len(files) > 0
            
            for name, path in files.items():
                assert Path(path).exists(), f"File not created: {path}"
                print(f"   ✓ {name}: {Path(path).stat().st_size} bytes")
            
            print("   PASS ✅")
            
        except Exception as e:
            print(f"   FAIL ❌: {e}")
            raise


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 BACKTESTING INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        TestBacktestingEngine(),
        TestBacktestingAnalyzer(),
    ]
    
    passed = 0
    failed = 0
    
    for test_obj in tests:
        # Get all test methods
        test_methods = [m for m in dir(test_obj) if m.startswith("test_")]
        
        for method_name in sorted(test_methods):
            try:
                method = getattr(test_obj, method_name)
                method()
                passed += 1
            except Exception as e:
                failed += 1
                logger_error = f"Error in {method_name}: {e}"
    
    # Summary
    print("\n" + "="*70)
    print(f"📊 TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"❌ {failed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
