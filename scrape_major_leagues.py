#!/usr/bin/env python3
"""
Scraper automatique pour les ligues majeures
Basé sur la méthode Bulgaria (référence)

Ligues supportées:
- Ligue 1 (France)
- Premier League (England)
- La Liga (Spain)
- Serie A (Italy)
- Bundesliga (Germany)
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import time
from typing import List, Tuple, Optional
from datetime import datetime

class MajorLeaguesScraper:
    """Scraper pour les 5 ligues majeures européennes"""
    
    BASE_URL = "https://www.soccerstats.com"
    DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
    
    # Configuration des ligues (même format que Bulgaria)
    LEAGUES = {
        'france': {
            'code': 'france',
            'name': 'Ligue 1',
            'db_name': 'Ligue 1'
        },
        'england': {
            'code': 'england',
            'name': 'Premier League',
            'db_name': 'Premier League'
        },
        'spain': {
            'code': 'spain',
            'name': 'La Liga',
            'db_name': 'La Liga'
        },
        'italy': {
            'code': 'italy',
            'name': 'Serie A',
            'db_name': 'Serie A'
        },
        'germany': {
            'code': 'germany',
            'name': 'Bundesliga',
            'db_name': 'Bundesliga'
        }
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_team_codes(self, league_code: str) -> List[Tuple[str, str]]:
        """
        ÉTAPE 1 : Extraire tous les codes équipes depuis formtable.asp
        (Méthode Bulgaria référence)
        """
        url = f"{self.BASE_URL}/formtable.asp?league={league_code}"
        
        print(f"\n🔍 Extraction codes équipes : {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver tous les liens vers teamstats
            links = soup.find_all('a', href=re.compile(r'teamstats\.asp\?league=' + league_code + r'&stats=u\d+-'))
            
            teams = []
            for link in links:
                href = link.get('href')
                match = re.search(r'stats=(u\d+-[^&]+)', href)
                if match:
                    team_code = match.group(1)
                    team_name = link.get_text(strip=True)
                    teams.append((team_code, team_name))
            
            # Dédupliquer
            teams = sorted(set(teams), key=lambda x: x[1])
            
            print(f"   ✅ {len(teams)} équipes trouvées")
            
            return teams
            
        except Exception as e:
            print(f"   ❌ Erreur extraction : {e}")
            return []
    
    def _extract_goals_from_tooltip(self, tooltip_html: str, team_is_home: bool) -> Tuple[List[int], List[int]]:
        """Extraire buts marqués/encaissés depuis tooltip (méthode Bulgaria)"""
        goals_scored = []
        goals_conceded = []
        
        if not tooltip_html or 'span' not in tooltip_html.lower():
            return goals_scored, goals_conceded
        
        soup = BeautifulSoup(tooltip_html, 'html.parser')
        score_tags = soup.find_all('b')
        
        prev_home = 0
        prev_away = 0
        
        for score_tag in score_tags:
            score_text = score_tag.get_text(strip=True)
            match = re.match(r'(\d+)-(\d+)', score_text)
            
            if match:
                curr_home = int(match.group(1))
                curr_away = int(match.group(2))
                
                # Chercher la minute du but
                parent = score_tag.find_parent('span')
                if parent:
                    minute_match = re.search(r"(\d{1,3})['′]", parent.get_text())
                    if minute_match:
                        minute = int(minute_match.group(1))
                        
                        # Déterminer qui a marqué
                        if curr_home > prev_home:
                            if team_is_home:
                                goals_scored.append(minute)
                            else:
                                goals_conceded.append(minute)
                        elif curr_away > prev_away:
                            if team_is_home:
                                goals_conceded.append(minute)
                            else:
                                goals_scored.append(minute)
                
                prev_home = curr_home
                prev_away = curr_away
        
        return goals_scored, goals_conceded
    
    def scrape_team_matches(self, league_code: str, team_code: str, team_name: str, league_db_name: str) -> int:
        """
        ÉTAPE 2 : Scraper tous les matchs d'une équipe
        (Méthode Bulgaria référence)
        """
        url = f"{self.BASE_URL}/teamstats.asp?league={league_code}&stats={team_code}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver la table des résultats
            results_table = None
            for table in soup.find_all('table'):
                header = table.find('th', string=re.compile(r'.*Date.*'))
                if header:
                    results_table = table
                    break
            
            if not results_table:
                return 0
            
            matches_data = []
            rows = results_table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 5:
                    continue
                
                # Extraire la date
                date_cell = cells[0]
                date_match = re.search(r'(\d{1,2})\s+(\w+)', date_cell.get_text())
                if not date_match:
                    continue
                
                day = date_match.group(1)
                month_str = date_match.group(2)
                
                # Convertir mois
                months = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                month = months.get(month_str[:3], '01')
                match_date = f"{day} {month_str[:3]}"
                
                # Extraire H/A
                ha_cell = cells[1]
                is_home = 'H' in ha_cell.get_text()
                
                # Extraire adversaire
                opponent_cell = cells[2]
                opponent_link = opponent_cell.find('a')
                opponent = opponent_link.get_text(strip=True) if opponent_link else opponent_cell.get_text(strip=True)
                
                # Extraire score
                score_cell = cells[3]
                tooltip_span = score_cell.find('span', class_='tooltiptext')
                tooltip_html = str(tooltip_span) if tooltip_span else ''
                
                score_link = score_cell.find('a')
                if not score_link:
                    continue
                
                score_text = score_link.get_text(strip=True)
                score_match = re.match(r'(\d+)-(\d+)', score_text)
                if not score_match:
                    continue
                
                score_us = int(score_match.group(1))
                score_them = int(score_match.group(2))
                
                # Extraire buts avec tooltip
                goals_scored, goals_conceded = self._extract_goals_from_tooltip(tooltip_html, is_home)
                
                # Construire les données du match
                if is_home:
                    home_team = team_name
                    away_team = opponent
                    home_goals = score_us
                    away_goals = score_them
                    home_goal_times = goals_scored
                    away_goal_times = goals_conceded
                else:
                    home_team = opponent
                    away_team = team_name
                    home_goals = score_them
                    away_goals = score_us
                    home_goal_times = goals_conceded
                    away_goal_times = goals_scored
                
                matches_data.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'league': league_db_name,
                    'match_date': match_date,
                    'final_score': f"{home_goals}-{away_goals}",
                    'home_goals': home_goals,
                    'away_goals': away_goals,
                    'home_goal_times': json.dumps(home_goal_times),
                    'away_goal_times': json.dumps(away_goal_times)
                })
            
            # Sauvegarder en DB
            if matches_data:
                self._save_to_db(matches_data, team_name)
            
            return len(matches_data)
            
        except Exception as e:
            print(f"   ❌ Erreur scraping {team_name}: {e}")
            return 0
    
    def _save_to_db(self, matches_data: List[dict], team_name: str):
        """Sauvegarder les matchs en DB (méthode Bulgaria)"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier structure table
        cursor.execute("PRAGMA table_info(matches)")
        columns = [col[1] for col in cursor.fetchall()]
        has_goal_times = 'home_goal_times' in columns
        
        for match in matches_data:
            # Vérifier si existe déjà
            cursor.execute("""
                SELECT id FROM matches 
                WHERE home_team = ? AND away_team = ? AND match_date = ?
            """, (match['home_team'], match['away_team'], match['match_date']))
            
            existing = cursor.fetchone()
            
            if existing:
                # UPDATE
                if has_goal_times:
                    cursor.execute("""
                        UPDATE matches SET
                            league = ?,
                            final_score = ?,
                            home_goals = ?,
                            away_goals = ?,
                            home_goal_times = ?,
                            away_goal_times = ?
                        WHERE id = ?
                    """, (match['league'], match['final_score'], match['home_goals'],
                          match['away_goals'], match['home_goal_times'],
                          match['away_goal_times'], existing[0]))
                else:
                    cursor.execute("""
                        UPDATE matches SET
                            league = ?,
                            final_score = ?,
                            home_goals = ?,
                            away_goals = ?
                        WHERE id = ?
                    """, (match['league'], match['final_score'], match['home_goals'],
                          match['away_goals'], existing[0]))
            else:
                # INSERT
                if has_goal_times:
                    cursor.execute("""
                        INSERT INTO matches (home_team, away_team, league, match_date,
                                           final_score, home_goals, away_goals,
                                           home_goal_times, away_goal_times)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (match['home_team'], match['away_team'], match['league'],
                          match['match_date'], match['final_score'], match['home_goals'],
                          match['away_goals'], match['home_goal_times'], match['away_goal_times']))
                else:
                    cursor.execute("""
                        INSERT INTO matches (home_team, away_team, league, match_date,
                                           final_score, home_goals, away_goals)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (match['home_team'], match['away_team'], match['league'],
                          match['match_date'], match['final_score'], match['home_goals'],
                          match['away_goals']))
        
        conn.commit()
        conn.close()
    
    def scrape_league(self, league_key: str):
        """Scraper une ligue complète (méthode Bulgaria)"""
        league_info = self.LEAGUES.get(league_key)
        if not league_info:
            print(f"❌ Ligue inconnue: {league_key}")
            return
        
        print("\n" + "="*80)
        print(f"🏆 SCRAPING: {league_info['name']}")
        print("="*80)
        
        # ÉTAPE 1: Extraire codes équipes
        teams = self.extract_team_codes(league_info['code'])
        if not teams:
            print(f"❌ Aucune équipe trouvée pour {league_info['name']}")
            return
        
        # ÉTAPE 2: Scraper chaque équipe
        print(f"\n📊 Scraping de {len(teams)} équipes...")
        total_matches = 0
        
        for i, (team_code, team_name) in enumerate(teams, 1):
            print(f"\n[{i}/{len(teams)}] {team_name}...")
            nb_matches = self.scrape_team_matches(
                league_info['code'],
                team_code,
                team_name,
                league_info['db_name']
            )
            total_matches += nb_matches
            print(f"   ✅ {nb_matches} matchs")
            
            # Throttling (respect robots.txt)
            time.sleep(3)
        
        print(f"\n{'='*80}")
        print(f"✅ {league_info['name']}: {total_matches} matchs scrapés")
        print(f"{'='*80}")
    
    def scrape_all_leagues(self):
        """Scraper toutes les ligues majeures"""
        print("\n" + "="*80)
        print("🌍 SCRAPING DES 5 LIGUES MAJEURES EUROPÉENNES")
        print("="*80)
        
        start_time = time.time()
        
        for league_key in self.LEAGUES.keys():
            self.scrape_league(league_key)
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  Temps total: {elapsed/60:.1f} minutes")

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper ligues majeures (méthode Bulgaria)')
    parser.add_argument('--league', choices=['france', 'england', 'spain', 'italy', 'germany', 'all'],
                       default='all', help='Ligue à scraper')
    
    args = parser.parse_args()
    
    scraper = MajorLeaguesScraper()
    
    if args.league == 'all':
        scraper.scrape_all_leagues()
    else:
        scraper.scrape_league(args.league)

if __name__ == '__main__':
    main()
