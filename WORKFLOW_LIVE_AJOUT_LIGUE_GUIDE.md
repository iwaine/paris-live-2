# AJOUT DE NOUVELLES LIGUES/PAYS AU WORKFLOW

Ce complément explique comment scraper et intégrer une nouvelle ligue ou un nouveau pays dans le workflow d'analyse et d'alertes live.

---

## 1. Scraper les données d'une nouvelle ligue
- **Fichier à utiliser :** `scrape_all_leagues_auto.py` ou script dédié (ex : `scrape_bulgaria_auto.py`)
- **Étapes :**
    1. Identifier l'URL SoccerStats de la nouvelle ligue (ex : `https://www.soccerstats.com/latest.asp?league=sweden`)
    2. Adapter le script pour inclure la nouvelle ligue dans la liste des ligues à scraper
    3. Lancer le script pour récupérer tous les matchs et stats de la ligue
    4. Les données sont insérées dans la base SQLite (`soccerstats_scraped_matches`)

## 2. Analyser les patterns historiques pour la nouvelle ligue
- **Fichier :** `analyze_all_leagues_patterns.py`
- **Étapes :**
    1. Vérifier que la nouvelle ligue est bien présente dans la base
    2. Lancer le script pour calculer les patterns de buts, SEM, IQR, etc. pour chaque équipe de la ligue
    3. Les stats avancées sont ajoutées dans la table `team_goal_recurrence`

## 3. Intégration dans le workflow live
- **Aucune modification majeure** :
    - Le pipeline live (`soccerstats_live_scraper.py`, `live_goal_probability_predictor.py`, `telegram_formatter_enriched.py`) fonctionne pour toute ligue présente dans la base
    - Il suffit de passer l'URL du match live de la nouvelle ligue
    - Les stats historiques et patterns seront automatiquement utilisés si la ligue est bien scrappée et analysée

## 4. Exemple d'ajout d'une ligue (Suède)
1. **Scraper la ligue Suède**
   ```bash
   python3 scrape_all_leagues_auto.py --league sweden
   # ou python3 scrape_sweden_auto.py
   ```
2. **Analyser les patterns**
   ```bash
   python3 analyze_all_leagues_patterns.py
   ```
3. **Tester sur un match live Suède**
   ```python
   url = "https://www.soccerstats.com/pmatch.asp?league=sweden&stats=41-11-2-2026"
   live_data = scrape_live_match(url)
   # ...suite du workflow classique
   ```

---

## Points de vigilance
- **Vérifier la présence de la ligue dans la base** : Si la ligue n'apparaît pas, vérifier le scraping et relancer si besoin
- **Adapter les scripts si le format SoccerStats change**
- **Répéter l'analyse des patterns après chaque ajout de ligue**

---

**En résumé :**
- Ajouter une nouvelle ligue = Scraper + Analyser patterns + Utiliser le workflow classique
- Aucun changement de code nécessaire dans le pipeline live si la base est à jour

---

**Ce guide complète le workflow principal pour garantir l'intégration facile de nouveaux pays/ligues.**
