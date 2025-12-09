import csv
from collections import defaultdict

CSV_PATH = "football-live-prediction/historical_matches.csv"
LEAGUE = "Ligue 1"
INTERVALS = [(30, 45), (75, 90)]
INTERVAL_LABELS = { (30, 45): "31-45+", (75, 90): "75-90+" }

# Structure : {(team, side, interval): [buts_marques, buts_encaissés, nb_matchs]}
patterns = defaultdict(lambda: [0, 0, 0])

def parse_goal_minutes(goal_minutes):
    if not goal_minutes:
        return []
    if ',' in goal_minutes:
        return [int(m.strip().replace('+','')) for m in goal_minutes.split(',') if m.strip().isdigit() or m.strip().replace('+','').isdigit()]
    m = goal_minutes.strip().replace('+','')
    return [int(m)] if m.isdigit() else []

with open(CSV_PATH, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["league"] != LEAGUE:
            continue
        try:
            interval = (int(row["interval_start"]), int(row["interval_end"]))
        except ValueError:
            continue
        if interval not in INTERVALS:
            continue
        home = row["home_team"]
        away = row["away_team"]
        # On compte le match pour chaque équipe/intervalle/side
        patterns[(home, "HOME", interval)][2] += 1
        patterns[(away, "AWAY", interval)][2] += 1
        # Analyse des buts dans l'intervalle
        goal_minutes = parse_goal_minutes(row["goal_minutes"])
        home_goals = int(row["home_goals"])
        away_goals = int(row["away_goals"])
        # Attribution des buts marqués/encaissés
        for minute in goal_minutes:
            if interval[0] <= minute <= interval[1]:
                # On suppose que le nombre de buts = len(goal_minutes), et que le split home/away est fait par l'ordre (pas optimal, mais faute de mieux)
                # Pour chaque but, on attribue d'abord à home, puis à away si plus de buts
                # Mais on ne sait pas qui a marqué à quelle minute sans info supplémentaire
                # Donc on répartit selon le score final et le nombre de buts dans l'intervalle
                # On fait une estimation : si home_goals > away_goals, home a marqué plus, etc.
                # Mais ici, on ne peut pas faire mieux sans info minute/équipe
                pass  # On ne peut pas attribuer précisément sans info minute/équipe

# Affichage d'avertissement si attribution impossible
print("ATTENTION : Attribution précise home/away impossible sans info minute/équipe. Les patterns ne peuvent pas être exacts.")

# Génération du top patterns par intervalle (affichage du nombre de matches seulement)
for interval in INTERVALS:
    label = INTERVAL_LABELS[interval]
    print(f"\nIntervalle {label}")
    filtered = [ (k, v) for k, v in patterns.items() if k[2] == interval and v[2] >= 6 ]
    filtered.sort(key=lambda x: (x[1][2]), reverse=True)
    for i, ((team, side, _), (marques, encaisses, matchs)) in enumerate(filtered[:5], 1):
        print(f"{i}. {team} {side} {label} : {matchs} matches (buts non attribuables sans info minute/équipe)")

print("\nMEILLEURS PATTERNS (≥6 matches joués) :")
all_patterns = [ (k, v) for k, v in patterns.items() if v[2] >= 6 ]
all_patterns.sort(key=lambda x: (x[1][2]), reverse=True)
for i, ((team, side, interval), (marques, encaisses, matchs)) in enumerate(all_patterns[:5], 1):
    label = INTERVAL_LABELS.get(interval, f"{interval[0]}-{interval[1]}")
    print(f"{i}. {team} {side} {label} : {matchs} matches (buts non attribuables sans info minute/équipe)")
