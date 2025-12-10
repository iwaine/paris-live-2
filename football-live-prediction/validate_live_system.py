#!/usr/bin/env python3
"""
Test de validation du système d'intégration live.
Vérifie que tous les composants fonctionnent ensemble.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

def test_import_soccerstats_scraper():
    """Test import du scraper SoccerStats."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from soccerstats_live_scraper import SoccerStatsLiveScraper, LiveMatchData
        print("✅ SoccerStatsLiveScraper imported successfully")
        
        # Créer une instance
        scraper = SoccerStatsLiveScraper()
        print("✅ SoccerStatsLiveScraper instance created")
        return True
    except Exception as e:
        print(f"❌ SoccerStatsLiveScraper import failed: {e}")
        return False

def test_import_live_selector():
    """Test import du sélecteur de matchs live."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from soccerstats_live_selector import get_live_matches
        print("✅ soccerstats_live_selector imported successfully")
        return True
    except Exception as e:
        print(f"❌ soccerstats_live_selector import failed: {e}")
        return False

def test_import_live_predictor():
    """Test import du prédicteur live."""
    try:
        from live_goal_predictor import LiveGoalPredictor, LiveMatchStats
        print("✅ LiveGoalPredictor imported successfully")
        
        # Vérifier la DB
        predictor = LiveGoalPredictor('data/predictions.db')
        print("✅ LiveGoalPredictor database connected")
        predictor.close()
        return True
    except Exception as e:
        print(f"❌ LiveGoalPredictor import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_pipeline():
    """Test import du pipeline complet."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from live_pipeline_with_scraper import LiveMatchPipeline
        print("✅ LiveMatchPipeline imported successfully")
        
        # Créer une instance
        pipeline = LiveMatchPipeline()
        print("✅ LiveMatchPipeline instance created")
        return True
    except Exception as e:
        print(f"❌ LiveMatchPipeline import failed: {e}")
        return False

def test_import_monitor():
    """Test import du monitor avec alertes."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from live_goal_monitor_with_alerts import LiveGoalMonitor
        print("✅ LiveGoalMonitor imported successfully")
        return True
    except Exception as e:
        print(f"❌ LiveGoalMonitor import failed: {e}")
        return False

def test_database():
    """Test l'accès à la base de données."""
    try:
        import sqlite3
        db_path = 'data/predictions.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier les tables
        tables = [
            'team_critical_intervals',
            'team_global_stats',
            'team_recent_form',
            'soccerstats_scraped_matches'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table}: {count} records")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_recurrence_data():
    """Vérifier les données recurrence."""
    try:
        import sqlite3
        db_path = 'data/predictions.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Compter les patterns valides
        cursor.execute('''
            SELECT COUNT(*) FROM team_critical_intervals
            WHERE matches_with_goals_scored >= 3
        ''')
        
        valid_scored = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM team_critical_intervals
            WHERE matches_with_goals_conceded >= 3
        ''')
        
        valid_conceded = cursor.fetchone()[0]
        
        print(f"✅ Recurrence patterns valid (scored): {valid_scored}")
        print(f"✅ Recurrence patterns valid (conceded): {valid_conceded}")
        
        conn.close()
        return valid_scored > 100 and valid_conceded > 100
    except Exception as e:
        print(f"❌ Recurrence data test failed: {e}")
        return False

def test_prediction_engine():
    """Test l'engine de prédiction."""
    try:
        from live_goal_predictor import LiveGoalPredictor, LiveMatchStats
        
        predictor = LiveGoalPredictor('data/predictions.db')
        
        # Obtenir une équipe de la DB
        cursor = predictor.conn.cursor()
        cursor.execute('SELECT DISTINCT team_name FROM team_critical_intervals LIMIT 2')
        teams = [row[0] for row in cursor.fetchall()]
        
        if len(teams) < 2:
            print("❌ Not enough teams in database")
            predictor.close()
            return False
        
        home_team = teams[0]
        away_team = teams[1]
        
        # Créer stats live de test
        live_stats = LiveMatchStats(
            minute=35,
            score_home=1,
            score_away=0,
            possession_home=0.65,
            possession_away=0.35,
            shots_home=5,
            shots_away=2,
            sot_home=2,
            sot_away=1,
            dangerous_attacks_home=3,
            dangerous_attacks_away=1
        )
        
        # Prédire
        predictions = predictor.predict_goal(home_team, away_team, live_stats)
        
        print(f"✅ Prediction test: {home_team} vs {away_team}")
        
        for team_type, pred in predictions.items():
            print(f"  • {team_type}: {pred.probability:.1%} ({pred.confidence})")
        
        predictor.close()
        return True
    except Exception as e:
        print(f"❌ Prediction engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    
    print("\n" + "="*80)
    print("🧪 VALIDATION SYSTÈME D'INTÉGRATION LIVE")
    print("="*80 + "\n")
    
    tests = [
        ("SoccerStats Scraper", test_import_soccerstats_scraper),
        ("Live Selector", test_import_live_selector),
        ("Live Predictor", test_import_live_predictor),
        ("Live Pipeline", test_import_pipeline),
        ("Live Monitor", test_import_monitor),
        ("Database Access", test_database),
        ("Recurrence Data", test_recurrence_data),
        ("Prediction Engine", test_prediction_engine),
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n📋 Testing: {name}")
        print("-" * 80)
        
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {name}")
    
    print(f"\n{'─'*80}")
    print(f"Result: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80 + "\n")
    
    if passed == total:
        print("✅ SYSTÈME COMPLET OPÉRATIONNEL!")
        print("\nPour démarrer le monitoring:")
        print("  cd /workspaces/paris-live")
        print("  python3 live_goal_monitor_with_alerts.py")
        print("\nOu pour traiter un match spécifique:")
        print("  python3 live_pipeline_with_scraper.py <URL_SOCCERSTATS>")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
