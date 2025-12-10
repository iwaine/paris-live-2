#!/usr/bin/env python3
"""
Analyse des buts UNIQUEMENT dans les intervalles clés 31-45 et 76-90
pour RKC Waalwijk et VVV
"""

import sqlite3
import json
import numpy as np

db_path = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

print("="*100)
print("📊 BUTS DANS LES INTERVALLES CLÉS UNIQUEMENT")
print("="*100)
print()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

teams = [
    ('RKC Waalwijk', 1, 'HOME'),
    ('RKC Waalwijk', 0, 'AWAY'),
    ('VVV', 1, 'HOME'),
    ('VVV', 0, 'AWAY')
]

intervals = [
    ('31-45', 31, 45, '1ère MT - Fin de mi-temps'),
    ('76-90', 76, 90, '2ème MT - Fin de match')
]

for team_name, is_home, lieu in teams:
    print(f"{'='*100}")
    print(f"🔍 {team_name} ({lieu})")
    print(f"{'='*100}")
    print()
    
    # Récupérer tous les matchs
    cursor.execute("""
        SELECT id, date, opponent, goal_times, goal_times_conceded
        FROM soccerstats_scraped_matches
        WHERE team = ? AND is_home = ?
        ORDER BY date DESC
    """, (team_name, is_home))
    
    matches = cursor.fetchall()
    total_matches = len(matches)
    
    print(f"📋 Total matchs analysés : {total_matches}")
    print()
    
    for interval_name, min_start, min_end, description in intervals:
        print(f"🎯 INTERVALLE {interval_name} ({description})")
        print("-"*100)
        
        buts_in_interval = []
        matches_with_goal = set()
        
        for match_id, date, opponent, goals_str, conceded_str in matches:
            try:
                goals_scored = json.loads(goals_str) if goals_str else []
                goals_conceded = json.loads(conceded_str) if conceded_str else []
            except:
                goals_scored = []
                goals_conceded = []
            
            # Filtrer les buts dans l'intervalle
            goals_in_range = [g for g in goals_scored if min_start <= g <= min_end]
            conceded_in_range = [g for g in goals_conceded if min_start <= g <= min_end]
            
            all_goals_in_interval = goals_in_range + conceded_in_range
            
            if all_goals_in_interval:
                buts_in_interval.extend(all_goals_in_interval)
                matches_with_goal.add(match_id)
                
                # Afficher détail du match
                detail = f"   • Match vs {opponent} ({date[:10]}) : "
                if goals_in_range:
                    detail += f"⚽ Marqué {goals_in_range} "
                if conceded_in_range:
                    detail += f"🔴 Encaissé {conceded_in_range}"
                print(detail)
        
        total_buts = len(buts_in_interval)
        nb_matches_with_goal = len(matches_with_goal)
        recurrence_pct = (total_buts / total_matches * 100) if total_matches > 0 else 0
        freq_at_least_one = (nb_matches_with_goal / total_matches * 100) if total_matches > 0 else 0
        
        print()
        print(f"📊 STATISTIQUES {interval_name} :")
        print(f"   • Buts totaux dans intervalle : {total_buts}")
        print(f"   • Matchs avec au moins 1 but : {nb_matches_with_goal}/{total_matches}")
        print(f"   • Récurrence : {recurrence_pct:.1f}% (buts/matchs)")
        print(f"   • Probabilité ≥1 but : {freq_at_least_one:.1f}% (pour Formula MAX)")
        
        if buts_in_interval:
            arr = np.array(buts_in_interval)
            avg = np.mean(arr)
            sem = np.std(arr, ddof=1) / np.sqrt(len(arr)) if len(arr) > 1 else 0
            q1, q3 = np.percentile(arr, [25, 75]) if len(arr) >= 4 else (min(arr), max(arr))
            
            print(f"   • Timing moyen : {avg:.1f}' ±{sem:.1f}' (SEM)")
            print(f"   • Zone IQR : [{q1:.0f}' - {q3:.0f}']")
        
        print()
    
    print()

conn.close()

print("="*100)
print("💡 DIFFÉRENCE AVEC LA TABLE team_goal_recurrence")
print("="*100)
print()
print("La table team_goal_recurrence contient :")
print("  • TOUS les buts de la 1ère mi-temps (1-45') pour period=1")
print("  • TOUS les buts de la 2ème mi-temps (46-90+') pour period=2")
print()
print("Ce script calcule :")
print("  • UNIQUEMENT les buts dans 31-45' pour l'intervalle 31-45")
print("  • UNIQUEMENT les buts dans 76-90' pour l'intervalle 76-90")
print()
print("="*100)
