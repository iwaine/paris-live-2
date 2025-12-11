import pandas as pd
import ast
import sqlite3

# Charger le CSV Bundesliga
csv_path = "CLEAN_WORKFLOW/data/predictions_bundesliga_only.csv"
df_csv = pd.read_csv(csv_path)
frankfurt_csv = df_csv[(df_csv['team'] == 'E. Frankfurt') & (df_csv['is_home'] == 0)]

def extract_goals_31_45(goal_times_col):
    return sum([1 for m in ast.literal_eval(goal_times_col) if isinstance(m, int) and 31 <= m <= 45])

total_csv = frankfurt_csv['goal_times'].apply(extract_goals_31_45).sum()

# Charger la base SQLite
conn = sqlite3.connect("CLEAN_WORKFLOW/data/predictions.db")
df_db = pd.read_sql_query("SELECT * FROM soccerstats_scraped_matches WHERE team = 'E. Frankfurt' AND is_home = 0", conn)
conn.close()

def parse_minutes(s):
    if not s or not isinstance(s, str):
        return []
    return [int(x) for x in s.split(',') if x.strip().isdigit()]

df_db['Goal_Minutes'] = df_db['goal_times'].apply(parse_minutes)
total_db = sum([1 for row in df_db['Goal_Minutes'] for m in row if 31 <= m <= 45])

print(f"Total buts 31-45 E. Frankfurt AWAY (CSV): {total_csv}")
print(f"Total buts 31-45 E. Frankfurt AWAY (DB):  {total_db}")
print(f"Nb matches CSV: {len(frankfurt_csv)} | Nb matches DB: {len(df_db)}")
