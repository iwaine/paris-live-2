# Phase 1 → Phase 2 Transition Guide

## 🎯 Overview

This document explains how to transition from **Phase 1 (Data Collection)** to **Phase 2 (ML Training & Live Prediction)**.

**Phase 1 Status**: ✅ COMPLETE (4 components, 9/9 tests passing)  
**Phase 2 Status**: 🔄 READY TO START (template provided, awaiting historical data)

---

## 📋 Phase 1 Completion Checklist

Before starting Phase 2, verify:

- ✅ `headless_parser_prototype.py` created (600+ lines)
- ✅ `feature_extractor.py` created + tested (350+ lines, 1/1 test pass)
- ✅ `historical_scraper.py` created + tested (600+ lines, 9/9 tests pass)
- ✅ Documentation complete (2 guides: `PHASE_1_IMPLEMENTATION.md`, `LIMITS_AND_SOLUTIONS.md`)
- ✅ All files in `/workspaces/paris-live/football-live-prediction/`

### Verify Installation
```bash
cd /workspaces/paris-live/football-live-prediction

# Check all Phase 1 files exist
ls -la headless_parser_prototype.py feature_extractor.py historical_scraper.py
# Output: all 3 files should be listed

# Run tests
python test_scraper_comprehensive.py
# Expected: "✅ TESTS PASSED: 9/9"
```

---

## 🚀 Phase 2 Components

### 1️⃣ Data Preparation (Complete Phase 1 Scraper First)

**Status**: Waiting for historical data  
**Prerequisite**: Run Phase 1 historical scraper

```bash
# Generate 1000-2000 historical matches with labels
python historical_scraper.py

# Output: historical_matches.csv (ready for ML training)
```

**Expected output format** (from Phase 1):
```csv
match_id,match_date,league,home_team,away_team,home_goals,away_goals,interval_start,interval_end,label,goals_count,goal_minutes
12345678,2024-11-15,france,Paris SG,Lyon,2,1,30,45,1,1,38
...
```

### 2️⃣ ML Model Training

**File**: `ml_model_training.py` (ready to use)  
**Status**: Template created, ready for real data  

**What it does**:
1. Load `historical_matches.csv`
2. Prepare 28 features (from Phase 1 features)
3. Train LightGBM with Stratified 5-fold CV
4. Apply Platt scaling for probability calibration
5. Save trained model + scaler

**Usage**:
```bash
# Ensure historical data exists
ls historical_matches.csv

# Run training
python ml_model_training.py

# Output:
# - models/au_moins_1_but_model.pkl (trained model)
# - models/scaler.pkl (feature scaler)
# - Console logs showing CV scores, test AUC, feature importance
```

**Expected output**:
```
✅ CV completed:
   Mean AUC: 0.72-0.78 (typical range)
   Overall AUC: 0.74-0.79

✅ Final model trained:
   Test AUC: 0.71-0.76
   
📊 Top 10 features:
   saturation_score, elo_diff, shot_delta_5m, recent_goal_count_5m, ...
```

### 3️⃣ Live Prediction Pipeline

**Status**: Template provided in `live_predictor_prototype.py` (to be created)  
**Purpose**: Integrate parser + features + model for real-time predictions

**Pseudocode** (to implement):
```python
# Pseudo-implementation (Phase 2)
from headless_parser_prototype import HeadlessMatchParser
from feature_extractor import FeatureExtractor
from ml_model_training import ModelLoader  # Load trained model

parser = HeadlessMatchParser()
parser.initialize()
extractor = FeatureExtractor()
model = ModelLoader.load('models/au_moins_1_but_model.pkl')

while match_is_live:
    # Capture live snapshot
    snapshot = parser.capture_snapshot()
    
    # Extract 28 features
    features = extractor.extract_features(snapshot)
    
    # Predict danger score
    danger_score = model.predict_proba(features)[1]  # 0-100%
    
    # Output to Telegram / trading API
    send_alert(match_id, danger_score)
    
    # Wait 45 seconds
    time.sleep(45)
```

### 4️⃣ Penalty Detection & Market Suspension

**Status**: Design complete (in `LIMITS_AND_SOLUTIONS.md`), code to be created  
**Purpose**: Freeze predictions when penalty is called

**State machine**:
```
NORMAL
  ↓ (penalty detected)
PENDING (freeze predictions)
  ↓ (penalty scored or missed)
RESOLVED (resume predictions)
  ↓ (after 2min OR match resumes)
NORMAL
```

### 5️⃣ Error Handling & Auto-Recovery

**Status**: Design complete, code to be created  
**Purpose**: Keep predictions running 24/7 without manual intervention

**Features**:
- Health checks every 5 minutes
- Auto-reconnect on network failure
- Fallback to previous valid snapshot if current fails
- Exponential backoff for retries

---

## 📊 Data Flow Architecture

```
Phase 1 Outputs                Phase 2 Processes              Phase 2 Outputs
─────────────────              ─────────────────              ──────────────

historical_scraper.py    →    ML Training    →    model.pkl
    ↓                         + Calibration           ↓
historical_matches.csv   →    (ml_model_training.py) ↓
    (1000-2000 labels)                               ↓
                         ┌─ Live Predictor ←────────┘
                         │    (pipeline)
                         │       ↓
headless_parser          │    Parse live stats
+ feature_extractor  ────→    Extract 28 features
    ↓                    │    Predict danger score
Live match data       ────→    Check penalty state
    ↓                    │    Output alert
SoccerStats.com      ────→    ↓
                              Telegram / Betting API
                         │    (Phase 3)
                         └────────┘
```

---

## 🗓️ Recommended Timeline

### Phase 2 Execution Timeline

| Days | Task | Effort | Status |
|------|------|--------|--------|
| **Day 1** | Run Phase 1 historical scraper (250-2500 matches) | 1-3h | 🔄 Ready |
| **Day 2-3** | ML model training + calibration | 1-2 days | 📋 Template ready |
| **Day 4** | Penalty detection state machine | 1-2 hours | 📋 Design complete |
| **Day 5** | Live prediction pipeline integration | 2-3 hours | 📋 Pseudocode ready |
| **Day 6** | Error handling + auto-recovery | 1-2 hours | 📋 Design complete |
| **Day 7** | Integration testing (5 matches simulated) | 2-3 hours | 📋 Checklist ready |

**Total Phase 2 Duration**: 4-7 days

**Recommended Start Date**: December 1-5, 2025  
**Projected Completion**: December 8-15, 2025

---

## 🔧 Implementation Steps

### Step 1: Generate Historical Data (Day 1)

```bash
# Navigate to project directory
cd /workspaces/paris-live/football-live-prediction

# Run scraper (will take 1-3 hours for 250+ matches)
python historical_scraper.py

# Verify output
ls -lh historical_matches.csv
wc -l historical_matches.csv  # Should be ~501 lines (250 matches × 2 + header)
```

### Step 2: Train ML Model (Day 2-3)

```bash
# Verify historical data exists
head -5 historical_matches.csv

# Run training (will take 5-15 minutes)
python ml_model_training.py

# Verify model saved
ls -la models/
# Should show: au_moins_1_but_model.pkl, scaler.pkl
```

### Step 3: Test Model with Live Data (Day 3-4)

**Pseudo-code for testing** (create `test_live_prediction.py`):
```python
import pickle
import numpy as np
from feature_extractor import FeatureExtractor

# Load trained model
with open('models/au_moins_1_but_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Load scaler
with open('models/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Test with mock live data
mock_snapshot = {...}  # Simulate live match snapshot
features = FeatureExtractor().extract_features(mock_snapshot)

# Predict
danger_score = model.predict_proba(scaler.transform([features]))[0][1]
print(f"Danger score: {danger_score * 100:.1f}%")
```

### Step 4: Build Penalty Detection (Day 4-5)

**Key functions**:
- `parse_event()`: Extract event from live HTML
- `PenaltyStateMachine`: Track penalty state (NORMAL/PENDING/RESOLVED)
- `should_predict()`: Return False if PENDING

### Step 5: Integrate Pipeline (Day 5-6)

**Main loop** (create `live_predictor_pipeline.py`):
```python
while match_is_live:
    # Step 1: Capture snapshot
    snapshot = parser.capture_snapshot()
    
    # Step 2: Extract features
    features = extractor.extract_features(snapshot)
    
    # Step 3: Check penalty state
    penalty_state = penalty_machine.get_state()
    if penalty_state == 'PENDING':
        logger.info("⏸️  Penalty detected, predictions frozen")
        time.sleep(45)
        continue
    
    # Step 4: Predict
    danger_score = model.predict_proba(scaler.transform([features]))[0][1]
    
    # Step 5: Output
    if danger_score > 0.65:  # Confidence threshold
        send_telegram_alert(match_id, danger_score)
    
    # Step 6: Wait 45 seconds
    time.sleep(45)
```

### Step 6: Testing & Validation (Day 7)

**Integration test checklist**:
- [ ] Parser captures 5 snapshots in a row
- [ ] Feature extraction produces 28 valid features
- [ ] Model predictions fall in [0, 1] range
- [ ] Penalty state machine transitions correctly
- [ ] Alerts sent to Telegram
- [ ] Auto-recovery works after 1 simulated failure
- [ ] Total latency < 50s per cycle (meets 45s spec with buffer)

---

## 📦 Deliverables Phase 2

### Files to Create

| File | Purpose | Effort |
|------|---------|--------|
| `ml_model_training.py` | ML training pipeline | ✅ Ready (template provided) |
| `penalty_state_machine.py` | Penalty detection + state | 2 hours |
| `live_predictor_pipeline.py` | Main prediction loop | 3 hours |
| `test_live_prediction.py` | Integration tests | 2 hours |
| `PHASE_2_IMPLEMENTATION.md` | Phase 2 guide (similar to Phase 1) | 1 hour |

### Files to Modify

| File | Changes |
|------|---------|
| `config.yaml` | Add penalty detection thresholds |
| `headless_parser_prototype.py` | Optimize latency (if needed) |
| `feature_extractor.py` | Add penalty flag to features |

---

## 🎓 Key Learnings from Phase 1 → Phase 2

### 1. Feature Consistency
**Issue**: Phase 1 features might not align with Phase 2 live features  
**Solution**: Test feature extraction on real live data (Phase 2 Day 3)

### 2. Model Performance
**Expectation**: Test AUC ~0.75 (good but not perfect)  
**Action**: If AUC < 0.65, investigate feature quality or add more historical data

### 3. Penalty Handling Complexity
**Note**: Penalty detection timing is critical (must freeze BEFORE market moves)  
**Solution**: Test with multiple bookmakers to find optimal threshold

### 4. Latency Buffer
**Spec**: 45s update cadence  
**Reality**: Aim for 40s actual (5s buffer for network delays)

---

## 🚨 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'lightgbm'` | LightGBM not installed | `pip install lightgbm scikit-learn` |
| `historical_matches.csv not found` | Phase 1 scraper not run | Run `python historical_scraper.py` |
| Model AUC very low (<0.55) | Features are wrong/missing | Check feature_extractor output format |
| Penalty state machine stuck | Event parsing missed penalty | Add fallback event parser (ESPN, Flashscore) |
| Predictions very slow (>60s) | Feature extraction bottleneck | Profile with `cProfile`, optimize loops |

---

## 📞 Phase 2 Support

### Documentation Files
- `PHASE_1_COMPLETION_SUMMARY.md` - Phase 1 status (this session)
- `LIMITS_AND_SOLUTIONS.md` - Technical deep-dive (all 9 limits + solutions)
- `PHASE_1_IMPLEMENTATION.md` - Architecture reference

### Template Files
- `ml_model_training.py` - Training pipeline (ready to use)
- `headless_parser_prototype.py` - Live parser (from Phase 1)
- `feature_extractor.py` - Feature extraction (from Phase 1)

### Code References
- LightGBM: https://lightgbm.readthedocs.io/
- Platt scaling: https://en.wikipedia.org/wiki/Platt_scaling
- K-fold CV: https://scikit-learn.org/stable/modules/cross_validation.html

---

## ✅ Phase 1 → Phase 2 Handoff Checklist

Before declaring Phase 2 ready:

- [ ] All Phase 1 files exist and pass tests
- [ ] Historical scraper produces valid `historical_matches.csv`
- [ ] ML training script (`ml_model_training.py`) created and tested
- [ ] Model successfully trains on historical data (AUC > 0.60)
- [ ] Penalty detection design reviewed and approved
- [ ] Live pipeline pseudocode documented
- [ ] Error handling strategy defined
- [ ] Testing plan created
- [ ] Timeline agreed (4-7 days for Phase 2)

---

## 🎉 Next Actions

**For Phase 2 Start**:

1. ✅ Run `python historical_scraper.py` (generates training data)
2. ✅ Run `python ml_model_training.py` (trains model)
3. ✅ Create `penalty_state_machine.py` (penalty detection)
4. ✅ Create `live_predictor_pipeline.py` (main loop)
5. ✅ Integration testing (5 matches simulated)
6. ✅ Deploy to production (Phase 3)

**Status**: Ready to proceed  
**Timeline**: December 1-15, 2025 (estimated)

---

*Generated: November 28, 2025*  
*Phase 1: COMPLETE ✅ | Phase 2: READY TO START 🚀*
