"""
SoccerStats Historical Scraper - CORRIGÉ pour stats par 10 min

Ce scraper extrait DIRECTEMENT les stats par 10 minutes depuis SoccerStats :
- Goals scored / conceded par intervalle de 10min
- Format: "2-1" = 2 marqués, 1 encaissé
- Pas de conversion nécessaire !
"""
import re
from typing import Dict, List, Optional, Tuple
import pandas as pd
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.base_scraper import BaseScraper
from utils.config_loader import get_config
from utils.logger import get_logger


class SoccerStatsHistoricalScraper(BaseScraper):
    """Scraper pour les statistiques historiques par 10 min"""
    
    # Intervalles de 10 minutes
    INTERVALS_10MIN = ['0-10', '11-20', '21-30', '31-40', '41-50', 
                       '51-60', '61-70', '71-80', '81-90']
    
    def __init__(self):
        """Initialise le scraper historique"""
        super().__init__()
        self.logger.info("SoccerStatsHistoricalScraper initialized (10min version)")
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse le HTML avec BeautifulSoup (html.parser, pas lxml)"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def scrape_timing_stats(self, league_code: str) -> Optional[pd.DataFrame]:
        """
        Scrape les statistiques de timing pour une ligue (stats par 10min)
        
        Args:
            league_code: Code de la ligue (ex: "england")
            
        Returns:
            DataFrame avec stats par équipe ou None si erreur
        """
        self.logger.info(f"Scraping 10-min timing stats for league: {league_code}")
        
        # Construire l'URL
        url = f"https://www.soccerstats.com/timing.asp?league={league_code}"
        
        try:
            # Récupérer la page
            response = self.fetch_page(url)
            
            if not self.validate_response(response):
                self.logger.error(f"Invalid response for {league_code}")
                return None
            
            # Parser le HTML
            soup = self.parse_html(response.text)
            
            # Extraire les stats
            stats_df = self._extract_timing_table_10min(soup, league_code)
            
            if stats_df is not None and not stats_df.empty:
                self.logger.success(f"Successfully scraped {len(stats_df)} teams from {league_code}")
                return stats_df
            else:
                self.logger.warning(f"No data found for {league_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error scraping {league_code}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _extract_timing_table_10min(self, soup: BeautifulSoup, league_code: str) -> Optional[pd.DataFrame]:
        """
        Extrait la table de timing par 10min depuis le HTML
        
        Args:
            soup: BeautifulSoup object
            league_code: Code de la ligue
            
        Returns:
            DataFrame avec les stats ou None
        """
        # Méthode 1: Chercher la table avec width="99%" et cellspacing="1"
        table = soup.find('table', {'width': '99%', 'cellspacing': '1'})
        
        # Méthode 2: Si pas trouvé, chercher n'importe quelle table avec "Overall" dans le header
        if not table:
            self.logger.debug("Method 1 failed, trying method 2...")
            tables = soup.find_all('table')
            for t in tables:
                # Chercher "Overall" dans la première ligne
                first_row = t.find('tr')
                if first_row and 'Overall' in first_row.get_text():
                    table = t
                    self.logger.debug("Found table with 'Overall' header")
                    break
        
        # Méthode 3: Chercher une table qui contient "0-10" dans l'en-tête
        if not table:
            self.logger.debug("Method 2 failed, trying method 3...")
            tables = soup.find_all('table')
            for t in tables:
                header_text = str(t)[:500]  # Premiers 500 caractères
                if '0-10' in header_text and '11-20' in header_text:
                    table = t
                    self.logger.debug("Found table with time intervals")
                    break
        
        if not table:
            self.logger.warning(f"No timing table found for {league_code}")
            self.logger.debug(f"Total tables in page: {len(soup.find_all('table'))}")
            return None
        
        try:
            # Extraire les lignes
            rows = table.find_all('tr', {'class': 'trow8'})
            
            # Si pas de class="trow8", chercher toutes les lignes avec des <a> (liens équipes)
            if not rows:
                self.logger.debug("No trow8 rows, searching for rows with team links...")
                all_rows = table.find_all('tr')
                rows = [r for r in all_rows if r.find('a', href=lambda h: h and 'teamstats.asp' in h)]
                self.logger.debug(f"Found {len(rows)} rows with team links")
            
            if not rows:
                self.logger.warning(f"No data rows found for {league_code}")
                return None
            
            data = []
            
            for row in rows:
                cols = row.find_all('td')
                
                if len(cols) < 13:  # Team + GP + 9 intervals + 2 halves
                    self.logger.debug(f"Row has only {len(cols)} columns, skipping")
                    continue
                
                # Extraire le nom de l'équipe
                team_link = cols[0].find('a')
                if not team_link:
                    continue
                team_name = team_link.get_text(strip=True)
                
                # Extraire GP (games played)
                gp_text = cols[1].get_text(strip=True)
                try:
                    gp = int(gp_text)
                except:
                    gp = 0
                
                # Extraire les stats par intervalle (format: "2-1")
                row_data = {
                    'team': team_name,
                    'gp': gp
                }
                
                # Intervalles de 10min (colonnes 2 à 10)
                for idx, interval in enumerate(self.INTERVALS_10MIN):
                    cell_text = cols[idx + 2].get_text(strip=True)
                    scored, conceded = self._parse_score_cell(cell_text)
                    
                    row_data[f'{interval}_scored'] = scored
                    row_data[f'{interval}_conceded'] = conceded
                
                # Totaux 1ère et 2ème mi-temps (colonnes 12 et 13)
                first_half_text = cols[12].get_text(strip=True)
                second_half_text = cols[13].get_text(strip=True)
                
                first_scored, first_conceded = self._parse_score_cell(first_half_text)
                second_scored, second_conceded = self._parse_score_cell(second_half_text)
                
                row_data['1st_half_scored'] = first_scored
                row_data['1st_half_conceded'] = first_conceded
                row_data['2nd_half_scored'] = second_scored
                row_data['2nd_half_conceded'] = second_conceded
                
                data.append(row_data)
                self.logger.debug(f"Extracted: {team_name}")
            
            if not data:
                self.logger.warning(f"No valid data extracted for {league_code}")
                return None
            
            df = pd.DataFrame(data)
            
            self.logger.debug(f"Extracted {len(df)} teams with {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error parsing table: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _parse_score_cell(self, cell_text: str) -> Tuple[int, int]:
        """
        Parse une cellule de score (format: "2-1")
        
        Args:
            cell_text: Texte de la cellule (ex: "2-1")
        
        Returns:
            Tuple (scored, conceded)
        """
        try:
            # Extraire les chiffres
            match = re.search(r'(\d+)-(\d+)', cell_text)
            if match:
                scored = int(match.group(1))
                conceded = int(match.group(2))
                return scored, conceded
            else:
                return 0, 0
        except:
            return 0, 0
    
    def scrape_team_stats(
        self, 
        team_name: str, 
        league_code: str
    ) -> Optional[Dict[str, Dict]]:
        """
        Scrape les statistiques d'une équipe spécifique
        
        Args:
            team_name: Nom de l'équipe
            league_code: Code de la ligue
            
        Returns:
            Dict avec stats ou None
        """
        self.logger.info(f"Scraping team stats: {team_name} ({league_code})")
        
        # Récupérer toutes les stats de la ligue
        timing_df = self.scrape_timing_stats(league_code)
        
        if timing_df is None:
            return None
        
        # Filtrer pour l'équipe spécifique
        team_data = timing_df[timing_df['team'].str.contains(team_name, case=False, na=False)]
        
        if team_data.empty:
            self.logger.warning(f"Team not found: {team_name}")
            return None
        
        # Convertir en dictionnaire structuré
        return self._dataframe_to_team_dict(team_data.iloc[0])
    
    def _dataframe_to_team_dict(self, row: pd.Series) -> Dict:
        """
        Convertit une ligne DataFrame en dictionnaire structuré
        
        Args:
            row: Ligne du DataFrame
        
        Returns:
            Dict structuré avec stats par intervalle
        """
        team_stats = {
            'team': row['team'],
            'gp': row['gp'],
            'goals_by_interval': {}
        }
        
        # Extraire les stats par intervalle
        for interval in self.INTERVALS_10MIN:
            scored_col = f'{interval}_scored'
            conceded_col = f'{interval}_conceded'
            
            if scored_col in row and conceded_col in row:
                team_stats['goals_by_interval'][interval] = {
                    'scored': int(row[scored_col]),
                    'conceded': int(row[conceded_col])
                }
        
        # Ajouter totaux par mi-temps
        team_stats['first_half'] = {
            'scored': int(row['1st_half_scored']),
            'conceded': int(row['1st_half_conceded'])
        }
        
        team_stats['second_half'] = {
            'scored': int(row['2nd_half_scored']),
            'conceded': int(row['2nd_half_conceded'])
        }
        
        return team_stats
    
    def build_team_profile(
        self,
        team_name: str,
        league_code: str
    ) -> Optional[Dict]:
        """
        Construit le profil complet d'une équipe
        
        Args:
            team_name: Nom de l'équipe
            league_code: Code de la ligue
            
        Returns:
            Dict avec profil complet ou None
        """
        self.logger.info(f"Building profile for {team_name}")
        
        # Récupérer les stats
        stats = self.scrape_team_stats(team_name, league_code)
        
        if not stats:
            return None
        
        # Retourner le profil (déjà au bon format !)
        profile = {
            'team': stats['team'],
            'league': league_code,
            'gp': stats['gp'],
            'intervals_10min': stats['goals_by_interval'],
            'first_half': stats['first_half'],
            'second_half': stats['second_half']
        }
        
        return profile
    
    def scrape(self, *args, **kwargs):
        """Implémentation de la méthode abstraite"""
        if "league_code" in kwargs:
            return self.scrape_timing_stats(kwargs["league_code"])
        return None


# Test du scraper
if __name__ == "__main__":
    from utils.logger import setup_logger
    
    # Setup logger
    log = setup_logger(level="DEBUG")
    
    print("=" * 60)
    print("TEST SOCCERSTATS HISTORICAL SCRAPER (10MIN VERSION)")
    print("=" * 60)
    print()
    
    # Créer le scraper
    scraper = SoccerStatsHistoricalScraper()
    
    # Test 1: Scraper timing stats pour Premier League
    print("📊 Test 1: Scraping Premier League 10-min stats...")
    df = scraper.scrape_timing_stats("england")
    
    if df is not None:
        print(f"✅ Success! Retrieved {len(df)} teams")
        print(f"Columns: {df.columns.tolist()}")
        print(f"\nFirst team (Arsenal):")
        if not df.empty:
            arsenal = df[df['team'] == 'Arsenal']
            if not arsenal.empty:
                print(arsenal.iloc[0].to_dict())
    else:
        print("❌ Failed to retrieve data")
    
    print("\n" + "=" * 60)
    
    # Test 2: Scraper stats d'une équipe spécifique
    print("\n📊 Test 2: Arsenal team stats...")
    team_stats = scraper.scrape_team_stats("Arsenal", "england")
    
    if team_stats:
        print(f"✅ Team: {team_stats['team']}")
        print(f"   Games played: {team_stats['gp']}")
        print(f"   First half: {team_stats['first_half']['scored']}-{team_stats['first_half']['conceded']}")
        print(f"   Second half: {team_stats['second_half']['scored']}-{team_stats['second_half']['conceded']}")
        
        print(f"\n   Goals by interval:")
        for interval, data in team_stats['goals_by_interval'].items():
            print(f"   {interval}: {data['scored']}-{data['conceded']}")
    else:
        print("❌ Failed")
    
    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    
    # Cleanup
    scraper.cleanup()
