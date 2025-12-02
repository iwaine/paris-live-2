# Historical Data Scraper - SoccerStats.com

## Purpose

Scrape 1000-2000 historical football matches from **SoccerStats.com** to create training dataset for ML model (Phase 2).

**Target**: Binary classification model for "au moins 1 but" (at least 1 goal) prediction in intervals **[30,45]** and **[75,90]** minutes.

---

## Installation

### Prerequisites
```bash
# Ensure packages installed
pip install requests beautifulsoup4 pandas selenium

# Virtual environment (if not already activated)
source /workspaces/paris-live/.venv/bin/activate
```

### Setup
```bash
cd /workspaces/paris-live/football-live-prediction

# Make script executable
chmod +x run_historical_scraper.sh
```

---

## Usage

### Quick Start (Direct Python)
```bash
python historical_scraper.py
```

### Background Execution (Recommended)
```bash
./run_historical_scraper.sh
```

This will:
1. Run scraper in background
2. Log to `logs/historical_scraper_YYYYMMDD_HHMMSS.log`
3. Timeout after 1 hour (configurable)
4. Print summary when complete

---

## Output Format

### CSV Output: `historical_matches.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `match_id` | str | Unique match ID from SoccerStats | "12345678" |
| `match_date` | str | Match date (YYYY-MM-DD) | "2024-11-15" |
| `league` | str | League name | "france", "england", "germany", "spain", "italy" |
| `home_team` | str | Home team name | "Paris Saint-Germain" |
| `away_team` | str | Away team name | "Olympique Lyonnais" |
| `home_goals` | int | Final home goals | 2 |
| `away_goals` | int | Final away goals | 1 |
| `interval_start` | int | Interval start minute | 30 or 75 |
| `interval_end` | int | Interval end minute | 45 or 90 |
| `label` | int | **Target: 1 if goal in interval, 0 otherwise** | 1 or 0 |
| `goals_count` | int | Number of goals in interval | 0, 1, 2... |
| `goal_minutes` | str | Comma-separated goal minutes in interval | "38,42" or "" |

### Example Records
```
match_id,match_date,league,home_team,away_team,home_goals,away_goals,interval_start,interval_end,label,goals_count,goal_minutes
12345678,2024-11-15,france,Paris SG,Lyon,2,1,30,45,1,1,38
12345678,2024-11-15,france,Paris SG,Lyon,2,1,75,90,1,1,82
87654321,2024-11-14,england,Manchester United,Liverpool,0,0,30,45,0,0,
87654321,2024-11-14,england,Manchester United,Liverpool,0,0,75,90,0,0,
```

### Database Output: `paris_live.db`

SQLite database with 2 tables:

**Table: `historical_matches`**
```sql
CREATE TABLE historical_matches (
    match_id TEXT PRIMARY KEY,
    match_date TEXT,
    league TEXT,
    home_team TEXT,
    away_team TEXT,
    home_goals INTEGER,
    away_goals INTEGER,
    events_json TEXT,  -- Full events as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Table: `historical_labels`**
```sql
CREATE TABLE historical_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT,
    interval_start INTEGER,
    interval_end INTEGER,
    label INTEGER,
    goals_count INTEGER,
    goal_minutes TEXT,
    FOREIGN KEY(match_id) REFERENCES historical_matches(match_id)
);
```

---

## Scraping Strategy

### Leagues Configured
1. **France** - Ligue 1 2024-2025
2. **England** - Premier League 2024-2025
3. **Germany** - Bundesliga 2024-2025
4. **Spain** - La Liga 2024-2025
5. **Italy** - Serie A 2024-2025

### Process Per League
1. Fetch league season page
2. Extract 50 recent match links (default limit)
3. For each match:
   - Parse final score
   - Extract events (goals @ minute, cards, penalties)
   - Generate labels for [30,45] and [75,90]
4. Rate limit: 1 second between requests

### Events Extraction
Parser identifies:
- **Goals**: ⚽ (captures minute and team)
- **Red cards**: 🔴 (flagged but not used in Phase 1)
- **Yellow cards**: 🟡 (flagged but not used in Phase 1)
- **Penalties**: ✏️ (flagged but not used in Phase 1)
- **Injuries**: 🤕 (flagged but not used in Phase 1)

**Phase 1 Focus**: Goals only (labels based on goal presence in interval)

---

## Expected Output

### Typical Run (50 matches × 5 leagues = 250 matches, 500 labels)

```
🚀 Starting Historical Data Scraper for SoccerStats.com
============================================================

============================================================
🏆 SCRAPING LEAGUE: FRANCE
============================================================
📥 Fetching france (page 1)...
✅ Found 50 matches in france
📋 Processing 50 matches from france...
  [1/50] Paris SG vs Lyon...
  [2/50] Marseille vs Nice...
  ...
  [50/50] Toulouse vs Lens...

... (repeat for England, Germany, Spain, Italy) ...

============================================================
✅ TOTAL MATCHES SCRAPED: 250
============================================================

============================================================
📊 SUMMARY
============================================================
Total matches scraped: 250
CSV output: historical_matches.csv
Database output: paris_live.db
Total labels: 500
  - Label 1 (goal in interval): 287
  - Label 0 (no goal): 213
Class balance: 57.4% goal interval
============================================================
```

### Class Balance

Expected from real data:
- **~50-60% Label 1**: Matches with at least 1 goal in interval [30,45] or [75,90]
- **~40-50% Label 0**: Matches with no goals in interval

This is typically **balanced enough** for ML (no extreme class imbalance).

---

## Monitoring & Logging

### Log File
All runs logged to `logs/historical_scraper_YYYYMMDD_HHMMSS.log`

### Progress
```bash
# Watch in real-time
tail -f logs/historical_scraper_*.log
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "No score found" | SoccerStats page structure changed → update CSS selectors |
| Timeout after 1 hour | More matches needed → increase `limit_per_league` |
| Duplicate matches | SQLite `INSERT OR IGNORE` handles this |
| Missing events | Some matches may not have event data → label based on final score fallback |
| Connection errors | Check internet, add retry logic (see Phase 2) |

---

## Next Steps (Phase 2 - ML Training)

Once `historical_matches.csv` is created (500+ labels):

1. **Load CSV**:
   ```python
   import pandas as pd
   df = pd.read_csv('historical_matches.csv')
   X = df[['match_id', 'interval_start', 'home_goals', 'away_goals', ...]]
   y = df['label']
   ```

2. **Feature Engineering**:
   - Combine with live features from `feature_extractor.py`
   - Create derived features (goal_rate = goals / 90 minutes, etc.)

3. **Model Training**:
   - Use LightGBM with Stratified K-fold CV (5 folds)
   - Apply Platt scaling for calibration
   - Evaluate on test set (20% holdout)

4. **Generate Predictions**:
   - Run on live matches during play
   - Output danger scores (probability of goal in interval)

---

## Configuration (For Scaling)

To scrape more matches (e.g., 2000 total):

### Modify in `historical_scraper.py`:
```python
# In main():
matches = scraper.scrape_all_leagues(limit_per_league=200)  # 200 per league × 5 = 1000
```

### Or pass as argument (future enhancement):
```bash
python historical_scraper.py --limit-per-league 200 --leagues france england germany
```

### Estimated Time
- **50 matches/league** (250 total): ~15-30 minutes
- **200 matches/league** (1000 total): ~2-3 hours
- **500 matches/league** (2500 total): ~6-8 hours

---

## Class Distribution Analysis

After scraping, run analysis:

```python
import pandas as pd

df = pd.read_csv('historical_matches.csv')

# Label distribution
print(df['label'].value_counts())
print(f"Class balance: {df['label'].mean() * 100:.1f}% goals")

# Goals per match
goals_per_match = df.groupby('match_id')['goals_count'].max()
print(f"Avg goals per match: {goals_per_match.mean():.2f}")
print(f"Matches with 0 goals: {(goals_per_match == 0).sum()}")
print(f"Matches with 3+ goals: {(goals_per_match >= 3).sum()}")
```

---

## Production Hardening (Future)

For stable 2000+ match collection:

1. **Distributed scraping**: Multi-threaded downloads
2. **Retry logic**: Exponential backoff on connection errors
3. **Validation**: Verify scores against match date (data consistency)
4. **Incremental updates**: Daily scrape + append new matches
5. **Source rotation**: Alternate between SoccerStats, Flashscore, ESPN

---

## References

- **SoccerStats**: https://www.soccerstats.com/
- **Data format**: CSV (importable to pandas, Excel, SQL)
- **ML integration**: See `PHASE_1_IMPLEMENTATION.md` for feature pipeline
- **Next phase**: `ml_model_training.py` (to be created)

---

**Status**: Ready to run. Start scraper with `./run_historical_scraper.sh`
