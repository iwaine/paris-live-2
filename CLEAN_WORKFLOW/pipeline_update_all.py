import subprocess

# 1. Scraping de toutes les ligues
print("=== [1/4] Scraping de toutes les ligues ===")
subprocess.run(["python3", "CLEAN_WORKFLOW/scrape_all_leagues_batch.py"])

# 2. Synchronisation SQL
print("\n=== [2/4] Synchronisation SQL avec tous les CSV ===")
subprocess.run(["python3", "CLEAN_WORKFLOW/import_all_leagues_csv_to_sql.py"])

# 3. Export agrégé
print("\n=== [3/4] Génération de l’export agrégé ===")
subprocess.run(["python3", "CLEAN_WORKFLOW/export_recurrence_stats.py"])

# 4. Analyse top patterns (optionnel)
print("\n=== [4/4] Analyse top patterns toutes ligues confondues ===")
subprocess.run(["python3", "CLEAN_WORKFLOW/top_recurrence_all_leagues.py"])

print("\nPipeline complet terminé ! Toutes les données sont à jour.")
