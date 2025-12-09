import sqlite3
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python3 list_patterns_top_by_interval.py <league>")
    sys.exit(1)

league = sys.argv[1]
DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
INTERVALS = [(31, 45), (75, 120)]
INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = ?", (league,))
teams = [row[0] for row in cursor.fetchall()]

results = {interval: [] for interval in INTERVALS}

for team in teams:
    for side in ["HOME", "AWAY"]:
        for interval in INTERVALS:
            cursor.execute("""
                SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches
                WHERE league = ? AND team = ?
            """, (league, team))
            matchs = cursor.fetchall()
            total = 0
            avec_but = 0
            buts_marques = 0
            buts_encaisses = 0
            for goal_times, goal_times_conceded, is_home in matchs:
                if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                    continue
                try:
                    goals = json.loads(goal_times) if goal_times else []
                    conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                except Exception:
                    goals, conceded = [], []
                start, end = interval
                n_marques = sum(1 for m in goals if start <= m <= end)
                n_encaisses = sum(1 for m in conceded if start <= m <= end)
                buts_marques += n_marques
                buts_encaisses += n_encaisses
                total += 1
                if (n_marques + n_encaisses) > 0:
                    avec_but += 1
            if total > 0:
                recurrence = int(round(100 * avec_but / total))
                total_buts = buts_marques + buts_encaisses
                label = INTERVAL_LABELS[interval]
                results[interval].append({
                    "team": team,
                    "side": side,
                    "label": label,
                    "recurrence": recurrence,
                    "total_buts": total_buts,
                    "total": total,
                    "buts_marques": buts_marques,
                    "buts_encaisses": buts_encaisses
                })

for interval in INTERVALS:
    label = INTERVAL_LABELS[interval]
    print(f"\n--- TOP {label} ---")
    sorted_patterns = sorted(results[interval], key=lambda x: x["recurrence"], reverse=True)
    for p in sorted_patterns[:10]:
        print(f"{p['team']} {p['side']} {p['label']} : {p['recurrence']}% ({p['total_buts']} buts sur {p['total']} matches) - {p['buts_marques']} marqués + {p['buts_encaisses']} encaissés")

conn.close()
