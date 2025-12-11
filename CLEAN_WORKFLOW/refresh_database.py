#!/usr/bin/env python3
"""
Script de (re)création de la base SoccerStats pour le workflow CLEAN_WORKFLOW.
- Télécharge les données SoccerStats pour les ligues suivies
- Remplit la base SQLite predictions.db dans CLEAN_WORKFLOW/data/
- À lancer au moins une fois par semaine pour garantir la fraîcheur des analyses

Usage :
    python3 refresh_database.py
"""
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "predictions.db")
LEAGUES = []  # Placeholder for leagues, will be populated from the database

# Charger la liste des ligues actives depuis leagues_dates.db
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
    return leagues
# Table cible : soccerstats_scraped_matches
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS soccerstats_scraped_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league TEXT,
    team TEXT,
    goal_times TEXT,
    goal_times_conceded TEXT,
    is_home INTEGER
);
"""

SOCCERSTATS_URL = "https://www.soccerstats.com/latest.asp?league={league}"


def fetch_and_parse_league(league):
    url = SOCCERSTATS_URL.format(league=league)
    r = requests.get(url, headers={"User-Agent": "paris-live-bot/1.0"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Extraction simplifiée : à adapter selon la structure réelle
    matches = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue
        # Extraction naïve, à adapter selon la page
        home_team = tds[1].get_text(strip=True)
        away_team = tds[3].get_text(strip=True)
        # Buts marqués/encaissés (extraction fictive)
        goal_times_home = []  # À extraire selon la page
        goal_times_away = []
        # ...
        # Pour l'exemple, on stocke des listes vides
        matches.append({
            "league": league,
            "team": home_team,
            "goal_times": json.dumps(goal_times_home),
            "goal_times_conceded": json.dumps(goal_times_away),
            "is_home": 1
        })
        matches.append({
            "league": league,
            "team": away_team,
            "goal_times": json.dumps(goal_times_away),
            "goal_times_conceded": json.dumps(goal_times_home),
            "is_home": 0
        })
    return matches

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(CREATE_TABLE)
    c.execute("DELETE FROM soccerstats_scraped_matches")
    total = 0
    active_leagues = get_active_leagues()
    print(f"[INFO] Ligues actives détectées : {active_leagues}")
    for league in active_leagues:
        print(f"[INFO] Téléchargement et parsing de la ligue : {league}")
        matches = fetch_and_parse_league(league)
        for m in matches:
            c.execute("""
                INSERT INTO soccerstats_scraped_matches (league, team, goal_times, goal_times_conceded, is_home)
                VALUES (?, ?, ?, ?, ?)
            """, (m["league"], m["team"], m["goal_times"], m["goal_times_conceded"], m["is_home"]))
        total += len(matches)
    conn.commit()
    conn.close()
    print(f"[OK] Base de données régénérée avec {total} entrées.")

if __name__ == "__main__":
    main()
