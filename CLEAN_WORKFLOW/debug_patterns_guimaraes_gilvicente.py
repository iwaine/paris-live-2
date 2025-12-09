import sqlite3, json

INTERVAL = (75, 120)
LEAGUE = 'portugal'
TEAMS = ['Guimaraes', 'Gil Vicente']
SIDES = ['HOME', 'AWAY']

def normalize_team_name(name):
    return name.strip().lower().replace('.', '').replace('-', ' ').replace("'", '').replace('  ', ' ')

def debug_patterns(team, side):
    conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT team, goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league=? AND team=?", (LEAGUE, team))
    rows = cursor.fetchall()
    conn.close()
    print(f"\n=== {team} {side} {INTERVAL} ===")
    total_matches = 0
    matches_with_goal = 0
    buts_marques = 0
    buts_encaisses = 0
    for db_team, goal_times, goal_times_conceded, is_home in rows:
        if (side == 'HOME' and not is_home) or (side == 'AWAY' and is_home):
            continue
        total_matches += 1
        try:
            goals = json.loads(goal_times) if goal_times else []
            conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
        except Exception:
            goals, conceded = [], []
        buts_intervalle = [m for m in goals if INTERVAL[0] <= m <= INTERVAL[1]] + [m for m in conceded if INTERVAL[0] <= m <= INTERVAL[1]]
        n_marques = sum(1 for m in goals if INTERVAL[0] <= m <= INTERVAL[1])
        n_encaisses = sum(1 for m in conceded if INTERVAL[0] <= m <= INTERVAL[1])
        buts_marques += n_marques
        buts_encaisses += n_encaisses
        if buts_intervalle:
            matches_with_goal += 1
        print(f"Match: {db_team} | HOME={is_home} | Buts dans intervalle: {buts_intervalle} | Marqués: {n_marques} | Encaissés: {n_encaisses}")
    print(f"Total matches: {total_matches}")
    print(f"Matches avec but dans intervalle: {matches_with_goal}")
    print(f"Buts marqués: {buts_marques} | encaissés: {buts_encaisses}")
    if total_matches > 0:
        print(f"Récurrence: {matches_with_goal/total_matches*100:.1f}%")
    else:
        print("Aucun match historique trouvé.")

if __name__ == "__main__":
    for team in TEAMS:
        for side in SIDES:
            debug_patterns(team, side)
