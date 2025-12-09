import sqlite3
import json
from collections import defaultdict

DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
LEAGUE = "france"
INTERVAL = (31, 90)  # 31-45+ (on considère 45+ comme <=90 pour la logique)
INTERVAL_LABEL = "31-45+"
TEAM = "Nice"
SIDE = "AWAY"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT team, opponent, is_home, goal_times, goal_times_conceded
    FROM soccerstats_scraped_matches
    WHERE league = ? AND team = ?
""", (LEAGUE, TEAM))

total_matches = 0
matches_with_goal = 0
match_details = []

for row in cursor.fetchall():
    team, opponent, is_home, goal_times, goal_times_conceded = row
    is_home = bool(is_home)
    if SIDE == "HOME" and not is_home:
        continue
    if SIDE == "AWAY" and is_home:
        continue
    try:
        goals = json.loads(goal_times) if goal_times else []
        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
    except Exception:
        goals, conceded = [], []
    buts_marques = sum(1 for m in goals if INTERVAL[0] <= m <= 45)
    buts_encaisses = sum(1 for m in conceded if INTERVAL[0] <= m <= 45)
    total_matches += 1
    if (buts_marques + buts_encaisses) > 0:
        matches_with_goal += 1
        match_details.append((opponent, buts_marques, buts_encaisses))

conn.close()

print(f"Nice AWAY {INTERVAL_LABEL} : {matches_with_goal} matchs avec but sur {total_matches}")
for opp, m, e in match_details:
    print(f"  vs {opp} : {m} marqués, {e} encaissés dans l'intervalle")
