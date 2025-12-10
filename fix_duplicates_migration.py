#!/usr/bin/env python3
"""
Script de migration pour ajouter contrainte UNIQUE sur match_id
et nettoyer les doublons existants
"""

import sqlite3
from datetime import datetime

DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

def clean_duplicates():
    """Nettoyer les doublons existants en gardant le plus récent"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔍 Recherche des doublons...")
    
    # Trouver les match_id en double
    cursor.execute('''
        SELECT match_id, COUNT(*) as count 
        FROM soccerstats_scraped_matches 
        WHERE match_id IS NOT NULL
        GROUP BY match_id 
        HAVING count > 1
        ORDER BY count DESC
    ''')
    
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("✅ Aucun doublon trouvé !")
        conn.close()
        return 0
    
    print(f"⚠️  {len(duplicates)} match_id en double trouvés")
    print(f"   Total de lignes dupliquées : {sum(count - 1 for _, count in duplicates)}")
    
    # Pour chaque match_id en double, garder le plus récent
    deleted = 0
    for match_id, count in duplicates:
        # Garder uniquement l'ID le plus récent (plus grand = plus récent)
        cursor.execute('''
            DELETE FROM soccerstats_scraped_matches 
            WHERE match_id = ? 
            AND id NOT IN (
                SELECT MAX(id) 
                FROM soccerstats_scraped_matches 
                WHERE match_id = ?
            )
        ''', (match_id, match_id))
        deleted += cursor.rowcount
    
    conn.commit()
    print(f"🗑️  {deleted} doublons supprimés")
    
    conn.close()
    return deleted

def add_unique_constraint():
    """Ajouter contrainte UNIQUE sur match_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n🔧 Ajout de la contrainte UNIQUE sur match_id...")
    
    # SQLite ne permet pas ALTER TABLE ADD CONSTRAINT
    # On doit recréer la table
    
    # 1. Créer nouvelle table avec UNIQUE
    cursor.execute('''
        CREATE TABLE soccerstats_scraped_matches_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            league TEXT NOT NULL,
            league_display_name TEXT,
            team TEXT NOT NULL,
            opponent TEXT NOT NULL,
            date TEXT,
            is_home INTEGER,
            score TEXT,
            goals_for INTEGER,
            goals_against INTEGER,
            goal_times TEXT,
            result TEXT,
            match_url TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            match_id TEXT UNIQUE,  -- CONTRAINTE UNIQUE AJOUTÉE
            goal_times_conceded TEXT
        )
    ''')
    
    # 2. Copier les données
    cursor.execute('''
        INSERT INTO soccerstats_scraped_matches_new 
        SELECT * FROM soccerstats_scraped_matches
    ''')
    
    # 3. Supprimer ancienne table
    cursor.execute('DROP TABLE soccerstats_scraped_matches')
    
    # 4. Renommer nouvelle table
    cursor.execute('ALTER TABLE soccerstats_scraped_matches_new RENAME TO soccerstats_scraped_matches')
    
    # 5. Recréer les index
    cursor.execute('CREATE INDEX idx_country_league ON soccerstats_scraped_matches(country, league)')
    cursor.execute('CREATE INDEX idx_team_context ON soccerstats_scraped_matches(team, is_home)')
    cursor.execute('CREATE INDEX idx_match_id ON soccerstats_scraped_matches(match_id)')
    
    conn.commit()
    conn.close()
    
    print("✅ Contrainte UNIQUE ajoutée sur match_id")

def verify_constraint():
    """Vérifier que la contrainte a bien été ajoutée"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupérer le schéma
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='soccerstats_scraped_matches'")
    schema = cursor.fetchone()[0]
    
    conn.close()
    
    if 'UNIQUE' in schema and 'match_id' in schema:
        print("\n✅ Vérification : Contrainte UNIQUE active sur match_id")
        return True
    else:
        print("\n❌ Vérification : Contrainte UNIQUE non trouvée !")
        return False

def show_stats():
    """Afficher les statistiques de la table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM soccerstats_scraped_matches')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT match_id) FROM soccerstats_scraped_matches WHERE match_id IS NOT NULL')
    unique_matches = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT team) FROM soccerstats_scraped_matches')
    teams = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT league) FROM soccerstats_scraped_matches')
    leagues = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n📊 Statistiques de la base de données :")
    print(f"   • Total de lignes : {total}")
    print(f"   • Matches uniques : {unique_matches}")
    print(f"   • Équipes : {teams}")
    print(f"   • Ligues : {leagues}")

if __name__ == "__main__":
    print("="*80)
    print("🔧 MIGRATION : Ajout contrainte UNIQUE + Nettoyage doublons")
    print("="*80)
    
    # Backup recommandé
    print("\n⚠️  RECOMMANDÉ : Faire un backup avant migration")
    print(f"   cp {DB_PATH} {DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    response = input("\nContinuer la migration ? (y/n) : ")
    if response.lower() != 'y':
        print("❌ Migration annulée")
        exit(0)
    
    # 1. Nettoyer les doublons
    deleted = clean_duplicates()
    
    # 2. Ajouter contrainte UNIQUE
    add_unique_constraint()
    
    # 3. Vérifier
    verify_constraint()
    
    # 4. Stats finales
    show_stats()
    
    print("\n" + "="*80)
    print("✅ MIGRATION TERMINÉE AVEC SUCCÈS !")
    print("="*80)
    print("\n💡 Maintenant, les scrapers automatiques ignoreront les doublons")
    print("   lors des scraping hebdomadaires.")
