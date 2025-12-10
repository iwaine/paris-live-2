# METHODOLOGIE_SCRAPING_LIGUES.md

## Méthodologie recommandée pour le scraping multi-ligues

### 1. Source de vérité des ligues
- Utiliser le fichier `CLEAN_WORKFLOW/config.yaml` comme référence unique pour la liste des ligues à scraper.
- Ce fichier contient les ligues activées (clé `enabled: true`) avec leur nom et leur code SoccerStats (extrait de l’URL).

### 2. Extraction des ligues
- Extraire dynamiquement la liste des codes de ligue activés depuis `config.yaml`.
- Exemple de script : `extract_leagues_from_config_yaml.py`.

### 3. Scraping automatique
- Adapter le script principal (`scrape_all_leagues_auto.py`) pour lire la config depuis `CLEAN_WORKFLOW/config.yaml`.
- Lancer le scraping avec l’option `--league all` pour traiter toutes les ligues activées.
- Chaque ligue est traitée séquentiellement : extraction des équipes, scraping des matches, insertion/mise à jour en base.

### 4. Avantages
- Contrôle centralisé et flexible des ligues suivies.
- Facilité d’ajout/suppression d’une ligue via le YAML.
- Cohérence entre la config, le scraping et l’analyse.

### 5. Exemple de commande
```
python3 /workspaces/paris-live/CLEAN_WORKFLOW/scrape_all_leagues_auto.py --league all
```

### 6. Analyse post-scraping
- Une fois le scraping terminé, relancer l’analyse des patterns globaux pour toutes les ligues.

---

**En cas d’oubli, se référer à ce fichier pour reproduire la méthodologie ou corriger le workflow.**
