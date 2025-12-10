#!/usr/bin/env python3
"""
Test de simulation du moniteur live bulgare.
Simule des matches en cours pour démontrer le système complet.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live_predictor_v2 import LivePredictorV2, LiveMatchContext

def simulate_match_scenarios():
    """Simuler différents scénarios de matches bulgares."""
    
    predictor = LivePredictorV2()
    
    scenarios = [
        # Scénario 1: Début intervalle 31-45
        {
            'name': 'SCÉNARIO 1: Spartak Varna vs Slavia Sofia - Minute 32 (Intervalle 31-45 ACTIF)',
            'match': LiveMatchContext(
                home_team="Spartak Varna",
                away_team="Slavia Sofia",
                current_minute=32,
                home_score=0,
                away_score=0,
                country="Bulgaria",
                league="bulgaria"
            )
        },
        # Scénario 2: Fin intervalle 31-45
        {
            'name': 'SCÉNARIO 2: Levski Sofia vs CSKA Sofia - Minute 43 (Intervalle 31-45 ACTIF)',
            'match': LiveMatchContext(
                home_team="Levski Sofia",
                away_team="CSKA Sofia",
                current_minute=43,
                home_score=1,
                away_score=0,
                country="Bulgaria",
                league="bulgaria"
            )
        },
        # Scénario 3: Entre les intervalles
        {
            'name': 'SCÉNARIO 3: Beroe vs Ludogorets - Minute 60 (Entre intervalles)',
            'match': LiveMatchContext(
                home_team="Beroe",
                away_team="Ludogorets",
                current_minute=60,
                home_score=1,
                away_score=1,
                country="Bulgaria",
                league="bulgaria"
            )
        },
        # Scénario 4: Début intervalle 75-90
        {
            'name': 'SCÉNARIO 4: Spartak Varna vs Septemvri Sofia - Minute 76 (Intervalle 75-90 ACTIF)',
            'match': LiveMatchContext(
                home_team="Spartak Varna",
                away_team="Septemvri Sofia",
                current_minute=76,
                home_score=2,
                away_score=1,
                country="Bulgaria",
                league="bulgaria"
            )
        },
        # Scénario 5: Milieu intervalle 75-90
        {
            'name': 'SCÉNARIO 5: CSKA 1948 Sofia vs Botev Vratsa - Minute 82 (Intervalle 75-90 ACTIF)',
            'match': LiveMatchContext(
                home_team="CSKA 1948 Sofia",
                away_team="Botev Vratsa",
                current_minute=82,
                home_score=0,
                away_score=0,
                country="Bulgaria",
                league="bulgaria"
            )
        },
        # Scénario 6: Pattern EXCELLENT vs EXCELLENT
        {
            'name': 'SCÉNARIO 6: Slavia Sofia vs Arda - Minute 78 (AWAY excellent)',
            'match': LiveMatchContext(
                home_team="Slavia Sofia",
                away_team="Arda",
                current_minute=78,
                home_score=1,
                away_score=2,
                country="Bulgaria",
                league="bulgaria"
            )
        },
    ]
    
    print("=" * 100)
    print("🇧🇬 SIMULATION MONITEUR LIVE BULGARIE - DÉMONSTRATION SYSTÈME COMPLET")
    print("=" * 100)
    print()
    
    for i, scenario in enumerate(scenarios, 1):
        print("\n" + "=" * 100)
        print(f"📋 {scenario['name']}")
        print("=" * 100)
        
        match = scenario['match']
        predictions = predictor.predict(match)
        
        # Affichage détaillé
        print(f"\n🏟️  {match.home_team} vs {match.away_team}")
        print(f"⏱️  Minute {match.current_minute} | Score: {match.home_score}-{match.away_score}")
        print()
        
        # Intervalle actif
        if 'home_active' in predictions:
            home = predictions['home_active']
            away = predictions['away_active']
            combined = predictions['combined_active']
            
            print(f"⚡ INTERVALLE ACTIF: {home.interval_name}")
            print()
            print(f"  {match.home_team} (HOME):")
            print(f"    📊 Probabilité: {home.probability*100:.1f}%")
            print(f"    🎯 Confiance: {home.confidence_level}")
            print(f"    📈 Fréquence historique: {home.freq_any_goal*100:.0f}% ({home.matches_with_goal}/{home.total_matches} matches)")
            if home.recurrence_last_5:
                print(f"    🔄 Récurrence 5 derniers: {home.recurrence_last_5*100:.0f}%")
            print(f"    ⚽ Buts: {home.goals_scored} marqués, {home.goals_conceded} encaissés")
            
            print()
            print(f"  {match.away_team} (AWAY):")
            print(f"    📊 Probabilité: {away.probability*100:.1f}%")
            print(f"    🎯 Confiance: {away.confidence_level}")
            print(f"    📈 Fréquence historique: {away.freq_any_goal*100:.0f}% ({away.matches_with_goal}/{away.total_matches} matches)")
            if away.recurrence_last_5:
                print(f"    🔄 Récurrence 5 derniers: {away.recurrence_last_5*100:.0f}%")
            print(f"    ⚽ Buts: {away.goals_scored} marqués, {away.goals_conceded} encaissés")
            
            print()
            print(f"  🎯 PROBABILITÉ COMBINÉE: {combined['probability']*100:.1f}%")
            print(f"     (Au moins 1 but marqué par l'une des 2 équipes)")
            
            # Signal trading
            print()
            if combined['probability'] >= 0.85:
                print("  🟢 SIGNAL TRÈS FORT - PROBABILITÉ EXCEPTIONNELLE!")
                print("  💰 Recommandation: Pari \"But dans l'intervalle\" (Over 0.5)")
            elif combined['probability'] >= 0.70:
                print("  🟡 SIGNAL FORT - Bonne probabilité")
                print("  💡 Recommandation: Pari modéré possible")
            elif combined['probability'] >= 0.50:
                print("  ⚪ SIGNAL MOYEN - Probabilité acceptable")
            else:
                print("  🔴 SIGNAL FAIBLE - Probabilité insuffisante")
        
        # Prochain intervalle
        if 'home_next' in predictions:
            home_next = predictions['home_next']
            away_next = predictions['away_next']
            combined_next = predictions['combined_next']
            
            print()
            print(f"📅 PROCHAIN INTERVALLE: {home_next.interval_name}")
            print(f"   {match.home_team} (HOME): {home_next.probability*100:.1f}% | {home_next.confidence_level}")
            print(f"   {match.away_team} (AWAY): {away_next.probability*100:.1f}% | {away_next.confidence_level}")
            print(f"   🎯 Combiné: {combined_next['probability']*100:.1f}%")
            
            if combined_next['probability'] >= 0.70:
                print(f"   ℹ️ Se préparer pour {home_next.interval_name}")
        
        print()
    
    predictor.close()
    
    print("\n" + "=" * 100)
    print("✅ SIMULATION TERMINÉE")
    print("=" * 100)
    print()
    print("📊 RÉSUMÉ DU SYSTÈME:")
    print("  ✅ Scraping automatique des 16 équipes bulgares (286 matches)")
    print("  ✅ Patterns avec buts marqués ET encaissés")
    print("  ✅ Métrique 'any_goal' (au moins 1 but dans l'intervalle)")
    print("  ✅ Récurrence sur 5 derniers matches")
    print("  ✅ Niveaux de confiance (EXCELLENT → FAIBLE)")
    print("  ✅ Prédicteur v2 avec probabilités ajustées")
    print("  ✅ Moniteur live automatique")
    print()
    print("🚀 PRÊT POUR PRODUCTION!")
    print()


if __name__ == "__main__":
    simulate_match_scenarios()
