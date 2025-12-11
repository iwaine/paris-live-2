# MÉTHODOLOGIE COMPLÈTE – DE L’EXTRACTION DES PATTERNS HISTORIQUES À L’ANALYSE LIVE

Ce guide fusionne et synthétise les deux méthodologies clés du projet : l’extraction et l’analyse des patterns historiques, et le pipeline complet d’analyse live SoccerStats. Il est conçu pour être accessible à un débutant, étape par étape.

---

## 1. Objectif général

- Extraire, calculer et afficher les patterns historiques pour chaque équipe et intervalle.
- Mettre en place un pipeline automatisé pour le monitoring live SoccerStats, avec analyse récurrentielle et reporting.

---

## 2. Source et extraction des données

- Les données proviennent du scraping SoccerStats, stockées dans la base SQLite `predictions.db`, table `soccerstats_scraped_matches`.
- Les scripts de scraping (`scrape_all_leagues_auto.py`, `scrape_all_leagues_batch.py`) collectent les matches, minutes de but, scores, etc., et exportent en CSV.
- Synchronisation SQL/CSV via `import_all_leagues_csv_to_sql.py` pour garantir la fraîcheur et la cohérence des historiques.

---

## 3. Extraction et calcul des patterns historiques

- Pour chaque équipe (home/away), extraction de tous les matches historiques dans la ligue concernée.
- Filtrage par côté (HOME/AWAY) et intervalle d’intérêt (ex : 31-45, 75-120).
- Calcul de la récurrence : proportion de matches avec but marqué/encaissé dans l’intervalle.
- Calcul du nombre total de buts, moyenne, SEM, IQR, stats par mi-temps (MT1, MT2), récurrence récente (n derniers matches).
- Utilisation de fonctions utilitaires : `print_full_patterns`, `get_recent_pattern_score`, `compute_mt_goals`, `normalize_team_name`.

---

## 4. Pipeline d’analyse live

### a) Détection des matches live
- Script principal : `soccerstats_live_selector.py`.
- Extraction de la minute de jeu, filtrage sur les ligues suivies, affichage enrichi en terminal (codes couleurs, stats historiques, etc.).

### b) Scraping et synchronisation
- Scraping massif de toutes les ligues.
- Stockage des données brutes en CSV, import dans la base SQLite.

### c) Agrégation et export
- Calcul des patterns récurrents par période via `export_recurrence_stats.py`, `top_recurrence_all_leagues.py`.
- Export des résultats dans des CSV dédiés.

### d) Analyse et reporting
- Visualisation et diagnostic via `dashboard_web.py`, `FINAL_REPORT.py`.
- Comparaison des périodes, analyse des écarts, reporting personnalisé.

### e) Automatisation
- Orchestration complète via `pipeline_update_all.py`.
- Enchaînement automatique : scraping → sync SQL/CSV → export → analyse.
- Planification possible via cron.

---

## 5. Bonnes pratiques et robustesse

- Toujours synchroniser la base avant extraction pour garantir la fraîcheur des historiques.
- Valider la logique d’extraction sur un script de test avant intégration.
- Utiliser la normalisation des noms d’équipes pour éviter les incohérences.
- Gérer les exceptions sur le parsing des minutes et des buts.
- Modularité : fonctions critiques isolées pour faciliter la maintenance et l’extension.
- Debugging : logs détaillés, diagnostics sur les patterns historiques et la récurrence récente.

---

## 6. Extension et adaptation

- Ajout de nouvelles ligues : ajouter l’identifiant dans la base et relancer le pipeline.
- Adaptation des intervalles : modifier les intervalles d’intérêt dans les scripts d’agrégation/analyse.
- Reporting personnalisé : adapter les scripts d’export/visualisation selon les besoins métier.

---

## 7. Fichiers et scripts clés

- `soccerstats_live_selector.py` : détection et affichage live enrichi.
- `scrape_all_leagues_auto.py` / `scrape_all_leagues_batch.py` : scraping massif.
- `import_all_leagues_csv_to_sql.py` : synchronisation SQL/CSV.
- `export_recurrence_stats.py` / `top_recurrence_all_leagues.py` : agrégation et export.
- `pipeline_update_all.py` : automatisation complète.
- `dashboard_web.py`, `FINAL_REPORT.py` : analyse et reporting.
- Base de données : `predictions.db`, table `soccerstats_scraped_matches`.

---

## 8. Résumé du pipeline automatisé

1. **Scraping** : Extraction brute de tous les matches de toutes les ligues suivies.
2. **Sync SQL/CSV** : Import des données brutes dans la base, suppression des doublons.
3. **Agrégation** : Calcul des patterns récurrents par période.
4. **Export** : Génération des fichiers CSV d’analyse.
5. **Analyse** : Visualisation, diagnostic, reporting.
6. **Automatisation** : Orchestration de toutes les étapes via un script unique.

---

## 9. Conseils pour la production

- Toujours valider les modifications sur un sous-ensemble de ligues avant déploiement complet.
- Utiliser les logs/debug pour diagnostiquer rapidement toute anomalie.
- Documenter toute adaptation métier ou ajout de ligue/intervalles.
- Suivre la méthodologie de test et de validation avant intégration dans le pipeline principal.

---

Ce document est une synthèse évolutive, à adapter selon les besoins spécifiques du projet ou de l’équipe. Pour tout approfondissement, se référer aux scripts et à la documentation métier.
