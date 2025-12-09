import sqlite3
import json
from collections import defaultdict

DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
LEAGUE = "france"
INTERVALS = [(31, 45), (75, 120)]
INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }

# Structure : {(team, side, interval): [buts_marques, buts_encaissés, nb_matchs, nb_matchs_avec_but]}
patterns = defaultdict(lambda: [0, 0, 0, 0])

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT team, opponent, is_home, goal_times, goal_times_conceded
    FROM soccerstats_scraped_matches
    WHERE league = ?
""", (LEAGUE,))

for row in cursor.fetchall():
    team, opponent, is_home, goal_times, goal_times_conceded = row
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
        patterns[(team, side, interval)][0] += buts_marques
        patterns[(team, side, interval)][1] += buts_encaisses
        patterns[(team, side, interval)][2] += 1
        # Récurrence : au moins 1 but (marqué ou encaissé) dans l'intervalle
        if (buts_marques + buts_encaisses) > 0:
            patterns[(team, side, interval)][3] += 1

conn.close()

# Génération du top patterns par intervalle (trié par récurrence)
for interval in INTERVALS:
    label = INTERVAL_LABELS[interval]
    print(f"\nIntervalle {label}")
    filtered = [ (k, v) for k, v in patterns.items() if k[2] == interval and v[3] > 0 and v[2] > 0 ]
    filtered.sort(key=lambda x: (x[1][3]/x[1][2], x[1][0]+x[1][1]), reverse=True)
    for i, ((team, side, _), (marques, encaisses, matchs, matchs_avec_but)) in enumerate(filtered[:5], 1):
        recurrence = int(round(100 * matchs_avec_but / matchs)) if matchs else 0
        print(f"{i}. {team} {side} {label} : {recurrence}% récurrence ({matchs_avec_but} matchs sur {matchs}) - {marques} marqués + {encaisses} encaissés")

print("\nMEILLEURS PATTERNS (≥6 matchs avec but) :")
all_patterns = [ (k, v) for k, v in patterns.items() if v[3] >= 6 ]
all_patterns.sort(key=lambda x: (x[1][3]/x[1][2], x[1][0]+x[1][1]), reverse=True)
for i, ((team, side, interval), (marques, encaisses, matchs, matchs_avec_but)) in enumerate(all_patterns[:5], 1):
    label = INTERVAL_LABELS.get(interval, f"{interval[0]}-{interval[1]}")
    recurrence = int(round(100 * matchs_avec_but / matchs)) if matchs else 0
    print(f"{i}. {team} {side} {label} : {recurrence}% récurrence ({matchs_avec_but} matchs sur {matchs}) - {marques} marqués + {encaisses} encaissés")
