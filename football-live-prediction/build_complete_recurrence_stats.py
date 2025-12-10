#!/usr/bin/env python3
"""
Extraction complète des récurrences par équipe/ligue/contexte (HOME/AWAY)
Inclut les minutes de buts avec moyenne + écart-type par mi-temps
"""

import sys
from pathlib import Path
import sqlite3
import json
from statistics import mean, stdev
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))


def extract_goal_minutes():
    """
    Extrait les minutes de buts depuis paris_live.db et reconstruit les récurrences
    """
    
    source_db = "./paris_live.db"
    target_db = "data/predictions.db"
    
    print("\n" + "=" * 120)
    print("🎯 CONSTRUCTION COMPLÈTE DES RÉCURRENCES: ÉQUIPE/LIGUE/CONTEXTE (HOME/AWAY) + MINUTES")
    print("=" * 120)
    
    # Charger données source
    source_conn = sqlite3.connect(source_db)
    source_conn.row_factory = sqlite3.Row
    source_cursor = source_conn.cursor()
    
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()
    
    # 1. Récupérer les matches avec events
    source_cursor.execute("SELECT * FROM historical_matches")
    source_matches = source_cursor.fetchall()
    
    print(f"\n✅ {len(source_matches)} matchs à traiter")
    
    # Structures pour stocker les récurrences
    team_context_stats = defaultdict(lambda: {
        "HOME": {"goals_scored_min": [], "goals_conceded_min": [], "h1_goals": [], "h2_goals": [], "h1_conceded": [], "h2_conceded": []},
        "AWAY": {"goals_scored_min": [], "goals_conceded_min": [], "h1_goals": [], "h2_goals": [], "h1_conceded": [], "h2_conceded": []}
    })
    
    # Traiter chaque match
    for match in source_matches:
        home_team = match['home_team']
        away_team = match['away_team']
        league = match['league']
        
        # Parser les events JSON
        try:
            events = json.loads(match.get('events_json', '[]')) if match.get('events_json') else []
        except:
            events = []
        
        # Séparer les buts HOME et AWAY
        home_goals_min = []
        away_goals_min = []
        
        for event in events:
            if event.get('event_type') == 'goal':
                minute = int(event.get('minute', 0))
                if event.get('team') == 'home':
                    home_goals_min.append(minute)
                elif event.get('team') == 'away':
                    away_goals_min.append(minute)
        
        # Classer par mi-temps
        h1_home = [m for m in home_goals_min if m <= 45]
        h2_home = [m for m in home_goals_min if m > 45]
        h1_away = [m for m in away_goals_min if m <= 45]
        h2_away = [m for m in away_goals_min if m > 45]
        
        # HOME TEAM
        stats_home = team_context_stats[home_team]["HOME"]
        stats_home["goals_scored_min"].extend(home_goals_min)
        stats_home["goals_conceded_min"].extend(away_goals_min)
        stats_home["h1_goals"].extend(h1_home)
        stats_home["h2_goals"].extend(h2_home)
        stats_home["h1_conceded"].extend(h1_away)
        stats_home["h2_conceded"].extend(h2_away)
        
        # AWAY TEAM
        stats_away = team_context_stats[away_team]["AWAY"]
        stats_away["goals_scored_min"].extend(away_goals_min)
        stats_away["goals_conceded_min"].extend(home_goals_min)
        stats_away["h1_goals"].extend(h1_away)
        stats_away["h2_goals"].extend(h2_away)
        stats_away["h1_conceded"].extend(h1_home)
        stats_away["h2_conceded"].extend(h2_home)
    
    # Créer table pour stocker les récurrences détaillées
    print("\n💾 Création de la table 'recurrence_stats'...")
    
    target_cursor.execute("""
        DROP TABLE IF EXISTS recurrence_stats
    """)
    
    target_cursor.execute("""
        CREATE TABLE recurrence_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            league TEXT,
            context TEXT,  -- HOME ou AWAY
            total_matches INTEGER,
            goals_scored_avg REAL,
            goals_scored_stdev REAL,
            goals_conceded_avg REAL,
            goals_conceded_stdev REAL,
            h1_goals_avg REAL,
            h1_goals_stdev REAL,
            h2_goals_avg REAL,
            h2_goals_stdev REAL,
            h1_conceded_avg REAL,
            h1_conceded_stdev REAL,
            h2_conceded_avg REAL,
            h2_conceded_stdev REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team, context)
        )
    """)
    
    # Insérer les statistiques
    print("\n📊 Calcul et insertion des statistiques...")
    
    inserted = 0
    for team, contexts_data in team_context_stats.items():
        for context in ["HOME", "AWAY"]:
            stats = contexts_data[context]
            
            # Compter les matchs
            total_matches = max(
                len(set([len(stats["goals_scored_min"]), len(stats["goals_conceded_min"])])),
                1
            )
            
            # Calculer moyennes et écarts-types
            def calc_stats(values):
                if not values:
                    return 0.0, 0.0
                avg = mean(values)
                stdev_val = stdev(values) if len(values) > 1 else 0.0
                return avg, stdev_val
            
            gs_avg, gs_stdev = calc_stats(stats["goals_scored_min"])
            gc_avg, gc_stdev = calc_stats(stats["goals_conceded_min"])
            
            h1g_avg, h1g_stdev = calc_stats(stats["h1_goals"])
            h2g_avg, h2g_stdev = calc_stats(stats["h2_goals"])
            h1c_avg, h1c_stdev = calc_stats(stats["h1_conceded"])
            h2c_avg, h2c_stdev = calc_stats(stats["h2_conceded"])
            
            # Récupérer la ligue depuis matches
            target_cursor.execute("""
                SELECT DISTINCT league FROM matches 
                WHERE (home_team = ? AND ? = 'HOME') OR (away_team = ? AND ? = 'AWAY')
                LIMIT 1
            """, (team, context, team, context))
            
            league_row = target_cursor.fetchone()
            league = league_row[0] if league_row else "Unknown"
            
            # Insérer
            try:
                target_cursor.execute("""
                    INSERT INTO recurrence_stats (
                        team, league, context, total_matches,
                        goals_scored_avg, goals_scored_stdev,
                        goals_conceded_avg, goals_conceded_stdev,
                        h1_goals_avg, h1_goals_stdev,
                        h2_goals_avg, h2_goals_stdev,
                        h1_conceded_avg, h1_conceded_stdev,
                        h2_conceded_avg, h2_conceded_stdev
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    team, league, context, len(stats["goals_scored_min"]),
                    gs_avg, gs_stdev,
                    gc_avg, gc_stdev,
                    h1g_avg, h1g_stdev,
                    h2g_avg, h2g_stdev,
                    h1c_avg, h1c_stdev,
                    h2c_avg, h2c_stdev
                ))
                inserted += 1
            except Exception as e:
                print(f"⚠️ Erreur insertion {team}/{context}: {e}")
    
    target_conn.commit()
    
    print(f"✅ {inserted} records insérés")
    
    # Afficher résumé
    print("\n" + "-" * 120)
    print("📋 TOP TEAMS: STATISTIQUES DE RÉCURRENCE")
    print("-" * 120)
    
    target_cursor.execute("""
        SELECT team, context, total_matches,
               ROUND(goals_scored_avg, 2) as gs_avg,
               ROUND(goals_scored_stdev, 2) as gs_std,
               ROUND(h1_goals_avg, 2) as h1_avg,
               ROUND(h2_goals_avg, 2) as h2_avg
        FROM recurrence_stats
        WHERE total_matches >= 3
        ORDER BY goals_scored_avg DESC
        LIMIT 15
    """)
    
    print(f"\n{'Team':25} | {'Context':6} | {'Matches':7} | {'Goals Avg±Std':15} | {'H1 Avg':8} | {'H2 Avg':8}")
    print("-" * 120)
    
    for row in target_cursor.fetchall():
        team, context, matches, gs_avg, gs_std, h1_avg, h2_avg = row
        print(f"{team:25} | {context:6} | {matches:7d} | {gs_avg:5.2f}±{gs_std:5.2f}       | {h1_avg:8.2f} | {h2_avg:8.2f}")
    
    # Stats globales par contexte
    print("\n" + "-" * 120)
    print("🏆 RÉSUMÉ GLOBAL: HOME vs AWAY")
    print("-" * 120)
    
    target_cursor.execute("""
        SELECT context,
               COUNT(*) as teams,
               ROUND(AVG(goals_scored_avg), 3) as avg_goals_scored,
               ROUND(AVG(goals_conceded_avg), 3) as avg_goals_conceded,
               ROUND(AVG(h1_goals_avg), 3) as h1_avg,
               ROUND(AVG(h2_goals_avg), 3) as h2_avg
        FROM recurrence_stats
        GROUP BY context
    """)
    
    for row in target_cursor.fetchall():
        context, teams, scored, conceded, h1, h2 = row
        print(f"{context:6} | {teams:3d} teams | Goals scored: {scored:.3f} | Conceded: {conceded:.3f} | H1: {h1:.3f} | H2: {h2:.3f}")
    
    source_conn.close()
    target_conn.close()
    
    print("\n" + "=" * 120)
    print("✅ CONSTRUCTION COMPLÈTE TERMINÉE")
    print("=" * 120 + "\n")


if __name__ == "__main__":
    try:
        extract_goal_minutes()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
