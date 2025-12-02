"""
SoccerStats Historical Scraper - Version Home/Away/Overall
Extrait les statistiques par intervalles de 10 minutes pour les 3 contextes
"""
from typing import Optional, Dict, List
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from pathlib import Path
import sys
import time

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger


class SoccerStatsHistoricalScraper:
    """Scraper pour statistiques historiques avec support Home/Away/Overall"""
    
    def __init__(self):
        self.logger = get_logger()
        self.base_url = "https://www.soccerstats.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.logger.info("SoccerStatsHistoricalScraper initialized (Home/Away version)")
    
    def _build_url(self, league_code: str, page_type: str = 'timing') -> str:
        """Construit l'URL pour une ligue"""
        return f"{self.base_url}/{page_type}.asp?league={league_code}"
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Récupère le contenu HTML d'une page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_html(self, html_content: str) -> Optional[BeautifulSoup]:
        """Parse le contenu HTML"""
        try:
            return BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}")
            return None
    
    def _extract_timing_table_for_venue(
        self, 
        soup: BeautifulSoup, 
        league_code: str, 
        venue: str
    ) -> Optional[pd.DataFrame]:
        """
        Extrait la table de timing pour un venue spécifique (overall/home/away)
        
        Args:
            soup: BeautifulSoup object
            league_code: Code de la ligue
            venue: 'overall', 'home', ou 'away'
        """
        try:
            # Mapping des venues vers les IDs des onglets
            league_prefix_map = {
                'england': 'eng',
                'spain': 'esp',
                'france': 'fra',
                'italy': 'ita',
                'germany': 'ger'
            }
            
            tab_suffix_map = {
                'overall': '_1',
                'home': '_2',
                'away': '_3'
            }
            
            prefix = league_prefix_map.get(league_code, league_code[:3])
            tab_id = f"{prefix}_GTS10{tab_suffix_map[venue]}"
            
            # Chercher l'input radio correspondant
            tab_input = soup.find('input', {'id': tab_id})
            
            if not tab_input:
                self.logger.warning(f"Tab {tab_id} not found for {venue}")
                return None
            
            # Trouver le div.tab suivant
            current = tab_input.find_next_sibling()
            tab_div = None
            
            while current:
                if current.name == 'div' and 'tab' in current.get('class', []):
                    tab_div = current
                    break
                current = current.find_next_sibling()
            
            if not tab_div:
                self.logger.warning(f"Tab div not found for {venue}")
                return None
            
            # Chercher la table dans ce div
            table = tab_div.find('table', {'cellspacing': '1'})
            
            if not table:
                self.logger.warning(f"Table not found in {venue} tab")
                return None
            
            # Extraire les données de la table
            rows = table.find_all('tr', {'class': 'trow8'})
            
            if not rows:
                self.logger.warning(f"No data rows found for {venue}")
                return None
            
            data = []
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) < 13:
                    continue
                
                # Extraire le nom de l'équipe
                team_link = cells[0].find('a')
                if not team_link:
                    continue
                
                team_name = team_link.get_text(strip=True)
                
                # Extraire GP
                gp = cells[1].get_text(strip=True)
                
                # Extraire les scores par intervalle (colonnes 2-10)
                intervals = {}
                interval_names = ['0-10', '11-20', '21-30', '31-40', '41-50', 
                                 '51-60', '61-70', '71-80', '81-90']
                
                for i, interval_name in enumerate(interval_names):
                    cell_idx = i + 2
                    if cell_idx < len(cells):
                        score_text = cells[cell_idx].get_text(strip=True)
                        match = re.match(r'(\d+)-(\d+)', score_text)
                        if match:
                            intervals[interval_name] = {
                                'scored': int(match.group(1)),
                                'conceded': int(match.group(2))
                            }
                
                # Extraire 1st H et 2nd H (colonnes 12 et 13)
                first_half_text = cells[12].get_text(strip=True) if len(cells) > 12 else "0-0"
                second_half_text = cells[13].get_text(strip=True) if len(cells) > 13 else "0-0"
                
                fh_match = re.match(r'(\d+)-(\d+)', first_half_text)
                sh_match = re.match(r'(\d+)-(\d+)', second_half_text)
                
                first_half = {
                    'scored': int(fh_match.group(1)) if fh_match else 0,
                    'conceded': int(fh_match.group(2)) if fh_match else 0
                }
                
                second_half = {
                    'scored': int(sh_match.group(1)) if sh_match else 0,
                    'conceded': int(sh_match.group(2)) if sh_match else 0
                }
                
                data.append({
                    'team': team_name,
                    'gp': gp,
                    'goals_by_interval': intervals,
                    'first_half': first_half,
                    'second_half': second_half
                })
            
            if not data:
                return None
            
            df = pd.DataFrame(data)
            return df
            
        except Exception as e:
            self.logger.error(f"Error extracting {venue} table: {e}")
            return None
    
    def scrape_timing_stats_all_venues(self, league_code: str) -> Dict[str, pd.DataFrame]:
        """
        Scrape les stats de timing pour les 3 venues (Overall, Home, Away)
        
        Args:
            league_code: Code de la ligue (ex: 'england')
            
        Returns:
            Dict avec les 3 DataFrames: {'overall': df, 'home': df, 'away': df}
        """
        self.logger.info(f"Scraping timing stats (all venues) for: {league_code}")
        
        url = self._build_url(league_code, 'timing')
        html_content = self.fetch_page(url)
        
        if not html_content:
            return {}
        
        soup = self.parse_html(html_content)
        if not soup:
            return {}
        
        results = {}
        
        for venue in ['overall', 'home', 'away']:
            df = self._extract_timing_table_for_venue(soup, league_code, venue)
            if df is not None and not df.empty:
                results[venue] = df
                self.logger.success(f"✓ {venue.capitalize()}: {len(df)} teams")
            else:
                self.logger.warning(f"✗ {venue.capitalize()}: No data")
                results[venue] = pd.DataFrame()
        
        time.sleep(1)  # Rate limiting
        
        return results
    
    def scrape_team_stats(self, team_name: str, league_code: str) -> Optional[Dict]:
        """
        Scrape les stats complètes d'une équipe (Overall + Home + Away)
        
        Args:
            team_name: Nom de l'équipe
            league_code: Code de la ligue
            
        Returns:
            Dict avec les stats pour les 3 venues
        """
        self.logger.info(f"Scraping team stats: {team_name} ({league_code})")
        
        # Récupérer les stats pour les 3 venues
        all_venues = self.scrape_timing_stats_all_venues(league_code)
        
        if not all_venues:
            self.logger.warning(f"No data retrieved for {league_code}")
            return None
        
        # Construire le profil complet de l'équipe
        team_profile = {
            'team': team_name,
            'league': league_code
        }
        
        for venue, df in all_venues.items():
            if df.empty:
                continue
            
            # Chercher l'équipe dans le DataFrame
            team_row = df[df['team'] == team_name]
            
            if team_row.empty:
                self.logger.warning(f"Team '{team_name}' not found in {venue} data")
                continue
            
            # Extraire les données
            row = team_row.iloc[0]
            
            team_profile[venue] = {
                'gp': row['gp'],
                'goals_by_interval': row['goals_by_interval'],
                'first_half': row['first_half'],
                'second_half': row['second_half']
            }
        
        # Vérifier qu'on a au moins une venue
        if not any(k in team_profile for k in ['overall', 'home', 'away']):
            self.logger.warning(f"No venue data found for {team_name}")
            return None
        
        self.logger.success(f"✓ Team profile complete for {team_name}")
        return team_profile
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.session.close()
        self.logger.info("Scraper cleaned up")


def test_scraper():
    """Test du scraper"""
    print("\n" + "="*60)
    print("🧪 TEST DU SCRAPER HOME/AWAY")
    print("="*60 + "\n")
    
    scraper = SoccerStatsHistoricalScraper()
    
    # Test avec Manchester City
    print("📊 Test avec Manchester City (England)...\n")
    
    team_stats = scraper.scrape_team_stats("Manchester City", "england")
    
    if team_stats:
        print("\n✅ DONNÉES RÉCUPÉRÉES:\n")
        
        for venue in ['overall', 'home', 'away']:
            if venue in team_stats:
                print(f"\n{'='*50}")
                print(f"📍 {venue.upper()}")
                print(f"{'='*50}")
                
                data = team_stats[venue]
                print(f"GP: {data['gp']}")
                
                # Afficher l'intervalle 31-40
                if '31-40' in data['goals_by_interval']:
                    interval = data['goals_by_interval']['31-40']
                    print(f"\n31-40 min:")
                    print(f"  Scored: {interval['scored']}")
                    print(f"  Conceded: {interval['conceded']}")
                
                # Afficher 1st/2nd half
                print(f"\n1st Half: {data['first_half']['scored']}-{data['first_half']['conceded']}")
                print(f"2nd Half: {data['second_half']['scored']}-{data['second_half']['conceded']}")
    else:
        print("\n❌ Erreur lors de la récupération")
    
    scraper.cleanup()
    
    print("\n" + "="*60)
    print("✅ TEST TERMINÉ")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_scraper()
