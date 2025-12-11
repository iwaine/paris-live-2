import subprocess

# Liste des ligues à tester (exemple : france et germany)
test_leagues = ["france", "germany"]

# 1. Scraping des ligues sélectionnées
print("=== [1/4] Scraping des ligues de test ===")
for league in test_leagues:
    subprocess.run(["python3", "CLEAN_WORKFLOW/scrape_all_leagues_auto.py", "--league", league])

# 2. Synchronisation SQL (ne synchronisera que les CSV présents)
print("\n=== [2/4] Synchronisation SQL avec les CSV présents ===")
subprocess.run(["python3", "CLEAN_WORKFLOW/import_all_leagues_csv_to_sql.py"])

# 3. Export agrégé
print("\n=== [3/4] Génération de l’export agrégé ===")
subprocess.run(["python3", "CLEAN_WORKFLOW/export_recurrence_stats.py"])

# 4. Analyse top patterns (optionnel)
print("\n=== [4/4] Analyse top patterns toutes ligues confondues ===")
subprocess.run(["python3", "CLEAN_WORKFLOW/top_recurrence_all_leagues.py"])

print("\nPipeline test terminé ! Données à jour pour les ligues de test.")
