#!/usr/bin/env python3
"""
Scraper pour extraire les minutes exactes des buts depuis les pages teamstats.asp
Remplit la colonne goal_times dans soccerstats_scraped_matches
"""

import requests
import re
import time
import sqlite3
import json
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple
from collections import defaultdict

class TeamGoalTimesScraper:
    """Extrait les minutes de buts depuis les tooltips des pages d'équipe"""
    
    def __init__(self, db_path='/workspaces/paris-live/football-live-prediction/data/predictions.db', throttle=3):
        self.db_path = db_path
        self.throttle = throttle
        self.last_request = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "paris-live-bot/1.0 (Match Analysis)"
        })
        
    def _respect_throttle(self):
        """Respect robots.txt throttling"""
        elapsed = time.time() - self.last_request
        if elapsed < self.throttle:
            time.sleep(self.throttle - elapsed)
        self.last_request = time.time()
    
    def _extract_goal_minutes_from_tooltip(self, tooltip_div, team_is_home: bool) -> Tuple[List[int], List[int]]:
        """
        Extrait les minutes de buts en séparant marqués/encaissés selon le score
        
        Format HTML:
        <b>0-1</b>&nbsp;&nbsp;<font color="#000000">Martin Petkov (13)</font>
        <b>1-1</b>&nbsp;&nbsp;<font color="#000000">Roberto Raychev (50)</font>
        
        Args:
            tooltip_div: Élément BeautifulSoup du tooltip
            team_is_home: True si l'équipe scrapée joue à domicile
        
        Returns:
            (goals_scored_minutes, goals_conceded_minutes)
        """
        goals_scored = []
        goals_conceded = []
        
        try:
            html_text = str(tooltip_div)
            prev_home_score = 0
            prev_away_score = 0
            
            # Split par <b> pour isoler chaque but
            parts = html_text.split('<b>')
            
            for part in parts:
                if '</b>' not in part:
                    continue
                
                try:
                    # Extraire score et minute
                    score_part = part.split('</b>')[0].strip()
                    rest = part.split('</b>')[1] if '</b>' in part else ''
                    
                    # Parser le score (format: "1-0", "2-1", etc.)
                    score_match = re.search(r'(\d+)\s*-\s*(\d+)', score_part)
                    if not score_match:
                        continue
                    
                    current_home = int(score_match.group(1))
                    current_away = int(score_match.group(2))
                    
                    # Extraire la minute
                    minute_match = re.search(r'\((\d{1,3})(?:\+\d{1,2})?\)', rest)
                    if not minute_match:
                        continue
                    
                    minute = int(minute_match.group(1))
                    if not (0 <= minute <= 130):
                        continue
                    
                    # Déterminer qui a marqué en comparant avec le score précédent
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
                    
                    # Mettre à jour les scores précédents
                    prev_home_score = current_home
                    prev_away_score = current_away
                    
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return goals_scored, goals_conceded
    
    def scrape_team_matches(self, league: str, team_url_slug: str, team_name: str) -> dict:
        """
        Scrape les matches d'une équipe depuis teamstats.asp
        
        Args:
            league: Code ligue (ex: 'bulgaria')
            team_url_slug: Slug URL équipe (ex: 'u1752-botev-vratsa')
            team_name: Nom équipe pour matching DB
        
        Returns:
            {match_url: {'goal_times': [list], 'is_home': bool}}
        """
        url = f"https://www.soccerstats.com/teamstats.asp?league={league}&stats={team_url_slug}"
        
        print(f"  Scraping {team_name}...")
        self._respect_throttle()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"    ❌ Erreur requête: {e}")
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        matches_data = {}
        
        # Trouver la table principale des matches
        main_table = soup.find('table', attrs={'cellspacing': '0', 'cellpadding': '0', 'bgcolor': '#cccccc'})
        
        if not main_table:
            print(f"    ⚠️ Table de matches non trouvée")
            return {}
        
        # Parcourir les lignes de matches
        for tr in main_table.find_all('tr', attrs={'height': '36'}):
            try:
                # Extraire le lien stats (pmatch.asp)
                stats_link = tr.find('a', class_='SmallButton')
                if not stats_link or 'pmatch.asp' not in stats_link.get('href', ''):
                    continue
                
                match_url = stats_link['href']
                cells = tr.find_all('td')
                
                # Extraire les noms d'équipes depuis les colonnes
                # Structure: [date, HOME (padding-right), score, AWAY (padding-left), ...]
                team_home = None
                team_away = None
                is_home = False
                
                if len(cells) >= 4:
                    # Colonne 1 (index 1): Équipe HOME
                    cell_home = cells[1]
                    home_text = cell_home.get_text(strip=True)
                    
                    # Colonne 3 (index 3): Équipe AWAY  
                    cell_away = cells[3]
                    away_text = cell_away.get_text(strip=True)
                    
                    # Déterminer si notre équipe est HOME ou AWAY en vérifiant le <b> (gras)
                    # L'équipe scrapée est toujours en gras
                    if cell_home.find('b'):
                        # Notre équipe est en gras dans la colonne HOME
                        is_home = True
                        team_home = team_name
                        team_away = away_text
                    elif cell_away.find('b'):
                        # Notre équipe est en gras dans la colonne AWAY
                        is_home = False
                        team_home = home_text
                        team_away = team_name
                    else:
                        # Fallback: vérifier par nom
                        if team_name.upper() in home_text.upper():
                            is_home = True
                            team_home = team_name
                            team_away = away_text
                        else:
                            is_home = False
                            team_home = home_text
                            team_away = team_name
                        is_home = bool(cell_home.find('b'))
                
                # Extraire le tooltip avec les buts séparés (marqués vs encaissés)
                tooltip_link = tr.find('a', class_='tooltip4')
                goals_scored = []
                goals_conceded = []
                
                if tooltip_link:
                    tooltip_span = tooltip_link.find('span')
                    if tooltip_span:
                        goals_scored, goals_conceded = self._extract_goal_minutes_from_tooltip(tooltip_span, is_home)
                
                matches_data[match_url] = {
                    'goals_scored': goals_scored,
                    'goals_conceded': goals_conceded,
                    'is_home': is_home,
                    'team': team_home,
                    'opponent': team_away
                }
                
            except Exception as e:
                continue
        
        print(f"    ✅ {len(matches_data)} matches extraits")
        return matches_data
    
    def update_database(self, league: str, matches_data: dict):
        """
        Met à jour la colonne goal_times dans la DB
        Stocke UNIQUEMENT les buts marqués par l'équipe (pas les encaissés)
        Le builder trouvera les buts encaissés en interrogeant l'adversaire
        
        Args:
            league: Code ligue
            matches_data: {match_url: {'goals_scored': [...], 'goals_conceded': [...], 'is_home': bool, 'team': str, 'opponent': str}}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updated = 0
        
        for match_url, data in matches_data.items():
            goals_scored = data.get('goals_scored', [])
            is_home = 1 if data['is_home'] else 0
            team = data.get('team', '')
            opponent = data.get('opponent', '')
            
            # Convertir liste en JSON string - UNIQUEMENT les buts marqués
            goal_times_str = json.dumps(goals_scored) if goals_scored else None
            
            # Update UNIQUEMENT l'équipe scrapée avec SES buts marqués
            cursor.execute('''
                UPDATE soccerstats_scraped_matches
                SET goal_times = ?
                WHERE league = ? 
                  AND is_home = ?
                  AND UPPER(team) = UPPER(?)
                  AND UPPER(opponent) = UPPER(?)
            ''', (goal_times_str, league, is_home, team, opponent))
            
            if cursor.rowcount > 0:
                updated += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ {updated} matches mis à jour dans la base")
        return updated
    
    def scrape_bulgaria_teams(self):
        """Scrape toutes les équipes bulgares"""
        
        # Liste des équipes bulgares de la saison 2025/26
        bulgaria_teams = [
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
        
        print(f"\n🇧🇬 SCRAPING BULGARIE - {len(bulgaria_teams)} équipes")
        print("=" * 80)
        
        all_matches = {}
        
        for team_slug, team_name in bulgaria_teams:
            matches = self.scrape_team_matches('bulgaria', team_slug, team_name)
            all_matches.update(matches)
        
        print(f"\n📊 Total: {len(all_matches)} matches uniques extraits")
        
        # Update DB
        print(f"\n💾 Mise à jour base de données...")
        updated = self.update_database('bulgaria', all_matches)
        print(f"✅ {updated} entrées mises à jour dans la DB")
        
        return all_matches


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("🎯 EXTRACTION MINUTES DE BUTS - SOCCERSTATS BULGARIE")
    print("=" * 80)
    
    scraper = TeamGoalTimesScraper()
    scraper.scrape_bulgaria_teams()
    
    print("\n" + "=" * 80)
    print("✅ EXTRACTION TERMINÉE")
    print("=" * 80)
    print("\nProchaine étape: Rebuild des patterns avec:")
    print("  cd football-live-prediction")
    print("  python3 build_critical_interval_recurrence.py")


if __name__ == '__main__':
    main()
