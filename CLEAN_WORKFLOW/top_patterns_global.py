import sqlite3
import json
from collections import defaultdict

def top_patterns_global(n=20):
    DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
    INTERVALS = [(31, 45), (75, 120)]
    INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }
    patterns = defaultdict(lambda: ["", "", 0, 0, 0, 0])  # league, team, side, buts_marques, encaisses, matchs, matchs_avec_but
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT league, team, is_home, goal_times, goal_times_conceded FROM soccerstats_scraped_matches")
    for row in cursor.fetchall():
        league, team, is_home, goal_times, goal_times_conceded = row
        is_home = bool(is_home)
        try:
            goals = json.loads(goal_times) if goal_times else []
            conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
        except Exception:
            goals, conceded = [], []
        for interval in INTERVALS:
            start, end = interval
            buts_marques = sum(1 for m in goals if start <= m <= end)
            buts_encaisses = sum(1 for m in conceded if start <= m <= end)
            side = "HOME" if is_home else "AWAY"
            key = (league, team, side, interval)
            if key not in patterns:
                patterns[key] = [league, team, side, interval, 0, 0, 0, 0]  # league, team, side, interval, buts_marques, encaisses, matchs, matchs_avec_but
            patterns[key][4] += buts_marques
            patterns[key][5] += buts_encaisses
            patterns[key][6] += 1
            if (buts_marques + buts_encaisses) > 0:
                patterns[key][7] += 1
    conn.close()
    for interval in INTERVALS:
        label = INTERVAL_LABELS[interval]
        print(f"\nTop {n} patterns toutes ligues - Intervalle {label}")
        filtered = [v for v in patterns.values() if v[3] == interval and v[6] >= 5]
        filtered.sort(key=lambda x: (x[7]/x[6], x[4]+x[5]), reverse=True)
        for i, (league, team, side, interval, marques, encaisses, matchs, matchs_avec_but) in enumerate(filtered[:n], 1):
            recurrence = int(round(100 * matchs_avec_but / matchs)) if matchs else 0
            print(f"{i}. [{league}] {team} {side} {label} : {recurrence}% récurrence ({matchs_avec_but} matchs sur {matchs}) - {marques} marqués + {encaisses} encaissés")

if __name__ == "__main__":
    top_patterns_global(n=20)
