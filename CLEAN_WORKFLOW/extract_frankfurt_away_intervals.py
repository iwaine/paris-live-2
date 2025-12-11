import pandas as pd
import ast

# Charger le CSV Bundesliga
csv_path = "CLEAN_WORKFLOW/data/predictions_bundesliga_only.csv"
df = pd.read_csv(csv_path)

# Filtrer E. Frankfurt AWAY
frankfurt_away = df[(df['team'] == 'E. Frankfurt') & (df['is_home'] == 0)]

print("Détail E. Frankfurt AWAY :")
for idx, row in frankfurt_away.iterrows():
    date = row['date']
    opponent = row['opponent']
    score = row['score']
    # Conversion des listes de minutes
    goal_times = [int(x) for x in ast.literal_eval(row['goal_times']) if int(x) > 0]
    conceded_times = [int(x) for x in ast.literal_eval(row['goal_times_conceded']) if int(x) > 0]
    # 31-45
    goals_31_45 = [m for m in goal_times if 31 <= m <= 45]
    conceded_31_45 = [m for m in conceded_times if 31 <= m <= 45]
    # 75-90
    goals_75_90 = [m for m in goal_times if 75 <= m <= 90]
    conceded_75_90 = [m for m in conceded_times if 75 <= m <= 90]
    print(f"{date} vs {opponent} | Score: {score}")
    print(f"  31-45: marqués {goals_31_45}, encaissés {conceded_31_45}")
    print(f"  75-90: marqués {goals_75_90}, encaissés {conceded_75_90}")
    print()
