"""
Script de démonstration pour la détection FT sur England Championship
Affiche le statut et le score réel pour chaque match listé
"""

import re
import requests
import sqlite3
import json
from bs4 import BeautifulSoup
import argparse
import time

DEFAULT_URL = "https://www.soccerstats.com/latest.asp?league=england2"
UA = {"User-Agent": "paris-live-bot/1.0 (Match Detection)"}

def get_ft_matches(index_url=DEFAULT_URL):
    r = requests.get(index_url, headers=UA, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    # Cherche les lignes de match avec FT
    for tr in soup.find_all("tr"):
        txt = tr.get_text(" ", strip=True)
        if re.search(r"FT", txt):
            # Cherche le score et les équipes
            m = re.search(r"([A-Za-z .']+)\s+(\d+)\s*[-:]\s*(\d+)\s+([A-Za-z .']+)", txt)
            if m:
                home_team = m.group(1).strip()
                score_home = m.group(2)
                score_away = m.group(3)
                away_team = m.group(4).strip()
                results.append({
                    "status": "FT",
                    "home_team": home_team,
                    "score_home": score_home,
                    "score_away": score_away,
                    "away_team": away_team
                })
            else:
                # Format alternatif : FT Bristol City 2:2 Leicester City
                m2 = re.search(r"FT\s+([A-Za-z .']+)\s+(\d+)[:](\d+)\s+([A-Za-z .']+)", txt)
                if m2:
                    home_team = m2.group(1).strip()
                    score_home = m2.group(2)
                    score_away = m2.group(3)
                    away_team = m2.group(4).strip()
                    results.append({
                        "status": "FT",
                        "home_team": home_team,
                        "score_home": score_home,
                        "score_away": score_away,
                        "away_team": away_team
                    })
    return results

def main():
    matches = get_ft_matches()
    if not matches:
        print("Aucun match FT trouvé.")
    else:
        for m in matches:
            print(f"MATCH TERMINE (FT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")

if __name__ == "__main__":
    main()
