
import pandas as pd

# Charger le fichier CSV
csv_path = "/workspaces/paris-live/data/recurrence_stats_export.csv"
df = pd.read_csv(csv_path)

# Nettoyage des doublons (équipe/contexte/période)
df = df.drop_duplicates(subset=["Team", "Context", "Period"])

def get_top(df, period, top_n=10):
    dff = df[df["Period"] == period].copy()
    dff["Recurrence"] = dff["Goal_Count"] / dff["Total_Matches"]
    dff = dff[dff["Total_Matches"] >= 5]
    dff = dff.sort_values("Recurrence", ascending=False)
    return dff.head(top_n)

def print_top_formatted(df, period_label, top_n=10):
    print(f"\nMEILLEURS PATTERNS {period_label} (≥5 matches) :")
    for i, row in enumerate(df.itertuples(), 1):
        team = row.Team
        context = row.Context
        goal_count = int(row.Goal_Count)
        total_matches = int(row.Total_Matches)
        recurrence = int(round(100 * row.Recurrence))
        # Si le CSV contient les colonnes marqués/encaissés
        marques = getattr(row, "marques", None)
        encaisses = getattr(row, "encaisses", None)
        if marques is not None and encaisses is not None:
            detail = f"- {marques} marqués + {encaisses} encaissés"
        else:
            detail = ""
        print(f"{i}. {team} {context} {period_label} : {recurrence}% ({goal_count} buts sur {total_matches} matches) {detail}")

top_31_45 = get_top(df, 1, 10)
top_75_90 = get_top(df, 2, 10)

print_top_formatted(top_31_45, "31-45", 10)
print_top_formatted(top_75_90, "75-90", 10)

# Export CSV
top_31_45.to_csv("top_recurrence_31_45.csv", index=False)
top_75_90.to_csv("top_recurrence_75_90.csv", index=False)
print("\nExport terminé : top_recurrence_31_45.csv et top_recurrence_75_90.csv")
