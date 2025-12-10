import sqlite3
import json
import requests
from bs4 import BeautifulSoup
import re

DB_PATH = "data/production.db"
JSON_PATH = "data/team_matches.json"
LEAGUES_TO_FOLLOW = [
    "germany2", "england", "france", "italy", "spain", "netherlands", "portugal", "belgium"
]

# Exemple d'URL SoccerStats pour une équipe (à adapter selon la structure réelle)
TEAM_URL_TEMPLATE = "https://www.soccerstats.com/team.asp?league={league}&team={team}"

# Fonction pour scraper l'historique d'une équipe (à adapter selon la page cible)
def scrape_team_history(league, team):
    url = TEAM_URL_TEMPLATE.format(league=league, team=team.replace(' ', '-').lower())
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extraction simplifiée : à adapter selon la structure SoccerStats
        matches = []
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 5:
                opponent = cells[1].get_text(strip=True)
                score = cells[2].get_text(strip=True)
                date = cells[0].get_text(strip=True)
                is_home = 'home' in cells[3].get_text(strip=True).lower()
                result = cells[4].get_text(strip=True)
                matches.append({
                    "opponent": opponent,
                    "is_home": is_home,
                    "score": score,
                    "result": result,
                    "date": date
                })
        return matches
    except Exception as e:
        print(f"Erreur scraping {team} ({league}): {e}")
        return []

def enrich_json(json_path, leagues):
    from modules.get_teams_by_league import get_teams_by_league
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    for league in leagues:
        print(f"Scraping ligue {league}...")
        teams = get_teams_by_league(league)
        for team in teams:
            print(f"  - {team}")
            matches = scrape_team_history(league, team)
            if matches:
                data[team] = {
                    "team_id": f"{league}-{team}",
                    "matches": matches
                }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("team_matches.json enrichi.")

def insert_all_matches(db_path, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for team, info in data.items():
        for match in info["matches"]:
            home_team = team if match.get("is_home", True) else match.get("opponent")
            away_team = match.get("opponent") if match.get("is_home", True) else team
            cursor.execute("""
                INSERT OR IGNORE INTO matches (home_team, away_team, league, match_date, final_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                home_team,
                away_team,
                info["team_id"].split('-')[0],
                match.get("date"),
                match.get("score")
            ))
    conn.commit()
    conn.close()
    print("Base enrichie avec tous les historiques.")

if __name__ == "__main__":
    enrich_json(JSON_PATH, LEAGUES_TO_FOLLOW)
    insert_all_matches(DB_PATH, JSON_PATH)
