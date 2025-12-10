#!/usr/bin/env python3
"""
Scraper SoccerStats - Historique complet des matchs par équipe
Format: https://www.soccerstats.com/teamstats.asp?league=france&stats=u512-lens
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
    
    def parse_match_from_row(self, match_text: str, score_text: str, team_name: str) -> Optional[Dict]:
        """
        Parse un match depuis le tableau
        match_text: "Angers - Lens"
        score_text: "1 - 2" suivi de détails "0-1Florian Thauvin (45)"
        """
        # Extraire le score au début du score_text (avant les minutages)
        # Format: "1 - 2----..." ou "3 - 0---..." 
        # Le score est à la position immédiate du début
        
        score_text_stripped = score_text.strip()
        
        # Chercher le pattern "X - Y" au début
        # Les minutages commencent avec pattern "0-1Joueur", "1-1Joueur", etc sans espace
        # donc le score aura des espaces autour du tiret
        match = re.match(r'(\d{1,2})\s+-\s+(\d{1,2})', score_text_stripped)
        if not match:
            return None
        
        score1 = int(match.group(1))
        score2 = int(match.group(2))
        
        # Parser match_text pour récupérer les équipes
        # Format: "Home - Away" ou "Home- Away"
        # Remplacer " -" et "- " par juste "-" pour simplifier
        normalized = match_text.replace(' -', '-').replace('- ', '-')
        teams = normalized.split('-')
        if len(teams) < 2:
            return None
        
        home = teams[0].strip()
        away = teams[1].strip()
        
        # Déterminer home/away
        is_home = team_name.lower() in home.lower()
        opponent = away if is_home else home
        
        # Extraire minutes des buts du score_text
        goal_times = re.findall(r'\((\d+)\)', score_text)
        
        return {
            'opponent': opponent,
            'is_home': is_home,
            'score': f"{score1}-{score2}",
            'goals_for': score1 if is_home else score2,
            'goals_against': score2 if is_home else score1,
            'goal_times': goal_times,
            'result': 'W' if (score1 if is_home else score2) > (score2 if is_home else score1) else ('L' if (score1 if is_home else score2) < (score2 if is_home else score1) else 'D')
        }
    
    def parse_match_details(self, match_text: str, team_name: str) -> Optional[Dict]:
        """
        Parse un texte de match pour extraire: adversaire, score, contexte home/away
        Format: "Angers -Lens 1 - 2" ou "Lens- Strasbourg 3 - 0"
        """
        # D'abord, extraire le score au format "X - Y" 
        # Il y a généralement un espace autour du tiret du score
        score_match = re.search(r'(\d{1,2})\s+-\s+(\d{1,2})', match_text)
        if not score_match:
            return None
        
        score1 = int(score_match.group(1))
        score2 = int(score_match.group(2))
        
        # Vérifier que ce score n'est pas trop tard (minutages typiquement après 90+)
        score_pos = match_text.find(score_match.group(0))
        if score_pos > 100:  # Score trop loin = pas le bon
            return None
        
        # Extraire la partie texte AVANT le score (contient les noms d'équipes)
        teams_part = match_text[:score_pos].strip()
        
        # Split par "-" pour séparer home et away (il n'y a qu'un "-" dans cette partie)
        if '-' not in teams_part:
            return None
        
        team_names = teams_part.split('-', 1)  # Split only on first "-"
        home_name = team_names[0].strip()
        away_name = team_names[1].strip() if len(team_names) > 1 else ""
        
        # Déterminer home/away
        is_home = team_name.lower() in home_name.lower()
        opponent = away_name if is_home else home_name
        
        # Extraire minutes des buts
        goal_times = re.findall(r'\((\d+)\)', match_text)
        
        return {
            'opponent': opponent.strip(),
            'is_home': is_home,
            'score': f"{score1}-{score2}",
            'goals_for': score1 if is_home else score2,
            'goals_against': score2 if is_home else score1,
            'goal_times': goal_times,
            'result': 'W' if (score1 if is_home else score2) > (score2 if is_home else score1) else ('L' if (score1 if is_home else score2) < (score2 if is_home else score1) else 'D')
        }
    
    def extract_team_matches(self, team_name: str, team_id: str) -> List[Dict]:
        """Scrape les matchs d'une équipe"""
        url = f"{self.BASE_URL}/teamstats.asp?league=france&stats={team_id}"
        print(f"  📥 {team_name} ({team_id})...", end=" ")
        
        html = self.fetch_page(url)
        if not html:
            print("❌")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        matches = []
        
        # Chercher la table des matchs
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 3:
                continue
            
            # Vérifier si c'est la table des matchs (dates au format "DD Mon")
            has_match_pattern = False
            for row in rows[:5]:
                tds = row.find_all('td')
                for td in tds:
                    if re.search(r'\d{1,2}\s+\w{3}', td.get_text(strip=True)):
                        has_match_pattern = True
                        break
                if has_match_pattern:
                    break
            
            if not has_match_pattern:
                continue
            
            # Parser les matchs de cette table
            found_matches = False
            for row in rows[1:]:
                tds = row.find_all('td')
                # Structure: [Date, Match, Score+Details]
                if len(tds) < 3:
                    continue
                
                date_text = tds[0].get_text(strip=True)
                match_text = tds[1].get_text(strip=True)  # "Angers - Lens"
                
                # IMPORTANT: le score est dans la balise <b> de la col 2
                score_cell = tds[2]
                bold_tag = score_cell.find('b')
                if bold_tag:
                    score_text = bold_tag.get_text(strip=True)  # "1 - 2" seulement
                else:
                    score_text = score_cell.get_text(strip=True)[:20]  # fallback
                
                if not re.search(r'\d{1,2}\s+\w{3}', date_text):
                    continue
                if not match_text or '-' not in match_text:
                    continue
                
                # Parser le match
                match_data = self.parse_match_from_row(match_text, score_text, team_name)
                if match_data:
                    match_data['date'] = date_text
                    # Ajouter aussi les buts si disponibles
                    full_score_text = score_cell.get_text(strip=True)
                    goal_times = re.findall(r'\((\d+)\)', full_score_text)
                    if goal_times:
                        match_data['goal_times'] = goal_times
                    
                    matches.append(match_data)
                    found_matches = True
            
            # Si on a trouvé des matchs, c'est la bonne table
            if found_matches:
                break
        
        print(f"✅ {len(matches)}")
        return matches
    
    def scrape_all_teams(self, output_file: str = 'data/team_matches.json'):
        """Scrape tous les matchs pour toutes les équipes"""
        print("="*70)
        print("SOCCERSTATS TEAM MATCHES SCRAPER")
        print("="*70 + "\n")
        
        # Récupérer les team IDs
        team_ids = self.get_team_ids_from_standings()
        if not team_ids:
            return {}
        
        # Scraper les matchs
        print("📊 Scraping des matchs par équipe:\n")
        all_data = {}
        total_matches = 0
        
        for team_name, team_id in sorted(team_ids.items()):
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
    
    def get_team_ids_from_standings(self) -> Dict[str, str]:
        """Récupère les IDs de toutes les équipes - données hardcodées pour Ligue 1"""
        # Les team IDs pour la Ligue 1 France (2024-2025)
        # Format: u{number}-{team_name_lowercase}
        print("🔍 Extraction des team IDs...\n")
        
        team_ids = {
            'Lens': 'u512-lens',
            'Marseille': 'u517-marseille',
            'Lille': 'u503-lille',
            'PSG': 'u518-paris-sg',
            'Monaco': 'u505-monaco',
            'Lyon': 'u513-lyon',
            'Rennes': 'u504-rennes',
            'Nantes': 'u500-nantes',
            'Strasbourg': 'u508-strasbourg',
            'Angers': 'u502-angers',
            'Toulouse': 'u7659-toulouse',
            'Nice': 'u511-nice',
            'Brest': 'u510-brest',
            'Lorient': 'u507-lorient',
            'Auxerre': 'u7648-auxerre',
            'Le Havre': 'u7655-le-havre',
            'Metz': 'u515-metz',
            'Paris FC': 'u7654-paris-fc'
        }
        
        for team_name, team_id in team_ids.items():
            print(f"  ✓ {team_name:20s} → {team_id}")
        
        print(f"\n✅ {len(team_ids)} équipes trouvées\n")
        return team_ids


def test_single_team():
    """Test avec Lens"""
    print("🧪 TEST: Lens (u512-lens)\n")
    
    scraper = SoccerStatsTeamMatchesScraper()
    matches = scraper.extract_team_matches("Lens", "u512-lens")
    
    if matches:
        print(f"\n✅ {len(matches)} matchs trouvés:\n")
        for i, match in enumerate(matches[:10], 1):
            home_away = "🏠 HOME" if match['is_home'] else "🚗 AWAY"
            print(f"  {i:2d}. {match['date']:12s} | {home_away} | vs {match['opponent']:15s} | {match['score']} | {match['result']}")
        
        if len(matches) > 10:
            print(f"  ... et {len(matches)-10} autres")
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
