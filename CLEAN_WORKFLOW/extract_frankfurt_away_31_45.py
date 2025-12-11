import pandas as pd
import ast

# Charger le CSV Bundesliga
csv_path = "CLEAN_WORKFLOW/data/predictions_bundesliga_only.csv"
df = pd.read_csv(csv_path)

# Filtrer E. Frankfurt AWAY
df_frankfurt_away = df[(df['team'] == 'E. Frankfurt') & (df['is_home'] == 0)]

print("Détail des buts E. Frankfurt AWAY (31-45) :")
total_goals_31_45 = 0
for idx, row in df_frankfurt_away.iterrows():
    date = row['date']
    opponent = row['opponent']
    score = row['score']
    # Conversion des listes de minutes
    goal_times = [int(x) for x in ast.literal_eval(row['goal_times']) if int(x) > 0]
    goals_31_45 = [m for m in goal_times if 31 <= m <= 45]
    total_goals_31_45 += len(goals_31_45)
    print(f"{date} vs {opponent} | Score: {score} | Buts 31-45: {goals_31_45}")
print(f"\nTotal buts marqués 31-45 (E. Frankfurt AWAY): {total_goals_31_45}")
