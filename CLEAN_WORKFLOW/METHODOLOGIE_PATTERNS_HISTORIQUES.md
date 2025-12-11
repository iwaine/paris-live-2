# MÉTHODOLOGIE – PATTERNS HISTORIQUES & ANALYSE LIVE

## 1. Objectif

Décrire la méthode d’extraction, de calcul et d’affichage des patterns historiques pour chaque équipe et chaque intervalle, dans le cadre du monitoring live SoccerStats.

---

## 2. Source des données

- Les patterns historiques sont calculés à partir de la base locale SQLite `predictions.db`, table `soccerstats_scraped_matches`.
- Les colonnes utilisées : `league`, `team`, `is_home`, `goal_times`, `goal_times_conceded`.
- Les données sont alimentées par les scripts de scraping et synchronisation CSV/SQL.

---

## 3. Extraction des historiques

- Pour chaque équipe (home/away), le script récupère tous les matchs historiques dans la ligue concernée.
- Filtrage selon le côté (HOME/AWAY) via le champ `is_home`.
- Pour chaque match, extraction des minutes de but marqués et encaissés (`goal_times`, `goal_times_conceded`).
- Calcul sur l’intervalle d’intérêt (ex : 31-45, 75-120).

---

## 4. Calcul des patterns

- Calcul de la récurrence : proportion de matchs où au moins un but a été marqué ou encaissé dans l’intervalle.
- Calcul du nombre total de buts, moyenne, SEM (erreur standard), IQR (intervalle interquartile) des minutes de but.
- Calcul du but récurrent par match (moyenne de buts dans l’intervalle pour les matchs concernés).
- Calcul des stats par mi-temps (MT1 : 1-45+, MT2 : 46-120).
- Calcul de la récurrence récente (n derniers matchs, typiquement 5).

---

## 5. Affichage et diagnostic

- Affichage enrichi en terminal : codes couleurs ANSI, détails par équipe/côté/intervalle.
- Affichage harmonisé des patterns historiques, stats MT1/MT2, récurrence récente, score combiné.
- Diagnostic : liste brute des buts par mi-temps, stats avancées (moyenne, SEM, IQR).

---

## 6. Bonnes pratiques

- Toujours synchroniser la base avant extraction pour garantir la fraîcheur des historiques.
- Valider la logique d’extraction sur un script de test avant intégration.
- Utiliser la normalisation des noms d’équipes pour éviter les incohérences.
- Gérer les exceptions sur le parsing des minutes et des buts.

---

## 7. Extension

- Pour ajouter une nouvelle ligue ou intervalle, adapter la requête SQL et les intervalles dans le script.
- Pour des analyses personnalisées, enrichir les fonctions de scoring ou d’affichage.

---

## 8. Fichiers et fonctions clés

- Script principal : `soccerstats_live_selector.py`
- Fonctions : `print_full_patterns`, `get_recent_pattern_score`, `compute_mt_goals`, `normalize_team_name`, etc.
- Base de données : `predictions.db`, table `soccerstats_scraped_matches`

---

Ce document peut être enrichi selon les besoins métier ou d’analyse.
