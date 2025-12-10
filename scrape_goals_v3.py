#!/usr/bin/env python3
"""
Scraper V3 - OPTIMISÉ avec retry + parallélisation
Parse le tableau complet des matches avec buts des 2 équipes
Extrait TOUS les buts (marqués + encaissés) depuis le tooltip
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Tuple

class GoalsScraperV3:
    """Scrape les buts marqués ET encaissés depuis le tableau HTML"""
    
    BASE_URL = "https://www.soccerstats.com"
    DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'paris-live-bot/3.0 (Match Analysis)'
        })
    
    def _extract_goals_from_tooltip(self, tooltip_html: str, team_is_home: bool) -> tuple:
        """
        Parse le HTML du tooltip pour extraire buts marqués et encaissés
        
        Format tooltip:
        <b>0-1</b> Joueur (13)  ← adversaire marque (away)
        <b>1-1</b> Joueur (50)  ← team marque (home)
        
        Args:
            tooltip_html: HTML du tooltip
            team_is_home: True si l'équipe est à domicile
        
        Returns:
            (goals_scored, goals_conceded) - listes de minutes
        """
        goals_scored = []
        goals_conceded = []
        
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
            # Structure: <font><br/><b>0-1</b> <font>Joueur (13)</font></font>
            parent = score_tag.parent
            if parent:
                parent_text = parent.get_text()
                minute_match = re.search(r'\((\d+)\)', parent_text)
                if minute_match:
                    minute = int(minute_match.group(1))
                    
                    # Déterminer qui a marqué en comparant avec le score précédent
                    if home_score > prev_home:
                        # But marqué par l'équipe à domicile
                        if team_is_home:
                            goals_scored.append(minute)
                        else:
                            goals_conceded.append(minute)
                    
                    elif away_score > prev_away:
                        # But marqué par l'équipe à l'extérieur
                        if not team_is_home:
                            goals_scored.append(minute)
                        else:
                            goals_conceded.append(minute)
                    
                    prev_home = home_score
                    prev_away = away_score
        
        return goals_scored, goals_conceded
    
    def scrape_team(self, country: str, league: str, league_code: str, 
                    team_slug: str, team_name: str, max_retries: int = 3) -> Optional[dict]:
        """
        Scrape tous les matches d'une équipe depuis le tableau HTML
        Avec retry automatique en cas d'erreur
        
        Args:
            country: Pays (Bulgaria)
            league: Nom affiché (A PFG)
            league_code: Code SoccerStats (bulgaria)
            team_slug: Slug URL (u1752-botev-vratsa)
            team_name: Nom équipe (Botev Vratsa)
            max_retries: Nombre de tentatives en cas d'erreur (défaut: 3)
        
        Returns:
            Dict avec matches et métadonnées, ou None si échec
        """
        url = f"{self.BASE_URL}/teamstats.asp?league={league_code}&stats={team_slug}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                time.sleep(3)  # Respecter robots.txt
                break  # Succès, sortir de la boucle retry
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Backoff progressif: 5s, 10s, 15s
                    print(f"    ⚠️ Erreur (tentative {attempt + 1}/{max_retries}): {e}")
                    print(f"    ⏳ Retry dans {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"    ❌ Échec définitif après {max_retries} tentatives: {e}")
                    return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le tableau des matches
        # Structure: <table cellspacing="0" cellpadding="0" bgcolor="#cccccc" width="100%">
        table = soup.find('table', {'bgcolor': '#cccccc', 'width': '100%'})
        
        if not table:
            print(f"    ❌ Tableau non trouvé pour {team_name}")
            return None
        
        matches_data = []
        
        # Parser chaque ligne de match (TOUTES les lignes sauf le header)
        all_rows = table.find_all('tr')
        rows = all_rows[1:] if len(all_rows) > 1 else all_rows  # Skip header row
        
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 9:
                    continue
                
                # Date
                date_cell = cells[0]
                date = date_cell.get_text().strip()
                
                # Équipe à domicile (celle à droite, alignée à droite)
                home_cell = cells[1]
                home_team_raw = home_cell.get_text().strip()
                
                # Équipe à l'extérieur (celle à gauche, alignée à gauche)
                away_cell = cells[3]
                away_team_raw = away_cell.get_text().strip()
                
                # Déterminer si team_name est HOME ou AWAY
                # L'équipe en gras <b> est celle de la ligne
                team_is_home = bool(home_cell.find('b'))
                
                # Nettoyer les noms
                home_team = home_team_raw.replace('\n', '').strip()
                away_team = away_team_raw.replace('\n', '').strip()
                
                # Score
                score_cell = cells[2]
                score_link = score_cell.find('a', class_='tooltip4')
                
                if not score_link:
                    continue
                
                score_text = score_link.find('font').get_text().strip()
                score = score_text.replace(' ', '')
                
                # Tooltip avec détails des buts
                tooltip_span = score_link.find('span')
                tooltip_html = str(tooltip_span) if tooltip_span else ""
                
                # Extraire buts marqués et encaissés
                goals_scored, goals_conceded = self._extract_goals_from_tooltip(
                    tooltip_html, team_is_home
                )
                
                # Déterminer opponent
                if team_is_home:
                    opponent = away_team
                else:
                    opponent = home_team
                
                # Score HT (mi-temps)
                ht_cell = cells[7]
                ht_score = ht_cell.get_text().strip()
                
                matches_data.append({
                    'country': country,
                    'league': league,
                    'league_code': league_code,
                    'team': team_name,
                    'opponent': opponent,
                    'date': date,
                    'is_home': team_is_home,
                    'score': score,
                    'ht_score': ht_score,
                    'goals_scored': goals_scored,
                    'goals_conceded': goals_conceded
                })
                
            except Exception as e:
                continue
        
        print(f"    ✅ {len(matches_data)} matches")
        
        return {
            'country': country,
            'league': league,
            'league_code': league_code,
            'team': team_name,
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
                inserted += cursor.rowcount
            except Exception as e:
                print(f"  ⚠️ Erreur insertion: {e}")
                continue
        
        conn.commit()
        conn.close()
        return inserted


def scrape_bulgaria(parallel_workers: int = 4):
    """
    Scrape les 16 équipes de Bulgarie - A PFG
    
    Args:
        parallel_workers: Nombre de scrapers parallèles (défaut: 4)
    """
    
    scraper = GoalsScraperV3()
    
    teams = [
        ('u1751-arda', 'Arda'),
        ('u1759-beroe', 'Beroe'),
        ('u1754-botev-plovdiv', 'Botev Plovdiv'),
        ('u1752-botev-vratsa', 'Botev Vratsa'),
        ('u1760-cska-1948-sofia', 'CSKA 1948 Sofia'),
        ('u1749-cska-sofia', 'CSKA Sofia'),
        ('u1757-cherno-more', 'Cherno More'),
        ('u1775-dobrudzha', 'Dobrudzha'),
        ('u1758-levski-sofia', 'Levski Sofia'),
        ('u3783-lok.-plovdiv', 'Lok. Plovdiv'),
        ('u1769-lokomotiv-sofia', 'Lokomotiv Sofia'),
        ('u1753-ludogorets', 'Ludogorets'),
        ('u1750-montana', 'Montana'),
        ('u1771-septemvri-sofia', 'Septemvri Sofia'),
        ('u1756-slavia-sofia', 'Slavia Sofia'),
        ('u5934-spartak-varna', 'Spartak Varna'),
    ]
    
    print("\n" + "="*80)
    print(f"🇧🇬 BULGARIE - A PFG (16 équipes, {parallel_workers} workers parallèles)")
    print("="*80)
    
    total_inserted = 0
    successful = 0
    failed = 0
    
    # Fonction wrapper pour ThreadPoolExecutor
    def scrape_and_save(team_info):
        team_slug, team_name = team_info
        print(f"  📥 {team_name}...")
        
        data = scraper.scrape_team(
            country='Bulgaria',
            league='A PFG',
            league_code='bulgaria',
            team_slug=team_slug,
            team_name=team_name,
            max_retries=3
        )
        
        if data:
            inserted = scraper.save_to_db(data)
            print(f"    ✅ {team_name}: {len(data['matches'])} matches → {inserted} insérés")
            return (True, inserted)
        else:
            print(f"    ❌ {team_name}: Échec")
            return (False, 0)
    
    # Scraping parallèle
    with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
        futures = {executor.submit(scrape_and_save, team): team for team in teams}
        
        for future in as_completed(futures):
            success, inserted = future.result()
            if success:
                successful += 1
                total_inserted += inserted
            else:
                failed += 1
    
    print(f"\n✅ Succès: {successful}/{len(teams)} équipes")
    if failed > 0:
        print(f"❌ Échecs: {failed}/{len(teams)} équipes")
    print(f"📊 Total: {total_inserted} lignes insérées")
    print("="*80)


if __name__ == '__main__':
    scrape_bulgaria()
