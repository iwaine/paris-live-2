# PARIS LIVE PLUS - Phase 1 Implementation Guide
## Focus: Live "Au Moins 1 But" Betting (30-45', 75-90' Intervals)

**Version**: 0.1 (MVP Prototype)  
**Date**: November 2025  
**Scope**: Headless parser + Feature extraction + ML baseline

---

## 🎯 Project Vision

Build a **real-time goal prediction system** that:
1. **Monitors live matches** every 45 seconds on SoccerStats.com
2. **Targets specific intervals**: 30-45' (end of 1st half), 75-90' (end of 2nd half)
3. **Calculates danger scores** (probability of goal in interval) via ML model
4. **Emits trading signals** when statistical edge is detected (Phase 2)
5. **Only analyzes matches** where home team ≥ 5 home games AND away team ≥ 5 away games

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────┐
│ SoccerStats.com (Live Match Pages)  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Playwright Headless Parser          │
│ • Persistent page (no reload)       │
│ • MutationObserver for changes      │
│ • Polling every 45s                 │
│ • Fallback selectors (3+ per stat)  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Snapshot Cache (Rolling 20)         │
│ • Store last N snapshots            │
│ • Calculate deltas (momentum)       │
│ • Detect fresh vs stale data        │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Feature Extractor                   │
│ • 30+ features from current state   │
│ • Deltas over 5-min window         │
│ • Saturation score (10-min)        │
│ • Team Elo ratings                 │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ ML Model (LightGBM Baseline)        │
│ • P(goal in interval | features)    │
│ • Calibrated probabilities (%)      │
│ • Stratified K-fold CV              │
└────────────────┬────────────────────┘
                 │
    ┌────────────┴──────────────┐
    ▼                           ▼
┌─────────────────┐   ┌──────────────────┐
│ Penalty State   │   │ Signal Generator │
│ Machine         │   │ (Phase 2: edge   │
│ (NORMAL/SUSPEND)│   │  detection +     │
└─────────────────┘   │  trading logic)  │
                      └──────────────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │ Telegram Alert   │
                      │ (Manual betting) │
                      └──────────────────┘
```

---

## 🔧 Core Components

### 1. **Headless Parser** (`headless_parser_prototype.py`)

**Purpose**: Extract live stats from SoccerStats.com every 45 seconds without reloading.

**Key Features**:
- Persistent Playwright browser (keeps page open 6+ hours)
- MutationObserver injection (detects DOM changes)
- Fallback CSS selectors (3-4 per stat for robustness)
- User-Agent rotation (avoid bot detection)
- Health checks every 5 minutes with auto-recovery

**Output**: `MatchStats` snapshots with:
- minute, score_home/away
- possession, shots, SOT, corners
- red_cards, yellow_cards
- last_events (parsed from events list)

**Latency**: ~1-2s after page load, then ~0.5-1s per 45s poll (acceptable)

### 2. **Snapshot Cache** (built into parser)

**Purpose**: Keep rolling history for delta calculations (momentum).

**Policy**:
- Store last 20 snapshots (covers ~15 minutes @ 45s interval)
- Auto-pop oldest when limit exceeded
- Enable momentum calculation (e.g., "shots in last 5 minutes")

### 3. **Feature Extractor** (`feature_extractor.py`)

**Purpose**: Transform match stats into ML-ready feature vectors.

**Features Extracted** (30+):
- **Temporal**: minute, minute_bucket (30-35, 75-80)
- **Score**: score_home/away, goal_diff
- **Possession**: possession_home/away
- **Shots**: shots_home/away, SOT, ratios
- **Deltas (5m)**: shot changes, SOT changes, corner changes
- **Events**: red_cards, yellow_cards
- **Team Strength**: Elo_home, Elo_away, elo_diff
- **Activity**: recent_goal_count_5m, saturation_score (10m)
- **Context**: home_advantage flag

**Output**: `FeatureVector` (dict format for ML model)

### 4. **ML Model** (Phase 1 Baseline - LightGBM)

**Target Variable**: `P(goal in interval | current state)` as percentage (0-100%)

**Data Requirements**:
- 1000-2000 historical matches with labeled events
- Stratified K-fold CV (maintain class distribution)
- Platt scaling for probability calibration

**Expected Metrics**:
- AUC: 0.65-0.75 (binary classification)
- Brier score: 0.20-0.25 (probability calibration)
- Accuracy: Not used (class imbalance)

### 5. **Penalty Detection** (built into parser)

**Purpose**: Suspend market during penalty pending.

**Policy**:
- Parse events list for "penalty awarded"
- Set state machine: NORMAL → PENDING → RESOLVED
- Don't emit signals while PENDING (market frozen)
- Timeout after 2 minutes (penalty missed or incident)

### 6. **Signal Generator** (Phase 2, not yet implemented)

**Purpose**: Detect statistical edge and emit trading signals.

**Logic** (placeholder):
```
edge = P_ml(goal) - P_bookmaker(goal)
if edge > 0.08 (8% threshold) + 0.03 (slippage buffer):
    emit_signal(match_id, probability, confidence)
```

---

## 📊 Feature Engineering Details

### Minute Bucketing
Groups minutes into 5-min windows (not critical for Phase 1, useful for ML):
- 1st half: 30-35, 35-40, 40-45
- 2nd half: 75-80, 80-85, 85-90

### Saturation Score
Measures recent activity density (helps detect "open" vs "defensive" phases):
```
saturation = (goals_in_10m * 10) + (SOT_in_10m / 2)
```
- Low (0-5): Defensive, few chances
- Medium (5-20): Balanced
- High (20+): Open, many chances

### Team Elo
Pre-computed daily (via cron or manual update):
- Baseline: 1500 (neutral)
- Range: 1200-1800 (most teams)
- Updated after each match using standard Elo formula (K=32)

### Momentum (Deltas)
Changes over 5-minute window:
```
shots_delta = shots_now - shots_5m_ago
```
Captures if team is increasing offensive pressure.

---

## 🛠️ Setup & Deployment

### Prerequisites
```bash
python 3.10+
pip install playwright lightgbm scikit-learn pandas numpy loguru
playwright install chromium
```

### Phase 1 Minimal Setup

1. **Update requirements.txt**:
   ```bash
   pip install playwright lightgbm scikit-learn
   ```

2. **Run feature extractor test**:
   ```bash
   cd /workspaces/paris-live/football-live-prediction
   python feature_extractor.py
   ```
   Expected: Feature dict printed (no browser needed)

3. **Test headless parser** (requires real match URL):
   ```bash
   # Edit headless_parser_prototype.py: set real SoccerStats match URL
   python headless_parser_prototype.py --duration 300  # 5 min test
   ```

### Phase 1 Timeline

| Week | Task | Deliverable | Effort |
|------|------|-------------|--------|
| 1    | Headless parser proto + hist scraper | Live stats stream + 1000 matches | 3-4 days |
| 2    | Feature extractor + ML baseline | LightGBM model trained | 2-3 days |
| 3    | Integration (5 matches live sim) + penalty detection | Full pipeline working | 2-3 days |
| 4    | Backtesting + deployment | MVP ready | 1-2 days |

---

## 📊 Limits & Solutions (Quick Reference)

| Limit | Severity | Solution |
|-------|----------|----------|
| 40+ matches RAM/CPU | HIGH | Tier-1 (1-10), Tier-2 later |
| Match eligibility (≥5 games) | MED | Pre-screen @06:00 daily |
| 45s headless latency | HIGH | Persistent page + Observer |
| Historical data | HIGH | SoccerStats scraper (1-2 days) |
| Feature parsing | MED | Fallback selectors (3+) |
| ML calibration | HIGH | K-fold CV + Platt scaling |
| Penalty suspension | MED | Event parser + state machine |
| Data freshness | MED | TTL signals (60s) + age discount |
| Browser crashes | MED | Health checks + auto-recovery |

---

## ⚠️ Known Limitations & Trade-offs

1. **Minute-level precision only**: SoccerStats doesn't provide second-level timestamps
   - Impact: Can't distinguish "45:00" vs "45:59"
   - Workaround: Use minute bucket + assume events spread uniformly

2. **No official SoccerStats API**:
   - Impact: Scraping must handle page changes
   - Workaround: Fallback selectors + regular monitoring

3. **Class imbalance**: P(goal | 15-min window) ≈ 30-40%
   - Impact: Model biases toward "no goal"
   - Workaround: Class weighting + proper metrics (AUC, Brier, not accuracy)

4. **Penalty market suspension**:
   - Impact: Can't bet during penalty pending (15-30s)
   - Workaround: Track penalty state, pause signal emission

5. **Slippage in live betting**:
   - Impact: Odds move faster than we can compute
   - Workaround: Add 3% slippage buffer to edge threshold

---

## 🎯 Phase 2 (Future) - Trading Signals

Once Phase 1 is stable (1-2 weeks):
1. Integrate bookmaker odds API (Betfair or scraper)
2. Implement edge detection (P_ml - P_book)
3. Add Kelly staking formula
4. Backtesting on historical odds
5. Live trading automation (or manual Telegram alerts)

---

## 📝 Testing Checklist

- [ ] Feature extractor: runs without errors
- [ ] Headless parser: opens page, captures snapshot
- [ ] Snapshot cache: accumulates & calculates deltas
- [ ] Penalty detection: parses events, detects penalty
- [ ] ML baseline: trains on 500+ historical matches
- [ ] Signal generation: emits when edge > threshold
- [ ] Integration: pipeline runs 5 live matches in parallel
- [ ] Backtesting: ROI calculation on historical odds

---

## 📞 Support & Questions

See `LIMITS_AND_SOLUTIONS.md` for detailed technical explainers.
