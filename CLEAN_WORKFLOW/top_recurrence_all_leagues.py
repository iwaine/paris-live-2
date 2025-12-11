

import os
import pandas as pd
import sqlite3

LEAGUE_DATES_DB = os.path.join(os.path.dirname(__file__), "leagues_dates.db")

def get_active_leagues():
    conn = sqlite3.connect(LEAGUE_DATES_DB)
    c = conn.cursor()
    c.execute("SELECT league FROM leagues_dates WHERE season_finished=0")
    leagues = [row[0] for row in c.fetchall()]
    conn.close()
    return set(leagues)

# Charger le fichier CSV (chemin relatif à CLEAN_WORKFLOW)
csv_path = os.path.join(os.path.dirname(__file__), "data", "recurrence_stats_export.csv")
df = pd.read_csv(csv_path)

# Nettoyage des doublons (équipe/contexte/période)
df = df.drop_duplicates(subset=["Team", "Context", "Period"])

# Filtrage par ligue active (colonne 'League' ou 'league' selon export)
active_leagues = get_active_leagues()
if 'League' in df.columns:
    df = df[df['League'].str.lower().isin([l.lower() for l in active_leagues])]
elif 'league' in df.columns:
    df = df[df['league'].str.lower().isin([l.lower() for l in active_leagues])]

def get_top(df, period, top_n=10):
    dff = df[df["Period"] == period].copy()
    # Pourcentage = (matches avec but dans l'intervalle) / (total matches)
    dff["Recurrence"] = dff["Match_With_Goal_Count"] / dff["Total_Matches"]
    dff["Total_Buts"] = dff["Goal_Count"] + dff["Conceded_Count"]
    dff = dff[dff["Total_Matches"] >= 5]
    dff = dff.sort_values("Recurrence", ascending=False)
    return dff.head(top_n)

def print_top_formatted(df, period_label, top_n=10):
    print(f"\nMEILLEURS PATTERNS {period_label} (≥5 matches) :")
    for i, row in enumerate(df.itertuples(), 1):
        team = row.Team
        context = row.Context
        total_matches = int(row.Total_Matches)
        match_with_goal_count = int(row.Match_With_Goal_Count)
        recurrence = round(100 * (match_with_goal_count / total_matches), 1) if total_matches else 0
        total_buts = int(row.Goal_Count) + int(row.Conceded_Count)
        goal_count = int(row.Goal_Count)
        conceded_count = int(row.Conceded_Count)
        print(f"{i}. {team} {context} {period_label} : {recurrence}% ({total_buts} buts sur {match_with_goal_count} matches) - {goal_count} marqués + {conceded_count} encaissés")

top_31_45 = get_top(df, 1, 10)
top_75_90 = get_top(df, 2, 10)

print_top_formatted(top_31_45, "31-45", 10)
print_top_formatted(top_75_90, "75-90", 10)

# Export CSV
top_31_45.to_csv("top_recurrence_31_45.csv", index=False)
top_75_90.to_csv("top_recurrence_75_90.csv", index=False)
print("\nExport terminé : top_recurrence_31_45.csv et top_recurrence_75_90.csv")
