#!/usr/bin/env python3
"""
Démonstration finale du système complet avec timing détaillé.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live_predictor_v2 import LivePredictorV2, LiveMatchContext

def demo_complete():
    """Démonstration complète avec tous les détails."""
    
    predictor = LivePredictorV2()
    
    print("=" * 100)
    print("🇧🇬 SYSTÈME COMPLET - PRÉDICTION LIVE BULGARIE")
    print("=" * 100)
    print()
    print("📊 CARACTÉRISTIQUES:")
    print("  ✅ 80% Pattern historique (286 matches, 16 équipes)")
    print("  ✅ 20% Momentum live (possession, shots, attacks)")
    print("  ✅ Récurrence sur 5 derniers matches")
    print("  ✅ Niveaux de confiance (EXCELLENT → FAIBLE)")
    print("  ✅ Timing précis (minute moyenne + écart-type)")
    print()
    
    # ========================================================================
    # SCÉNARIO: Match avec stats live complètes
    # ========================================================================
    print("=" * 100)
    print("📋 SCÉNARIO: Spartak Varna vs Slavia Sofia - Minute 78")
    print("=" * 100)
    print()
    print("🏟️  CONTEXTE DU MATCH:")
    print("  Score: 1-1")
    print("  Minute: 78 (Intervalle 75-90 ACTIF)")
    print()
    print("📊 STATS LIVE:")
    print("  Possession:          55% - 45%  (Spartak domine)")
    print("  Corners:             4 - 2")
    print("  Total shots:         8 - 5")
    print("  Shots on target:     4 - 2")
    print("  Attacks:             28 - 22")
    print("  Dangerous attacks:   12 - 8")
    print()
    
    match = LiveMatchContext(
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
    
    predictions = predictor.predict(match)
    
    print("=" * 100)
    print("🔮 PRÉDICTIONS")
    print("=" * 100)
    
    home = predictions['home_active']
    away = predictions['away_active']
    combined = predictions['combined_active']
    
    print()
    print(f"📍 SPARTAK VARNA (HOME) - Intervalle {home.interval_name}")
    print("-" * 100)
    print(f"  🎯 PROBABILITÉ FINALE: {home.probability*100:.1f}%")
    print(f"  📊 Confiance: {home.confidence_level}")
    print()
    print("  📈 PATTERN HISTORIQUE:")
    print(f"     Fréquence: {home.freq_any_goal*100:.0f}% ({home.matches_with_goal}/{home.total_matches} matches avec but)")
    if home.recurrence_last_5:
        print(f"     Récurrence 5 derniers: {home.recurrence_last_5*100:.0f}%")
    print(f"     Buts marqués: {home.goals_scored} (fréq: {home.freq_scored*100:.0f}%)")
    print(f"     Buts encaissés: {home.goals_conceded} (fréq: {home.freq_conceded*100:.0f}%)")
    
    if home.avg_minute:
        print()
        print("  ⏰ TIMING DES BUTS:")
        print(f"     Minute moyenne: {home.avg_minute:.1f}", end="")
        if home.std_minute:
            min_range = max(home.avg_minute - home.std_minute, 75)
            max_range = min(home.avg_minute + home.std_minute, 90)
            print(f" (±{home.std_minute:.1f})")
            print(f"     ➡️ Buts attendus entre {min_range:.0f}' et {max_range:.0f}'")
            if home.std_minute < 4:
                print(f"     💡 Écart-type FAIBLE ({home.std_minute:.1f}) = Timing TRÈS PRÉCIS!")
            elif home.std_minute > 6:
                print(f"     ⚠️ Écart-type ÉLEVÉ ({home.std_minute:.1f}) = Timing VARIABLE")
        else:
            print()
    
    print()
    print(f"📍 SLAVIA SOFIA (AWAY) - Intervalle {away.interval_name}")
    print("-" * 100)
    print(f"  🎯 PROBABILITÉ FINALE: {away.probability*100:.1f}%")
    print(f"  📊 Confiance: {away.confidence_level}")
    print()
    print("  📈 PATTERN HISTORIQUE:")
    print(f"     Fréquence: {away.freq_any_goal*100:.0f}% ({away.matches_with_goal}/{away.total_matches} matches avec but)")
    if away.recurrence_last_5:
        print(f"     Récurrence 5 derniers: {away.recurrence_last_5*100:.0f}%")
    print(f"     Buts marqués: {away.goals_scored} (fréq: {away.freq_scored*100:.0f}%)")
    print(f"     Buts encaissés: {away.goals_conceded} (fréq: {away.freq_conceded*100:.0f}%)")
    
    if away.avg_minute:
        print()
        print("  ⏰ TIMING DES BUTS:")
        print(f"     Minute moyenne: {away.avg_minute:.1f}", end="")
        if away.std_minute:
            min_range = max(away.avg_minute - away.std_minute, 75)
            max_range = min(away.avg_minute + away.std_minute, 90)
            print(f" (±{away.std_minute:.1f})")
            print(f"     ➡️ Buts attendus entre {min_range:.0f}' et {max_range:.0f}'")
            if away.std_minute < 4:
                print(f"     💡 Écart-type FAIBLE ({away.std_minute:.1f}) = Timing TRÈS PRÉCIS!")
            elif away.std_minute > 6:
                print(f"     ⚠️ Écart-type ÉLEVÉ ({away.std_minute:.1f}) = Timing VARIABLE")
        else:
            print()
    
    print()
    print("=" * 100)
    print(f"🎯 PROBABILITÉ COMBINÉE: {combined['probability']*100:.1f}%")
    print("   (Au moins 1 but marqué par l'une des 2 équipes)")
    print("=" * 100)
    print()
    
    # Recommandation
    prob_pct = combined['probability'] * 100
    if prob_pct >= 90:
        print("✅ SIGNAL TRÈS FORT - Excellente opportunité de pari!")
        print("💰 Recommandation: Pari \"But dans l'intervalle\" (Over 0.5)")
        print(f"📊 Justification: {prob_pct:.1f}% de probabilité combinée")
    elif prob_pct >= 75:
        print("🟡 SIGNAL FORT - Bonne opportunité")
        print("💡 Recommandation: Pari modéré possible")
    elif prob_pct >= 60:
        print("⚪ SIGNAL MOYEN - Probabilité acceptable")
        print("💭 Recommandation: Prudence, pari faible si expérimenté")
    else:
        print("🔴 SIGNAL FAIBLE - Probabilité insuffisante")
        print("⛔ Recommandation: NE PAS parier")
    
    print()
    print("=" * 100)
    print("📋 DÉTAILS CALCUL HYBRIDE")
    print("=" * 100)
    print()
    print("SPARTAK VARNA:")
    print(f"  Pattern historique: {home.freq_any_goal*100:.0f}%")
    print(f"  Ajustements: +{(home.probability - home.freq_any_goal)*100:.1f}% (récurrence, confiance, momentum)")
    print(f"  ➡️ Probabilité finale: {home.probability*100:.1f}%")
    print()
    print("SLAVIA SOFIA:")
    print(f"  Pattern historique: {away.freq_any_goal*100:.0f}%")
    print(f"  Ajustements: +{(away.probability - away.freq_any_goal)*100:.1f}% (récurrence, confiance, momentum)")
    print(f"  ➡️ Probabilité finale: {away.probability*100:.1f}%")
    print()
    
    predictor.close()
    
    print("=" * 100)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("=" * 100)


if __name__ == "__main__":
    demo_complete()
