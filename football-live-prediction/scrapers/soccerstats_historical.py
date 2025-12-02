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
                'spain': 'spa',
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
            tab_id = f"{prefix}_GTS{tab_suffix_map[venue]}"  # GTS pour 15min (tid=k)
            
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
                self.self.logger.warning(f"Table not found in {venue} tab")
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
                interval_names = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90']
                
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
        
        url = self._build_url(league_code, 'timing') + '&tid=k'  # 15min intervals
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
                self.self.logger.warning(f"Team '{team_name}' not found in {venue} data")
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
        
        # Scraper forme récente
        self.logger.info(f"Scraping recent form for {team_name}...")
        team_profile['recent_home'] = self.scrape_recent_form(team_name, league_code, venue='home', last_n=4)
        team_profile['recent_away'] = self.scrape_recent_form(team_name, league_code, venue='away', last_n=4)
        
        self.logger.success(f"✓ Team profile complete for {team_name}")
        return team_profile
    
    def scrape_recent_form(self, team_name: str, league_code: str, venue: str = 'home', last_n: int = 5) -> Dict:
        """
        Scrape la forme récente depuis formtable.asp
        
        Args:
            team_name: Nom de l'équipe
            league_code: Code de la ligue  
            venue: 'home' ou 'away'
            last_n: Nombre de matchs (4 ou 8)
        """
        self.logger.info(f"Scraping recent form: {team_name} ({venue}, last {last_n})")
        
        url = f"https://www.soccerstats.com/formtable.asp?league={league_code}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher la section appropriée
            if venue == 'home':
                search_text = f"Last {last_n} (AT HOME)"
            else:
                search_text = f"Last {last_n} (AWAY)"
            
            # Chercher le label avec ce texte (recherche exacte)
            label = None
            for lbl in soup.find_all('label'):
                if search_text in lbl.get_text(strip=True):
                    label = lbl
                    break
            
            if not label:
                self.logger.warning(f"Label '{search_text}' not found")
                return None
            
            # Trouver le tableau associé (généralement juste après ou via l'attribut 'for')
            # Chercher le div parent puis le tableau
            parent_div = label.find_parent('div')
            if parent_div:
                table = parent_div.find('table', {'id': 'btable'})
            else:
                table = label.find_next('table', {'id': 'btable'})
            
            if not table:
                self.logger.warning(f"Table not found after '{section_title}'")
                return None
            
            # Chercher la ligne de l'équipe
            rows = table.find_all('tr', {'class': 'odd'})
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) < 8:
                    continue
                
                # La 2ème colonne contient le nom de l'équipe
                team_cell = cells[1]
                team_link = team_cell.find('a')
                
                if team_link:
                    team_text = team_link.get_text(strip=True)
                else:
                    team_text = team_cell.get_text(strip=True)
                
                # Vérifier si c'est notre équipe
                if team_text == team_name:
                    # Extraire les données
                    gp = int(cells[2].get_text(strip=True))  # Games Played
                    gf = int(cells[6].get_text(strip=True))  # Goals For
                    ga = int(cells[7].get_text(strip=True))  # Goals Against
                    
                    avg_scored = round(gf / gp, 2) if gp > 0 else 0
                    avg_conceded = round(ga / gp, 2) if gp > 0 else 0
                    
                    stats = {
                        'matches_analyzed': gp,
                        'total_scored': gf,
                        'total_conceded': ga,
                        'avg_scored': avg_scored,
                        'avg_conceded': avg_conceded
                    }
                    
                    self.logger.success(f"Recent form: {gp} matches, avg {avg_scored} scored")
                    return stats
            
            self.logger.warning(f"Team '{team_name}' not found in {venue} form table")
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping recent form: {e}")
            return None



    def _convert_df_to_dict_15min(self, df: pd.DataFrame) -> dict:
        """
        Convertit un DataFrame avec intervalles 10min en dict avec intervalles 15min
        """
        if df is None or df.empty:
            return None
        
        # Extraire les données de la première ligne (l'équipe)
        row = df.iloc[0]
        
        # Mapping des intervalles 10min → 15min
        # Règle: prendre 50% des intervalles qui chevauchent
        intervals_15min = {
            '0-15': {
                'scored': row.get('0-15_scored', 0) + row.get('16-30_scored', 0) * 0.5,
                'conceded': row.get('0-15_conceded', 0) + row.get('16-30_conceded', 0) * 0.5
            },
            '16-30': {
                'scored': row.get('16-30_scored', 0) * 0.5 + row.get('31-45_scored', 0),
                'conceded': row.get('16-30_conceded', 0) * 0.5 + row.get('31-45_conceded', 0)
            },
            '31-45': {
                'scored': row.get('46-60_scored', 0) + row.get('61-75_scored', 0) * 0.5,
                'conceded': row.get('46-60_conceded', 0) + row.get('61-75_conceded', 0) * 0.5
            },
            '46-60': {
                'scored': row.get('61-75_scored', 0) * 0.5 + row.get('76-90_scored', 0),
                'conceded': row.get('61-75_conceded', 0) * 0.5 + row.get('76-90_conceded', 0)
            },
            '61-75': {
                'scored': row.get('76-90_scored', 0) + row.get('76-90_scored', 0) * 0.5,
                'conceded': row.get('76-90_conceded', 0) + row.get('76-90_conceded', 0) * 0.5
            },
            '76-90': {
                'scored': row.get('76-90_scored', 0) * 0.5 + row.get('76-90_scored', 0),
                'conceded': row.get('76-90_conceded', 0) * 0.5 + row.get('76-90_conceded', 0)
            }
        }
        
        # Calculer first_half et second_half
        first_half = {
            'scored': sum(intervals_15min[i]['scored'] for i in ['0-15', '16-30', '31-45']),
            'conceded': sum(intervals_15min[i]['conceded'] for i in ['0-15', '16-30', '31-45'])
        }
        
        second_half = {
            'scored': sum(intervals_15min[i]['scored'] for i in ['46-60', '61-75', '76-90']),
            'conceded': sum(intervals_15min[i]['conceded'] for i in ['46-60', '61-75', '76-90'])
        }
        
        return {
            'gp': row.get('gp', 0),
            'goals_by_interval': intervals_15min,
            'first_half': first_half,
            'second_half': second_half
        }


    def convert_10min_to_15min(self, timing_data_10min: pd.DataFrame) -> pd.DataFrame:
        """
        Convertit les données d'intervalles de 10min en intervalles de 15min
        
        Intervalles 10min sur le site:
        1-10, 11-20, 21-30, 31-40, 41-50, 51-60, 61-70, 71-80, 81-90
        
        Nouveaux intervalles 15min:
        0-15, 16-30, 31-45, 46-60, 61-75, 76-90
        """
        if timing_data_10min is None or timing_data_10min.empty:
            return timing_data_10min
        
        # Créer un nouveau DataFrame avec les colonnes nécessaires
        df_15min = timing_data_10min[['team', 'gp']].copy()
        
        # Mapping des intervalles 10min vers 15min
        # Format: {intervalle_15min: [intervalles_10min_à_combiner]}
        interval_mapping = {
            '0-15': ['1-10', '11-20'],       # Prendre 1-10 complet + moitié de 11-20
            '16-30': ['11-20', '21-30'],     # Prendre moitié de 11-20 + 21-30 complet
            '31-45': ['31-40', '41-50'],     # 31-40 complet + moitié de 41-50 (avant HT)
            '46-60': ['41-50', '51-60'],     # Moitié de 41-50 (après HT) + 51-60 complet
            '61-75': ['61-70', '71-80'],     # 61-70 complet + moitié de 71-80
            '76-90': ['71-80', '81-90']      # Moitié de 71-80 + 81-90 complet
        }
        
        # Pour chaque intervalle 15min
        for interval_15, intervals_10 in interval_mapping.items():
            scored_col = f'{interval_15}_scored'
            conceded_col = f'{interval_15}_conceded'
            
            # Initialiser les colonnes
            df_15min[scored_col] = 0.0
            df_15min[conceded_col] = 0.0
            
            # Combiner les données des intervalles 10min
            for interval_10 in intervals_10:
                col_scored = f'{interval_10}_scored'
                col_conceded = f'{interval_10}_conceded'
                
                if col_scored in timing_data_10min.columns:
                    # Si l'intervalle 10min est partagé entre deux 15min
                    if interval_10 in ['11-20', '41-50', '71-80']:
                        # Prendre 50% pour chaque intervalle 15min
                        df_15min[scored_col] += timing_data_10min[col_scored] * 0.5
                        df_15min[conceded_col] += timing_data_10min[col_conceded] * 0.5
                    else:
                        # Prendre 100%
                        df_15min[scored_col] += timing_data_10min[col_scored]
                        df_15min[conceded_col] += timing_data_10min[col_conceded]
        
        # Créer la structure goals_by_interval
        goals_by_interval = {}
        
        for interval in ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90']:
            scored_col = f'{interval}_scored'
            conceded_col = f'{interval}_conceded'
            
            if scored_col in df_15min.columns:
                goals_by_interval[interval] = {
                    'scored': df_15min[scored_col].values[0],
                    'conceded': df_15min[conceded_col].values[0]
                }
        
        # Calculer first_half et second_half
        first_half = {
            'scored': sum(goals_by_interval[i]['scored'] for i in ['0-15', '16-30', '31-45']),
            'conceded': sum(goals_by_interval[i]['conceded'] for i in ['0-15', '16-30', '31-45'])
        }
        
        second_half = {
            'scored': sum(goals_by_interval[i]['scored'] for i in ['46-60', '61-75', '76-90']),
            'conceded': sum(goals_by_interval[i]['conceded'] for i in ['46-60', '61-75', '76-90'])
        }
        
        # Ajouter à df_15min
        df_15min['goals_by_interval'] = [goals_by_interval]
        df_15min['first_half'] = [first_half]
        df_15min['second_half'] = [second_half]
        
        return df_15min


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
