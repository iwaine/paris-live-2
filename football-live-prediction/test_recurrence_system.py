"""
Test complet du système de récurrence
"""

from predictors.recurrence_analyzer import RecurrenceAnalyzer
from predictors.recurrence_predictor import RecurrencePredictor
import json


def test_system():
    print("\n" + "="*70)
    print("🎯 RECURRENCE SYSTEM TEST")
    print("="*70)

    # 1. Analyser les données
    print("\n📊 Phase 1: Analyzing historical data...")
    analyzer = RecurrenceAnalyzer()
    teams = ['Arsenal', 'Chelsea', 'Manchester City', 'Liverpool', 'Manchester United']

    analyzer.analyze_and_save_all(teams)

    # 2. Tester la prédiction
    print("\n\n⚽ Phase 2: Live Prediction Test")
    print("-"*70)

    predictor = RecurrencePredictor()

    # Test 1: Arsenal (home) vs Chelsea (away) @ minute 38
    print("\n🔴 TEST 1: Arsenal (HOME) vs Chelsea (AWAY) @ minute 38")
    prediction = predictor.predict_at_minute(
        home_team='Arsenal',
        away_team='Chelsea',
        current_minute=38,
        home_possession=0.62,
        away_possession=0.38
    )

    if 'error' not in prediction:
        print(f"  Danger Score: {prediction['danger_score_percentage']}%")
        print(f"  Home Goal: {prediction['home_goal_probability']}%")
        print(f"  Away Goal: {prediction['away_goal_probability']}%")
        print(f"  Optimal Range: {prediction['optimal_minute_range']}")
        print(f"  Data: Arsenal({prediction['data_summary']['home_matches_total']} matches, {prediction['data_summary']['home_matches_recent']} recent)")
        print(f"       Chelsea({prediction['data_summary']['away_matches_total']} matches, {prediction['data_summary']['away_matches_recent']} recent)")
    else:
        print(f"  ❌ {prediction['error']}")

    # Test 2: Manchester City (home) vs Liverpool (away) @ minute 80
    print("\n🔵 TEST 2: Manchester City (HOME) vs Liverpool (AWAY) @ minute 80")
    prediction = predictor.predict_at_minute(
        home_team='Manchester City',
        away_team='Liverpool',
        current_minute=80,
        home_possession=0.55,
        away_possession=0.45
    )

    if 'error' not in prediction:
        print(f"  Danger Score: {prediction['danger_score_percentage']}%")
        print(f"  Home Goal: {prediction['home_goal_probability']}%")
        print(f"  Away Goal: {prediction['away_goal_probability']}%")
        print(f"  Optimal Range: {prediction['optimal_minute_range']}")
        print(f"  Data: ManCity({prediction['data_summary']['home_matches_total']} matches, {prediction['data_summary']['home_matches_recent']} recent)")
        print(f"       Liverpool({prediction['data_summary']['away_matches_total']} matches, {prediction['data_summary']['away_matches_recent']} recent)")
    else:
        print(f"  ❌ {prediction['error']}")

    # Test 3: Wrong minute
    print("\n⚠️  TEST 3: Test invalid minute (50) - should fail")
    prediction = predictor.predict_at_minute(
        home_team='Arsenal',
        away_team='Chelsea',
        current_minute=50
    )

    if 'error' in prediction:
        print(f"  ✓ Correctly rejected: {prediction['error']}")
    else:
        print(f"  ❌ Should have failed")

    print("\n" + "="*70)
    print("✅ Tests complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_system()
