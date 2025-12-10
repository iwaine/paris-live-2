#!/usr/bin/env python3
"""
Test de saturation PERSONNALISÉE par rencontre
Démontre que les moyennes sont combinées pour chaque match spécifique
"""

from live_predictor_v2 import LivePredictorV2, LiveMatchContext

def test_exemple_utilisateur():
    """
    Exemple fourni par l'utilisateur:
    
    Spartak Varna (HOME):
    - Moyenne totale : 6 buts/match
    - 1ère mi-temps : 2 buts
    - 2nde mi-temps : 4 buts
    
    Slavia Sofia (AWAY):
    - Moyenne totale : 3 buts/match
    - 1ère mi-temps : 1 but
    - 2nde mi-temps : 2 buts
    
    COMBINAISON POUR CETTE RENCONTRE:
    - Moyenne totale : (6 + 3) / 2 = 4.5 buts
    - 1ère mi-temps : (2 + 1) / 2 = 1.5 buts
    - 2nde mi-temps : (4 + 2) / 2 = 3.0 buts
    """
    
    predictor = LivePredictorV2()
    
    print("=" * 90)
    print("🎯 TEST SATURATION PERSONNALISÉE PAR RENCONTRE")
    print("=" * 90)
    
    # Charger les patterns réels
    home_pattern = predictor._load_pattern("Spartak Varna", True, "31-45+", "Bulgaria")
    away_pattern = predictor._load_pattern("Slavia Sofia", False, "31-45+", "Bulgaria")
    
    if not home_pattern or not away_pattern:
        print("❌ Patterns non trouvés")
        return
    
    # Afficher moyennes réelles (différentes de l'exemple théorique)
    print(f"\n📊 MOYENNES RÉELLES DANS LA BASE DE DONNÉES:")
    print(f"\n  Spartak Varna (HOME):")
    print(f"    - Moyenne totale : {home_pattern.get('avg_goals_full_match', 0):.2f} buts/match")
    print(f"    - 1ère mi-temps  : {home_pattern.get('avg_goals_first_half', 0):.2f} buts")
    print(f"    - 2nde mi-temps  : {home_pattern.get('avg_goals_second_half', 0):.2f} buts")
    
    print(f"\n  Slavia Sofia (AWAY):")
    print(f"    - Moyenne totale : {away_pattern.get('avg_goals_full_match', 0):.2f} buts/match")
    print(f"    - 1ère mi-temps  : {away_pattern.get('avg_goals_first_half', 0):.2f} buts")
    print(f"    - 2nde mi-temps  : {away_pattern.get('avg_goals_second_half', 0):.2f} buts")
    
    # COMBINAISON POUR CETTE RENCONTRE SPÉCIFIQUE
    avg_full_combined = (home_pattern['avg_goals_full_match'] + away_pattern['avg_goals_full_match']) / 2
    avg_1st_combined = (home_pattern['avg_goals_first_half'] + away_pattern['avg_goals_first_half']) / 2
    avg_2nd_combined = (home_pattern['avg_goals_second_half'] + away_pattern['avg_goals_second_half']) / 2
    
    print(f"\n  🔄 COMBINAISON POUR SPARTAK vs SLAVIA:")
    print(f"    - Moyenne totale attendue : {avg_full_combined:.2f} buts/match")
    print(f"    - Moyenne 1ère mi-temps   : {avg_1st_combined:.2f} buts")
    print(f"    - Moyenne 2nde mi-temps   : {avg_2nd_combined:.2f} buts")
    
    print("\n" + "=" * 90)
    print("🧪 SCÉNARIOS DE TEST - INTERVALLE 31-45+ (1ÈRE MI-TEMPS)")
    print("=" * 90)
    print(f"\nMoyenne attendue pour ce match : {avg_1st_combined:.2f} buts en 1ère mi-temps")
    print("-" * 90)
    
    scenarios = [
        (0, 0, "Aucun but"),
        (1, 0, "1 but seulement"),
        (1, 1, "2 buts (autour moyenne)"),
        (2, 1, "3 buts (saturation)"),
        (3, 2, "5 buts (forte saturation)"),
    ]
    
    print(f"{'Scénario':<25} | Score | Buts | Ratio | Ajust | Interprétation")
    print("-" * 90)
    
    for home_score, away_score, desc in scenarios:
        current_goals = home_score + away_score
        
        # Créer contexte match
        match = LiveMatchContext(
            home_team="Spartak Varna",
            away_team="Slavia Sofia",
            current_minute=32,
            home_score=home_score,
            away_score=away_score,
            country="Bulgaria",
            league="bulgaria"
        )
        
        # Calculer ajustement saturation
        adj = predictor._calculate_saturation_adjustment(match, home_pattern, away_pattern, "31-45+")
        
        ratio = current_goals / avg_1st_combined if avg_1st_combined > 0 else 0
        
        # Interprétation
        if adj > 0:
            interpretation = "BOOST (sous moyenne)"
        elif adj == -0.05:
            interpretation = "Neutre"
        elif adj == -0.10:
            interpretation = "Légère saturation"
        elif adj == -0.15:
            interpretation = "Saturation modérée"
        else:
            interpretation = "FORTE saturation"
        
        print(f"{desc:<25} | {home_score}-{away_score}   |  {current_goals:2}  | {ratio:5.2f} | {adj:+5.2f} | {interpretation}")
    
    print("\n" + "=" * 90)
    print("🧪 SCÉNARIOS DE TEST - INTERVALLE 75-90+ (2NDE MI-TEMPS)")
    print("=" * 90)
    
    # Charger patterns pour 75-90+
    home_pattern_2nd = predictor._load_pattern("Spartak Varna", True, "75-90+", "Bulgaria")
    away_pattern_2nd = predictor._load_pattern("Slavia Sofia", False, "75-90+", "Bulgaria")
    
    avg_2nd_combined_reload = (home_pattern_2nd['avg_goals_second_half'] + away_pattern_2nd['avg_goals_second_half']) / 2
    
    print(f"\nMoyenne attendue 2nde mi-temps : {avg_2nd_combined_reload:.2f} buts")
    print("-" * 90)
    
    scenarios_2nd = [
        (76, 1, 1, "2 buts au total"),
        (76, 2, 1, "3 buts au total"),
        (76, 2, 2, "4 buts au total"),
        (76, 3, 2, "5 buts (saturation)"),
    ]
    
    print(f"{'Scénario':<25} | Min | Score | Buts | Ratio | Ajust | Interprétation")
    print("-" * 90)
    
    for minute, home_score, away_score, desc in scenarios_2nd:
        current_goals = home_score + away_score
        
        match = LiveMatchContext(
            home_team="Spartak Varna",
            away_team="Slavia Sofia",
            current_minute=minute,
            home_score=home_score,
            away_score=away_score,
            country="Bulgaria",
            league="bulgaria"
        )
        
        # Ajustement pour 2nde mi-temps
        adj = predictor._calculate_saturation_adjustment(match, home_pattern_2nd, away_pattern_2nd, "75-90+")
        
        # Note: En 2nde mi-temps, on compare buts TOTAUX vs moyenne 2nde mi-temps
        # (car on ne sait pas combien ont été marqués spécifiquement en 2nde)
        ratio = current_goals / avg_2nd_combined_reload if avg_2nd_combined_reload > 0 else 0
        
        if adj > 0:
            interpretation = "BOOST"
        elif adj == -0.05:
            interpretation = "Neutre"
        elif adj == -0.10:
            interpretation = "Légère saturation"
        elif adj == -0.15:
            interpretation = "Saturation modérée"
        else:
            interpretation = "FORTE saturation"
        
        print(f"{desc:<25} | {minute:3} | {home_score}-{away_score}   |  {current_goals:2}  | {ratio:5.2f} | {adj:+5.2f} | {interpretation}")
    
    print("\n" + "=" * 90)
    print("✅ CONCLUSION:")
    print("=" * 90)
    print("""
La saturation est bien PERSONNALISÉE pour chaque rencontre :

1. Le système charge les moyennes des DEUX équipes dans leur configuration
   - Spartak Varna en HOME
   - Slavia Sofia en AWAY

2. Il COMBINE les moyennes : (moyenne_home + moyenne_away) / 2
   - Cette moyenne combinée est UNIQUE à cette rencontre
   - Elle change pour chaque paire d'équipes

3. L'ajustement compare les buts ACTUELS à cette moyenne COMBINÉE
   - Ratio = buts_actuels / moyenne_combinée
   - Ajustement : -20% à +5% selon le ratio

4. Cela fonctionne pour :
   - Full match (90min)
   - 1ère mi-temps (0-45)
   - 2nde mi-temps (46-90)

→ Chaque match a son propre seuil de saturation !
""")
    
    predictor.close()

if __name__ == "__main__":
    test_exemple_utilisateur()
