#!/usr/bin/env python3
"""
Scraper rapide pour Bulgarie en utilisant le système existant
"""

import sys
import yaml
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "football-live-prediction"))

from scrape_config_leagues import ConfigDrivenScraper
from utils.database_manager import DatabaseManager

def scrape_bulgaria():
    """Scrape uniquement la Bulgarie depuis config.yaml"""
    
    print("\n" + "=" * 80)
    print("🇧🇬 SCRAPING BULGARIA - Utilisant config.yaml")
    print("=" * 80)
    
    # Charger config
    config_path = "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Trouver la Bulgarie
    bulgaria_config = None
    for league in config.get('leagues', []):
        if 'Bulgaria' in league['name'] or 'bulgaria' in league['url']:
            bulgaria_config = league
            break
    
    if not bulgaria_config:
        print("❌ Bulgaria non trouvée dans config.yaml")
        return
    
    print(f"\n✅ Trouvé: {bulgaria_config['name']}")
    print(f"   URL: {bulgaria_config['url']}")
    
    # Utiliser le scraper existant
    scraper = ConfigDrivenScraper(config_path)
    scraper.load_config()
    
    # Scraper la Bulgarie
    league_id = scraper.extract_league_id_from_url(bulgaria_config['url'])
    print(f"\n🔄 Scraping league_id: {league_id}\n")
    
    data = scraper.scrape_league(bulgaria_config['name'], league_id)
    
    if not data or not data.get('teams'):
        print("\n❌ Aucune donnée scrapée")
        return
    
    print(f"\n✅ Données scrapées:")
    print(f"   Équipes: {len(data['teams'])}")
    
    total_matches = sum(len(team_data.get('matches', [])) for team_data in data['teams'].values())
    print(f"   Matches: {total_matches}")
    
    # Insérer dans la base de données
    db = DatabaseManager(db_path="data/predictions.db")
    
    inserted_matches = 0
    teams_set = set()
    
    for team_name, team_data in data['teams'].items():
        teams_set.add(team_name)
        
        for match in team_data.get('matches', []):
            try:
                match_id = db.insert_match({
                    'home_team': match.get('home_team'),
                    'away_team': match.get('away_team'),
                    'league': league_id,
                    'match_date': match.get('date'),
                    'final_score': match.get('score'),
                    'home_goals': match.get('home_goals'),
                    'away_goals': match.get('away_goals'),
                })
                
                if match_id:
                    inserted_matches += 1
            except Exception as e:
                # Ignorer doublons
                pass
    
    print(f"\n📊 INSERTION BASE DE DONNÉES:")
    print(f"   Matches insérés: {inserted_matches}")
    print(f"   Équipes uniques: {len(teams_set)}")
    
    print("\n✅ SCRAPING TERMINÉ!")
    print("=" * 80)

if __name__ == "__main__":
    scrape_bulgaria()
