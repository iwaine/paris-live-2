#!/usr/bin/env python3
"""
Top patterns Bulgaria - Classement par récurrence et fiabilité
Critère : Fréquence d'apparition de buts dans un intervalle spécifique
"""
import sqlite3
import json
from collections import defaultdict

def get_interval(minute):
    if 0 <= minute <= 15: return '0-15'
    elif 16 <= minute <= 30: return '16-30'
    elif 31 <= minute <= 45: return '31-45'
    elif 46 <= minute <= 60: return '46-60'
    elif 61 <= minute <= 75: return '61-75'
    elif 76 <= minute <= 90: return '76-90'
    return None

def analyze_patterns():
    conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
    cursor = conn.cursor()
    
    # Structure : {(team, is_home, interval): {'matches_with_goals': set(), 'total_goals': 0, 'scored': 0, 'conceded': 0, 'total_matches': 0}}
    patterns = defaultdict(lambda: {
        'matches_with_goals': set(),
        'total_goals': 0,
        'scored': 0,
        'conceded': 0,
        'total_matches': 0
    })
    
    # Récupérer toutes les équipes
    cursor.execute("""
        SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = 'bulgaria'
    """)
    teams = [row[0] for row in cursor.fetchall()]
    
    for team in teams:
        for is_home in [0, 1]:
            # Récupérer tous les matchs
            cursor.execute("""
                SELECT goal_times, goal_times_conceded, date, opponent
                FROM soccerstats_scraped_matches 
                WHERE league = 'bulgaria' AND team = ? AND is_home = ?
            """, (team, is_home))
            
            matches = cursor.fetchall()
            location = "HOME" if is_home else "AWAY"
            
            # Pour chaque intervalle, compter les matchs où il y a eu des buts
            # FOCUS sur les intervalles clés : 31-45 et 76-90
            for interval_name in ['31-45', '76-90']:
                key = (team, location, interval_name)
                patterns[key]['total_matches'] = len(matches)
                
                for match in matches:
                    goal_times = json.loads(match[0]) if match[0] else []
                    goal_times_conceded = json.loads(match[1]) if match[1] else []
                    date = match[2]
                    opponent = match[3]
                    match_id = f"{date}_{opponent}"
                    
                    goals_in_interval = 0
                    scored_in_interval = 0
                    conceded_in_interval = 0
                    
                    # Buts marqués dans cet intervalle
                    for minute in goal_times:
                        if minute > 0 and get_interval(minute) == interval_name:
                            goals_in_interval += 1
                            scored_in_interval += 1
                    
                    # Buts encaissés dans cet intervalle
                    for minute in goal_times_conceded:
                        if minute > 0 and get_interval(minute) == interval_name:
                            goals_in_interval += 1
                            conceded_in_interval += 1
                    
                    # Si au moins un but dans cet intervalle, compter le match
                    if goals_in_interval > 0:
                        patterns[key]['matches_with_goals'].add(match_id)
                        patterns[key]['total_goals'] += goals_in_interval
                        patterns[key]['scored'] += scored_in_interval
                        patterns[key]['conceded'] += conceded_in_interval
    
    # Calculer le pourcentage de récurrence et filtrer
    results = []
    
    for (team, location, interval), data in patterns.items():
        total_matches = data['total_matches']
        matches_with_goals = len(data['matches_with_goals'])
        total_goals = data['total_goals']
        scored = data['scored']
        conceded = data['conceded']
        
        if total_matches == 0:
            continue
        
        # Pourcentage de matchs avec au moins 1 but dans cet intervalle
        recurrence_pct = (matches_with_goals / total_matches * 100)
        
        # Filtre : au moins 6 buts totaux ET au moins 3 matchs différents avec des buts
        if total_goals >= 6 and matches_with_goals >= 3:
            results.append({
                'team': team,
                'location': location,
                'interval': interval,
                'recurrence_pct': recurrence_pct,
                'matches_with_goals': matches_with_goals,
                'total_matches': total_matches,
                'total_goals': total_goals,
                'scored': scored,
                'conceded': conceded
            })
    
    # Trier par récurrence décroissante
    results.sort(key=lambda x: x['recurrence_pct'], reverse=True)
    
    # Affichage
    print("\n" + "="*110)
    print("                    🏆 TOP PATTERNS BULGARIA PARVA LIGA 2025-2026")
    print("="*110)
    print("\n🎯 FOCUS : Intervalles 31-45 min (fin 1ère MT) et 76-90 min (fin match)")
    print("Critères : ≥6 buts totaux | ≥3 matchs avec buts | Classement par % de récurrence")
    print("\n" + "="*110 + "\n")
    
    for i, pattern in enumerate(results[:30], 1):
        team = pattern['team']
        location = pattern['location']
        interval = pattern['interval']
        recurrence_pct = pattern['recurrence_pct']
        matches_with_goals = pattern['matches_with_goals']
        total_matches = pattern['total_matches']
        total_goals = pattern['total_goals']
        scored = pattern['scored']
        conceded = pattern['conceded']
        
        # Symbole selon la récurrence
        if recurrence_pct >= 70:
            symbol = "🔥"
        elif recurrence_pct >= 50:
            symbol = "⭐"
        else:
            symbol = "✅"
        
        print(f"{i:2}. {symbol} {team:20} {location:4} {interval:6} : {recurrence_pct:5.1f}% "
              f"({total_goals} buts sur {matches_with_goals}/{total_matches} matches)")
        print(f"    └─ {scored} marqués + {conceded} encaissés")
    
    print("\n" + "="*110)
    print("\n📊 Légende :")
    print("   🔥 = Récurrence ≥70% (très fiable)")
    print("   ⭐ = Récurrence ≥50% (fiable)")
    print("   ✅ = Récurrence <50% (modéré)")
    print("\n" + "="*110 + "\n")
    
    conn.close()

if __name__ == "__main__":
    analyze_patterns()
