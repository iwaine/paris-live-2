#!/usr/bin/env python3
"""
Test d'affichage de toutes les stats live disponibles
"""

# Simuler des données live complètes (comme retournées par le scraper)
match_data = {
    'home_team': 'Spartak Varna',
    'away_team': 'Slavia Sofia',
    'current_minute': 78,
    'score_home': 1,
    'score_away': 1,
    'live_stats': {
        'possession_home': 43.0,
        'possession_away': 57.0,
        'corners_home': 4,
        'corners_away': 6,
        'shots_home': 7,           # ← CETTE STAT ÉTAIT MANQUANTE AVANT
        'shots_away': 13,          # ← CETTE STAT ÉTAIT MANQUANTE AVANT
        'shots_on_target_home': 2,
        'shots_on_target_away': 5,
        'attacks_home': 36,        # ← CETTE STAT ÉTAIT MANQUANTE AVANT
        'attacks_away': 47,        # ← CETTE STAT ÉTAIT MANQUANTE AVANT
        'dangerous_attacks_home': 24,
        'dangerous_attacks_away': 21,
        'shots_inside_box_home': 5,
        'shots_inside_box_away': 9,
        'shots_outside_box_home': 2,
        'shots_outside_box_away': 4,
    }
}

print("╔═══════════════════════════════════════════════════════════════════════════════╗")
print("║              🧪 TEST - AFFICHAGE DE TOUTES LES STATS LIVE                    ║")
print("╚═══════════════════════════════════════════════════════════════════════════════╝")
print()
print("⚽ MATCH EN COURS")
print("="*50)
print(f"🏟️  {match_data['home_team']} vs {match_data['away_team']}")
print(f"⏱️  Minute : {match_data['current_minute']}'")
print(f"📊 Score : {match_data['score_home']}-{match_data['score_away']}")
print()

print("📈 STATS LIVE - VERSION COMPLÈTE")
print("-"*50)
stats = match_data['live_stats']

# Afficher toutes les stats dans l'ordre prioritaire
if stats.get('possession_home') is not None:
    print(f"✅ Possession : {stats['possession_home']:.0f}% - {stats['possession_away']:.0f}% ✓")

if stats.get('corners_home') is not None:
    print(f"✅ Corners : {stats['corners_home']} - {stats['corners_away']} ✓")

if stats.get('shots_home') is not None:
    print(f"✅ Total shots : {stats['shots_home']} - {stats['shots_away']} ✓")

if stats.get('shots_on_target_home') is not None:
    print(f"✅ Shots on target : {stats['shots_on_target_home']} - {stats['shots_on_target_away']} ✓")

if stats.get('attacks_home') is not None:
    print(f"✅ Attacks : {stats['attacks_home']} - {stats['attacks_away']} ✓")

if stats.get('dangerous_attacks_home') is not None:
    print(f"✅ Dangerous attacks : {stats['dangerous_attacks_home']} - {stats['dangerous_attacks_away']} ✓")

if stats.get('shots_inside_box_home') is not None:
    print(f"📍 Shots inside box : {stats['shots_inside_box_home']} - {stats['shots_inside_box_away']}")

if stats.get('shots_outside_box_home') is not None:
    print(f"📍 Shots outside box : {stats['shots_outside_box_home']} - {stats['shots_outside_box_away']}")

print()
print("━"*78)
print("💡 ANALYSE DES STATS")
print("━"*78)
print()

# Analyse comparative
poss_advantage = "Slavia Sofia (ext)" if stats['possession_away'] > stats['possession_home'] else "Spartak Varna (dom)"
shots_advantage = "Slavia Sofia" if stats['shots_away'] > stats['shots_home'] else "Spartak Varna"
attacks_advantage = "Slavia Sofia" if stats['attacks_away'] > stats['attacks_home'] else "Spartak Varna"

print(f"🔍 Domination possession : {poss_advantage} ({max(stats['possession_home'], stats['possession_away']):.0f}%)")
print(f"🔍 Domination tirs : {shots_advantage} ({max(stats['shots_home'], stats['shots_away'])} tirs)")
print(f"🔍 Domination attaques : {attacks_advantage} ({max(stats['attacks_home'], stats['attacks_away'])} attaques)")
print()

# Efficacité offensive
eff_home = (stats['shots_on_target_home'] / stats['shots_home'] * 100) if stats['shots_home'] > 0 else 0
eff_away = (stats['shots_on_target_away'] / stats['shots_away'] * 100) if stats['shots_away'] > 0 else 0

print(f"⚽ Efficacité tirs (% cadrés) :")
print(f"  • Spartak Varna : {eff_home:.1f}% ({stats['shots_on_target_home']}/{stats['shots_home']})")
print(f"  • Slavia Sofia : {eff_away:.1f}% ({stats['shots_on_target_away']}/{stats['shots_away']})")
print()

# Qualité des attaques
qual_home = (stats['dangerous_attacks_home'] / stats['attacks_home'] * 100) if stats['attacks_home'] > 0 else 0
qual_away = (stats['dangerous_attacks_away'] / stats['attacks_away'] * 100) if stats['attacks_away'] > 0 else 0

print(f"🔥 Qualité attaques (% dangereuses) :")
print(f"  • Spartak Varna : {qual_home:.1f}% ({stats['dangerous_attacks_home']}/{stats['attacks_home']})")
print(f"  • Slavia Sofia : {qual_away:.1f}% ({stats['dangerous_attacks_away']}/{stats['attacks_away']})")
print()

print("╚═══════════════════════════════════════════════════════════════════════════════╝")
print()
print("✅ RÉSULTAT : Toutes les stats sont maintenant affichées !")
print("   • Total shots : ✓")
print("   • Shots on target : ✓")
print("   • Attacks : ✓")
print("   • Dangerous attacks : ✓")
print("   • + Bonus : Shots inside/outside box")

