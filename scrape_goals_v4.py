#!/usr/bin/env python3
"""
Scraper V4 - OPTIMISÉ
Scrape TOUS les matches d'une ligue en 1 seule requête HTTP
URL: https://www.soccerstats.com/latest.asp?league=bulgaria
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import time
import re

class LeagueScraperV4:
    """Scrape tous les matches d'une ligue en 1 requête"""
    
    BASE_URL = "https://www.soccerstats.com"
    DB_PATH = "football-live-prediction/data/predictions.db"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'paris-live-bot/4.0 (Match Analysis)'
        })
    
    def _extract_goals_from_tooltip(self, tooltip_html: str) -> tuple:
        """
        Parse le HTML du tooltip pour extraire buts HOME et AWAY
        
        Format tooltip:
        <b>0-1</b> Joueur (13)  ← away marque
        <b>1-1</b> Joueur (50)  ← home marque
        
        Returns:
            (goals_home, goals_away) - listes de minutes
        """
        goals_home = []
        goals_away = []
        
        # Parser le HTML
        soup = BeautifulSoup(tooltip_html, 'html.parser')
        
        # Trouver tous les scores progressifs <b>X-Y</b>
        score_tags = soup.find_all('b')
        
        prev_home = 0
        prev_away = 0
        
        for score_tag in score_tags:
            score_text = score_tag.get_text().strip()
            match = re.match(r'(\d+)-(\d+)', score_text)
            
            if not match:
                continue
            
            home_score = int(match.group(1))
            away_score = int(match.group(2))
            
            # Trouver la minute du but dans le parent <font>
            parent = score_tag.parent
            if parent:
                parent_text = parent.get_text()
                minute_match = re.search(r'\((\d+)\)', parent_text)
                if minute_match:
                    minute = int(minute_match.group(1))
                    
                    # Déterminer qui a marqué
                    if home_score > prev_home:
                        goals_home.append(minute)
                    elif away_score > prev_away:
                        goals_away.append(minute)
                    
                    prev_home = home_score
                    prev_away = away_score
        
        return goals_home, goals_away
    
    def scrape_league(self, country: str, league: str, league_code: str) -> dict:
        """
        Scrape TOUS les matches d'une ligue depuis latest.asp
        
        Args:
            country: Pays (Bulgaria)
            league: Nom affiché (A PFG)
            league_code: Code SoccerStats (bulgaria)
        
        Returns:
            Dict avec tous les matches
        """
        url = f"{self.BASE_URL}/latest.asp?league={league_code}"
        
        print(f"\n📥 Scraping {country} - {league}...")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            time.sleep(3)  # Respecter robots.txt
        except Exception as e:
            print(f"❌ Erreur HTTP: {e}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver toutes les lignes de match
        # Structure: <tr> avec des <td> contenant équipes, score, date
        matches_data = []
        
        # Chercher les tooltips avec scores
        score_links = soup.find_all('a', class_='tooltip4')
        
        print(f"✅ {len(score_links)} matches trouvés")
        
        for score_link in score_links:
            try:
                # Remonter au <tr> parent pour trouver les équipes
                parent_tr = score_link.find_parent('tr')
                if not parent_tr:
                    continue
                
                cells = parent_tr.find_all('td')
                if len(cells) < 5:
                    continue
                
                # Structure typique:
                # [0] Date | [1] Home team | [2] ? | [3] Score | [4] Away team | [5] ?
                # Mais peut varier, cherchons les équipes autour du score
                
                # Trouver l'index de la cellule avec le score
                score_idx = None
                for i, cell in enumerate(cells):
                    if score_link.parent == cell or score_link in cell.descendants:
                        score_idx = i
                        break
                
                if score_idx is None:
                    continue
                
                # Équipes : avant et après le score
                # Généralement: [..., home_team, score, away_team, ...]
                if score_idx < 1 or score_idx >= len(cells) - 1:
                    continue
                
                home_cell = cells[score_idx - 1]
                away_cell = cells[score_idx + 1]
                
                home_team = home_cell.get_text().strip()
                away_team = away_cell.get_text().strip()
                
                # Nettoyer les noms
                home_team = re.sub(r'\s+', ' ', home_team)
                away_team = re.sub(r'\s+', ' ', away_team)
                
                if not home_team or not away_team:
                    continue
                
                # Score
                score_text = score_link.get_text().strip()
                score = re.sub(r'\s+', '', score_text)
                
                # Date - chercher dans les cellules précédentes
                date = None
                for i in range(score_idx - 1, -1, -1):
                    cell_text = cells[i].get_text().strip()
                    # Format date: "4 Dec" ou "04 Dec"
                    if re.match(r'\d+\s+\w+', cell_text):
                        date = cell_text
                        break
                
                if not date:
                    date = "Unknown"
                
                # Tooltip avec détails des buts
                tooltip_span = score_link.find('span')
                tooltip_html = str(tooltip_span) if tooltip_span else ""
                
                # Extraire buts HOME et AWAY
                goals_home, goals_away = self._extract_goals_from_tooltip(tooltip_html)
                
                # Créer 2 lignes : une pour HOME, une pour AWAY
                # Ligne HOME
                matches_data.append({
                    'country': country,
                    'league': league,
                    'league_code': league_code,
                    'team': home_team,
                    'opponent': away_team,
                    'date': date,
                    'is_home': True,
                    'score': score,
                    'goals_scored': goals_home,
                    'goals_conceded': goals_away
                })
                
                # Ligne AWAY
                matches_data.append({
                    'country': country,
                    'league': league,
                    'league_code': league_code,
                    'team': away_team,
                    'opponent': home_team,
                    'date': date,
                    'is_home': False,
                    'score': score,
                    'goals_scored': goals_away,
                    'goals_conceded': goals_home
                })
                
            except Exception as e:
                continue
        
        print(f"✅ {len(matches_data)} lignes créées (2 par match)")
        
        return {
            'country': country,
            'league': league,
            'league_code': league_code,
            'matches': matches_data
        }
    
    def save_to_db(self, data: dict):
        """Sauvegarde les données en DB"""
        if not data or 'matches' not in data:
            return 0
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        inserted = 0
        
        for match in data['matches']:
            # Convertir goals_scored en JSON
            goal_times_json = json.dumps(match['goals_scored'])
            
            # Générer match_id unique
            teams_sorted = sorted([match['team'], match['opponent']])
            match_id = f"{match['date']}_{teams_sorted[0]}_vs_{teams_sorted[1]}"
            
            try:
                cursor.execute('''
                    INSERT INTO soccerstats_scraped_matches 
                    (country, league, league_display_name, team, opponent, date, is_home, 
                     score, goals_for, goals_against, goal_times, match_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match['country'],
                    match['league_code'],
                    match['league'],
                    match['team'],
                    match['opponent'],
                    match['date'],
                    1 if match['is_home'] else 0,
                    match['score'],
                    len(match['goals_scored']),
                    len(match['goals_conceded']),
                    goal_times_json,
                    match_id
                ))
                inserted += cursor.rowcount
            except Exception as e:
                print(f"  ⚠️ Erreur insertion: {e}")
                continue
        
        conn.commit()
        conn.close()
        return inserted


def scrape_bulgaria():
    """Scrape la Bulgarie A PFG en 1 requête"""
    
    scraper = LeagueScraperV4()
    
    print("\n" + "="*80)
    print("🇧🇬 BULGARIE - A PFG (scraping optimisé)")
    print("="*80)
    
    data = scraper.scrape_league(
        country='Bulgaria',
        league='A PFG',
        league_code='bulgaria'
    )
    
    if data:
        inserted = scraper.save_to_db(data)
        print(f"\n✅ Total: {inserted} lignes insérées")
    
    print("="*80)


if __name__ == '__main__':
    scrape_bulgaria()
