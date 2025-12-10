#!/usr/bin/env python3
"""
Multi-League Data Importer

Importe les données scrappées de SoccerStats dans predictions.db
Supporte multiple ligues (Ligue 1, Premier, La Liga, Serie A, Bundesliga)

Le système crée/gère une table générique pour tous les matchs historiques
avec colonne 'league' pour identifier la source
"""

import json
import sqlite3
from pathlib import Path
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiLeagueImporter:
    """Import scraped data from multiple leagues into predictions.db"""
    
    def __init__(self, db_path: str = "data/predictions.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def ensure_tables(self):
        """Create necessary tables if they don't exist"""
        
        # Table pour données scrappées multi-ligues
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS soccerstats_scraped_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league TEXT NOT NULL,
                team TEXT NOT NULL,
                opponent TEXT NOT NULL,
                date TEXT,
                score TEXT,
                goals_for INTEGER,
                goals_against INTEGER,
                is_home BOOLEAN,
                result TEXT,
                goal_times TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table pour données intégrées (fusion SoccerStats + existant)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrated_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                date TEXT,
                home_goals INTEGER,
                away_goals INTEGER,
                goal_times_home TEXT,
                goal_times_away TEXT,
                source TEXT,
                season TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def import_league(self, league_data: Dict, league_id: str):
        """
        Import data for a specific league
        
        Args:
            league_data: Dict with structure {'league': 'Name', 'teams': {...}}
            league_id: league identifier (france, england, etc.)
        """
        league_name = league_data.get('league', 'Unknown')
        teams = league_data.get('teams', {})
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📥 Importing {league_name}")
        logger.info(f"{'='*80}")
        
        total_inserted = 0
        
        for team_name, team_data in teams.items():
            matches = team_data.get('matches', [])
            
            for match in matches:
                try:
                    self.cursor.execute("""
                        INSERT INTO soccerstats_scraped_matches 
                        (league, team, opponent, date, score, goals_for, goals_against, 
                         is_home, result, goal_times)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        league_id,
                        team_name,
                        match.get('opponent', ''),
                        match.get('date', ''),
                        match.get('score', ''),
                        match.get('goals_for', 0),
                        match.get('goals_against', 0),
                        int(match.get('is_home', False)),
                        match.get('result', ''),
                        ','.join(match.get('goal_times', []))
                    ))
                    total_inserted += 1
                except Exception as e:
                    logger.error(f"Error inserting match for {team_name}: {e}")
        
        self.conn.commit()
        logger.info(f"✅ {total_inserted} matches inserted for {league_name}")
        return total_inserted
    
    def import_from_json(self, json_path: str):
        """Import data from multi-league JSON file"""
        
        if not Path(json_path).exists():
            logger.error(f"File not found: {json_path}")
            return False
        
        logger.info(f"Loading data from {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.ensure_tables()
        
        total_all = 0
        
        # Handle both formats: dict of leagues or single league
        if 'league' in data and 'teams' in data:
            # Single league format
            league_id = data.get('league_id', 'unknown')
            total_all = self.import_league(data, league_id)
        else:
            # Multi-league format
            for league_id, league_data in data.items():
                total = self.import_league(league_data, league_id)
                total_all += total
        
        logger.info(f"\n✅ Total: {total_all} matches imported")
        return True
    
    def print_summary(self):
        """Print summary statistics"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 IMPORT SUMMARY")
        logger.info(f"{'='*80}\n")
        
        # Count by league
        self.cursor.execute("""
            SELECT league, COUNT(*) as count, COUNT(DISTINCT team) as teams
            FROM soccerstats_scraped_matches
            GROUP BY league
            ORDER BY count DESC
        """)
        
        results = self.cursor.fetchall()
        total_matches = 0
        
        for league, count, teams in results:
            logger.info(f"📍 {league}: {count} matches ({teams} teams)")
            total_matches += count
        
        logger.info(f"\n📊 Overall: {total_matches} total matches")
        
        # Sample matches
        logger.info(f"\n🎯 Sample matches:")
        self.cursor.execute("""
            SELECT league, team, opponent, score, result, date
            FROM soccerstats_scraped_matches
            LIMIT 5
        """)
        
        for league, team, opponent, score, result, date in self.cursor.fetchall():
            logger.info(f"  {league:12s} | {team:15s} vs {opponent:15s} | {score:5s} {result} | {date}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-League Data Importer")
    parser.add_argument(
        '--input',
        default='data/soccerstats_multi_league.json',
        help='Input JSON file (output from scraper)'
    )
    parser.add_argument(
        '--db',
        default='data/predictions.db',
        help='Path to predictions.db'
    )
    
    args = parser.parse_args()
    
    importer = MultiLeagueImporter(args.db)
    
    try:
        if importer.import_from_json(args.input):
            importer.print_summary()
    finally:
        importer.close()


if __name__ == "__main__":
    main()
