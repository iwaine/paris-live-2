# 🔍 Scraping - Quick Reference

## 📊 Données Historiques

### Fichier Principal: `soccerstats_live_selector.py`

**Quoi**: Scrape les matchs HISTORIQUES (terminés)

**Commande**:
```bash
python3 soccerstats_live_selector.py
```

**Résultat**: Table `soccerstats_scraped_matches` avec:
- 1120 matches scraped
- home_team_name, away_team_name
- league_name
- date, score final
- **Goal times** (minute + équipe pour chaque but)
- Lieux: PL, LaLiga, Serie A, Bundesliga, Ligue 1

**Output Example**:
```
AC Milan 2:1 Inter
  Goals:
    23' AC Milan
    45' Inter  
    78' AC Milan
```

**Utilité**: 
- Créer les patterns recurrence (31-45 & 76-90)
- Analyser où les équipes marquent des buts
- Dataset pour machine learning

---

## 🔴 Données Live (Temps Réel)

### Fichier Principal: `soccerstats_live_scraper.py`

**Quoi**: Scrape UN MATCH EN DIRECT

**Classe**: `SoccerStatsLiveScraper`

**Utilisation**:
```python
from soccerstats_live_scraper import SoccerStatsLiveScraper, LiveMatchData

scraper = SoccerStatsLiveScraper()
live_data = scraper.scrape_match("https://www.soccerstats.com/match/...")

# Output: LiveMatchData
live_data.home_team         → "AC Milan"
live_data.away_team         → "Inter"
live_data.minute            → 35 (minute actuelle)
live_data.score_home        → 1
live_data.score_away        → 0
live_data.possession_home   → 0.65 (65%)
live_data.shots_home        → 5
live_data.sot_home          → 2 (shots on target)
live_data.dangerous_attacks_home → 3
```

**Résultat**: `LiveMatchData` avec 20+ métriques en temps réel

**Utilité**:
- Monitoring live du match
- Extraction de stats instantanées
- Input pour prédictions

---

## 🎯 Détection Automatique de Matchs Live

### Fichier: `soccerstats_live_selector.py`

**Fonction**: `get_live_matches()`

**Utilisation**:
```python
from soccerstats_live_selector import get_live_matches

matches = get_live_matches()
# Retourne: Liste des URLs de matchs live maintenant

for url in matches:
    print(f"Live: {url}")
    # https://www.soccerstats.com/match/...
    # https://www.soccerstats.com/match/...
    # etc.
```

**Résultat**: Liste des matchs en direct actuellement

**Utilité**:
- Détecter automatiquement quels matchs sont en direct
- Lancer des monitors en parallèle
- Auto-discovery de matchs

---

## 📋 Résumé Rapide

| Besoin | Fichier | Fonction | Input | Output |
|--------|---------|----------|-------|--------|
| **Scraper historique** | `soccerstats_live_selector.py` | `main()` | Rien | DB (1120 matches) |
| **Scraper un match live** | `soccerstats_live_scraper.py` | `scrape_match(url)` | URL | `LiveMatchData` |
| **Détecter matchs live** | `soccerstats_live_selector.py` | `get_live_matches()` | Rien | Liste URLs |

---

## 🚀 Workflows

### Workflow 1: Construire Dataset (UNE FOIS)
```bash
# Scrape tous les matchs historiques
python3 soccerstats_live_selector.py

# Résultat: soccerstats_scraped_matches (1120 records)
# Utilisé pour: Recurrence patterns
```

### Workflow 2: Monitor Un Match Live
```python
from soccerstats_live_scraper import SoccerStatsLiveScraper

url = "https://www.soccerstats.com/match/123456789"

scraper = SoccerStatsLiveScraper()
while True:
    data = scraper.scrape_match(url)
    print(f"{data.home_team} {data.score_home}:{data.score_away} {data.away_team}")
    time.sleep(8)  # Throttle 8 sec
```

### Workflow 3: Monitor Tous les Matchs Live
```python
from soccerstats_live_selector import get_live_matches
from live_goal_monitor_with_alerts import LiveGoalMonitor

matches = get_live_matches()

for url in matches:
    monitor = LiveGoalMonitor(url)
    monitor.start()  # Thread daemon

# Monitors tous les matchs en parallèle
```

---

## ⚠️ Important

### Throttling (Respecter robots.txt)
- Minimum **3 secondes** entre requêtes au même domaine
- Déjà implémenté dans `SoccerStatsLiveScraper`

### Limitations
- SoccerStats peut bloquer si trop de requêtes
- Solution: Augmenter `throttle_seconds`

### Data Completeness
- **Historique**: Données complètes (tout est terminé)
- **Live**: Données partielles (match en cours)

---

## 📚 Références

```python
# Import pour historique
from soccerstats_live_selector import get_live_matches

# Import pour live
from soccerstats_live_scraper import SoccerStatsLiveScraper, LiveMatchData

# Monitoring
from live_goal_monitor_with_alerts import LiveGoalMonitor
```

---

**Summary**: 
- 📊 **Historique**: `soccerstats_live_selector.py` (batch mode)
- 🔴 **Live**: `soccerstats_live_scraper.py` (single match)
