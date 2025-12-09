import sqlite3
import sys

if len(sys.argv) < 2:
    print("Usage: python3 list_teams_in_league.py <league>")
    sys.exit(1)

league = sys.argv[1]
DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = ?", (league,))
teams = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"Équipes présentes dans la ligue '{league}' :")
for t in teams:
    print(f"- {t}")
