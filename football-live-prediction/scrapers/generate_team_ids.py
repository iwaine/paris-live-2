#!/usr/bin/env python3
"""
Script pour scraper les team_ids de toutes les équipes sur SoccerStats
et générer la configuration complète
"""
import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path

# Ligues principales à scraper
LEAGUES = {
    'england': 'Premier League',
    'spain': 'LaLiga',
    'france': 'Ligue 1',
    'italy': 'Serie A',
    'germany': 'Bundesliga',
    'portugal': 'Liga Portugal',
    'netherlands': 'Eredivisie',
    'belgium': 'Pro League',
    'scotland': 'Premiership',
    'turkey': 'Super Lig',
    'greece': 'Super League',
    'austria': 'Bundesliga',
    'switzerland': 'Super League',
    'denmark': 'Superligaen',
    'sweden': 'Allsvenskan',
    'norway': 'Eliteserien',
    'usa': 'MLS',
    'mexico': 'Liga MX',
    'argentina': 'Liga Profesional',
    'brazil': 'Serie A',
    'australia': 'A-League',
    'japan': 'J1 League',
    'iran': 'Persian Gulf Pro League',
}

class TeamIDScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.teams_data = {}
    
    def scrape_league(self, league_code: str, league_name: str):
        """Scrape les équipes et leurs IDs pour une ligue"""
        print(f"\n🔄 Scraping {league_name} ({league_code})...")
        
        url = f"https://www.soccerstats.com/latest.asp?league={league_code}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher tous les liens vers les profils d'équipes
            links = soup.find_all('a', href=re.compile(r'teamstats\.asp\?league=' + league_code))
            
            teams = {}
            for link in links:
                href = link.get('href', '')
                team_name = link.get_text(strip=True)
                
                # Extraire le team_id de l'URL
                # Format: teamstats.asp?league=england&stats=u321-manchester-city
                match = re.search(r'stats=(u\d+)', href)
                if match and team_name:
                    team_id = match.group(1)
                    teams[team_name] = {
                        'id': team_id,
                        'league': league_code
                    }
                    print(f"  ✓ {team_name:30s} : {team_id}")
            
            self.teams_data[league_code] = teams
            return len(teams)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return 0
    
    def generate_yaml(self):
        """Génère la configuration YAML"""
        yaml_content = """teams:
"""
        
        total_teams = 0
        for league_code in sorted(self.teams_data.keys()):
            teams = self.teams_data[league_code]
            for team_name in sorted(teams.keys()):
                team_info = teams[team_name]
                yaml_content += f"""  {team_name}:
    id: {team_info['id']}
    league: {team_info['league']}
"""
                total_teams += 1
        
        return yaml_content, total_teams
    
    def save_config(self, output_file: str = None):
        """Sauvegarde la configuration"""
        if not output_file:
            output_file = Path(__file__).parent.parent / 'config' / 'config_teams_updated.yaml'
        
        yaml_content, total_teams = self.generate_yaml()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print(f"\n✅ Configuration générée avec {total_teams} équipes")
        print(f"📁 Sauvegardé dans: {output_file}")
        
        return yaml_content

if __name__ == '__main__':
    scraper = TeamIDScraper()
    
    print("="*70)
    print("🔍 SCRAPER DE TEAM IDs - SoccerStats.com")
    print("="*70)
    
    total_scraped = 0
    for league_code, league_name in LEAGUES.items():
        count = scraper.scrape_league(league_code, league_name)
        total_scraped += count
    
    print("\n" + "="*70)
    print(f"📊 RÉSUMÉ: {total_scraped} équipes scrapées")
    print("="*70)
    
    # Générer et sauvegarder
    scraper.save_config()
    
    # Afficher un aperçu
    yaml_content, _ = scraper.generate_yaml()
    print("\n📄 Aperçu du fichier généré:\n")
    print(yaml_content[:1000])
    print("...")
