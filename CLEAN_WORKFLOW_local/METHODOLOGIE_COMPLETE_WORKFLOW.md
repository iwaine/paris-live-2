# Méthodologie complète du workflow SoccerStats

Ce document détaille la logique d'extraction, de scoring, de filtrage et d'affichage des matches live et historiques.

- Extraction robuste de la minute
- Affichage enrichi (patterns, stats MT1/MT2, récurrence)
- Modularité des fonctions
- Utilisation de la base SQLite `predictions.db`
- Voir le script principal : `soccerstats_live_selector_clean.py`
