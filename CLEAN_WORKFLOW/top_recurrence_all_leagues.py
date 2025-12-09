import pandas as pd

# Charger le fichier CSV
csv_path = "/workspaces/paris-live/data/recurrence_stats_export.csv"
df = pd.read_csv(csv_path)

# Fonction pour calculer la récurrence
# Période 1 = 31-45+, Période 2 = 75-90+
def get_top(df, period, top_n=30):
    dff = df[df["Period"] == period].copy()
    dff["Recurrence"] = dff["Goal_Count"] / dff["Total_Matches"]
    dff = dff[dff["Total_Matches"] >= 5]  # Filtre pour éviter les petits échantillons
    dff = dff.sort_values("Recurrence", ascending=False)
    return dff[["Team", "Context", "Goal_Count", "Total_Matches", "Recurrence"]].head(top_n)

# Top équipes 31-45+
top_31_45 = get_top(df, 1, 30)
# Top équipes 75-90+
top_75_90 = get_top(df, 2, 30)

# Export CSV
top_31_45.to_csv("top_recurrence_31_45.csv", index=False)
top_75_90.to_csv("top_recurrence_75_90.csv", index=False)
print("Export terminé : top_recurrence_31_45.csv et top_recurrence_75_90.csv")
