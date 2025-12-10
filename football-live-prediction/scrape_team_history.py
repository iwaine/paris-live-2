#!/usr/bin/env python3
"""
Scraper SoccerStats - Historique complet des matchs par équipe
Format: URL teamstats.asp?league=france&stats=u512-lens
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sqlite3
from typing import List, Dict, Any, Optional
import time

class SoccerStatsTeamHistoryScraper:
    """Scrape l'historique complet des matchs par équipe"""
    
    BASE_URL = "https://www.soccerstats.com"
    
    def __init__(self, timeout=15, retry=3):
        self.timeout = timeout
        self.retry = retry
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
    
    def fetch_with_retry(self, url: str) -> Optional[requests.Response]:
        """Récupère l'URL avec retry automatique"""
        for attempt in range(self.retry):
            try:
                print(f"  📥 {url.split('/')[-1][:50]}... (tentative {attempt+1}/{self.retry})")
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                print(f"     ⚠ {str(e)[:60]}")
                if attempt < self.retry - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def extract_team_ids_from_standings(self, standings_url: str) -> Dict[str, str]:
        """
        Extrait tous les team_id (u512-lens, u517-marseille, etc) 
        depuis la page de classement
        """
        print(f"🔍 Extraction des team IDs depuis le classement...\n")
        
        response = self.fetch_with_retry(standings_url)
        if not response:
            print("❌ Impossible de récupérer le classement")
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'btable'})
        
        if not table:
            print("❌ Tableau de classement non trouvé")
            return {}
        
        team_ids = {}
        rows = table.find_all('tr', {'class': 'odd'})
        
        for row in rows:
            try:
                tds = row.find_all('td')
                if len(tds) < 2:
                    continue
                
                # Extraire le lien team
                team_link = tds[1].find('a')
                if not team_link:
                    continue
                
                team_name = team_link.get_text(strip=True)
                href = team_link.get('href', '')
                
                # Extraire team_id: u512-lens
                match = re.search(r'stats=([^&\s"\']+)', href)
                if match:
                    team_id = match.group(1)
                    team_ids[team_name] = team_id
                    print(f"  ✓ {team_name:20s} → {team_id}")
            
            except Exception as e:
                print(f"  ⚠ Erreur: {e}")
        
        print(f"\n✅ {len(team_ids)} team IDs extraits\n")
        return team_ids
    
    def scrape_team_history(self, team_name: str, team_id: str) -> List[Dict[str, Any]]:
        """
        Scrape l'historique complet des matchs pour une équipe
        
        URL: https://www.soccerstats.com/teamstats.asp?league=france&stats=u512-lens
        """
        url = f"{self.BASE_URL}/teamstats.asp?league=france&stats={team_id}"
        
        response = self.fetch_with_retry(url)
        if not response:
            print(f"    ❌ Impossible de récupérer l'historique")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        matches = []
        
        # Chercher le tableau des matchs (peut avoir différents noms)
        # Chercher d'abord par class, sinon par id
        match_tables = soup.find_all('table')
        
        for table in match_tables:
            # Les lignes de matchs ont généralement class="odd" ou "even"
            rows = table.find_all('tr')
            
            for row in rows:
                try:
                    match_data = self.extract_match_from_row(row, team_name)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    # Silencieux pour les lignes qui ne sont pas des matchs
                    pass
        
        return matches
    
    def extract_match_from_row(self, row, home_team: str) -> Optional[Dict[str, Any]]:
        """
        Extrait les données d'un match depuis une ligne du tableau
        
        Format typique SoccerStats:
        | Date | Home | vs | Away | Score | H1 | H2 | ... |
        """
        tds = row.find_all('td')
        
        # Filtre: les lignes de match ont généralement au moins 5 colonnes
        if len(tds) < 5:
            return None
        
        try:
            # Essayer de détecter le format de la ligne
            cells_text = [td.get_text(strip=True) for td in tds]
            
            # Chercher une date (format JJ/MM ou DD/MM/YYYY)
            has_date = False
            for cell in cells_text:
                if re.match(r'\d{1,2}/\d{1,2}', cell):
                    has_date = True
                    break
            
            if not has_date:
                return None
            
            # Structure approximative: Date | Home | vs | Away | Score | ...
            # Parsing flexible basé sur contenu
            
            data = {}
            data['team'] = home_team
            data['date'] = cells_text[0]
            
            # Score est généralement vers le milieu/fin
            score_text = ""
            opponent = ""
            is_home = None
            
            # Chercher le pattern score (ex: "1-0", "2-1", etc)
            for cell in cells_text:
                if re.match(r'^\d+-\d+$', cell):
                    score_text = cell
                    break
            
            if not score_text:
                return None
            
            # Déterminer home/away et adversaire
            # Stratégie: si on voit le team_name en gras, c'est home
            bold_text = row.find('b')
            if bold_text:
                bold_content = bold_text.get_text(strip=True)
                is_home = (bold_content.lower() == home_team.lower())
            
            # Extraire score
            score_parts = score_text.split('-')
            data['goals_for'] = int(score_parts[0])
            data['goals_against'] = int(score_parts[1])
            
            # Déterminer résultat
            if data['goals_for'] > data['goals_against']:
                data['result'] = 'W'
            elif data['goals_for'] < data['goals_against']:
                data['result'] = 'L'
            else:
                data['result'] = 'D'
            
            # Chercher l'adversaire dans la ligne
            # C'est généralement le team qui n'est pas en gras
            for cell in tds:
                cell_text = cell.get_text(strip=True)
                if (cell_text and 
                    cell_text.lower() != home_team.lower() and
                    cell_text not in score_text and
                    len(cell_text) > 2 and
                    not re.match(r'\d', cell_text[0])):
                    
                    # Vérifier que c'est pas un élément statique
                    if cell_text not in ['vs', 'Score', 'H1', 'H2', 'HT', 'FT']:
                        opponent = cell_text
                        break
            
            data['opponent'] = opponent
            data['is_home'] = is_home if is_home is not None else None
            
            return data if opponent else None
            
        except (ValueError, AttributeError, IndexError):
            return None
    
    def scrape_all_teams(self, standings_url: str, output_file: str = 'data/team_history.json'):
        """
        Scrape l'historique complet pour toutes les équipes
        """
        print("="*70)
        print("SOCCERSTATS TEAM HISTORY SCRAPER")
        print("="*70 + "\n")
        
        # Étape 1: Extraire les team IDs
        team_ids = self.extract_team_ids_from_standings(standings_url)
        
        if not team_ids:
            print("❌ Aucun team ID trouvé")
            return {}
        
        # Étape 2: Scraper l'historique de chaque équipe
        print("🔍 Scraping de l'historique des matchs par équipe:\n")
        
        all_team_history = {}
        
        for team_name, team_id in team_ids.items():
            print(f"📊 {team_name} ({team_id}):")
            matches = self.scrape_team_history(team_name, team_id)
            all_team_history[team_name] = {
                'team_id': team_id,
                'matches': matches,
                'total_matches': len(matches)
            }
            print(f"    ✅ {len(matches)} matchs trouvés\n")
        
        # Sauvegarder
        self.save_history(all_team_history, output_file)
        
        return all_team_history
    
    def save_history(self, history: Dict, output_file: str):
        """Sauvegarde l'historique en JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Données sauvegardées: {output_file}")
        print(f"   Total: {len(history)} équipes")
        total_matches = sum(h['total_matches'] for h in history.values())
        print(f"   Matchs: {total_matches}")


def test_scraper():
    """Test le scraper avec Lens"""
    print("🧪 TEST: Scraping de Lens\n")
    
    scraper = SoccerStatsTeamHistoryScraper()
    
    # Lens: u512-lens
    matches = scraper.scrape_team_history("Lens", "u512-lens")
    
    if matches:
        print(f"\n✅ Extraction réussie: {len(matches)} matchs")
        print("\nPremiers matchs de Lens:")
        for i, match in enumerate(matches[:5], 1):
            print(f"  {i}. {match['date']}: Lens {match['goals_for']}-{match['goals_against']} {match['opponent']} ({match['result']})")
    else:
        print("❌ Aucun match trouvé")


if __name__ == '__main__':
    # Test d'abord
    test_scraper()
    
    print("\n" + "="*70)
    print("Pour scraper toutes les équipes:")
    print("="*70)
    print("""
    scraper = SoccerStatsTeamHistoryScraper()
    standings_url = "https://www.soccerstats.com/standings.asp?league=france"
    history = scraper.scrape_all_teams(standings_url)
    """)
