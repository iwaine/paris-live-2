import sqlite3
import json

DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
INTERVALS = [(31, 45), (75, 120)]
INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT league FROM soccerstats_scraped_matches ORDER BY league;")
leagues = [row[0] for row in cursor.fetchall()]

for league in leagues:
    print(f"\n================= {league.upper()} =================")
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
                # On trie les matchs du plus récent au plus ancien si possible (supposé que l'ordre d'insertion est chronologique)
                matchs = list(matchs)[-50:]  # sécurité, on ne garde que les 50 derniers au cas où
                total = 0
                avec_but = 0
                buts_marques = 0
                buts_encaisses = 0
                recent_windows = [3, 4, 5]
                recents = {}
                for w in recent_windows:
                    recent_total = 0
                    recent_avec_but = 0
                    for idx, (goal_times, goal_times_conceded, is_home) in enumerate(reversed(matchs)):
                        if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                            continue
                        if recent_total < w:
                            try:
                                goals = json.loads(goal_times) if goal_times else []
                                conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                            except Exception:
                                goals, conceded = [], []
                            start, end = interval
                            n_marques = sum(1 for m in goals if start <= m <= end)
                            n_encaisses = sum(1 for m in conceded if start <= m <= end)
                            if (n_marques + n_encaisses) > 0:
                                recent_avec_but += 1
                            recent_total += 1
                    recents[w] = int(round(100 * recent_avec_but / recent_total)) if recent_total > 0 else 0
                # On garde la fenêtre qui maximise la différence absolue avec la globale (plus discriminante)
                if total > 0:
                    recurrence = int(round(100 * avec_but / total))
                    # Choix : la fenêtre qui s'écarte le plus de la globale (pour la prise de décision)
                    best_w = max(recents, key=lambda w: abs(recents[w] - recurrence))
                    recurrence_recent = recents[best_w]
                    score_moyen = int(round((recurrence + recurrence_recent) / 2))
                    total_buts = buts_marques + buts_encaisses
                    label = INTERVAL_LABELS[interval]
                    results[interval].append({
                        "team": team,
                        "side": side,
                        "label": label,
                        "recurrence": recurrence,
                        "recurrence_recent": recurrence_recent,
                        "score_moyen": score_moyen,
                        "recent_window": best_w,
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


# --- GLOBAL TOP ---
print("\n================= GLOBAL TOP =================")
global_patterns = []
for league in leagues:
    cursor.execute("SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = ?", (league,))
    teams = [row[0] for row in cursor.fetchall()]
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
                recent_windows = [3, 4, 5]
                recents = {}
                matchs_list = list(matchs)[-50:]
                for w in recent_windows:
                    recent_total = 0
                    recent_avec_but = 0
                    for idx, (goal_times, goal_times_conceded, is_home) in enumerate(reversed(matchs_list)):
                        if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                            continue
                        if recent_total < w:
                            try:
                                goals = json.loads(goal_times) if goal_times else []
                                conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                            except Exception:
                                goals, conceded = [], []
                            start, end = interval
                            n_marques = sum(1 for m in goals if start <= m <= end)
                            n_encaisses = sum(1 for m in conceded if start <= m <= end)
                            if (n_marques + n_encaisses) > 0:
                                recent_avec_but += 1
                            recent_total += 1
                    recents[w] = int(round(100 * recent_avec_but / recent_total)) if recent_total > 0 else 0
                for goal_times, goal_times_conceded, is_home in matchs_list:
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
                    best_w = max(recents, key=lambda w: abs(recents[w] - recurrence))
                    recurrence_recent = recents[best_w]
                    score_moyen = int(round((recurrence + recurrence_recent) / 2))
                    total_buts = buts_marques + buts_encaisses
                    label = INTERVAL_LABELS[interval]
                    global_patterns.append({
                        "team": team,
                        "side": side,
                        "label": label,
                        "recurrence": recurrence,
                        "recurrence_recent": recurrence_recent,
                        "score_moyen": score_moyen,
                        "recent_window": best_w,
                        "total_buts": total_buts,
                        "total": total,
                        "buts_marques": buts_marques,
                        "buts_encaisses": buts_encaisses
                    })

global_patterns_sorted = sorted(global_patterns, key=lambda x: x["recurrence"], reverse=True)

# --- TOP 10 GLOBAL PAR INTERVALLE ---
for interval in INTERVALS:
    label = INTERVAL_LABELS[interval]
    print(f"\n--- TOP 10 GLOBAL {label} ---")
    patterns_interval = [p for p in global_patterns if p["label"] == label and p["total"] >= 5]
    patterns_interval_sorted = sorted(patterns_interval, key=lambda x: x["score_moyen"], reverse=True)
    for p in patterns_interval_sorted[:10]:
        print(f"{p['team']} {p['side']} {p['label']} : {p['recurrence']}% (global) | {p['recurrence_recent']}% ({p['recent_window']} derniers) | SCORE {p['score_moyen']}%  ({p['total_buts']} buts sur {p['total']} matches) - {p['buts_marques']} marqués + {p['buts_encaisses']} encaissés")

conn.close()
