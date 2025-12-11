import pandas as pd
import sqlite3
import ast
from datetime import datetime

# Charger le CSV Bundesliga
csv_path = "CLEAN_WORKFLOW/data/predictions_bundesliga_only.csv"
df = pd.read_csv(csv_path)

# Adapter les colonnes pour la table SQL (mêmes noms et types)
def safe_int(x):
    try:
        return int(x)
    except:
        return 0

def safe_str(x):
    return str(x) if pd.notnull(x) else ''

def safe_goal_times(x):
    # Convertit la liste [12, 45, ...] en '12,45,...'
    if pd.isnull(x):
        return ''
    if isinstance(x, str) and x.startswith('['):
        try:
            l = ast.literal_eval(x)
            return ','.join(str(int(i)) for i in l if int(i) > 0)
        except:
            return ''
    return safe_str(x)

# Connexion à la base
conn = sqlite3.connect("CLEAN_WORKFLOW/data/predictions.db")
c = conn.cursor()

# Vider la table pour éviter les doublons
c.execute("DELETE FROM soccerstats_scraped_matches WHERE league_code = 'germany' AND country = 'Bulgaria'")
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

conn.commit()
conn.close()
print("Import Bundesliga CSV -> SQL terminé et synchronisé.")
