#!/usr/bin/env python3
"""
Script de test complet pour valider le système bolivien.
Teste prédictions sur un match simulé avec données réelles de la DB.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from live_predictor_v2 import LivePredictorV2, LiveMatchContext
import sqlite3

def test_bolivia_system():
    """Tester le système avec données boliviennes."""
    
    print("\n" + "="*80)
    print("🇧🇴 TEST SYSTÈME BOLIVIE - DIVISION PROFESIONAL")
    print("="*80)
    
    # 1. Vérifier données en DB
    db_path = 'data/predictions.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Compter matches boliviens
    cursor.execute("SELECT COUNT(*) FROM soccerstats_scraped_matches WHERE country='Bolivia'")
    nb_matches = cursor.fetchone()[0]
    print(f"\n✅ {nb_matches} matches boliviens en base")
    
    # Compter patterns boliviens
    cursor.execute("SELECT COUNT(*) FROM team_critical_intervals WHERE country='Bolivia'")
    nb_patterns = cursor.fetchone()[0]
    print(f"✅ {nb_patterns} patterns boliviens générés")
    
    # Récupérer équipes boliviennes
    cursor.execute("""
        SELECT DISTINCT team 
        FROM soccerstats_scraped_matches 
        WHERE country='Bolivia' 
        ORDER BY team
    """)
    teams = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 {len(teams)} équipes boliviennes :")
    for team in teams[:10]:  # Afficher 10 premières
        print(f"   • {team}")
    if len(teams) > 10:
        print(f"   ... et {len(teams)-10} autres")
    
    # 2. Récupérer un match récent pour test
    cursor.execute("""
        SELECT team, opponent, date, is_home, score, goal_times, goal_times_conceded
        FROM soccerstats_scraped_matches
        WHERE country='Bolivia' 
        AND goal_times != '[]'
        ORDER BY date DESC
        LIMIT 1
    """)
    
    match = cursor.fetchone()
    if not match:
        print("\n❌ Aucun match avec buts trouvé pour test")
        conn.close()
        return
    
    team, opponent, date, is_home, score, goal_times, goal_times_conceded = match
    
    print(f"\n{'='*80}")
    print(f"📊 MATCH TEST : {team} vs {opponent}")
    print(f"{'='*80}")
    print(f"📅 Date: {date}")
    print(f"🏠 Lieu: {'Domicile' if is_home else 'Extérieur'} pour {team}")
    print(f"⚽ Score: {score}")
    print(f"🎯 Buts marqués: {goal_times}")
    print(f"🎯 Buts encaissés: {goal_times_conceded}")
    
    conn.close()
    
    # 3. Tester prédictions à différents moments
    predictor = LivePredictorV2(db_path=db_path)
    
    test_scenarios = [
        {
            'minute': 35,
            'score_home': 1,
            'score_away': 0,
            'description': 'Intervalle 31-45 ACTIF, 1 but marqué'
        },
        {
            'minute': 78,
            'score_home': 1,
            'score_away': 1,
            'description': 'Intervalle 75-90 ACTIF, match nul'
        },
        {
            'minute': 25,
            'score_home': 0,
            'score_away': 0,
            'description': 'Avant intervalle critique, 0-0'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*80}")
        print(f"🧪 TEST {i}/3 : {scenario['description']}")
        print(f"{'='*80}")
        print(f"⏱️ Minute {scenario['minute']}' - Score {scenario['score_home']}-{scenario['score_away']}")
        
        # Créer contexte (sans stats live pour commencer)
        context = LiveMatchContext(
            home_team=team if is_home else opponent,
            away_team=opponent if is_home else team,
            current_minute=scenario['minute'],
            home_score=scenario['score_home'],
            away_score=scenario['score_away'],
            country="Bolivia",
            league="bolivia"
        )
        
        # Générer prédictions
        try:
            predictions = predictor.predict(context)
            
            if not predictions:
                print("⚠️ Aucune prédiction générée (patterns manquants en DB)")
                continue
            
            for pred in predictions:
                status = "🚨 ACTIF" if pred.is_active else "⏳ Prochain"
                print(f"\n{status} - Intervalle {pred.interval_name}")
                print(f"  🎯 Probabilité: {pred.probability*100:.1f}%")
                
                # Signal
                if pred.probability >= 0.90:
                    print(f"  🟢 SIGNAL TRÈS FORT")
                elif pred.probability >= 0.75:
                    print(f"  🟡 SIGNAL FORT")
                elif pred.probability >= 0.60:
                    print(f"  ⚪ SIGNAL MODÉRÉ")
                else:
                    print(f"  🔴 SIGNAL FAIBLE")
                
                print(f"  📈 Confiance: {pred.confidence_level}")
                print(f"  📊 Pattern: {pred.freq_any_goal*100:.1f}% "
                      f"({pred.matches_with_goal}/{pred.total_matches} matches)")
                
                if pred.avg_minute:
                    min_range = max(pred.avg_minute - (pred.std_minute or 0), 
                                   int(pred.interval_name.split('-')[0]))
                    max_range = min(pred.avg_minute + (pred.std_minute or 0), 
                                   int(pred.interval_name.split('-')[1].replace('+', '')))
                    print(f"  ⏰ Timing: {pred.avg_minute:.1f}' (±{pred.std_minute:.1f}) "
                          f"→ Buts entre {min_range:.0f}-{max_range:.0f}min")
                
                if pred.recurrence_last_5 is not None:
                    print(f"  🔄 Récurrence 5 derniers: {pred.recurrence_last_5*100:.0f}%")
                
                # Détails buts
                print(f"\n  📌 Détails Pattern:")
                print(f"     • Buts marqués: {pred.goals_scored}")
                print(f"     • Buts encaissés: {pred.goals_conceded}")
                print(f"     • Freq marqués: {pred.freq_scored*100:.1f}%")
                print(f"     • Freq encaissés: {pred.freq_conceded*100:.1f}%")
                
        except Exception as e:
            print(f"\n❌ Erreur prédiction: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. Test avec stats live simulées
    print(f"\n{'='*80}")
    print(f"🧪 TEST 4/4 : Avec stats live simulées (momentum)")
    print(f"{'='*80}")
    print(f"⏱️ Minute 80' - Score 1-1")
    print(f"📊 Stats: Poss 60-40, Shots 12-7, SOT 5-3, DA 18-10")
    
    context_with_stats = LiveMatchContext(
        home_team=team if is_home else opponent,
        away_team=opponent if is_home else team,
        current_minute=80,
        home_score=1,
        away_score=1,
        country="Bolivia",
        league="bolivia",
        possession_home=60.0,
        possession_away=40.0,
        shots_home=12,
        shots_away=7,
        shots_on_target_home=5,
        shots_on_target_away=3,
        dangerous_attacks_home=18,
        dangerous_attacks_away=10,
        attacks_home=45,
        attacks_away=32,
        corners_home=6,
        corners_away=3
    )
    
    try:
        predictions_with_momentum = predictor.predict(context_with_stats)
        
        for pred in predictions_with_momentum:
            if pred.is_active:
                print(f"\n🚨 ACTIF - Intervalle {pred.interval_name}")
                print(f"  🎯 Probabilité AVEC momentum: {pred.probability*100:.1f}%")
                print(f"  💡 Le système a combiné pattern historique (80%) + momentum live (20%)")
                print(f"  📈 Domination nette de l'équipe à domicile détectée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    print(f"\n{'='*80}")
    print(f"✅ TESTS TERMINÉS")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_bolivia_system()
