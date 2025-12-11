def sem(x):
    return np.std(x, ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0

def iqr_q1(x):
    return np.percentile(x, 25) if len(x) > 0 else 0

def iqr_q3(x):
    return np.percentile(x, 75) if len(x) > 0 else 0

import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "predictions.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "recurrence_stats_export.csv")

def parse_minutes(s):
    """Transforme une chaîne '12,45,78' en liste d'entiers."""
    if not s or not isinstance(s, str):
        return []
    return [int(x) for x in s.split(',') if x.strip().isdigit()]

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT team, is_home, goal_times, goal_times_conceded FROM soccerstats_scraped_matches", conn)

df['Context'] = df['is_home'].apply(lambda x: 'HOME' if x else 'AWAY')
df['Goal_Minutes'] = df['goal_times'].apply(parse_minutes)
df['Conceded_Minutes'] = df['goal_times_conceded'].apply(parse_minutes)

results = []
for (team, context), group in df.groupby(['team', 'Context']):
    all_goal_minutes = sum(group['Goal_Minutes'], [])
    all_conceded_minutes = sum(group['Conceded_Minutes'], [])
    # Ajout de la logique Period : 1 (≤45), 2 (>45)
    for period in [1, 2]:
        if period == 1:
            period_goal_minutes = [m for m in all_goal_minutes if m <= 45]
            period_conceded_minutes = [m for m in all_conceded_minutes if m <= 45]
        else:
            period_goal_minutes = [m for m in all_goal_minutes if m > 45]
            period_conceded_minutes = [m for m in all_conceded_minutes if m > 45]
        total_matches = len(group)
        # Calcul du nombre de matches où au moins un but marqué/encaissé dans la période
        goal_match_count = 0
        conceded_match_count = 0
        match_with_goal_count = 0
        goal_count = 0
        conceded_count = 0
        for idx, row in group.iterrows():
            if period == 1:
                goals_in_period = [m for m in row['Goal_Minutes'] if m >= 31 and m <= 45]
                conceded_in_period = [m for m in row['Conceded_Minutes'] if m >= 31 and m <= 45]
            else:
                goals_in_period = [m for m in row['Goal_Minutes'] if m >= 75 and m <= 90]
                conceded_in_period = [m for m in row['Conceded_Minutes'] if m >= 75 and m <= 90]
            match_has_goal = (len(goals_in_period) > 0 or len(conceded_in_period) > 0)
            goal_count += len(goals_in_period)
            conceded_count += len(conceded_in_period)
            if match_has_goal:
                match_with_goal_count += 1
            if len(goals_in_period) > 0:
                goal_match_count += 1
            if len(conceded_in_period) > 0:
                conceded_match_count += 1
        # Statistiques diverses
        avg_minute = np.mean(period_goal_minutes) if period_goal_minutes else 0
        std_minute = np.std(period_goal_minutes, ddof=1) if len(period_goal_minutes) > 1 else 0
        sem_minute = std_minute / np.sqrt(len(period_goal_minutes)) if len(period_goal_minutes) > 1 else 0
        q1 = np.percentile(period_goal_minutes, 25) if period_goal_minutes else 0
        q3 = np.percentile(period_goal_minutes, 75) if period_goal_minutes else 0
        goals_scored_avg = goal_count / total_matches if total_matches else 0
        goals_scored_stdev = np.std([len([m for m in x if (m <= 45 if period == 1 else m > 45)]) for x in group['Goal_Minutes']], ddof=1) if total_matches > 1 else 0
        goals_conceded_avg = conceded_count / total_matches if total_matches else 0
        goals_conceded_stdev = np.std([len([m for m in x if (m <= 45 if period == 1 else m > 45)]) for x in group['Conceded_Minutes']], ddof=1) if total_matches > 1 else 0
        h1_goals_avg = h1_goals_stdev = h2_goals_avg = h2_goals_stdev = h1_conceded_avg = h1_conceded_stdev = h2_conceded_avg = h2_conceded_stdev = 0
        results.append({
            'Team': team,
            'Context': context,
            'Period': period,
            'Avg_Minute': avg_minute,
            'Std_Minute': std_minute,
            'SEM': sem_minute,
            'IQR_Q1': q1,
            'IQR_Q3': q3,
            'Goal_Count': goal_count,
            'Conceded_Count': conceded_count,
            'Total_Matches': total_matches,
            'Goal_Match_Count': goal_match_count,
            'Conceded_Match_Count': conceded_match_count,
            'Match_With_Goal_Count': match_with_goal_count,
            'Goals_Scored_Avg': goals_scored_avg,
            'Goals_Scored_Stdev': goals_scored_stdev,
            'Goals_Conceded_Avg': goals_conceded_avg,
            'Goals_Conceded_Stdev': goals_conceded_stdev,
            'H1_Goals_Avg': h1_goals_avg,
            'H1_Goals_Stdev': h1_goals_stdev,
            'H2_Goals_Avg': h2_goals_avg,
            'H2_Goals_Stdev': h2_goals_stdev,
            'H1_Conceded_Avg': h1_conceded_avg,
            'H1_Conceded_Stdev': h1_conceded_stdev,
            'H2_Conceded_Avg': h2_conceded_avg,
            'H2_Conceded_Stdev': h2_conceded_stdev
        })

out_df = pd.DataFrame(results)
out_df.to_csv(CSV_PATH, index=False)
print(f"Export terminé : {CSV_PATH} ({len(out_df)} lignes)")
conn.close()
