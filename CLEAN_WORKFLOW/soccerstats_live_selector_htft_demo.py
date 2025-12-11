"""
Copie du workflow principal avec affichage des matches HT et FT
"""
import re
import requests
import sqlite3
import json
import time
import argparse
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

DEFAULT_URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (Match Detection)"}

# ...existing code...

def get_ht_ft_matches(soup):
    # Liste des ligues suivies (exemple, à adapter selon ta base)
    LEAGUES_TO_FOLLOW = ["ENGLAND2", "FRANCE", "GERMANY", "SPAIN", "ITALY"]
    results = []
    btable = soup.find("table", id="btable")
    if btable is not None:
        for tr in btable.find_all("tr"):
            tds = tr.find_all("td")
            league_name = None
            for td in tds:
                txt = td.get_text(strip=True)
                for lid in LEAGUES_TO_FOLLOW:
                    if lid in txt.replace(" ","").upper():
                        league_name = lid
                        break
            for status in ["FT", "HT"]:
                found = False
                for td in tds:
                    if status in td.get_text(strip=True):
                        found = True
                        break
                if found and len(tds) >= 4 and league_name:
                    # Extraction : <td>1 = home, <td>2 = score, <td>3 = away
                    score_match = re.search(r"(\d+)[:](\d+)", tds[2].get_text(strip=True))
                    if score_match:
                        results.append({
                            "status": status,
                            "league": league_name,
                            "home_team": tds[1].get_text(strip=True),
                            "score_home": score_match.group(1),
                            "score_away": score_match.group(2),
                            "away_team": tds[3].get_text(strip=True)
                        })
    return results

# ...existing code...

def main():
    r = requests.get(DEFAULT_URL, headers=UA, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Affichage des matches HT/FT
    ht_ft_matches = get_ht_ft_matches(soup)
    if ht_ft_matches:
        print("\n=== Matches à la mi-temps (HT) et terminés (FT) des ligues suivies ===")
        for m in ht_ft_matches:
            if m["status"] == "HT":
                print(f"{m['league']} | MI-TEMPS (HT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")
            elif m["status"] == "FT":
                print(f"{m['league']} | MATCH TERMINE (FT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")
    else:
        print("Aucun match HT ou FT détecté dans les ligues suivies.")
    # ...existing code pour affichage des matches live...

if __name__ == "__main__":
    main()
