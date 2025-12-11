# MÉTHODOLOGIE COMPLÈTE – WORKFLOW SOCCERSTATS LIVE

## 1. Objectif général

- Fournir un pipeline robuste, automatisé et traçable pour la détection, l’extraction, la synchronisation et l’analyse des matches live SoccerStats, avec un focus sur les statistiques récurrentielles par période (ex : 31-45+, 75-90+), la fiabilité des données et la facilité d’extension à de nouvelles ligues.

---

## 2. Étapes du workflow

### a) Détection des matches live

- Utilisation du script `soccerstats_live_selector.py` pour détecter les matches en cours sur la page principale de SoccerStats.
- Extraction de la minute de jeu via parsing HTML (balises `<font color=...>`, regex sur les minutes, exclusion des lignes contenant des dates/heures futures).
- Filtrage sur les ligues suivies (synchronisation dynamique avec la base de données).
- Affichage enrichi en terminal (codes couleurs ANSI, détails patterns historiques, stats MT1/MT2, récurrence récente, etc.).

### b) Extraction et scraping des données

- Scraping automatisé de toutes les ligues via `scrape_all_leagues_auto.py` ou `scrape_all_leagues_batch.py`.
- Extraction robuste des minutes de but (y compris arrêts de jeu, penalties, csc).
- Stockage des données brutes dans des fichiers CSV par ligue.

### c) Synchronisation SQL/CSV

- Import des CSV dans la base SQLite (`import_all_leagues_csv_to_sql.py`), avec suppression préalable des anciennes données pour éviter les doublons.
- Structure de la base : table `soccerstats_scraped_matches` (colonnes : league, team, is_home, goal_times, goal_times_conceded, etc.).

### d) Agrégation et export des statistiques

- Calcul des patterns récurrents par période via `export_recurrence_stats.py` et `top_recurrence_all_leagues.py`.
- Export des résultats agrégés dans des CSV dédiés (ex : `recurrence_stats_export.csv`, `top_recurrence_31_45.csv`).
- Possibilité de filtrer par ligue, équipe, période, etc.

### e) Analyse et reporting

- Scripts d’analyse avancée (`dashboard_web.py`, `FINAL_REPORT.py`, etc.) pour visualiser les patterns, comparer les périodes, diagnostiquer les écarts entre brut et agrégé.
- Utilisation de fonctions utilitaires pour la normalisation des noms d’équipes, le calcul de la moyenne/SEM/IQR, la récurrence récente, etc.

### f) Automatisation du pipeline

- Orchestration complète via `pipeline_update_all.py` (ou `pipeline_update_test.py` pour tests sur un sous-ensemble de ligues).
- Enchaînement automatique : scraping → sync SQL/CSV → export → analyse.
- Possibilité de planifier via cron ou autre ordonnanceur.

---

## 3. Bonnes pratiques et robustesse

- **Validation systématique** : toute modification de la logique d’extraction doit être testée dans un script dédié avant intégration.
- **Synchronisation stricte SQL/CSV** : toujours supprimer les anciennes données avant import pour garantir la cohérence.
- **Gestion des exceptions** : try/except sur toutes les étapes critiques (scraping, parsing, SQL).
- **Modularité** : fonctions critiques isolées pour faciliter la maintenance et l’extension.
- **Debugging** : logs détaillés, affichage des minutes brutes, diagnostics sur les patterns historiques et la récurrence récente.

---

## 4. Extension et adaptation

- **Ajout de nouvelles ligues** : ajouter l’identifiant dans la base et relancer le pipeline.
- **Adaptation des intervalles** : modifier les intervalles d’intérêt dans les scripts d’agrégation/analyse.
- **Reporting personnalisé** : adapter les scripts d’export/visualisation selon les besoins métier.

---

## 5. Fichiers et scripts clés

- `soccerstats_live_selector.py` : détection et affichage live enrichi.
- `scrape_all_leagues_auto.py` / `scrape_all_leagues_batch.py` : scraping massif.
- `import_all_leagues_csv_to_sql.py` : synchronisation SQL/CSV.
- `export_recurrence_stats.py` / `top_recurrence_all_leagues.py` : agrégation et export.
- `pipeline_update_all.py` : automatisation complète.
- `dashboard_web.py`, `FINAL_REPORT.py` : analyse et reporting.

---

## 6. Résumé du pipeline automatisé

1. **Scraping** : Extraction brute de tous les matches de toutes les ligues suivies.
2. **Sync SQL/CSV** : Import des données brutes dans la base, suppression des doublons.
3. **Agrégation** : Calcul des patterns récurrents par période.
4. **Export** : Génération des fichiers CSV d’analyse.
5. **Analyse** : Visualisation, diagnostic, reporting.
6. **Automatisation** : Orchestration de toutes les étapes via un script unique.

---

## 7. Conseils pour la production

- Toujours valider les modifications sur un sous-ensemble de ligues avant déploiement complet.
- Utiliser les logs/debug pour diagnostiquer rapidement toute anomalie.
- Documenter toute adaptation métier ou ajout de ligue/intervalles.

---

**Pour toute modification majeure, suivre la méthodologie de test et de validation avant intégration dans le pipeline principal.**

---

Ce document peut être adapté ou enrichi selon les besoins spécifiques du projet ou de l’équipe.
