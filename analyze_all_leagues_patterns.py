#!/usr/bin/env python3
"""
Analyse des patterns historiques pour TOUTES les ligues
Génère un rapport complet par ligue avec :
- Top patterns 31-45 (fin 1ère MT)
- Top patterns 76-90 (fin match)
- Distribution des buts par intervalle
- Statistiques globales
"""

import sqlite3
import json
from collections import defaultdict

DB_PATH = '/workspaces/paris-live/football-live-prediction/data/predictions.db'

def analyze_league_patterns(league_code: str):
    """Analyse complète des patterns d'une ligue"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*100)
    print(f"🏆 ANALYSE PATTERNS - {league_code.upper()}")
    print("="*100)
    
    # Statistiques globales
    cursor.execute("""
        SELECT COUNT(*) as total_matchs,
               COUNT(DISTINCT team) as nb_teams,
               SUM(goals_for) as total_goals_for,
               SUM(goals_against) as total_goals_against
        FROM soccerstats_scraped_matches 
        WHERE league = ?
    """, (league_code,))
    
    stats = cursor.fetchone()
    total_matchs, nb_teams, total_goals_for, total_goals_against = stats
    
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print(f"   • Équipes: {nb_teams}")
    print(f"   • Matchs totaux: {total_matchs}")
    print(f"   • Buts marqués: {total_goals_for}")
    print(f"   • Buts encaissés: {total_goals_against}")
    print(f"   • Balance: {total_goals_for} = {total_goals_against} {'✅' if total_goals_for == total_goals_against else '❌'}")
    
    # Distribution des buts par intervalle
    cursor.execute("SELECT goal_times FROM soccerstats_scraped_matches WHERE league = ?", (league_code,))
    all_goals = []
    for row in cursor.fetchall():
        all_goals.extend([g for g in json.loads(row[0]) if g > 0])
    
    intervals = {
        '1-15': (1, 15),
        '16-30': (16, 30),
        '31-45': (31, 45),
        '46-60': (46, 60),
        '61-75': (61, 75),
        '76-90': (76, 90)
    }
    
    print(f"\n📈 DISTRIBUTION DES BUTS PAR INTERVALLE ({len(all_goals)} buts totaux):")
    for interval_name, (min_start, min_end) in intervals.items():
        count = sum(1 for g in all_goals if min_start <= g <= min_end)
        pct = (count / len(all_goals) * 100) if all_goals else 0
        bar = "█" * int(pct / 2)
        print(f"   {interval_name:6} : {count:4} buts ({pct:5.1f}%) {bar}")
    
    # Analyse patterns par équipe
    cursor.execute("""
        SELECT team, is_home, goal_times, goal_times_conceded, date, opponent
        FROM soccerstats_scraped_matches WHERE league = ?
    """, (league_code,))
    
    def categorize(minute):
        if 31 <= minute <= 45: return '31-45'
        elif 76 <= minute <= 90: return '76-90'
        return None
    
    match_has_goal_in_interval = defaultdict(lambda: defaultdict(set))
    match_counts = defaultdict(int)
    
    for row in cursor.fetchall():
        team = row[0]
        is_home = "HOME" if row[1] == 1 else "AWAY"
        goals_scored = json.loads(row[2])
        goals_conceded = json.loads(row[3])
        
        key = f"{team} {is_home}"
        match_counts[key] += 1
        match_id = f"{row[4]}_{row[5]}"
        
        intervals_with_goals = set()
        for minute in goals_scored + goals_conceded:
            if minute > 0:
                interval = categorize(minute)
                if interval:
                    intervals_with_goals.add(interval)
        
        for interval in intervals_with_goals:
            match_has_goal_in_interval[key][interval].add(match_id)
    
    patterns = {}
    for key in match_counts:
        patterns[key] = {}
        for interval in ['31-45', '76-90']:
            matches_with_goal = len(match_has_goal_in_interval[key][interval])
            total_matches = match_counts[key]
            recurrence = (matches_with_goal / total_matches) * 100 if total_matches > 0 else 0
            patterns[key][interval] = {
                'matches_with_goal': matches_with_goal,
                'total_matches': total_matches,
                'recurrence': recurrence
            }
    
    # TOP PATTERNS 31-45
    print("\n" + "="*100)
    print("🎯 TOP 15 PATTERNS 31-45 (FIN 1ÈRE MI-TEMPS)")
    print("="*100)
    
    interval_31_45 = [(k, d['matches_with_goal'], d['total_matches'], d['recurrence']) 
                      for k, v in patterns.items() for i, d in v.items() 
                      if i == '31-45' and d['matches_with_goal'] >= 3]
    interval_31_45.sort(key=lambda x: x[3], reverse=True)
    
    for i, (pattern, m, t, r) in enumerate(interval_31_45[:15], 1):
        status = "🔥" if r >= 50 else "✅" if r >= 40 else "📊"
        print(f"{i:2}. {status} {pattern:35} : {m:2}/{t:2} matchs = {r:5.1f}%")
    
    exploitable_31_45 = sum(1 for p in interval_31_45 if p[3] >= 50)
    print(f"\n📊 Résumé: {len(interval_31_45)} patterns | 🔥 {exploitable_31_45} exploitables (≥50%)")
    
    # TOP PATTERNS 76-90
    print("\n" + "="*100)
    print("🎯 TOP 15 PATTERNS 76-90 (FIN MATCH)")
    print("="*100)
    
    interval_76_90 = [(k, d['matches_with_goal'], d['total_matches'], d['recurrence']) 
                      for k, v in patterns.items() for i, d in v.items() 
                      if i == '76-90' and d['matches_with_goal'] >= 3]
    interval_76_90.sort(key=lambda x: x[3], reverse=True)
    
    for i, (pattern, m, t, r) in enumerate(interval_76_90[:15], 1):
        status = "🔥" if r >= 50 else "✅" if r >= 40 else "📊"
        print(f"{i:2}. {status} {pattern:35} : {m:2}/{t:2} matchs = {r:5.1f}%")
    
    exploitable_76_90 = sum(1 for p in interval_76_90 if p[3] >= 50)
    print(f"\n📊 Résumé: {len(interval_76_90)} patterns | 🔥 {exploitable_76_90} exploitables (≥50%)")
    
    print("\n" + "="*100 + "\n")
    
    conn.close()
    
    return {
        'league': league_code,
        'teams': nb_teams,
        'matches': total_matchs,
        'goals': len(all_goals),
        'patterns_31_45': len(interval_31_45),
        'exploitable_31_45': exploitable_31_45,
        'patterns_76_90': len(interval_76_90),
        'exploitable_76_90': exploitable_76_90
    }


def main():
    """Analyse toutes les ligues"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT league FROM soccerstats_scraped_matches ORDER BY league")
    leagues = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print("\n" + "="*100)
    print("🌍 ANALYSE PATTERNS HISTORIQUES - TOUTES LES LIGUES")
    print("="*100)
    print(f"📊 {len(leagues)} ligues à analyser: {', '.join([l.upper() for l in leagues])}")
    print("="*100)
    
    results = []
    for league in leagues:
        result = analyze_league_patterns(league)
        results.append(result)
    
    # Récapitulatif global
    print("\n" + "="*100)
    print("📊 RÉCAPITULATIF GLOBAL")
    print("="*100)
    print(f"\n{'LIGUE':15} | Équipes | Matchs | Buts | Patterns 31-45 | Exploit. | Patterns 76-90 | Exploit.")
    print("-"*100)
    
    for r in results:
        print(f"{r['league'].upper():15} | {r['teams']:7} | {r['matches']:6} | {r['goals']:4} | "
              f"{r['patterns_31_45']:14} | {r['exploitable_31_45']:8} | "
              f"{r['patterns_76_90']:14} | {r['exploitable_76_90']:8}")
    
    total_teams = sum(r['teams'] for r in results)
    total_matches = sum(r['matches'] for r in results)
    total_goals = sum(r['goals'] for r in results)
    total_patterns_31_45 = sum(r['patterns_31_45'] for r in results)
    total_exploitable_31_45 = sum(r['exploitable_31_45'] for r in results)
    total_patterns_76_90 = sum(r['patterns_76_90'] for r in results)
    total_exploitable_76_90 = sum(r['exploitable_76_90'] for r in results)
    
    print("-"*100)
    print(f"{'TOTAL':15} | {total_teams:7} | {total_matches:6} | {total_goals:4} | "
          f"{total_patterns_31_45:14} | {total_exploitable_31_45:8} | "
          f"{total_patterns_76_90:14} | {total_exploitable_76_90:8}")
    
    print("\n" + "="*100)
    print("✅ ANALYSE TERMINÉE")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
