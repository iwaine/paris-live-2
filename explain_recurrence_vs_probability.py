#!/usr/bin/env python3
"""
EXPLICATION : Récurrence vs Probabilité d'au moins 1 but
=========================================================

La RÉCURRENCE dans la table team_goal_recurrence représente :
    (total_buts / total_matchs) × 100%

La PROBABILITÉ d'au moins 1 but est calculée DIFFÉREMMENT dans le préditeur :
    (matchs_avec_au_moins_1_but / total_matchs) × 100%

Voyons la différence avec des exemples réels
"""

import sqlite3

db_path = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

print("="*100)
print("📊 DIFFÉRENCE : RÉCURRENCE vs PROBABILITÉ D'AU MOINS 1 BUT")
print("="*100)
print()

# Exemple 1: RKC Waalwijk HOME - 2MT (76-90+)
print("🔍 EXEMPLE 1 : RKC Waalwijk HOME - 2ème MT")
print("-"*100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Récurrence dans la table
cursor.execute("""
    SELECT goal_count, total_matches
    FROM team_goal_recurrence
    WHERE team_name = 'RKC Waalwijk' AND is_home = 1 AND period = 2
""")
goal_count, total_matches = cursor.fetchone()

recurrence_pct = (goal_count / total_matches) * 100

print(f"📈 RÉCURRENCE (table team_goal_recurrence) :")
print(f"   • {goal_count} buts analysés (marqués + encaissés)")
print(f"   • Sur {total_matches} matchs")
print(f"   • Récurrence = {goal_count}/{total_matches} × 100 = {recurrence_pct:.1f}%")
print(f"   • Interprétation : En moyenne {goal_count/total_matches:.2f} buts par match dans cet intervalle")
print()

# Récupérer les matchs réels
cursor.execute("""
    SELECT goal_times, goal_times_conceded, date
    FROM soccerstats_scraped_matches
    WHERE team = 'RKC Waalwijk' AND is_home = 1
    ORDER BY date DESC
""")
import json

matches = cursor.fetchall()
print(f"🎯 PROBABILITÉ D'AU MOINS 1 BUT (calculée par le préditeur) :")
print(f"   Vérification match par match dans l'intervalle 76-90' :")
print()

matches_with_goal = 0
match_details = []

for i, (goals_str, conceded_str, date) in enumerate(matches, 1):
    goals_scored = json.loads(goals_str)
    goals_conceded = json.loads(conceded_str)
    
    # Buts dans 76-90'
    goals_in_interval = [g for g in goals_scored if 76 <= g <= 90]
    conceded_in_interval = [g for g in goals_conceded if 76 <= g <= 90]
    
    has_goal = len(goals_in_interval) > 0 or len(conceded_in_interval) > 0
    
    if has_goal:
        matches_with_goal += 1
    
    detail = f"   Match {i}: "
    if goals_in_interval:
        detail += f"⚽ Marqué à {goals_in_interval}"
    if conceded_in_interval:
        detail += f" 🔴 Encaissé à {conceded_in_interval}"
    if not has_goal:
        detail += "❌ Aucun but dans 76-90'"
    
    match_details.append((has_goal, detail))

# Afficher détails
for has_goal, detail in match_details[:7]:  # Limiter à 7 matchs
    print(detail)

prob_at_least_one = (matches_with_goal / len(matches)) * 100

print()
print(f"   • {matches_with_goal}/{len(matches)} matchs avec au moins 1 but dans 76-90'")
print(f"   • Probabilité = {matches_with_goal}/{len(matches)} × 100 = {prob_at_least_one:.1f}%")
print()

print("="*100)
print()

# Exemple 2: Monaco AWAY - 2MT (76-90+)
print("🔍 EXEMPLE 2 : Monaco AWAY - 2ème MT (POUR COMPARAISON)")
print("-"*100)

cursor.execute("""
    SELECT goal_count, total_matches
    FROM team_goal_recurrence
    WHERE team_name = 'Monaco' AND is_home = 0 AND period = 2
""")
goal_count_m, total_matches_m = cursor.fetchone()

recurrence_pct_m = (goal_count_m / total_matches_m) * 100

print(f"📈 RÉCURRENCE (table) :")
print(f"   • {goal_count_m} buts / {total_matches_m} matchs = {recurrence_pct_m:.1f}%")
print()

cursor.execute("""
    SELECT goal_times, goal_times_conceded, date
    FROM soccerstats_scraped_matches
    WHERE team = 'Monaco' AND is_home = 0
    ORDER BY date DESC
""")

matches_m = cursor.fetchall()
matches_with_goal_m = 0

print(f"🎯 PROBABILITÉ D'AU MOINS 1 BUT :")
print(f"   Vérification match par match dans 76-90' :")
print()

for i, (goals_str, conceded_str, date) in enumerate(matches_m, 1):
    goals_scored = json.loads(goals_str)
    goals_conceded = json.loads(conceded_str)
    
    goals_in_interval = [g for g in goals_scored if 76 <= g <= 90]
    conceded_in_interval = [g for g in goals_conceded if 76 <= g <= 90]
    
    has_goal = len(goals_in_interval) > 0 or len(conceded_in_interval) > 0
    
    if has_goal:
        matches_with_goal_m += 1
    
    detail = f"   Match {i}: "
    if goals_in_interval:
        detail += f"⚽ Marqué à {goals_in_interval}"
    if conceded_in_interval:
        detail += f" 🔴 Encaissé à {conceded_in_interval}"
    if not has_goal:
        detail += "❌ Aucun but dans 76-90'"
    
    print(detail)

prob_at_least_one_m = (matches_with_goal_m / len(matches_m)) * 100

print()
print(f"   • {matches_with_goal_m}/{len(matches_m)} matchs avec au moins 1 but dans 76-90'")
print(f"   • Probabilité = {matches_with_goal_m}/{len(matches_m)} × 100 = {prob_at_least_one_m:.1f}%")
print()

print("="*100)
print()

print("💡 SYNTHÈSE")
print("-"*100)
print()
print("📊 RÉCURRENCE (dans la table team_goal_recurrence) :")
print("   • Formule : (total_buts / total_matchs) × 100%")
print("   • Compte TOUS les buts (peut y avoir plusieurs buts par match)")
print("   • Peut dépasser 100% si plusieurs buts par match")
print("   • Exemple : 16 buts / 7 matchs = 228.6%")
print()
print("🎯 PROBABILITÉ D'AU MOINS 1 BUT (calculée par le préditeur) :")
print("   • Formule : (matchs_avec_au_moins_1_but / total_matchs) × 100%")
print("   • Compte uniquement si le match a AU MOINS 1 but dans l'intervalle")
print("   • Ne peut PAS dépasser 100%")
print("   • C'est CETTE métrique qui est utilisée pour la Formula MAX")
print()
print("📈 RÉSULTATS :")
print(f"   RKC Waalwijk HOME 76-90+ :")
print(f"      • Récurrence : {recurrence_pct:.1f}% (moyenne de buts)")
print(f"      • Probabilité ≥1 but : {prob_at_least_one:.1f}%")
print()
print(f"   Monaco AWAY 76-90+ :")
print(f"      • Récurrence : {recurrence_pct_m:.1f}% (moyenne de buts)")
print(f"      • Probabilité ≥1 but : {prob_at_least_one_m:.1f}%")
print()
print("✅ Le préditeur utilise la PROBABILITÉ ≥1 BUT pour la Formula MAX")
print()
print("="*100)

conn.close()
