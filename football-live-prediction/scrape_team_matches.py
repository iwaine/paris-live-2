#!/usr/bin/env python3
"""
Scraper SoccerStats - Historique complet des matchs par équipe
Format: https://www.soccerstats.com/teamstats.asp?league=france&stats=u512-lens
Extraction: Dates, scores, adversaires, minutage des buts
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional
import time

class SoccerStatsTeamMatchesScraper:
    """Scrape l'historique complet des matchs par équipe"""
    
    BASE_URL = "https://www.soccerstats.com"
    
    def __init__(self, timeout=15, retry=3):
        self.timeout = timeout
        self.retry = retry
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Récupère une page avec retry"""
        for attempt in range(self.retry):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt < self.retry - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def parse_match_details(self, match_text: str, team_name: str) -> Dict:
        """
        Parse un texte de match pour extraire: adversaire, score, minutage buts
        
        Format:
        "Angers -Lens 1 - 20-1Florian Thauvin (45)"
        ou
        "Lens- Lorient 3 - 01-0Odsonne Édouard (6)"
        """
        data = {}
        
        # Extraire score: "1 - 2" (avec espaces autour du -)
        # Chercher le PREMIER match de "X - Y" où X et Y sont des chiffres simples
        # et qui sont généralement au début après le nom
        score_match = re.search(r'\b(\d)\s*-\s*(\d)\b', match_text)
        if not score_match:
            return None
        
        score1, score2 = int(score_match.group(1)), int(score_match.group(2))
        
        # Nettoyer le texte pour trouver l'adversaire
        cleaned = re.sub(r'\d\s*-\s*\d', ' ', match_text)
        cleaned = re.sub(r'\(\d+\)', '', cleaned)
        
        # Trouver l'adversaire (l'autre équipe)
        teams = [team.strip() for team in re.split(r'[\s-]+', cleaned) if team.strip() and len(team.strip()) > 2]
        
        opponent = None
        for team in teams:
            if team and team.lower() != team_name.lower():
                opponent = team
                break
        
        # Meilleure heuristique: si team_name est avant le score, c'est home
        if '-' in match_text:
            parts = match_text.split('-')
            is_home = team_name.lower() in parts[0].lower()
        else:
            is_home = None
        
        # Extraire minutes des buts
        goal_times = re.findall(r'\((\d+)\)', match_text)
        
        data['opponent'] = opponent
        data['is_home'] = is_home
        data['score'] = f"{score1}-{score2}"
        data['goals_for'] = score1 if is_home else score2
        data['goals_against'] = score2 if is_home else score1
        data['goal_times'] = goal_times
        data['result'] = 'W' if data['goals_for'] > data['goals_against'] else ('L' if data['goals_for'] < data['goals_against'] else 'D')
        
        return data
    
    def extract_team_matches(self, team_name: str, team_id: str) -> List[Dict]:
        """
        Scrape les matchs d'une équipe
        
        URL: https://www.soccerstats.com/teamstats.asp?league=france&stats=u512-lens
        """
        url = f"{self.BASE_URL}/teamstats.asp?league=france&stats={team_id}"
        print(f"  📥 {team_name} ({team_id})...", end=" ")
        
        html = self.fetch_page(url)
        if not html:
            print("❌ Impossible de récupérer")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Trouver la table des résultats
        # La table contient les résultats avec dates "DD Mon" et matchs
        tables = soup.find_all('table')
        
        matches = []
        
        # Chercher la table avec les résultats
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 3:
                continue
            
            # Vérifier si c'est la table des matchs
            has_match_pattern = False
            for row in rows[:5]:
                tds = row.find_all('td')
                for td in tds:
                    text = td.get_text(strip=True)
                    # Pattern: "30 Nov", "2 Dec", etc - date courte
                    if re.search(r'\d{1,2}\s+\w{3}', text):
                        has_match_pattern = True
                        break
                if has_match_pattern:
                    break
            
            if not has_match_pattern:
                continue
            
            # Parser les matchs de cette table
            found_any_match = False
            for row in rows[1:]:  # Skip header
                tds = row.find_all('td')
                if len(tds) < 2:
                    continue
                
                date_text = tds[0].get_text(strip=True)
                match_text = tds[1].get_text(strip=True) if len(tds) > 1 else ""
                
                # Vérifier si c'est un match valide (date format "30 Nov")
                if not re.search(r'\d{1,2}\s+\w{3}', date_text):
                    continue
                
                if not match_text or '-' not in match_text:
                    continue
                
                match_data = self.parse_match_details(match_text, team_name)
                if match_data:
                    match_data['date'] = date_text
                    matches.append(match_data)
                    found_any_match = True
            
            # Si on a trouvé des matchs dans cette table, c'est la bonne - stop ici
            if found_any_match:
                break
        
        print(f"✅ {len(matches)} matchs")
        return matches
    
    def get_team_ids_from_standings(self) -> Dict[str, str]:
        """
        Récupère les IDs de toutes les équipes depuis la page de classement
        """
        standings_url = f"{self.BASE_URL}/standings.asp?league=france"
        print("🔍 Extraction des team IDs...\n")
        
        html = self.fetch_page(standings_url)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'id': 'btable'})
        
        if not table:
            print("❌ Tableau de classement non trouvé")
            return {}
        
        team_ids = {}
        rows = table.find_all('tr', {'class': 'odd'})
        
        for row in rows:
            tds = row.find_all('td')
            if len(tds) < 2:
                continue
            
            team_link = tds[1].find('a')
            if team_link:
                team_name = team_link.get_text(strip=True)
                href = team_link.get('href', '')
                match = re.search(r'stats=([^&\s"\']+)', href)
                if match:
                    team_id = match.group(1)
                    team_ids[team_name] = team_id
                    print(f"  ✓ {team_name:20s} → {team_id}")
        
        print(f"\n✅ {len(team_ids)} équipes trouvées\n")
        return team_ids
    
    def scrape_all_teams(self, output_file: str = 'data/team_matches.json'):
        """Scrape tous les matchs pour toutes les équipes"""
        print("="*70)
        print("SOCCERSTATS TEAM MATCHES SCRAPER")
        print("="*70 + "\n")
        
        # Étape 1: Récupérer les team IDs
        team_ids = self.get_team_ids_from_standings()
        if not team_ids:
            return {}
        
        # Étape 2: Scraper les matchs de chaque équipe
        print("📊 Scraping des matchs par équipe:\n")
        all_data = {}
        total_matches = 0
        
        for team_name, team_id in team_ids.items():
            matches = self.extract_team_matches(team_name, team_id)
            all_data[team_name] = {
                'team_id': team_id,
                'matches': matches,
                'total': len(matches)
            }
            total_matches += len(matches)
        
        # Sauvegarder
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Scraping complet!")
        print(f"   Fichier: {output_file}")
        print(f"   Équipes: {len(all_data)}")
        print(f"   Matchs total: {total_matches}")
        
        return all_data


def test_single_team():
    """Test avec une seule équipe: Lens"""
    print("🧪 TEST: Lens (u512-lens)\n")
    
    scraper = SoccerStatsTeamMatchesScraper()
    matches = scraper.extract_team_matches("Lens", "u512-lens")
    
    if matches:
        print(f"\n✅ {len(matches)} matchs trouvés:\n")
        for i, match in enumerate(matches[:10], 1):
            print(f"  {i:2d}. {match['date']:12s} | Lens vs {match['opponent']:15s} | Score: {match['score']:5s} | Result: {match['result']} | Goals: {','.join(match['goal_times'])}")
        
        if len(matches) > 10:
            print(f"  ... et {len(matches)-10} autres matchs")
    else:
        print("❌ Aucun match trouvé")


if __name__ == '__main__':
    test_single_team()
    
    print("\n" + "="*70)
    print("Pour scraper toutes les équipes:")
    print("="*70)
    print("""
    scraper = SoccerStatsTeamMatchesScraper()
    data = scraper.scrape_all_teams()
    """)
