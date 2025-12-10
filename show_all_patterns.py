#!/usr/bin/env python3
"""
AFFICHAGE DES PATTERNS HISTORIQUES
Base de données : team_goal_recurrence
Formule V2.0 : Buts marqués + Buts encaissés
"""

import sqlite3
import sys

db_path = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

print("="*120)
print("📊 PATTERNS HISTORIQUES - TOUTES LES ÉQUIPES")
print("="*120)
print()

# Statistiques globales
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        COUNT(DISTINCT team_name) as total_teams,
        COUNT(*) as total_records,
        SUM(goal_count) as total_goals,
        SUM(total_matches) as total_matches_analyzed
    FROM team_goal_recurrence
""")
stats = cursor.fetchone()

print(f"📈 STATISTIQUES GLOBALES")
print(f"   • Équipes analysées : {stats[0]}")
print(f"   • Enregistrements : {stats[1]} (4 par équipe : HOME/AWAY × 1MT/2MT)")
print(f"   • Buts totaux analysés : {stats[2]:,}")
print(f"   • Matchs analysés : {stats[3]:,}")
print()

print("="*120)
print()

# Top patterns pour intervalle 31-45+ (pic entre 31-45')
print("🎯 TOP 20 - INTERVALLE 31-45+ (1ère Mi-Temps)")
print("-"*120)
print(f"{'Équipe':<25} {'Lieu':<6} {'Avg':<8} {'SEM':<8} {'Zone IQR':<20} {'Buts':<6} {'Matchs':<8} {'Réc%':<6}")
print("-"*120)

cursor.execute("""
    SELECT 
        team_name,
        CASE WHEN is_home = 1 THEN 'HOME' ELSE 'AWAY' END as venue,
        ROUND(avg_minute, 1) as avg_min,
        ROUND(sem_minute, 1) as sem,
        ROUND(iqr_q1, 0) as q1,
        ROUND(iqr_q3, 0) as q3,
        goal_count,
        total_matches,
        ROUND(goal_count * 100.0 / total_matches, 0) as rec_pct
    FROM team_goal_recurrence
    WHERE period = 1
    AND avg_minute BETWEEN 31 AND 45
    ORDER BY rec_pct DESC, sem_minute ASC
    LIMIT 20
""")

for row in cursor.fetchall():
    team, venue, avg, sem, q1, q3, goals, matches, rec = row
    print(f"{team:<25} {venue:<6} {avg:>6.1f}' {sem:>6.1f}' [{q1:>3.0f}'-{q3:>3.0f}']      {goals:>4} {matches:>6}   {rec:>5.0f}%")

print()
print("="*120)
print()

# Top patterns pour intervalle 76-90+ (pic entre 76-90')
print("🎯 TOP 20 - INTERVALLE 76-90+ (2ème Mi-Temps)")
print("-"*120)
print(f"{'Équipe':<25} {'Lieu':<6} {'Avg':<8} {'SEM':<8} {'Zone IQR':<20} {'Buts':<6} {'Matchs':<8} {'Réc%':<6}")
print("-"*120)

cursor.execute("""
    SELECT 
        team_name,
        CASE WHEN is_home = 1 THEN 'HOME' ELSE 'AWAY' END as venue,
        ROUND(avg_minute, 1) as avg_min,
        ROUND(sem_minute, 1) as sem,
        ROUND(iqr_q1, 0) as q1,
        ROUND(iqr_q3, 0) as q3,
        goal_count,
        total_matches,
        ROUND(goal_count * 100.0 / total_matches, 0) as rec_pct
    FROM team_goal_recurrence
    WHERE period = 2
    AND avg_minute BETWEEN 76 AND 90
    ORDER BY rec_pct DESC, sem_minute ASC
    LIMIT 20
""")

for row in cursor.fetchall():
    team, venue, avg, sem, q1, q3, goals, matches, rec = row
    precision = "🎯 PRÉCIS" if sem < 3 else "✅ Bon" if sem < 5 else ""
    print(f"{team:<25} {venue:<6} {avg:>6.1f}' {sem:>6.1f}' [{q1:>3.0f}'-{q3:>3.0f}']      {goals:>4} {matches:>6}   {rec:>5.0f}% {precision}")

print()
print("="*120)
print()

# Équipes avec meilleure précision (SEM le plus faible)
print("🎯 TOP 15 - MEILLEURE PRÉCISION (SEM le plus faible)")
print("-"*120)
print(f"{'Équipe':<25} {'Lieu':<6} {'MT':<4} {'Avg':<8} {'SEM':<8} {'Zone IQR':<20} {'Buts':<6} {'Matchs':<8}")
print("-"*120)

cursor.execute("""
    SELECT 
        team_name,
        CASE WHEN is_home = 1 THEN 'HOME' ELSE 'AWAY' END as venue,
        CASE WHEN period = 1 THEN '1MT' ELSE '2MT' END as half,
        ROUND(avg_minute, 1) as avg_min,
        ROUND(sem_minute, 1) as sem,
        ROUND(iqr_q1, 0) as q1,
        ROUND(iqr_q3, 0) as q3,
        goal_count,
        total_matches
    FROM team_goal_recurrence
    WHERE goal_count >= 10
    ORDER BY sem_minute ASC
    LIMIT 15
""")

for row in cursor.fetchall():
    team, venue, half, avg, sem, q1, q3, goals, matches = row
    iqr_width = q3 - q1
    print(f"{team:<25} {venue:<6} {half:<4} {avg:>6.1f}' ±{sem:>5.1f}' [{q1:>3.0f}'-{q3:>3.0f}'] (IQR:{iqr_width:>2.0f}') {goals:>4} {matches:>6}")

print()
print("="*120)
print()

# Recherche équipes françaises
print("🇫🇷 ÉQUIPES FRANÇAISES (Ligue 1)")
print("-"*120)
print(f"{'Équipe':<25} {'Lieu':<6} {'MT':<4} {'Avg':<8} {'SEM':<8} {'Zone IQR':<20} {'Buts':<6} {'Réc%':<6}")
print("-"*120)

french_teams = ['Monaco', 'PSG', 'Lyon', 'Marseille', 'Lille', 'Nice', 'Lens', 'Rennes', 
                'Brest', 'Reims', 'Toulouse', 'Montpellier', 'Strasbourg', 'Nantes',
                'Le Havre', 'Angers', 'Auxerre', 'Saint-Etienne']

for team in french_teams:
    cursor.execute("""
        SELECT 
            team_name,
            CASE WHEN is_home = 1 THEN 'HOME' ELSE 'AWAY' END as venue,
            CASE WHEN period = 1 THEN '1MT' ELSE '2MT' END as half,
            ROUND(avg_minute, 1) as avg_min,
            ROUND(sem_minute, 1) as sem,
            ROUND(iqr_q1, 0) as q1,
            ROUND(iqr_q3, 0) as q3,
            goal_count,
            total_matches,
            ROUND(goal_count * 100.0 / total_matches, 0) as rec_pct
        FROM team_goal_recurrence
        WHERE team_name = ?
        ORDER BY is_home DESC, period
    """, (team,))
    
    results = cursor.fetchall()
    if results:
        for row in results:
            team_name, venue, half, avg, sem, q1, q3, goals, matches, rec = row
            highlight = "🔥" if (half == '2MT' and avg >= 76 and rec >= 150) else ""
            print(f"{team_name:<25} {venue:<6} {half:<4} {avg:>6.1f}' ±{sem:>5.1f}' [{q1:>3.0f}'-{q3:>3.0f}']      {goals:>4} {rec:>5.0f}% {highlight}")

print()
print("="*120)
print()

print("💡 LÉGENDE")
print("-"*120)
print("• Avg : Minute moyenne du but (marqué ou encaissé)")
print("• SEM : Erreur standard de la moyenne (précision du timing)")
print("  → <3' = TRÈS PRÉCIS, <5' = Précis, >5' = Dispersé")
print("• Zone IQR : Intervalle interquartile [Q1-Q3] où se trouvent 50% des buts")
print("• Réc% : Récurrence = (buts marqués + buts encaissés) / matchs × 100%")
print("  → >200% = Plus de 2 buts par match dans cet intervalle")
print("  → 100% = 1 but par match en moyenne")
print()
print("🎯 INTERVALLES CLÉS pour signaux :")
print("   • 31-45+ (fin 1ère MT)")
print("   • 76-90+ (fin 2ème MT)")
print()
print("="*120)

conn.close()
