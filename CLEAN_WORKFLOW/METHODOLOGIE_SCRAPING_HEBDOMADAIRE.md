# METHODOLOGIE_SCRAPING_HEBDOMADAIRE.md

## Workflow hebdomadaire de mise à jour des données et patterns

### 1. Fichier de configuration centralisé
- Utiliser `CLEAN_WORKFLOW/config.yaml` comme source unique pour la liste des ligues à scraper.
- Les ligues activées sont celles avec `enabled: true`.

### 2. Script principal
- Script à utiliser : `CLEAN_WORKFLOW/scrape_all_leagues_weekly.py`
- Ce script :
  - Lit la liste des ligues activées depuis le YAML.
  - Lance le scraping pour chaque ligue via le workflow principal :
    ```
    python3 CLEAN_WORKFLOW/scrape_all_leagues_auto.py --league <code_ligue>
    ```
  - Met à jour la base de données pour chaque ligue, séquentiellement.
  - Calcule et affiche le top des patterns toutes ligues confondues à la fin.

### 3. Commande à lancer
```
python3 CLEAN_WORKFLOW/scrape_all_leagues_weekly.py
```

### 4. Fréquence
- À lancer chaque semaine (manuellement ou via cron) pour garantir des données et analyses à jour.

### 5. Avantages
- Ajout/suppression de ligue simple via le YAML.
- Workflow centralisé, maintenable et reproductible.
- Données et top patterns toujours à jour.

### 6. Exemple de sortie
```
🕒 2025-12-09 12:00 | Scraping France – Ligue 1
...scraping...
✅ France – Ligue 1 terminé!
... (toutes les ligues)
=== TOP GLOBAL TOUTES LIGUES CONFONDUES ===
[france] Lorient HOME 31-45+ : 75% ...
... (top 20)
=== FIN TOP GLOBAL ===
```

---

**En cas d’oubli, se référer à ce fichier pour reproduire le workflow hebdomadaire ou corriger la procédure.**
