# 🌍 ARCHITECTURE MULTI-LIGUES - SOCCERSTATS SCRAPING

## Vue d'ensemble

Le système a été conçu pour supporter le scraping de données historiques de **n'importe quelle ligue** depuis SoccerStats.

### Phase actuelle
- ✅ **Ligue 1 (France)**: 18 équipes, 144 matchs scrappés
- 🔄 **Prêt pour**: Premier League, La Liga, Serie A, Bundesliga

---

## Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│                    SOCCERSTATS SCRAPING                      │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─ scrape_multi_league.py (flexible, par ligue)
             │  └─ Supporte: france, england, spain, italy, germany, all
             │
             ├─ import_multi_league.py (import générique)
             │  └─ Table: soccerstats_scraped_matches (multi-ligue)
             │
             └─ build_recurrence_soccerstats.py (analyse récurrence)
                └─ Table: recurrence_stats_soccerstats

┌─────────────────────────────────────────────────────────────┐
│                   PREDICTIONS PIPELINE                       │
├─ feature_extractor.py (extraction de features)
├─ predict_danger_zone.py (calcul probabilités)
└─ live_predictor.py (prédictions en direct)
└─────────────────────────────────────────────────────────────┘
```

---

## Fichiers clés

### 1. `scrape_multi_league.py`
**Scraper générique pour toutes les ligues**

#### Configuration des ligues
```python
LEAGUE_CONFIGS = {
    "france": {
        "name": "Ligue 1",
        "league_id": "france",
        "teams": { ... }  # 18 équipes
    },
    "england": {
        "name": "Premier League",
        "league_id": "england",
        "teams": {}  # Auto-détecté
    },
    # etc.
}
```

#### Utilisation
```bash
# Scraper Ligue 1 uniquement
python3 scrape_multi_league.py france

# Scraper Premier League
python3 scrape_multi_league.py england

# Scraper toutes les ligues
python3 scrape_multi_league.py all

# Export personnalisé
python3 scrape_multi_league.py france --output data/ligue1_2024.json
```

#### Output format
```json
{
  "france": {
    "league": "Ligue 1",
    "league_id": "france",
    "season": "2024",
    "teams": {
      "Lens": {
        "team_id": "u512-lens",
        "matches_count": 24,
        "matches": [
          {
            "opponent": "Angers",
            "is_home": false,
            "score": "1-2",
            "goals_for": 1,
            "goals_against": 2,
            "goal_times": ["45", "74", "76"],
            "result": "L",
            "date": "30 Nov"
          }
        ]
      }
    }
  }
}
```

### 2. `import_multi_league.py`
**Importe les données JSON dans predictions.db**

#### Utilisation
```bash
# Import données Ligue 1
python3 import_multi_league.py --input data/soccerstats_multi_league.json

# Import avec DB personnalisée
python3 import_multi_league.py --input data/ligue1.json --db data/predictions.db
```

#### Tables créées/modifiées
- **soccerstats_scraped_matches**: Stockage brut multi-ligues
  - Colonnes: league, team, opponent, date, score, goals_for, goals_against, is_home, result, goal_times
  - ~432 matches pour Ligue 1 (18 équipes × 24 matches avg)

### 3. `build_recurrence_soccerstats.py`
**Analyse les statistiques de récurrence à partir des données SoccerStats**

#### Utilisation
```bash
# Calculer les stats de récurrence intégrées
python3 build_recurrence_soccerstats.py
```

#### Logique
1. Charge tous les matches de `soccerstats_scraped_matches`
2. Distribue les buts par intervalle temporel (1-15, 16-30, ..., 76-90)
3. Calcule probabilités de but par équipe/intervalle/contexte (home/away)
4. Crée table `recurrence_stats_soccerstats`

#### Output
```
📍 france
   Total matches: 144
   Avg goals/match: 2.50
   Goals by interval:
      1-15    :  14 goals (10.0%)
      16-30   :  17 goals (12.1%)
      31-45   :  21 goals (15.0%)
      46-60   :  17 goals (12.1%)
      61-75   :  20 goals (14.3%)
      76-90   :  39 goals (27.9%)
```

---

## Pipeline d'intégration complète

### Étape 1: Scraper une ligue
```bash
# Pour Ligue 1 (déjà complété)
python3 scrape_multi_league.py france
# → data/soccerstats_multi_league.json

# Pour Premier League
python3 scrape_multi_league.py england
# → data/soccerstats_multi_league.json (ou --output data/premier.json)
```

### Étape 2: Importer dans la base de données
```bash
# Importe JSON dans predictions.db
python3 import_multi_league.py

# Vérifie l'import
sqlite3 data/predictions.db "SELECT league, COUNT(*) FROM soccerstats_scraped_matches GROUP BY league;"
```

### Étape 3: Construire statistiques de récurrence
```bash
# Analyse les patterns de buts par intervalle
python3 build_recurrence_soccerstats.py

# Vérifier les stats créées
sqlite3 data/predictions.db "SELECT league, team, interval, AVG(goal_probability) FROM recurrence_stats_soccerstats GROUP BY league, team LIMIT 10;"
```

### Étape 4: Utiliser dans le prédicteur
Le prédicteur en direct peut maintenant utiliser les données intégrées:
```python
# Dans predict_danger_zone.py
from feature_extractor import FeatureExtractor

# Les probabilités utilisent les stats de récurrence SoccerStats
features = extractor.extract_features(
    current_stats=match_stats,
    snapshots=snapshots,
    home_team="Lens",
    away_team="Angers"
)

# Les stats par intervalle sont automatiquement utilisées
danger_score = model.predict(features)
```

---

## Team IDs par ligue

### Ligue 1 (France) ✅ COMPLET
```
Angers: u502-angers
Auxerre: u7648-auxerre
Brest: u510-brest
Le Havre: u7655-le-havre
Lens: u512-lens
Lille: u503-lille
Lorient: u507-lorient
Lyon: u513-lyon
Marseille: u517-marseille
Metz: u515-metz
Monaco: u505-monaco
Nantes: u500-nantes
Nice: u511-nice
PSG: u518-paris-sg
Paris FC: u7654-paris-fc
Rennes: u504-rennes
Strasbourg: u508-strasbourg
Toulouse: u7659-toulouse
```

### Premier League (England)
**À récupérer automatiquement ou manuellement**
```
Auto-detection: python3 scrape_multi_league.py england
               (extraction automatique des IDs depuis standings)
```

### La Liga (Spain)
```
À déterminer lors du scraping
```

### Serie A (Italy)
```
À déterminer lors du scraping
```

### Bundesliga (Germany)
```
À déterminer lors du scraping
```

---

## Structure de base de données

### Table: `soccerstats_scraped_matches`
```sql
CREATE TABLE soccerstats_scraped_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league TEXT NOT NULL,              -- 'france', 'england', 'spain', etc.
    team TEXT NOT NULL,                -- Équipe domicile
    opponent TEXT NOT NULL,            -- Adversaire
    date TEXT,                         -- "30 Nov", "2 Dec"
    score TEXT,                        -- "1-2"
    goals_for INTEGER,                 -- Buts marqués
    goals_against INTEGER,             -- Buts encaissés
    is_home BOOLEAN,                   -- 1 = domicile, 0 = extérieur
    result TEXT,                       -- 'W', 'D', 'L'
    goal_times TEXT,                   -- "45,74,76" (minutes des buts)
    scraped_at TIMESTAMP
);
```

### Table: `recurrence_stats_soccerstats`
```sql
CREATE TABLE recurrence_stats_soccerstats (
    id INTEGER PRIMARY KEY,
    league TEXT,                       -- Ligue source
    team TEXT,                         -- Équipe
    context TEXT,                      -- 'home', 'away'
    interval TEXT,                     -- "1-15", "16-30", etc.
    total_matches INTEGER,             -- Nombre de matchs
    total_goals INTEGER,               -- Total buts marqués
    avg_goals REAL,                    -- Moyenne buts/intervalle
    goal_probability REAL,             -- P(but marqué dans intervalle)
    source TEXT                        -- 'soccerstats'
);
```

---

## Intégration avec le pipeline existant

### 1. Feature Extraction
- `feature_extractor.py` utilise déjà `team_elo_map` optionnel
- Peut être étendu pour utiliser `recurrence_stats_soccerstats`

### 2. Live Predictions
- Prédicteur peut consulter les probas par intervalle
- Exemple: "Pour Lens à domicile en 76-90, proba de but = 0.35"

### 3. Backtesting
- Peut valider les prédictions contre matchs SoccerStats historiques
- Comparer accuracy before/after intégration des données

---

## Checklist - Prochaines étapes

- [x] Scraper Ligue 1 complètement (144 matches)
- [x] Créer architecture multi-ligues générique
- [ ] Scraper Premier League
- [ ] Scraper La Liga
- [ ] Scraper Serie A
- [ ] Scraper Bundesliga
- [ ] Intégrer toutes les données dans recurrence_stats
- [ ] Validation: comparer résultats prédicteur (avant/après)
- [ ] Optimiser: deduplication matches si présent dans DB existante
- [ ] Production: déployer avec données augmentées

---

## Troubleshooting

### Problème: Team IDs introuvables
```bash
# Solution: Auto-détection
python3 scrape_multi_league.py england --output debug_teams.json

# Examine debug_teams.json pour voir les IDs extraits
```

### Problème: HTML parsing échoue
```bash
# Vérifier l'URL
# Chercher table avec pattern date: \d{1,2}\s+\w{3}
# Adapter regex dans parse_match_details() si nécessaire
```

### Problème: Base de données corrompue
```bash
# Backup et réinitialiser
cp data/predictions.db data/predictions.db.backup
sqlite3 data/predictions.db "DROP TABLE soccerstats_scraped_matches; DROP TABLE recurrence_stats_soccerstats;"
```

---

## Performance

**Temps de scraping** (approximatif)
- Ligue 1 (18 teams × 24 matches): ~10 secondes
- Premier League (20 teams × 20 matches): ~12 secondes
- 5 ligues (88 teams total): ~60 secondes

**Taille données**
- Ligue 1: ~432 matches = ~100 KB JSON
- 5 ligues: ~2000 matches = ~500 KB JSON

**Espace DB**
- soccerstats_scraped_matches: ~500 KB
- recurrence_stats_soccerstats: ~300 KB

---

## API d'utilisation programmatique

### Scraper une ligue
```python
from scrape_multi_league import MultiLeagueScraper

scraper = MultiLeagueScraper()
data = scraper.scrape_league('france', auto_detect_teams=False)
scraper.save_to_json(data, 'data/france_matches.json')
```

### Importer dans DB
```python
from import_multi_league import MultiLeagueImporter

importer = MultiLeagueImporter(db_path='data/predictions.db')
importer.import_from_json('data/france_matches.json')
importer.print_summary()
importer.close()
```

### Analyser récurrence
```python
from build_recurrence_soccerstats import RecurrenceStatsBuilder

builder = RecurrenceStatsBuilder(db_path='data/predictions.db')
builder.build_stats_tables()
builder.close()
```

---

## Notes

- **Politesse**: Respecte délai 1s entre requêtes pour chaque site
- **Robustesse**: Retry automatique avec backoff exponentiel
- **Flexibilité**: Configurations faciles à étendre pour nouvelles ligues
- **Données**: Conserve traces d'importation (league_id, scraped_at)

