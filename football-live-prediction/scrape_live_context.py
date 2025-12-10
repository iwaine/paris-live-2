#!/usr/bin/env python3
"""
Scraper contextualisé pour matches live
Scrape UNIQUEMENT les matches historiques dans le bon contexte:
- Team A (home): uniquement matches AT HOME
- Team B (away): uniquement matches AWAY

Critique pour récurrence précise!
"""

import requests
import re
import time
import sqlite3
import json
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Tuple
from datetime import datetime

class LiveContextScraper:
    """
    Scrape données historiques pour équipes d'un match live
    Respecte le contexte home/away
    """
    
    DEFAULT_THROTTLE = 3  # secondes (respect robots.txt)
    
    def __init__(self, db_path='data/predictions.db'):
        self.db_path = db_path
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "paris-live-bot/1.0 (Match Analysis)"
        })
    
    def _respect_throttle(self):
        """Attend si nécessaire pour respecter le throttling"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.DEFAULT_THROTTLE:
            time.sleep(self.DEFAULT_THROTTLE - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Télécharge une page avec throttling"""
        try:
            self._respect_throttle()
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def _find_team_id(self, league: str, team_name: str) -> Optional[str]:
        """
        Trouve le team_id depuis la page latest.asp
        
        Args:
            league: Nom de la ligue (ex: 'bulgaria')
            team_name: Nom de l'équipe (ex: 'Ludogorets')
        
        Returns:
            team_id (ex: 'u1502-ludogorets') ou None
        """
        url = f"https://www.soccerstats.com/latest.asp?league={league}"
        soup = self._fetch_page(url)
        
        if not soup:
            return None
        
        # Chercher lien vers teamstats contenant le nom de l'équipe
        team_name_lower = team_name.lower()
        
        for link in soup.find_all('a', href=re.compile(r'teamstats\.asp\?')):
            link_text = link.get_text(strip=True).lower()
            
            if team_name_lower in link_text:
                # Extraire stats=uXXXX-team-name
                href = link['href']
                match = re.search(r'stats=(u\d+-[^&]+)', href)
                if match:
                    return match.group(1)
        
        return None
    
    def _scrape_team_matches(self, league: str, team_id: str, is_home: int, 
                           max_matches: int = 50) -> List[Dict]:
        """
        Scrape matches d'une équipe dans un contexte spécifique
        
        Args:
            league: Ligue (ex: 'bulgaria')
            team_id: ID équipe (ex: 'u1502-ludogorets')
            is_home: 1 pour home, 0 pour away
            max_matches: Maximum de matches à scraper
        
        Returns:
            Liste de dicts avec données matches
        """
        url = f"https://www.soccerstats.com/teamstats.asp?league={league}&stats={team_id}"
        soup = self._fetch_page(url)
        
        if not soup:
            return []
        
        # Extraire nom équipe propre
        team_name = team_id.split('-', 1)[1] if '-' in team_id else team_id
        team_name = team_name.replace('-', ' ').title()
        
        matches = []
        context_name = "HOME" if is_home else "AWAY"
        
        # Parser toutes les tables de résultats
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue
                
                # Structure typique: Date | Opponent | Score | ...
                try:
                    date_cell = cells[0].get_text(strip=True)
                    opponent_cell = cells[1].get_text(strip=True)
                    score_cell = cells[2].get_text(strip=True)
                    
                    # Vérifier si c'est bien un match (date au format DD/MM)
                    if not re.match(r'\d{1,2}/\d{1,2}', date_cell):
                        continue
                    
                    # Parser score (ex: "2-1" ou "1:0")
                    score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', score_cell)
                    if not score_match:
                        continue
                    
                    score1 = int(score_match.group(1))
                    score2 = int(score_match.group(2))
                    
                    # Parser adversaire (enlever suffixes comme " -Autre Equipe")
                    opponent_parts = re.split(r'\s*-\s*', opponent_cell)
                    opponent = opponent_parts[0].strip() if opponent_parts else opponent_cell
                    
                    # Déterminer si c'est un match home ou away
                    # Heuristique: si opponent contient un préfixe (ex: "@"), c'est away
                    # Sinon: vérifier si team apparaît en premier dans le texte
                    match_is_home = 1  # Par défaut home
                    
                    if opponent.startswith('@'):
                        match_is_home = 0
                        opponent = opponent[1:].strip()
                    elif '-' in opponent_cell:
                        # Format "Team A -Team B": si Team A = team_name → home
                        parts = opponent_cell.split('-')
                        if len(parts) >= 2:
                            first_team = parts[0].strip().lower()
                            if team_name.lower() in first_team:
                                match_is_home = 1
                            else:
                                match_is_home = 0
                    
                    # FILTRE CRITIQUE: ne garder que contexte demandé
                    if match_is_home != is_home:
                        continue
                    
                    # Déterminer buts for/against
                    if match_is_home:
                        goals_for = score1
                        goals_against = score2
                    else:
                        goals_for = score2
                        goals_against = score1
                    
                    # Résultat
                    if goals_for > goals_against:
                        result = 'W'
                    elif goals_for < goals_against:
                        result = 'L'
                    else:
                        result = 'D'
                    
                    # Chercher goal_times (minutes des buts)
                    # Généralement dans colonnes suivantes ou liens
                    goal_times = []
                    for cell in cells[3:]:
                        cell_text = cell.get_text(strip=True)
                        # Chercher patterns comme "42'" ou "42,"
                        minutes = re.findall(r'(\d{1,3})[\'\,]', cell_text)
                        goal_times.extend([int(m) for m in minutes if 0 <= int(m) <= 120])
                    
                    match_data = {
                        'team': team_name,
                        'opponent': opponent,
                        'is_home': is_home,
                        'date': date_cell,
                        'score': f"{score1}-{score2}",
                        'goals_for': goals_for,
                        'goals_against': goals_against,
                        'result': result,
                        'goal_times': ','.join(map(str, goal_times)) if goal_times else None,
                        'league': league
                    }
                    
                    matches.append(match_data)
                    
                    if len(matches) >= max_matches:
                        break
                
                except (ValueError, IndexError, AttributeError):
                    continue
            
            if len(matches) >= max_matches:
                break
        
        print(f"   ✅ {team_name} ({context_name}): {len(matches)} matches")
        return matches
    
    def scrape_live_match_context(self, league: str, home_team: str, away_team: str,
                                  max_matches: int = 50) -> Tuple[List[Dict], List[Dict]]:
        """
        Scrape données contextualisées pour un match live
        
        Args:
            league: Ligue (ex: 'bulgaria')
            home_team: Équipe domicile
            away_team: Équipe extérieur
            max_matches: Max matches par équipe
        
        Returns:
            (home_matches, away_matches) - listes de dicts
        """
        print(f"\n🔍 Scraping contextualisé: {home_team} (HOME) vs {away_team} (AWAY)")
        print(f"📍 Ligue: {league}")
        
        # Trouver team_ids
        print(f"\n[1/4] Recherche team_id pour {home_team}...")
        home_team_id = self._find_team_id(league, home_team)
        if not home_team_id:
            print(f"❌ Team ID non trouvé pour {home_team}")
            return [], []
        print(f"   ✅ {home_team}: {home_team_id}")
        
        print(f"\n[2/4] Recherche team_id pour {away_team}...")
        away_team_id = self._find_team_id(league, away_team)
        if not away_team_id:
            print(f"❌ Team ID non trouvé pour {away_team}")
            return [], []
        print(f"   ✅ {away_team}: {away_team_id}")
        
        # Scraper contextes
        print(f"\n[3/4] Scraping {home_team} (HOME uniquement)...")
        home_matches = self._scrape_team_matches(league, home_team_id, is_home=1, max_matches=max_matches)
        
        print(f"\n[4/4] Scraping {away_team} (AWAY uniquement)...")
        away_matches = self._scrape_team_matches(league, away_team_id, is_home=0, max_matches=max_matches)
        
        return home_matches, away_matches
    
    def save_to_db(self, matches: List[Dict]):
        """Sauvegarde matches dans predictions.db"""
        if not matches:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        inserted = 0
        for m in matches:
            try:
                c.execute('''
                    INSERT OR IGNORE INTO soccerstats_scraped_matches
                    (team, opponent, is_home, date, score, goals_for, goals_against,
                     result, goal_times, league)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    m['team'], m['opponent'], m['is_home'], m['date'], m['score'],
                    m['goals_for'], m['goals_against'], m['result'], m['goal_times'], m['league']
                ))
                inserted += c.rowcount
            except sqlite3.Error as e:
                print(f"⚠️ Erreur insertion: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"💾 {inserted} matches insérés dans DB")
    
    def scrape_and_save(self, league: str, home_team: str, away_team: str):
        """Scrape et sauvegarde en une seule opération"""
        home_matches, away_matches = self.scrape_live_match_context(league, home_team, away_team)
        
        print(f"\n📊 RÉSUMÉ:")
        print(f"   • {home_team} (HOME): {len(home_matches)} matches")
        print(f"   • {away_team} (AWAY): {len(away_matches)} matches")
        
        all_matches = home_matches + away_matches
        
        if all_matches:
            self.save_to_db(all_matches)
        
        return len(all_matches)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 4:
        # Usage: python scrape_live_context.py league home_team away_team
        league = sys.argv[1]
        home_team = sys.argv[2]
        away_team = sys.argv[3]
        
        scraper = LiveContextScraper()
        scraper.scrape_and_save(league, home_team, away_team)
    
    else:
        # Test par défaut
        print("="*80)
        print("🎯 SCRAPER CONTEXTUALISÉ - LIVE MATCH")
        print("="*80)
        print("\nUsage: python scrape_live_context.py <league> <home_team> <away_team>")
        print("\nExemple:")
        print("  python scrape_live_context.py bulgaria Ludogorets Dobrudzha")
        print("\n" + "="*80)
