import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "predictions.db")

# Connexion à la base SQLite
conn = sqlite3.connect(DB_PATH)
query = """
SELECT team, is_home, goals_for, goals_against, goal_times, goal_times_conceded, date
FROM soccerstats_scraped_matches
"""
df = pd.read_sql(query, conn)
conn.close()

# Regroupement par équipe et home/away
stats = []
grouped = df.groupby(['team', 'is_home'])
for (team, is_home), group in grouped:
    total_matches = len(group)
    avg_for = group['goals_for'].mean()
    avg_against = group['goals_against'].mean()
    rec_globale = (group['goals_for'] > 0).mean()
    last5 = group.sort_values('date').tail(5)
    rec_recente = (last5['goals_for'] > 0).mean()
    but_attendu = avg_for  # But attendu = but moyen
    stats.append({
        'team': team,
        'is_home': is_home,
        'but_attendu': but_attendu,
        'recurrence_globale': rec_globale,
        'recurrence_recente': rec_recente,
        'buts_marques': avg_for,
        'buts_encaisse': avg_against
    })

df_stats = pd.DataFrame(stats)

# Heatmap globale pour tous les matchs à domicile (home)
home_stats = df_stats[df_stats['is_home'] == True]
if len(home_stats) > 1:
    corr_home = home_stats[['but_attendu', 'recurrence_globale', 'recurrence_recente', 'buts_marques', 'buts_encaisse']].corr()
    sns.heatmap(corr_home, annot=True, cmap='coolwarm', vmin=0, vmax=1)
    plt.title("Corrélation des paramètres (Global Home)")
    plt.savefig("heatmap_global_home.png")
    plt.close()
    print("Heatmap globale home enregistrée sous : heatmap_global_home.png")
else:
    print("Pas assez de données pour la heatmap globale home.")

# Heatmap globale pour tous les matchs à l'extérieur (away)
away_stats = df_stats[df_stats['is_home'] == False]
if len(away_stats) > 1:
    corr_away = away_stats[['but_attendu', 'recurrence_globale', 'recurrence_recente', 'buts_marques', 'buts_encaisse']].corr()
    sns.heatmap(corr_away, annot=True, cmap='coolwarm', vmin=0, vmax=1)
    plt.title("Corrélation des paramètres (Global Away)")
    plt.savefig("heatmap_global_away.png")
    plt.close()
    print("Heatmap globale away enregistrée sous : heatmap_global_away.png")
else:
    print("Pas assez de données pour la heatmap globale away.")

# Analyse précise des corrélations
import numpy as np

def print_corr_summary(corr_matrix, label):
    print(f"\nAnalyse des corrélations ({label}):")
    for i, col1 in enumerate(corr_matrix.columns):
        for j, col2 in enumerate(corr_matrix.columns):
            if i < j:
                val = corr_matrix.iloc[i, j]
                if np.isnan(val):
                    continue
                if val > 0.7:
                    niveau = "forte corrélation"
                elif val > 0.4:
                    niveau = "corrélation modérée"
                elif val > 0.2:
                    niveau = "corrélation faible"
                else:
                    niveau = "pas de corrélation"
                print(f"- {col1} vs {col2} : {val:.2f} ({niveau})")

# Résumé automatique de l'influence des paramètres sur les buts marqués

def resume_influence(corr_matrix, label):
    target = 'buts_marques'
    print(f"\nRésumé de l'influence sur les buts marqués ({label}):")
    influences = []
    for col in corr_matrix.columns:
        if col != target:
            val = corr_matrix.loc[target, col]
            if np.isnan(val):
                continue
            influences.append((col, val))
    influences.sort(key=lambda x: abs(x[1]), reverse=True)
    for col, val in influences:
        if abs(val) > 0.7:
            niveau = "forte influence"
        elif abs(val) > 0.4:
            niveau = "influence modérée"
        elif abs(val) > 0.2:
            niveau = "influence faible"
        else:
            niveau = "influence négligeable"
        print(f"- {col} : {val:.2f} ({niveau})")
    if influences:
        plus_forte = influences[0]
        print(f"\n>> Le paramètre ayant la plus forte influence sur les buts marqués ({label}) est : {plus_forte[0]} (corrélation {plus_forte[1]:.2f})")

# Home
if len(home_stats) > 1:
    print_corr_summary(corr_home, "Home")
    resume_influence(corr_home, "Home")
# Away
if len(away_stats) > 1:
    print_corr_summary(corr_away, "Away")
    resume_influence(corr_away, "Away")
