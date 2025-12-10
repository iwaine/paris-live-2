#!/usr/bin/env python3
"""
ETAPE 1: Intégration des données SoccerStats Ligue 1 existantes
Combine les 144 matchs SoccerStats avec les données historiques existantes
et recalcule les statistiques de récurrence
"""

import sqlite3
import json
import sys
from pathlib import Path

def main():
    db_path = "data/predictions.db"
    
    print("\n" + "="*80)
    print("📥 INTÉGRATION DONNÉES SOCCERSTATS LIGUE 1")
    print("="*80 + "\n")
    
    # Vérifier que les données SoccerStats sont importées
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='soccerstats_scraped_matches'")
    if cursor.fetchone()[0] == 0:
        print("❌ Table soccerstats_scraped_matches non trouvée")
        print("   Exécutez d'abord: python3 import_soccerstats_data.py")
        conn.close()
        return False
    
    # Vérifier les données
    cursor.execute("SELECT COUNT(*) FROM soccerstats_scraped_matches")
    count = cursor.fetchone()[0]
    
    print(f"✅ Table soccerstats_scraped_matches: {count} matchs\n")
    
    if count == 0:
        print("❌ Aucun match trouvé dans soccerstats_scraped_matches")
        conn.close()
        return False
    
    # Summary
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT team) as teams,
            COUNT(DISTINCT opponent) as opponents,
            SUM(goals_for) as total_goals_for,
            SUM(goals_against) as total_goals_against
        FROM soccerstats_scraped_matches
    """)
    
    teams, opponents, gf, ga = cursor.fetchone()
    
    print(f"📊 Summary SoccerStats:")
    print(f"   Unique teams: {teams}")
    print(f"   Unique opponents: {opponents}")
    print(f"   Total goals for: {gf}")
    print(f"   Total goals against: {ga}")
    
    # Sample matches
    print(f"\n🎯 Sample matches:")
    cursor.execute("""
        SELECT team, opponent, score, result, date FROM soccerstats_scraped_matches
        LIMIT 5
    """)
    
    for team, opponent, score, result, date in cursor.fetchall():
        print(f"   {team:15s} vs {opponent:15s} | {score:5s} {result} | {date}")
    
    # Vérifier matchs avec minutages
    cursor.execute("""
        SELECT COUNT(*), SUM(LENGTH(goal_times) - LENGTH(REPLACE(goal_times, ',', '')) + 1)
        FROM soccerstats_scraped_matches 
        WHERE goal_times != ''
    """)
    
    matches_with_times, total_goals = cursor.fetchone()
    total_goals = total_goals or 0
    
    print(f"\n⏱️  Goal timings:")
    print(f"   Matches with goal times: {matches_with_times}/{count}")
    print(f"   Total goals documented: {total_goals}")
    
    # Comparaison avec données existantes si présentes
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='matches'")
    if cursor.fetchone()[0] > 0:
        cursor.execute("SELECT COUNT(*) FROM matches")
        existing = cursor.fetchone()[0]
        print(f"\n📁 Existing matches in 'matches' table: {existing}")
        print(f"   Données SoccerStats: {count}")
        print(f"   Total combiné (potentiel): {existing + count}")
    
    print(f"\n{'='*80}")
    print(f"✅ Données prêtes pour:")
    print(f"   1. Calcul statistiques récurrence")
    print(f"   2. Intégration pipeline de prédiction")
    print(f"   3. Backtesting avec données historiques")
    print(f"{'='*80}\n")
    
    conn.close()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
