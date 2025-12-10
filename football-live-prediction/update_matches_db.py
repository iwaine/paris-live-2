import sqlite3
import json

DB_PATH = "data/production.db"
JSON_PATH = "data/team_matches.json"

def load_team_matches(json_path, team_names):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {team: data[team] for team in team_names if team in data}

def insert_matches(db_path, team_data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for team, info in team_data.items():
        for match in info["matches"]:
            home_team = team if match.get("is_home", True) else match.get("opponent")
            away_team = match.get("opponent") if match.get("is_home", True) else team
            cursor.execute("""
                INSERT INTO matches (home_team, away_team, league, match_date, final_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                home_team,
                away_team,
                "germany2",  # à adapter si besoin
                match.get("date"),
                match.get("score")
            ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    teams_to_update = ["Paderborn", "Elversberg"]
    team_data = load_team_matches(JSON_PATH, teams_to_update)
    insert_matches(DB_PATH, team_data)
    print("Historique Paderborn et Elversberg injecté dans la base matches.")
