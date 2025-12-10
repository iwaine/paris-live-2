#!/usr/bin/env python3
"""
Script de vérification des doublons dans la base de données
"""

import sqlite3

DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

def check_duplicates():
    """Vérifier les doublons existants"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("="*80)
    print("🔍 ANALYSE DES DOUBLONS")
    print("="*80)
    
    # Total de lignes
    cursor.execute('SELECT COUNT(*) FROM soccerstats_scraped_matches')
    total_rows = cursor.fetchone()[0]
    
    # Matches uniques
    cursor.execute('SELECT COUNT(DISTINCT match_id) FROM soccerstats_scraped_matches WHERE match_id IS NOT NULL')
    unique_matches = cursor.fetchone()[0]
    
    # Matches avec match_id NULL
    cursor.execute('SELECT COUNT(*) FROM soccerstats_scraped_matches WHERE match_id IS NULL')
    null_matches = cursor.fetchone()[0]
    
    print(f"\n📊 Statistiques globales :")
    print(f"   • Total de lignes : {total_rows}")
    print(f"   • Matches uniques (match_id) : {unique_matches}")
    print(f"   • Matches sans match_id : {null_matches}")
    print(f"   • Doublons potentiels : {total_rows - unique_matches - null_matches}")
    
    # Doublons détaillés
    cursor.execute('''
        SELECT match_id, COUNT(*) as count, 
               GROUP_CONCAT(team || ' vs ' || opponent || ' (' || date || ')') as matches
        FROM soccerstats_scraped_matches 
        WHERE match_id IS NOT NULL
        GROUP BY match_id 
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 20
    ''')
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\n⚠️  Top 20 match_id en double :")
        print(f"{'Match ID':<40} {'Count':>8} {'Exemple'}")
        print("-"*80)
        for match_id, count, example in duplicates:
            example_short = example.split(',')[0] if example else 'N/A'
            print(f"{match_id:<40} {count:>8} {example_short[:50]}")
        
        total_dup = sum(count - 1 for _, count, _ in duplicates)
        print(f"\n   Total de doublons à supprimer : {total_dup}")
    else:
        print("\n✅ Aucun doublon trouvé !")
    
    # Vérifier la contrainte UNIQUE
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='soccerstats_scraped_matches'")
    schema = cursor.fetchone()[0]
    
    print("\n🔧 Contrainte UNIQUE :")
    if 'UNIQUE' in schema and 'match_id' in schema:
        print("   ✅ ACTIVE - Les nouveaux doublons seront automatiquement rejetés")
    else:
        print("   ❌ ABSENTE - Les doublons peuvent être insérés !")
        print("   💡 Exécutez fix_duplicates_migration.py pour corriger")
    
    # Stats par ligue
    print("\n📊 Matches par ligue :")
    cursor.execute('''
        SELECT league_display_name, COUNT(*) as count,
               COUNT(DISTINCT match_id) as unique_count
        FROM soccerstats_scraped_matches 
        GROUP BY league_display_name
        ORDER BY count DESC
    ''')
    
    leagues = cursor.fetchall()
    print(f"{'Ligue':<30} {'Total':>8} {'Uniques':>10} {'Doublons':>10}")
    print("-"*80)
    for league, count, unique in leagues:
        league_name = league or 'N/A'
        duplicates_count = count - unique
        print(f"{league_name:<30} {count:>8} {unique:>10} {duplicates_count:>10}")
    
    conn.close()
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_duplicates()
