#!/usr/bin/env python3
"""
Import des données SoccerStats scraped vers predictions.db
Intégration avec les données existantes de paris_live.db
"""

import json
import sqlite3
from datetime import datetime
import statistics

def import_soccerstats_matches():
    """Importe les matchs SoccerStats dans predictions.db"""
    
    # Charger les données scraped
    with open('data/soccerstats_team_matches.json', 'r', encoding='utf-8') as f:
        soccerstats_data = json.load(f)
    
    # Connexion
    conn = sqlite3.connect('data/predictions.db')
    cursor = conn.cursor()
    
    print("📥 Import des données SoccerStats\n")
    print("=" * 70)
    
    # Créer table si nécessaire
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soccerstats_scraped_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            opponent TEXT NOT NULL,
            date TEXT,
            score TEXT,
            goals_for INTEGER,
            goals_against INTEGER,
            is_home INTEGER,
            result TEXT,
            goal_times TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insérer les données
    total_inserted = 0
    for team, team_data in soccerstats_data.items():
        matches = team_data.get('matches', [])
        
        for match in matches:
            cursor.execute('''
                INSERT INTO soccerstats_scraped_matches 
                (team, opponent, date, score, goals_for, goals_against, is_home, result, goal_times)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team,
                match['opponent'],
                match['date'],
                match['score'],
                match['goals_for'],
                match['goals_against'],
                1 if match['is_home'] else 0,
                match['result'],
                ','.join(match['goal_times']) if match['goal_times'] else ''
            ))
            total_inserted += 1
    
    conn.commit()
    
    print(f"✅ {total_inserted} matchs importés dans soccerstats_scraped_matches\n")
    
    # Comparaison avec données existantes
    print("=" * 70)
    print("📊 COMPARAISON AVEC DONNÉES EXISTANTES\n")
    
    # Données existantes dans predictions.db
    cursor.execute("SELECT COUNT(*) FROM matches")
    existing_count = cursor.fetchone()[0]
    print(f"📁 predictions.db (matches existants): {existing_count} matchs")
    
    cursor.execute("SELECT DISTINCT home_team FROM matches")
    existing_teams = set(row[0] for row in cursor.fetchall())
    print(f"   Équipes uniques: {len(existing_teams)}")
    
    cursor.execute("SELECT COUNT(*) FROM soccerstats_scraped_matches")
    scraped_count = cursor.fetchone()[0]
    print(f"\n📁 SoccerStats scraped: {scraped_count} matchs")
    
    cursor.execute("SELECT COUNT(DISTINCT team) FROM soccerstats_scraped_matches")
    scraped_teams = cursor.fetchone()[0]
    print(f"   Équipes uniques: {scraped_teams}")
    
    # Analyse détaillée d'une équipe
    print("\n" + "=" * 70)
    print("🔍 ANALYSE DÉTAILLÉE: LENS\n")
    
    # Données predictions.db
    cursor.execute('''
        SELECT COUNT(*) as matches, 
               SUM(CASE WHEN home_team = ? THEN 1 ELSE 0 END) as home_count,
               SUM(CASE WHEN home_team = ? THEN home_goals ELSE away_goals END) as goals_for,
               SUM(CASE WHEN home_team = ? THEN away_goals ELSE home_goals END) as goals_against
        FROM matches 
        WHERE home_team = ? OR away_team = ?
    ''', ('Lens', 'Lens', 'Lens', 'Lens', 'Lens'))
    
    existing_stats = cursor.fetchone()
    
    print(f"predictions.db (Lens):")
    if existing_stats[0] and existing_stats[0] > 0:
        print(f"  Matchs: {existing_stats[0]}")
        print(f"  Home: {existing_stats[1] or 0}, Away: {(existing_stats[0] - (existing_stats[1] or 0))}")
        print(f"  Buts pour: {existing_stats[2]}, contre: {existing_stats[3]}")
        print(f"  Moyenne: {existing_stats[2]/existing_stats[0]:.2f} pour, {existing_stats[3]/existing_stats[0]:.2f} contre")
    else:
        print(f"  ⚠ Lens non trouvé dans predictions.db")
    
    # Données SoccerStats
    cursor.execute('''
        SELECT COUNT(*) as matches,
               SUM(CASE WHEN is_home = 1 THEN 1 ELSE 0 END) as home_count,
               SUM(goals_for) as goals_for,
               SUM(goals_against) as goals_against
        FROM soccerstats_scraped_matches
        WHERE team = ?
    ''', ('Lens',))
    
    scraped_stats = cursor.fetchone()
    
    print(f"\nSoccerStats scraped (Lens):")
    print(f"  Matchs: {scraped_stats[0]}")
    print(f"  Home: {scraped_stats[1]}, Away: {scraped_stats[0] - scraped_stats[1]}")
    print(f"  Buts pour: {scraped_stats[2]}, contre: {scraped_stats[3]}")
    if scraped_stats[0] > 0:
        print(f"  Moyenne: {scraped_stats[2]/scraped_stats[0]:.2f} pour, {scraped_stats[3]/scraped_stats[0]:.2f} contre")
    
    # Exemple de matchs
    print("\n" + "=" * 70)
    print("⚽ EXEMPLES DE MATCHS - LENS (SoccerStats)\n")
    
    cursor.execute('''
        SELECT date, opponent, score, is_home, goal_times
        FROM soccerstats_scraped_matches
        WHERE team = ?
        LIMIT 5
    ''', ('Lens',))
    
    for row in cursor.fetchall():
        date, opponent, score, is_home, goal_times = row
        home_away = "HOME" if is_home else "AWAY"
        goals_str = f" (mins: {goal_times})" if goal_times else ""
        print(f"  {date:12s} | vs {opponent:15s} {score:5s} {home_away:5s}{goals_str}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ Import terminé!")


if __name__ == '__main__':
    import_soccerstats_matches()
