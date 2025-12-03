# 🎯 Recurrence Prediction System

## Overview

Système de prédiction de paris en direct basé sur l'analyse de récurrence des minutes exactes de buts.

**Architecture:**
```
LIVE MONITOR (45 sec)
    ↓
Minute actuelle + stats live
    ↓ [COUPLAGE]
Données historiques (RecurrenceAnalyzer)
    ↓
RecurrencePredictor
    ↓
Danger Score (%)
    ↓
Décision: PARIER OUI/NON + TELEGRAM ALERT
```

---

## 📊 Key Components

### 1. **Database Schema**

**New tables:**
- `match_history`: Matchs historiques (home_team, away_team, date, score)
- `goals`: Buts minute-exact (match_id, team, minute)
- `goal_stats`: Statistiques pré-calculées (team, venue, interval, avg_minute, std_dev, distribution)

**Setup:**
```python
from utils.database_manager import DatabaseManager

db = DatabaseManager()  # Crée tables automatiquement
```

### 2. **RecurrenceAnalyzer**

Analyse les données historiques par contexte:
- **Team**: Arsenal, Chelsea, etc.
- **Venue**: "home" (domicile) ou "away" (extérieur)
- **Interval**: "31-45" (1ère mi-temps +), "76-90" (2ème mi-temps +)

**Usage:**
```python
from predictors.recurrence_analyzer import RecurrenceAnalyzer

analyzer = RecurrenceAnalyzer()

# Analyser Arsenal à domicile [31-45]
analysis = analyzer.analyze_team_venue_interval("Arsenal", "home", "31-45")

# Output:
# {
#   "overall": {
#     "total_matches": 42,
#     "goals_scored": 28,
#     "avg_minute": 37.2,
#     "std_dev": 5.3,
#     "minute_distribution": {"31": 0, "32": 1, ..., "45": 0}
#   },
#   "recent": {
#     "matches": 4,
#     "goals_scored": 3,
#     "avg_minute": 36.8
#   }
# }

# Sauvegarder en BD
analyzer.save_analysis_to_db(analysis)

# Analyser tous les teams
analyzer.analyze_and_save_all(["Arsenal", "Chelsea", "Man City"])
```

### 3. **RecurrencePredictor**

Combine données live + historiques pour prédire en temps réel:

**Usage:**
```python
from predictors.recurrence_predictor import RecurrencePredictor

predictor = RecurrencePredictor()

# Prédire à minute 38
prediction = predictor.predict_at_minute(
    home_team="Arsenal",
    away_team="Chelsea",
    current_minute=38,
    home_possession=0.62,    # Live stats
    away_possession=0.38,
    home_shots=3,
    away_shots=1
)

# Output:
# {
#   "danger_score_percentage": 67.3,
#   "home_goal_probability": 45.0,
#   "away_goal_probability": 22.3,
#   "optimal_minute_range": "35-42",
#   "data_summary": {
#     "home_matches_total": 42,
#     "home_matches_recent": 4,
#     "away_matches_total": 35,
#     "away_matches_recent": 4
#   }
# }
```

### 4. **HistoricalDataLoader**

Charge les données historiques:

```python
from scrapers.historical_data_loader import HistoricalDataLoader

loader = HistoricalDataLoader()

# Charger données de test
loader.load_test_data()

# Ou scraper depuis SoccerStats (TODO)
loader.load_from_soccerstats(league_code="england")

# Voir les stats
stats = loader.get_match_stats()
# {"total_matches": 100, "total_goals": 300, "total_teams": 5}
```

---

## 🎯 Decision Logic

### Formule Danger Score

```
DANGER_SCORE = Base × Minute_Factor × Possession_Factor × Recency_Boost

Where:
1. Base = (Home_Goals_Per_Match × 0.70) + (Away_Goals_Per_Match × 0.30)

2. Minute_Factor (fenêtre ±σ):
   - Si minute dans [avg ± σ]: factor = 0.5-1.0 (basé sur buts exactes)
   - Sinon: factor = exp(-distance/5) (décroissance exponentielle)

3. Possession_Factor = 0.7 + (possession × 0.3)  [0.7-1.0]

4. Recency_Boost = 1.0-1.2 (si en forme récente)
```

### Seuils de Décision

| Danger | Action | Confiance |
|--------|--------|-----------|
| ≥ 75% | 💪 PARIER FORT | Très haute |
| ≥ 65% | ✅ PARIER | Haute |
| ≥ 50% | ⚠️  CONSIDÉRER | Modérée |
| < 50% | ❌ NE PAS PARIER | Basse |

**Affichage:**
```
"Danger: 67.3% | 42 matchs globaux | 4 récents"
```

---

## 🔄 Workflow: Live Betting

### Setup Initial

```python
# 1. Charger données historiques
from scrapers.historical_data_loader import HistoricalDataLoader
loader = HistoricalDataLoader()
loader.load_test_data()  # Ou scraper réel

# 2. Analyser et pré-calculer
from predictors.recurrence_analyzer import RecurrenceAnalyzer
analyzer = RecurrenceAnalyzer()
analyzer.analyze_and_save_all([
    "Arsenal", "Chelsea", "Manchester City", "Liverpool", "Manchester United"
])
```

### During Live Match

```python
# 3. À chaque scrape live (45 sec)
from predictors.recurrence_predictor import RecurrencePredictor

predictor = RecurrencePredictor()

# Live data (du scraper SoccerStats)
current_minute = 38
home_possession = 0.62
away_possession = 0.38

# Prédire
prediction = predictor.predict_at_minute(
    home_team="Arsenal",
    away_team="Chelsea",
    current_minute=current_minute,
    home_possession=home_possession,
    away_possession=away_possession
)

# 4. Décider de parier
danger = prediction['danger_score_percentage']

if danger >= 65:
    # ALERT TELEGRAM
    send_telegram_alert(f"DANGER: {danger}% | {prediction['data_summary']}")
else:
    # NE PAS PARIER
    pass
```

---

## 📈 Statistics Explained

### Overall Stats
- **total_matches**: Nombre TOTAL de matchs pour cette équipe/contexte
- **goals_scored**: Nombre total de buts marqués
- **avg_minute**: Minute MOYENNE où l'équipe marque (ex: 37.2)
- **std_dev**: Écart-type (ex: 5.3) → Fenêtre optimale: avg ± σ = [31.9 → 42.5]
- **minute_distribution**: Dict {minute: count} pour chaque but

### Recent Stats
- **matches**: Derniers 4 matchs (fenêtre récence)
- **goals_scored**: Buts dans ces 4 matchs
- **avg_minute**: Minute moyenne RÉCENTE
- **Boost**: Si recent_rate > overall_rate → multiplier 1.2-1.4

---

## 🧪 Testing

### Run tests:
```bash
python3 test_recurrence_system.py
```

**Output:**
```
Arsenal (HOME) vs Chelsea (AWAY) @ minute 38
  Danger Score: 26.9%
  Home Goal: 21.9%
  Away Goal: 38.7%
  Optimal Range: 32-42
  Data: Arsenal(20 matches, 4 recent) Chelsea(20 matches, 4 recent)
```

---

## 🚀 Integration with Live Monitoring

*À faire:* Intégrer RecurrencePredictor dans `main_live_predictor.py`:

```python
# main_live_predictor.py

from predictors.recurrence_predictor import RecurrencePredictor

predictor = RecurrencePredictor()

def on_match_update(match_data):
    # Live scrape data
    minute = match_data['current_minute']
    home_poss = match_data['stats']['possession']['home']
    away_poss = match_data['stats']['possession']['away']

    # Prédire
    prediction = predictor.predict_at_minute(
        home_team=match_data['home_team'],
        away_team=match_data['away_team'],
        current_minute=minute,
        home_possession=home_poss,
        away_possession=away_poss
    )

    # Logger + Décider
    if prediction['danger_score_percentage'] >= 65:
        send_alert(prediction)
```

---

## 📝 Notes

- **Corners**: NOT used (bruit)
- **Elo**: NOT used yet (default 1500)
- **Confidence**: Pas de seuil rigide, juste afficher nb matchs
- **Récence**: 4 derniers matchs (configurable)
- **TTL**: Signal vieillit exponentiellement (si needed)
- **Fenêtre minute**: Dynamic ±σ (pas fixe ±5 min)

---

## 🎯 Next Steps

1. ✅ System working end-to-end with test data
2. 📌 Integrate with live monitoring
3. 📌 Add real SoccerStats scraping for historical data
4. 📌 Backtest on past matches
5. 📌 Fine-tune seuils based on results
6. 📌 Add Telegram alerts

---

**Created:** December 3, 2025
**Status:** ✅ Core system ready, integration pending
