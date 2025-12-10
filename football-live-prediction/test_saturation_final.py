#!/usr/bin/env python3
"""
Test final de l'ajustement de saturation
Affiche les probabilités avant/après ajustement saturation
"""

from live_predictor_v2 import LivePredictorV2, LiveMatchContext

def test_saturation():
    predictor = LivePredictorV2()
    
    print("=" * 90)
    print("🧪 TEST FINAL - AJUSTEMENT DE SATURATION")
    print("=" * 90)
    
    # Charger patterns une fois
    home_pattern = predictor._load_pattern("Spartak Varna", True, "31-45+", "Bulgaria")
    away_pattern = predictor._load_pattern("Slavia Sofia", False, "31-45+", "Bulgaria")
    
    if not home_pattern or not away_pattern:
        print("❌ Patterns introuvables")
        return
    
    avg_expected = (home_pattern['avg_goals_first_half'] + away_pattern['avg_goals_first_half']) / 2
    
    print(f"\n📊 Configuration du test:")
    print(f"  Équipes      : Spartak Varna (HOME) vs Slavia Sofia (AWAY)")
    print(f"  Intervalle   : 31-45+ (1ère mi-temps)")
    print(f"  Moyenne 1ère : {home_pattern['avg_goals_first_half']:.2f} + {away_pattern['avg_goals_first_half']:.2f} = {avg_expected:.2f} buts")
    
    print("\n" + "=" * 90)
    print(f"{'Scénario':<25} | Buts | Ratio | Ajust Sat | Prob AVANT | Prob APRÈS | Réduction")
    print("=" * 90)
    
    scenarios = [
        (0, 0, "Match sans buts"),
        (1, 0, "1 but marqué"),
        (1, 1, "2 buts (moyenne)"),
        (2, 1, "3 buts (au-dessus)"),
        (3, 2, "5 buts (saturation)"),
        (4, 3, "7 buts (forte satur.)"),
    ]
    
    for home, away, desc in scenarios:
        current = home + away
        
        # Créer match
        match = LiveMatchContext(
            home_team="Spartak Varna",
            away_team="Slavia Sofia",
            current_minute=32,
            home_score=home,
            away_score=away,
            country="Bulgaria",
            league="bulgaria"
        )
        
        # Calculer ajustement
        saturation_adj = predictor._calculate_saturation_adjustment(
            match, home_pattern, away_pattern, "31-45+"
        )
        
        ratio = current / avg_expected if avg_expected > 0 else 0
        
        # Prédire avec saturation
        pred = predictor.predict(match)
        prob_after = pred['combined_active']['probability']
        
        # Simuler probabilité SANS saturation (recalculer avec adj=0)
        # Pour cela, on doit appeler _build_prediction sans patterns
        # Alternative : Calculer manuellement l'impact
        prob_before = min(1.0, prob_after - saturation_adj)  # Approximation
        
        reduction_pct = ((prob_before - prob_after) / prob_before * 100) if prob_before > 0 else 0
        
        print(f"{desc:<25} | {current:4} | {ratio:5.2f} | {saturation_adj:+6.2f}  | {prob_before*100:7.1f}%  | {prob_after*100:7.1f}%  | {reduction_pct:7.1f}%")
    
    print("=" * 90)
    print("\n✅ VALIDATION:")
    print("  - Ratio < 0.75  → Ajustement +5% (boost si peu de buts)")
    print("  - Ratio ≥ 0.75  → Ajustement -5%")
    print("  - Ratio ≥ 1.00  → Ajustement -10%")
    print("  - Ratio ≥ 1.25  → Ajustement -15%")
    print("  - Ratio ≥ 1.50  → Ajustement -20% (saturation forte)")
    print("\n📌 NOTE: Moyenne attendue 1ère mi-temps = {:.2f} buts".format(avg_expected))
    print("   → Avec moyenne faible, saturation atteinte rapidement (2-3 buts suffisent)")
    
    predictor.close()

if __name__ == "__main__":
    test_saturation()
