import sqlite3
import pandas as pd

DB_PATH = "data/predictions.db"
LEAGUE_DATES_DB = "data/leagues_dates.db"
N_RECENT = 4  # Nombre de matchs récents à analyser
INTERVALS = {
    '31-45': [str(i) for i in range(31, 46)],
    '75-90': [str(i) for i in range(75, 91)]
}

def get_active_leagues():
    conn = sqlite3.connect(LEAGUE_DATES_DB)
    c = conn.cursor()
    c.execute("SELECT league FROM leagues_dates WHERE season_finished=0")
    leagues = [row[0] for row in c.fetchall()]
    conn.close()
    return set(leagues)

def has_goal_in_interval(goal_times, interval_minutes):
    if not goal_times:
        return False
    return any(minute in goal_times for minute in interval_minutes)

def compute_recent_recurrence(df, interval_key):
    results = []
    for (league, team, is_home), group in df.groupby(['league', 'team', 'is_home']):
        # Conversion date en datetime pour tri correct (format 'jour mois' => 'jour mois année')
        import re, datetime
        group = group.copy()
        current_year = datetime.datetime.now().year
        def add_year_if_missing(date_str):
            if re.match(r"^\d{1,2} [A-Za-zéû]+$", str(date_str).strip()):
                return f"{date_str} {current_year}"
            return date_str
        group['date_for_parse'] = group['date'].apply(add_year_if_missing)
        group['date_dt'] = pd.to_datetime(group['date_for_parse'], errors='coerce', dayfirst=True)
        group_sorted = group.sort_values('date_dt', ascending=False).head(N_RECENT)
        n_matches = len(group_sorted)
        n_recurrence = 0
        buts_marques = 0
        buts_encaisses = 0
        for _, row in group_sorted.iterrows():
            import json
            try:
                goals = json.loads(row.get('goal_times', '[]')) if row.get('goal_times', '') else []
                conceded = json.loads(row.get('goal_times_conceded', '[]')) if row.get('goal_times_conceded', '') else []
            except Exception:
                goals, conceded = [], []
            if isinstance(goals, int):
                goals = [goals]
            if isinstance(conceded, int):
                conceded = [conceded]
            if not isinstance(goals, list):
                goals = []
            if not isinstance(conceded, list):
                conceded = []
            if interval_key == '31-45':
                start, end = 31, 45
            elif interval_key == '75-90':
                start, end = 75, 90
            else:
                start, end = 0, 0
            buts_marques_match = sum(1 for m in goals if isinstance(m, (int, float)) and start <= m <= end)
            buts_encaisses_match = sum(1 for m in conceded if isinstance(m, (int, float)) and start <= m <= end)
            if (buts_marques_match + buts_encaisses_match) > 0:
                n_recurrence += 1
            buts_marques += buts_marques_match
            buts_encaisses += buts_encaisses_match
        rec_pct = (n_recurrence / n_matches * 100) if n_matches else 0
        results.append({
            'league': league,
            'team': team,
            'is_home': is_home,
            'n_matches': n_matches,
            'recurrence_recent': round(rec_pct, 1),
            'n_recurrence': n_recurrence,
            'buts_marques': buts_marques,
            'buts_encaisses': buts_encaisses
        })
    return pd.DataFrame(results)

def main():
    active_leagues = get_active_leagues()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT league, team, is_home, date, goal_times, goal_times_conceded FROM soccerstats_scraped_matches", conn)
    conn.close()
    df = df[df['league'].isin(active_leagues)]
    for interval_key in INTERVALS:
        print(f"\n--- Top récurrence récente {interval_key} (sur {N_RECENT} derniers matchs, ligues en cours) ---")
        df_rec = compute_recent_recurrence(df, interval_key)
        top = df_rec[df_rec['n_matches'] >= 4].sort_values('recurrence_recent', ascending=False).head(20)
        for _, row in top.iterrows():
            print(f"{row['team']} {'HOME' if row['is_home'] else 'AWAY'} {interval_key} : {row['recurrence_recent']}% ({row['buts_marques']} buts sur {row['n_recurrence']} matches / {row['n_matches']}) - {row['buts_marques']} marqués + {row['buts_encaisses']} encaissés")

if __name__ == "__main__":
    main()
