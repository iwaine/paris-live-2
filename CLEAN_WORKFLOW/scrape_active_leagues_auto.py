#!/usr/bin/env python3
"""
Scraper automatique pour championnat bulgare (adapté pour toutes ligues actives)
Stratégie en 2 étapes :
1. Extraire les codes équipes depuis formtable.asp
2. Scraper chaque équipe avec son code
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import time
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class BulgariaAutoScraper:
    BASE_URL = "https://www.soccerstats.com"
    DB_PATH = os.path.join(os.path.dirname(__file__), "data", "predictions.db")

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract_team_codes(self, league_code: str = "bulgaria") -> List[Tuple[str, str]]:
        url = f"{self.BASE_URL}/formtable.asp?league={league_code}"
        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='formtable')

        team_codes = []
        if table:
            rows = table.find_all('tr')[1:]  # Ignorer l'en-tête
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 1:
                    team_name = cols[1].text.strip()
                    team_link = cols[1].find('a')['href']
                    team_code = re.search(r'team=(\d+)', team_link)
                    if team_code:
                        team_codes.append((team_code.group(1), team_name))
        return team_codes

    def _extract_goals_from_tooltip(self, tooltip_html: str, team_is_home: bool) -> Tuple[List[int], List[int]]:
        # ...existing code...
        pass

    def scrape_team(self, league_code: str, team_code: str, team_name: str, 
                    country: str = "Bulgaria", league_display: str = "A PFG") -> Optional[List[dict]]:
        # ...existing code...
        pass

    def save_to_db(self, matches_data: List[dict]):
        # ...existing code...
        pass

    def run(self, league_code: str = "bulgaria", league_name: str = "Bulgaria", parallel_workers: int = 4):
        # ...existing code...
        pass

if __name__ == "__main__":
    import argparse
    import yaml
    import sqlite3
    parser = argparse.ArgumentParser()
    parser.add_argument('--league', default='all', help='League code or "all"')
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()

    # Fonction pour récupérer les ligues actives depuis leagues_dates.db
    def get_active_leagues():
        db_path = os.path.join(os.path.dirname(__file__), "data", "leagues_dates.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        try:
            c.execute("SELECT league FROM leagues_dates WHERE season_finished=0")
            leagues = [row[0] for row in c.fetchall()]
        except Exception as e:
            print(f"[ERREUR] Impossible de lire les ligues actives : {e}")
            leagues = []
        conn.close()
        return set(leagues)

    # Nettoyer UNIQUEMENT la ligue à scraper (pas tout)
    conn = sqlite3.connect(BulgariaAutoScraper.DB_PATH)
    cursor = conn.cursor()

    if args.league != 'all':
        cursor.execute("DELETE FROM soccerstats_scraped_matches WHERE league=?", (args.league,))
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ DB nettoyée pour {args.league} ({deleted} matchs supprimés)\n")
    else:
        print("⚠️  Mode 'all': conservation de toutes les données existantes\n")

    conn.close()

    # Lancer le scraping automatique
    scraper = BulgariaAutoScraper()

    if args.league == 'all':
        # Scraper toutes les ligues activées du fichier config.yaml (version CLEAN_WORKFLOW)
        config_path = '/workspaces/paris-live/CLEAN_WORKFLOW/config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        active_leagues = get_active_leagues()
        leagues = [(l['url'].split('=')[-1], l['name']) for l in config['leagues'] if l.get('enabled', True) and l['url'].split('=')[-1] in active_leagues]
        print(f"[INFO] Ligues actives détectées : {[code for code, _ in leagues]}")
        for code, name in leagues:
            print(f"\n\n{'='*80}")
            print(f"🌍 LIGUE: {name}")
            print(f"{'='*80}")
            scraper.run(league_code=code, league_name=name, parallel_workers=args.workers)
            print(f"\n✅ {name} terminé!")
    else:
        league_names = {l['url'].split('=')[-1]: l['name'] for l in yaml.safe_load(open('/workspaces/paris-live/CLEAN_WORKFLOW/config.yaml'))['leagues']}
        scraper.run(league_code=args.league, league_name=league_names.get(args.league, args.league.title()), parallel_workers=args.workers)
