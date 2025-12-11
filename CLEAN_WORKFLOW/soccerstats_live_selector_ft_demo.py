"""
Version modifiée du script soccerstats_live_selector.py
Correction : détection explicite du statut FT (Full Time) dans le scraping détaillé
- Exclut les matches FT dans l'affichage détaillé
- Affiche 'FT' au lieu de '90' si le match est terminé
- Affiche le score réel
"""

import re
import requests
import sqlite3
import json
from bs4 import BeautifulSoup
import argparse
import time

DEFAULT_URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (Match Detection)"}

def get_match_status_and_score(match_url):
    """
    Scrape le statut (FT, HT, minute) et le score réel depuis la page du match
    """
    r = requests.get(match_url, headers=UA, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Cherche la minute ou le statut dans les balises <font> ou <td>
    status = None
    minute = None
    score_home = None
    score_away = None
    home_team = None
    away_team = None
    # Cherche FT ou Full Time
    for font in soup.find_all("font"):
        txt = font.get_text(" ", strip=True)
        if re.search(r"FT|Full Time", txt, re.I):
            status = "FT"
            break
        m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*('|min)", txt)
        if m:
            minute = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
    # Cherche le score et les équipes
    score_block = soup.find("td", attrs={"class": "score"})
    if score_block:
        score_txt = score_block.get_text(" ", strip=True)
        m = re.search(r"(\d+)\s*[-:]\s*(\d+)", score_txt)
        if m:
            score_home = int(m.group(1))
            score_away = int(m.group(2))
    # Cherche les noms d'équipes
    team_blocks = soup.find_all("td", attrs={"class": "team"})
    if len(team_blocks) >= 2:
        home_team = team_blocks[0].get_text(" ", strip=True)
        away_team = team_blocks[1].get_text(" ", strip=True)
    return {
        "status": status,
        "minute": minute,
        "score_home": score_home,
        "score_away": score_away,
        "home_team": home_team,
        "away_team": away_team
    }

def main():
    parser = argparse.ArgumentParser(description="Détecte les matches live SoccerStats avec correction FT.")
    parser.add_argument("--url", help="URL du match à vérifier", required=True)
    args = parser.parse_args()
    match_info = get_match_status_and_score(args.url)
    if match_info["status"] == "FT":
        print(f"MATCH TERMINE (FT) : {match_info['home_team']} {match_info['score_home']} – {match_info['score_away']} {match_info['away_team']}")
    else:
        minute = match_info["minute"] if match_info["minute"] else "?"
        print(f"MATCH EN COURS : {match_info['home_team']} {match_info['score_home']} – {match_info['score_away']} {match_info['away_team']} | minute : {minute}")

if __name__ == "__main__":
    main()
