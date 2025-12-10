# METHODOLOGIE COMPLETE : DE LA BASE DE DONNEES AU LIVE MATCH

Ce document décrit la séquence optimale pour garantir des analyses fiables et un affichage live pertinent, en utilisant uniquement les scripts du dossier `CLEAN_WORKFLOW`.

## 1. Scraping & Mise à jour de la base de données

**Objectif :** Obtenir les historiques de buts pour toutes les ligues suivies, à jour.

### a) Scraping hebdomadaire (données brutes)
- Lancer le scraping automatique de toutes les ligues :
  ```bash
  python3 scrape_all_leagues_weekly.py
  ```
  (ou `scrape_all_leagues_auto.py` selon la config)
- Les fichiers bruts sont stockés dans `CLEAN_WORKFLOW/data/` ou un sous-dossier.

### b) Initialisation ou mise à jour de la base SQLite
- Générer ou mettre à jour la base à partir des fichiers bruts :
  ```bash
  python3 init_soccerstats_db.py
  ```
- La base `predictions.db` est créée/mise à jour dans `CLEAN_WORKFLOW/data/`.

**À faire au moins une fois par semaine pour garantir la fraîcheur des analyses.**

---

## 2. Analyse et extraction des patterns/statistiques

- Utiliser les scripts d'analyse pour explorer les patterns, la récurrence, les stats par intervalle, etc. Exemples :
  ```bash
  python3 patterns_all_leagues_from_db.py
  python3 top_patterns_global.py
  python3 list_patterns_in_league.py --league france
  ```
- Ces scripts lisent directement la base `predictions.db`.

---

## 3. Extraction et affichage des matches live

- Lancer le workflow principal pour détecter et afficher les matches live :
  ```bash
  python3 soccerstats_live_selector.py --all-live-details
  ```
- Ce script :
  - Scrape la page live SoccerStats
  - Extrait la minute, filtre FT/HT, applique les intervalles d'intérêt
  - Affiche les stats détaillées, patterns historiques, probabilités, etc.

---

## 4. Tests et robustesse

- Pour valider/améliorer l'extraction de la minute ou d'autres fonctions critiques :
  ```bash
  python3 test_extract_minute_robuste.py
  python3 debug_scan_all_minutes.py
  ```
- Pour debug ou analyse spécifique, utiliser les scripts `debug_*.py`.

---

## 5. Résumé de la séquence optimale

1. **Scraping hebdomadaire** : `scrape_all_leagues_weekly.py`
2. **Mise à jour base** : `init_soccerstats_db.py`
3. **Analyse patterns** : `patterns_all_leagues_from_db.py`, `top_patterns_global.py`, etc.
4. **Live match** : `soccerstats_live_selector.py --all-live-details`
5. **Tests/Debug** : `test_extract_minute_robuste.py`, `debug_scan_all_minutes.py`

---

**Remarques :**
- Tous les scripts et la base doivent rester dans `CLEAN_WORKFLOW`.
- Adapter la liste des ligues/équipes dans les fichiers de config YAML si besoin.
- Pour toute modification de la logique d’extraction, valider d’abord dans les scripts de test avant d’intégrer dans le workflow principal.
