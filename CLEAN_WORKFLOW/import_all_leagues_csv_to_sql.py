import pandas as pd
import sqlite3
import ast
from datetime import datetime
import glob
import os

# Dossier contenant tous les CSV par ligue
csv_dir = "CLEAN_WORKFLOW/data/"
# Pattern pour trouver tous les CSV de type predictions_xxx_only.csv
csv_pattern = os.path.join(csv_dir, "predictions_*_only.csv")

# Connexion à la base
conn = sqlite3.connect("CLEAN_WORKFLOW/data/predictions.db")
c = conn.cursor()

def safe_int(x):
    try:
        return int(x)
    except:
        return 0

def safe_str(x):
    return str(x) if pd.notnull(x) else ''

def safe_goal_times(x):
    if pd.isnull(x):
        return ''
    if isinstance(x, str) and x.startswith('['):
        try:
            l = ast.literal_eval(x)
            return ','.join(str(int(i)) for i in l if int(i) > 0)
        except:
            return ''
    return safe_str(x)

# Pour chaque CSV de type predictions_xxx_only.csv
for csv_path in glob.glob(csv_pattern):
    df = pd.read_csv(csv_path)
    # Déduire league_code et country à partir du premier match du CSV
    if len(df) == 0:
        continue
    league_code = safe_str(df.iloc[0]['league_code'])
    country = safe_str(df.iloc[0]['country'])
    # Vider la table pour cette ligue/pays
    c.execute("DELETE FROM soccerstats_scraped_matches WHERE league_code = ? AND country = ?", (league_code, country))
    conn.commit()
    # Insérer chaque ligne du CSV
    for _, row in df.iterrows():
        values = (
            None,  # id (auto)
            safe_str(row['country']),
            safe_str(row['league_code']),
            safe_str(row['league']),
            safe_str(row['league_display_name']),
            safe_str(row['team']),
            safe_str(row['opponent']),
            safe_str(row['date']),
            safe_int(row['is_home']),
            safe_str(row['score']),
            safe_int(row['goals_for']),
            safe_int(row['goals_against']),
            safe_goal_times(row['goal_times']),
            safe_goal_times(row['goal_times_conceded']),
            safe_str(row['match_id']),
            safe_str(row['ht_score']) if 'ht_score' in row else '',
            safe_str(row['url']) if 'url' in row else '',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        c.execute("INSERT INTO soccerstats_scraped_matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    print(f"Synchronisé : {os.path.basename(csv_path)} -> DB ({len(df)} lignes)")
    conn.commit()

conn.close()
print("Synchronisation automatique de tous les CSV terminée.")
