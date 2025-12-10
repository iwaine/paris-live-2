#!/usr/bin/env python3
"""
Scraper V2 - Extraction minutes de buts avec isolation country/league
Méthodologie corrigée : Sépare buts marqués/encaissés via analyse du score
"""

import requests
import re
import time
import sqlite3
import json
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict
from collections import defaultdict


class GoalsScraper:
    """Scraper pour extraire les minutes de buts depuis SoccerStats"""
    
    def __init__(self, db_path='/workspaces/paris-live/football-live-prediction/data/predictions.db'):
        self.db_path = db_path
        self.throttle = 3  # secondes entre requêtes
        self.last_request = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "paris-live-bot/2.0 (Match Analysis)"
        })
    
    def _respect_throttle(self):
        """Respecter le throttling"""
        elapsed = time.time() - self.last_request
        if elapsed < self.throttle:
            time.sleep(self.throttle - elapsed)
        self.last_request = time.time()
    
    def _extract_goals_from_tooltip(self, tooltip_span, team_is_home: bool) -> Tuple[List[int], List[int]]:
        """
        Extrait les minutes de buts marqués/encaissés depuis le tooltip
        
        Analyse le score pour déterminer qui a marqué :
        - Score passe de 0-0 à 1-0 → HOME a marqué
        - Score passe de 1-0 à 1-1 → AWAY a marqué
        
        Args:
            tooltip_span: Element BeautifulSoup du tooltip
            team_is_home: True si l'équipe scrapée est HOME
        
        Returns:
            (goals_scored_minutes, goals_conceded_minutes)
        """
        goals_scored = []
        goals_conceded = []
        
        try:
            html_text = str(tooltip_span)
            prev_home_score = 0
            prev_away_score = 0
            
            # Split par <b> pour isoler chaque but
            parts = html_text.split('<b>')
            
            for part in parts:
                if '</b>' not in part:
                    continue
                
                try:
                    # Extraire le score entre <b> et </b>
                    score_part = part.split('</b>')[0].strip()
                    rest = part.split('</b>')[1] if '</b>' in part else ''
                    
                    # Parser le score "1-0", "2-1", etc.
                    score_match = re.search(r'(\d+)\s*-\s*(\d+)', score_part)
                    if not score_match:
                        continue
                    
                    current_home = int(score_match.group(1))
                    current_away = int(score_match.group(2))
                    
                    # Extraire la minute (13), (45+2), etc.
                    minute_match = re.search(r'\((\d{1,3})(?:\+\d{1,2})?\)', rest)
                    if not minute_match:
                        continue
                    
                    minute = int(minute_match.group(1))
                    if not (0 <= minute <= 130):
                        continue
                    
                    # Déterminer qui a marqué
                    home_scored = (current_home > prev_home_score)
                    away_scored = (current_away > prev_away_score)
                    
                    if home_scored and team_is_home:
                        goals_scored.append(minute)
                    elif home_scored and not team_is_home:
                        goals_conceded.append(minute)
                    elif away_scored and not team_is_home:
                        goals_scored.append(minute)
                    elif away_scored and team_is_home:
                        goals_conceded.append(minute)
                    
                    # Mettre à jour scores précédents
                    prev_home_score = current_home
                    prev_away_score = current_away
                    
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return goals_scored, goals_conceded
    
    def scrape_team(self, country: str, league: str, league_code: str, team_slug: str, team_name: str) -> Dict:
        """
        Scrape tous les matches d'une équipe
        
        Args:
            country: 'Bulgaria', 'France', etc.
            league: Nom affiché 'A PFG', 'Ligue 1', etc.
            league_code: Code SoccerStats 'bulgaria', 'france', etc.
            team_slug: 'u1752-botev-vratsa'
            team_name: 'Botev Vratsa'
        
        Returns:
            Dict avec les matches extraits
        """
        url = f"https://www.soccerstats.com/teamstats.asp?league={league_code}&stats={team_slug}"
        
        print(f"  📥 {team_name}...")
        self._respect_throttle()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        matches_data = []
        
        # Trouver la table des matches
        main_table = soup.find('table', attrs={'cellspacing': '0', 'cellpadding': '0', 'bgcolor': '#cccccc'})
        
        if not main_table:
            print(f"    ⚠️ Table non trouvée")
            return {}
        
        # Parser chaque match
        for tr in main_table.find_all('tr', attrs={'height': '36'}):
            try:
                cells = tr.find_all('td')
                if len(cells) < 4:
                    continue
                
                # Date
                date = cells[0].get_text(strip=True)
                
                # Équipes
                cell_home = cells[1]
                cell_away = cells[3]
                
                # CRITIQUE : Détecter is_home via la balise <b> (gras)
                if cell_home.find('b'):
                    is_home = True
                    team = team_name
                    opponent = cell_away.get_text(strip=True)
                elif cell_away.find('b'):
                    is_home = False
                    team = team_name
                    opponent = cell_home.get_text(strip=True)
                else:
                    # Fallback
                    home_text = cell_home.get_text(strip=True)
                    if team_name.upper() in home_text.upper():
                        is_home = True
                        team = team_name
                        opponent = cell_away.get_text(strip=True)
                    else:
                        is_home = False
                        team = team_name
                        opponent = cell_home.get_text(strip=True)
                
                # Score
                score_cell = cells[2]
                score_text = score_cell.get_text(strip=True)
                score_match = re.search(r'(\d{1,2})\s*[-:]\s*(\d{1,2})', score_text)
                score = f"{score_match.group(1)}:{score_match.group(2)}" if score_match else "0:0"
                
                # Tooltip avec les buts
                tooltip_link = score_cell.find('a', class_='tooltip4')
                goals_scored = []
                goals_conceded = []
                
                if tooltip_link:
                    tooltip_span = tooltip_link.find('span')
                    if tooltip_span:
                        goals_scored, goals_conceded = self._extract_goals_from_tooltip(tooltip_span, is_home)
                
                matches_data.append({
                    'country': country,
                    'league': league,
                    'league_code': league_code,
                    'team': team,
                    'opponent': opponent,
                    'date': date,
                    'is_home': is_home,
                    'score': score,
                    'goals_scored': goals_scored,
                    'goals_conceded': goals_conceded
                })
                
            except Exception:
                continue
        
        print(f"    ✅ {len(matches_data)} matches")
        return {
            'country': country,
            'league': league,
            'league_code': league_code,
            'team': team_name,
            'matches': matches_data
        }
    
    def save_to_db(self, data: Dict):
        """Sauvegarde les données en DB"""
        if not data or 'matches' not in data:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        inserted = 0
        
        for match in data['matches']:
            # Convertir goals_scored en JSON
            goal_times_json = json.dumps(match['goals_scored'])
            
            try:
                cursor.execute('''
                    INSERT INTO soccerstats_scraped_matches 
                    (country, league, league_display_name, team, opponent, date, is_home, 
                     score, goals_for, goals_against, goal_times)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    goal_times_json
                ))
                # rowcount = 1 si inséré, 0 si ignoré (doublon)
                inserted += cursor.rowcount
            except Exception as e:
                print(f"  ⚠️ Erreur insertion: {e}")
                continue
        
        conn.commit()
        conn.close()
        return inserted


def scrape_bulgaria():
    """Scrape les 16 équipes de Bulgarie - A PFG"""
    
    scraper = GoalsScraper()
    
    teams = [
        ('u1752-botev-vratsa', 'Botev Vratsa'),
        ('u1753-spartak-varna', 'Spartak Varna'),
        ('u1748-ludogorets', 'Ludogorets'),
        ('u1751-cska-sofia', 'CSKA Sofia'),
        ('u1750-levski-sofia', 'Levski Sofia'),
        ('u1749-botev-plovdiv', 'Botev Plovdiv'),
        ('u1747-beroe', 'Beroe'),
        ('u1756-slavia-sofia', 'Slavia Sofia'),
        ('u1754-lokomotiv-plovdiv', 'Lok. Plovdiv'),
        ('u1756-arda', 'Arda'),
        ('u1757-cherno-more', 'Cherno More'),
        ('u1758-cska-1948-sofia', 'CSKA 1948 Sofia'),
        ('u1759-septemvri-sofia', 'Septemvri Sofia'),
        ('u1760-lokomotiv-sofia', 'Lokomotiv Sofia'),
        ('u1750-montana', 'Montana'),
        ('u1775-dobrudzha', 'Dobrudzha'),
    ]
    
    print("\n" + "="*80)
    print("🇧🇬 BULGARIE - A PFG (16 équipes)")
    print("="*80)
    
    total_inserted = 0
    
    for slug, name in teams:
        data = scraper.scrape_team(
            country='Bulgaria',
            league='A PFG',
            league_code='bulgaria',
            team_slug=slug,
            team_name=name
        )
        
        if data:
            inserted = scraper.save_to_db(data)
            total_inserted += inserted
    
    print(f"\n✅ Total: {total_inserted} matches insérés")
    print("="*80)


if __name__ == '__main__':
    scrape_bulgaria()
