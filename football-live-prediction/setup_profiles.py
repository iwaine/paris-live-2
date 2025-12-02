"""
Setup Profiles - Génération des profils d'équipes

Ce script :
1. Scrape les stats historiques pour les équipes configurées
2. Analyse les patterns
3. Génère et sauvegarde les profils
4. Exporte en JSON et Excel
"""
import yaml
import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from loguru import logger

from scrapers.recent_form_complete import RecentFormCompleteScraper
from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper


def load_config() -> Dict:
    """Charge la configuration"""
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)


def get_enabled_leagues(config: Dict) -> List[Dict]:
    """Retourne les ligues activées"""
    return [league for league in config.get('leagues', []) if league.get('enabled', False)]


def get_team_id(config: Dict, team_name: str) -> str:
    """Récupère le team_id depuis le config"""
    teams = config.get('teams', {})
    team_info = teams.get(team_name, {})
    return team_info.get('id', None)


def scrape_and_build_profiles():
    """Fonction principale - Scrape et génère les profils"""
    print("="*80)
    print("🔧 GÉNÉRATION DES PROFILS D'ÉQUIPES")
    print("="*80)
    
    config = load_config()
    leagues = get_enabled_leagues(config)
    
    print(f"\n📋 {len(leagues)} ligues activées")
    
    # Initialiser les scrapers
    historical_scraper = SoccerStatsHistoricalScraper()
    form_scraper = RecentFormCompleteScraper()
    
    # Créer le dossier de sortie
    output_dir = Path('data/team_profiles')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🔄 Scraping en cours...\n")
    
    all_profiles = []
    
    for league in leagues:
        league_name = league['name']
        league_url = league['url']
        
        # Extraire le code de ligue
        import re
        match = re.search(r'league=([^&]+)', league_url)
        league_code = match.group(1) if match else 'unknown'
        
        print(f"📊 {league_name}...")
        
        try:
            # 1. Scraper les stats historiques
            teams_data = historical_scraper.scrape_league(league_url)
            
            for team_data in teams_data:
                team_name = team_data['team']
                
                # 2. Récupérer le team_id
                team_id = get_team_id(config, team_name)
                
                # 3. Scraper la forme récente pour HOME et AWAY
                print(f"  • {team_name}...", end=" ")
                
                try:
                    # Home
                    recent_home = form_scraper.scrape_team_recent_matches(
                        team_name, league_code, 'home', num_matches=4, team_id=team_id
                    )
                    
                    # Away
                    recent_away = form_scraper.scrape_team_recent_matches(
                        team_name, league_code, 'away', num_matches=4, team_id=team_id
                    )
                    
                    # 4. Intégrer dans le profil
                    team_data['home']['recent_form_by_interval'] = aggregate_recent_form(recent_home)
                    team_data['away']['recent_form_by_interval'] = aggregate_recent_form(recent_away)
                    
                    print(f"✅ ({len(recent_home)}H + {len(recent_away)}A)")
                    
                except Exception as e:
                    logger.warning(f"Forme récente indisponible pour {team_name}: {e}")
                    print(f"⚠️")
                
                all_profiles.append(team_data)
                
                # Sauvegarder le profil individuel
                save_profile(team_data, output_dir)
        
        except Exception as e:
            logger.error(f"Erreur pour {league_name}: {e}")
            continue
    
    print(f"\n✅ {len(all_profiles)} profils générés")
    print(f"📁 Dossier: {output_dir}")


def aggregate_recent_form(matches: List[Dict]) -> Dict:
    """Agrège les matchs récents par intervalle"""
    if not matches:
        return {}
    
    aggregated = {
        '0-15': {'scored': 0, 'conceded': 0, 'matches': 0},
        '16-30': {'scored': 0, 'conceded': 0, 'matches': 0},
        '31-45': {'scored': 0, 'conceded': 0, 'matches': 0},
        '46-60': {'scored': 0, 'conceded': 0, 'matches': 0},
        '61-75': {'scored': 0, 'conceded': 0, 'matches': 0},
        '76-90': {'scored': 0, 'conceded': 0, 'matches': 0}
    }
    
    for match in matches:
        for interval in aggregated.keys():
            scored = match['scored_by_interval'].get(interval, 0)
            conceded = match['conceded_by_interval'].get(interval, 0)
            
            aggregated[interval]['scored'] += scored
            aggregated[interval]['conceded'] += conceded
            aggregated[interval]['matches'] = len(matches)
    
    return aggregated


def save_profile(profile: Dict, output_dir: Path):
    """Sauvegarde un profil en JSON"""
    team_name = profile['team'].replace(' ', '_').replace('.', '').lower()
    filename = f"{team_name}_profile.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    scrape_and_build_profiles()
