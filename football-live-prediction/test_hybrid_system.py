#!/usr/bin/env python3
"""
Test du système hybride : 80% Pattern historique + 20% Momentum live
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live_predictor_v2 import LivePredictorV2, LiveMatchContext

def test_hybrid_system():
    """Tester le système hybride avec différents scénarios de momentum."""
    
    predictor = LivePredictorV2()
    
    print("=" * 100)
    print("🔥 TEST SYSTÈME HYBRIDE : 80% PATTERN HISTORIQUE + 20% MOMENTUM LIVE")
    print("=" * 100)
    print()
    
    # ========================================================================
    # SCÉNARIO 1: Pattern EXCELLENT + Momentum FORT = Probabilité maximale
    # ========================================================================
    print("\n" + "=" * 100)
    print("📊 SCÉNARIO 1: PATTERN EXCELLENT + MOMENTUM FORT")
    print("=" * 100)
    print()
    print("Match: Spartak Varna (HOME) vs Slavia Sofia (AWAY)")
    print("Minute: 78 (Intervalle 75-90 ACTIF)")
    print("Score: 1-1")
    print()
    print("Stats live:")
    print("  Possession:        55% - 45%  (Spartak domine)")
    print("  Corners:           4 - 2")
    print("  Shots:             8 - 5")
    print("  Shots on target:   4 - 2")
    print("  Attacks:           28 - 22")
    print("  Dangerous attacks: 12 - 8")
    print()
    
    match1 = LiveMatchContext(
        home_team="Spartak Varna",
        away_team="Slavia Sofia",
        current_minute=78,
        home_score=1,
        away_score=1,
        country="Bulgaria",
        league="bulgaria",
        # Stats live
        possession_home=55.0,
        possession_away=45.0,
        corners_home=4,
        corners_away=2,
        shots_home=8,
        shots_away=5,
        shots_on_target_home=4,
        shots_on_target_away=2,
        attacks_home=28,
        attacks_away=22,
        dangerous_attacks_home=12,
        dangerous_attacks_away=8
    )
    
    pred1 = predictor.predict(match1)
    
    print("RÉSULTAT:")
    print(f"  Spartak Varna HOME:")
    print(f"    Pattern historique: {pred1['home_active'].freq_any_goal*100:.0f}% (89% attendu)")
    print(f"    Probabilité HYBRIDE: {pred1['home_active'].probability*100:.1f}%")
    print(f"    Confiance: {pred1['home_active'].confidence_level}")
    print()
    print(f"  Slavia Sofia AWAY:")
    print(f"    Pattern historique: {pred1['away_active'].freq_any_goal*100:.0f}% (75% attendu)")
    print(f"    Probabilité HYBRIDE: {pred1['away_active'].probability*100:.1f}%")
    print(f"    Confiance: {pred1['away_active'].confidence_level}")
    print()
    print(f"  🎯 PROBABILITÉ COMBINÉE: {pred1['combined_active']['probability']*100:.1f}%")
    
    # ========================================================================
    # SCÉNARIO 2: Pattern EXCELLENT + Momentum FAIBLE = Ajustement à la baisse
    # ========================================================================
    print("\n" + "=" * 100)
    print("📊 SCÉNARIO 2: PATTERN EXCELLENT + MOMENTUM FAIBLE")
    print("=" * 100)
    print()
    print("Match: Spartak Varna (HOME) vs Slavia Sofia (AWAY)")
    print("Minute: 78 (Intervalle 75-90 ACTIF)")
    print("Score: 0-1 (Spartak perd)")
    print()
    print("Stats live:")
    print("  Possession:        30% - 70%  (Spartak dominé!)")
    print("  Corners:           1 - 6")
    print("  Shots:             2 - 10")
    print("  Shots on target:   0 - 5")
    print("  Attacks:           15 - 35")
    print("  Dangerous attacks: 3 - 15")
    print()
    
    match2 = LiveMatchContext(
        home_team="Spartak Varna",
        away_team="Slavia Sofia",
        current_minute=78,
        home_score=0,
        away_score=1,
        country="Bulgaria",
        league="bulgaria",
        # Stats live (mauvaises pour Spartak)
        possession_home=30.0,
        possession_away=70.0,
        corners_home=1,
        corners_away=6,
        shots_home=2,
        shots_away=10,
        shots_on_target_home=0,
        shots_on_target_away=5,
        attacks_home=15,
        attacks_away=35,
        dangerous_attacks_home=3,
        dangerous_attacks_away=15
    )
    
    pred2 = predictor.predict(match2)
    
    print("RÉSULTAT:")
    print(f"  Spartak Varna HOME:")
    print(f"    Pattern historique: {pred2['home_active'].freq_any_goal*100:.0f}% (89%)")
    print(f"    Probabilité HYBRIDE: {pred2['home_active'].probability*100:.1f}% ⬇️ (AJUSTÉ À LA BAISSE)")
    print(f"    ➡️ Momentum faible compense le pattern fort!")
    print()
    print(f"  Slavia Sofia AWAY:")
    print(f"    Pattern historique: {pred2['away_active'].freq_any_goal*100:.0f}% (75%)")
    print(f"    Probabilité HYBRIDE: {pred2['away_active'].probability*100:.1f}% ⬆️ (BOOSTÉ)")
    print(f"    ➡️ Momentum fort booste le pattern!")
    print()
    print(f"  🎯 PROBABILITÉ COMBINÉE: {pred2['combined_active']['probability']*100:.1f}%")
    
    # ========================================================================
    # SCÉNARIO 3: SANS stats live (100% pattern historique)
    # ========================================================================
    print("\n" + "=" * 100)
    print("📊 SCÉNARIO 3: SANS STATS LIVE (100% Pattern historique)")
    print("=" * 100)
    print()
    print("Match: Levski Sofia (HOME) vs CSKA Sofia (AWAY)")
    print("Minute: 78")
    print("Stats live: NON DISPONIBLES")
    print()
    
    match3 = LiveMatchContext(
        home_team="Levski Sofia",
        away_team="CSKA Sofia",
        current_minute=78,
        home_score=1,
        away_score=1,
        country="Bulgaria",
        league="bulgaria"
        # Pas de stats live
    )
    
    pred3 = predictor.predict(match3)
    
    print("RÉSULTAT:")
    print(f"  Levski Sofia HOME:")
    print(f"    Pattern historique: {pred3['home_active'].freq_any_goal*100:.0f}%")
    print(f"    Probabilité: {pred3['home_active'].probability*100:.1f}%")
    print(f"    ➡️ 100% pattern (pas de momentum)")
    print()
    print(f"  CSKA Sofia AWAY:")
    print(f"    Pattern historique: {pred3['away_active'].freq_any_goal*100:.0f}%")
    print(f"    Probabilité: {pred3['away_active'].probability*100:.1f}%")
    print()
    print(f"  🎯 PROBABILITÉ COMBINÉE: {pred3['combined_active']['probability']*100:.1f}%")
    
    # ========================================================================
    # SCÉNARIO 4: Pattern MOYEN + Momentum FORT = Boost significatif
    # ========================================================================
    print("\n" + "=" * 100)
    print("📊 SCÉNARIO 4: PATTERN MOYEN + MOMENTUM FORT")
    print("=" * 100)
    print()
    print("Match: Beroe (HOME) vs Ludogorets (AWAY)")
    print("Minute: 33")
    print()
    print("Stats live:")
    print("  Possession:        65% - 35%  (Beroe domine fort!)")
    print("  Corners:           3 - 0")
    print("  Shots:             6 - 1")
    print("  Shots on target:   4 - 0")
    print("  Attacks:           22 - 10")
    print("  Dangerous attacks: 10 - 2")
    print()
    
    match4 = LiveMatchContext(
        home_team="Beroe",
        away_team="Ludogorets",
        current_minute=33,
        home_score=0,
        away_score=0,
        country="Bulgaria",
        league="bulgaria",
        # Stats live favorables à Beroe
        possession_home=65.0,
        possession_away=35.0,
        corners_home=3,
        corners_away=0,
        shots_home=6,
        shots_away=1,
        shots_on_target_home=4,
        shots_on_target_away=0,
        attacks_home=22,
        attacks_away=10,
        dangerous_attacks_home=10,
        dangerous_attacks_away=2
    )
    
    pred4 = predictor.predict(match4)
    
    print("RÉSULTAT:")
    print(f"  Beroe HOME:")
    print(f"    Pattern historique: {pred4['home_active'].freq_any_goal*100:.0f}%")
    print(f"    Probabilité HYBRIDE: {pred4['home_active'].probability*100:.1f}% ⬆️")
    print(f"    ➡️ Pattern moyen BOOSTÉ par momentum fort!")
    print()
    print(f"  🎯 PROBABILITÉ COMBINÉE: {pred4['combined_active']['probability']*100:.1f}%")
    
    predictor.close()
    
    print("\n" + "=" * 100)
    print("✅ TEST TERMINÉ")
    print("=" * 100)
    print()
    print("📊 FORMULE HYBRIDE:")
    print("   Probabilité finale = 80% × Pattern historique + 20% × Momentum live")
    print()
    print("   Momentum = 25% possession + 20% shots + 20% shots_on_target")
    print("            + 15% dangerous_attacks + 10% attacks + 10% corners")
    print()
    print("🎯 AVANTAGES:")
    print("   ✅ Pattern historique reste la base (80%) = récurrence fiable")
    print("   ✅ Momentum live ajuste (20%) = contexte actuel du match")
    print("   ✅ Si pas de stats live → 100% pattern historique (fallback)")
    print()


if __name__ == "__main__":
    test_hybrid_system()
