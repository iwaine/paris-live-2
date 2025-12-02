# 📊 PARIS LIVE - COMPRENDRE LE SCORING ET LA DÉCISION

## Vue d'ensemble

Le système fonctionne en **8 étapes** pour transformer les données de match en **DÉCISION D'ACHAT (BUY) ou ATTENDRE (SKIP)**.

---

## 🔄 FLUX COMPLET

```
DONNÉES MATCH EN DIRECT
        ↓
[ÉTAPE 1] Vérifier l'intervalle de minute
        ↓ (Doit être [30-45] ou [75-90])
[ÉTAPE 2] Extraire 30 features du match
        ↓
[ÉTAPE 3] Normaliser avec StandardScaler
        ↓
[ÉTAPE 4] Modèle LightGBM → Probabilité (0-1)
        ↓
[ÉTAPE 5] Calculer Danger Score = Prob × 100%
        ↓
[ÉTAPE 6] Appliquer pénalité (si penalty actif)
        ↓
[ÉTAPE 7] Appliquer décroissance TTL exponentielle
        ↓
[ÉTAPE 8] Vérifier seuils (Confiance & Danger)
        ↓
   DÉCISION: BUY ou SKIP
```

---

## 📝 LES 30 FEATURES

Les 30 features extraites des stats live du match :

### Temps & Structure (2)
- `minute` : Minute du match (0-90)
- `minute_bucket` : Intervalle ("30-35", "35-40", etc.)

### Score & But (4)
- `score_home` : Buts marqués à domicile
- `score_away` : Buts marqués à l'extérieur
- `goal_diff` : Différence de buts
- `recent_goal_count_5m` : Buts dans les 5 dernières minutes

### Possession (2)
- `possession_home` : % possession domicile
- `possession_away` : % possession extérieur

### Tirs (8)
- `shots_home` / `shots_away` : Tirs totaux
- `sot_home` / `sot_away` : Tirs cadrés
- `shot_accuracy_home` / `shot_accuracy_away` : Ratio de précision
- `shots_delta_5m_home` / `shots_delta_5m_away` : Tirs dernières 5 min

### Corners & Actions (6)
- `corners_home` / `corners_away` : Corners totaux
- `corners_delta_5m_home` / `corners_delta_5m_away` : Corners 5 dernières min
- `sot_delta_5m_home` / `sot_delta_5m_away` : Tirs cadrés 5 dernières min

### Cartons (4)
- `red_cards_home` / `red_cards_away` : Cartons rouges
- `yellow_cards_home` / `yellow_cards_away` : Cartons jaunes

### Force des Équipes (4)
- `team_elo_home` : Rating Elo domicile (~1500 moyen)
- `team_elo_away` : Rating Elo extérieur
- `elo_diff` : Différence d'Elo
- `saturation_score` : Intensité globale du jeu

---

## 🧠 LE MODÈLE ML (LightGBM)

```
ENTRÉE: Vecteur de 30 features
   ↓
StandardScaler: Normalisation pour mise à l'échelle
   ↓
LightGBM Classifier: Apprentissage graduel
   ↓
SORTIE: Probabilité P(≥1 but dans cet intervalle)
   ↓
   P ∈ [0.0, 1.0]
```

### Qu'apprend le modèle ?

Le modèle détecte les **patterns** qui précèdent un but :
- ✅ Possession élevée + tirs nombreux = souvent un but
- ✅ Corners successifs = augmente chance de but
- ✅ Tirs cadrés en accélération = signal fort
- ❌ Peu de shots malgré possession = signal faible
- ❌ Défenses serrées (peu de corners) = peu de buts

### Performance du Modèle

```
LightGBM Classifier (Trained)
├─ AUC Score: 0.7543 ✅
├─ Accuracy: ~75%
├─ Precision: ~32%
├─ Feature Importance: minute, possession, shots, corners
└─ Dataset: 1000 labeled historical matches
```

---

## 📊 CALCUL DU DANGER SCORE

### Formule Simple

```
Danger Score (%) = Probabilité du Modèle × 100
```

### Exemple Concret

```
Entrée:  PSG 2-1 Marseille (Minute 38, 9 tirs, 55% possession)
         ↓
         Features calculées (30 valeurs)
         ↓ StandardScaler
         ↓ LightGBM
         Probabilité = 0.68
         ↓
Danger Score = 0.68 × 100 = 68% ✅
```

### Interprétation

| Score | Signification |
|-------|--------------|
| 0-20% | Très peu de chances d'un but |
| 20-40% | Peu de chances |
| 40-60% | Moyennes chances |
| 60-80% | **Chances élevées ⚠️** |
| 80-100% | **Très fortes chances 🔴** |

---

## 🔻 DÉCROISSANCE EXPONENTIELLE TTL

### Pourquoi ?

Le signal perd de sa valeur avec le temps. Un tir cadré il y a 30 secondes est plus pertinent qu'un tir cadré il y a 8 minutes.

### Formule

```
freshness_factor = e^(-signal_age / TTL)

où:
- signal_age = temps depuis le dernier update (en secondes)
- TTL = Time To Live = 300 secondes (5 minutes)
```

### Exemples de Décroissance

Pour un danger_score brut de **68%** :

| Âge Signal | Facteur Frais | Score Ajusté |
|-----------|--------------|-------------|
| 0s | 1.000 | 68.0% ✅ Neuf |
| 30s | 0.905 | 61.5% ✅ Bon |
| 60s | 0.819 | 55.7% ✅ Acceptable |
| 150s | 0.606 | 41.2% ⚠️ Affaibli |
| 300s | 0.368 | 25.0% ❌ Très faible |
| 450s | 0.223 | 15.2% ❌ Quasi-mort |
| 600s | 0.135 | 9.2% ❌ Ignoré |

### Visualisation Graphique

```
Force du Signal (%)
│
100│ ●
   │  ╲
 80│   ╲
   │    ╲
 60│     ╲___
   │         ╲___
 40│             ╲___
   │                 ╲___
 20│                     ●─────
   │                          
  0│─────────────────────────────
   0    100   200   300   400   500
         Âge du Signal (secondes)
```

---

## ✅ LES 5 FILTRES DE DÉCISION

Tous ces filtres doivent passer pour un **BUY** :

### Filtre 1: INTERVALLE DE MINUTE
```
✅ PASS si: minute ∈ [30-45] ou [75-90]
❌ FAIL si: minute ∈ [0-30) ou (45-75) ou (90-∞)

Exemple:
  ✅ minute=38 → PASS (dans [30-45])
  ❌ minute=50 → FAIL (dans la zone morte [45-75])
```

### Filtre 2: MARCHÉ SUSPENDU (PENALTY)?
```
❌ FAIL si: penalty_active = True
✅ PASS si: penalty_active = False

Raison: Après un penalty, l'imprédictibilité augmente
        → Confidence divisée par 2 pendant 120s
```

### Filtre 3: ÂGE DU SIGNAL (TTL)
```
✅ PASS si: signal_age ≤ 300 secondes
❌ FAIL si: signal_age > 300 secondes

Raison: Signal trop vieux = information périmée
```

### Filtre 4: SEUIL DE CONFIANCE (Conservative)
```
Threshold = 50%

✅ PASS si: confidence ≥ 50%
❌ FAIL si: confidence < 50%

Exemples:
  ✅ confidence = 64.7% → PASS
  ❌ confidence = 41.2% → FAIL
```

### Filtre 5: SEUIL DE DANGER (Conservative)
```
Threshold = 50%

✅ PASS si: danger_score ≥ 50%
❌ FAIL si: danger_score < 50%

Exemples:
  ✅ danger = 68% → PASS
  ❌ danger = 35% → FAIL
```

---

## 🎯 PRISE DE DÉCISION FINALE

### Cas 1: Signal Accepté ✅

```
Tous les filtres passent:
  ✅ Minute 38 ∈ [30-45]
  ✅ Pas de penalty
  ✅ Signal age 15s < 300s
  ✅ Confidence 64.7% > 50%
  ✅ Danger 68% > 50%

→ DÉCISION: BUY ✅
→ ACTION: Alerte Telegram
→ MESSAGE: "Au moins 1 but attendu"
```

### Cas 2: Signal Rejeté ❌

```
Exemple 1 - Hors intervalle:
  ❌ Minute 50 ∉ [30-45] et ∉ [75-90]
  → RAISON: MINUTE_OUT_OF_RANGE
  → DÉCISION: SKIP

Exemple 2 - Confiance trop faible:
  ❌ Confidence 41.2% < 50%
  → RAISON: LOW_CONFIDENCE
  → DÉCISION: SKIP

Exemple 3 - Signal trop vieux:
  ❌ Signal age 350s > 300s
  → RAISON: SIGNAL_STALE
  → DÉCISION: SKIP

Exemple 4 - Penalty actif:
  ❌ Penalty active depuis 15s
  → RAISON: MARKET_SUSPENDED
  → DÉCISION: SKIP
```

---

## 📈 STRATÉGIES DE SEUILS

### Conservative (ACTUELLE ⭐)
```
Confidence Threshold: 50%
Danger Threshold: 50%

→ Moins de faux positifs
→ Signaux de haute qualité
→ Win Rate (backtest): 35.1%
→ Bets Triggered: 22.9%
```

### Moderate
```
Confidence Threshold: 30%
Danger Threshold: 35%

→ Plus de signaux
→ Qualité moyenne
→ Win Rate (backtest): 32.0%
→ Bets Triggered: 35%
```

### Aggressive
```
Confidence Threshold: 20%
Danger Threshold: 25%

→ Beaucoup de signaux (bruit)
→ Qualité faible
→ Win Rate (backtest): ~28%
→ Bets Triggered: 50%+
```

---

## 🔍 OUTILS DE DEBUG

### 1. Visualiser le Scoring
```bash
python SCORING_EXPLANATION.py
```
Affiche l'explication complète du système

### 2. Tester le Scoring
```bash
python scoring_debugger.py
```
Interface interactive pour tester avec des valeurs personnalisées

### 3. Backtesting Results
```bash
# Voir les décisions historiques
sqlite3 data/production.db \
  "SELECT * FROM predictions LIMIT 10;"
```

---

## 📋 RÉSUMÉ RAPIDE

| Étape | Quoi | Entrée | Sortie |
|-------|------|--------|--------|
| 1 | Check interval | Minute | PASS/FAIL |
| 2 | Extract features | Stats live | 30 features |
| 3 | Normalize | 30 features | Scaled features |
| 4 | ML Model | Scaled features | Probability |
| 5 | Danger Score | Probability | Score (0-100%) |
| 6 | Penalty Check | penalty_flag | Score ajusté |
| 7 | TTL Decay | signal_age | Confidence finale |
| 8 | Check Filters | Confidence, Danger | BUY ou SKIP |

---

## 💡 POINTS CLÉS À RETENIR

1. **Le modèle prédit la probabilité d'au moins 1 but**
   - Non la prédiction exacte du score
   - Basé sur 30 features de stats live

2. **Le score diminue exponentiellement avec le temps**
   - TTL = 300 secondes
   - e^(-t/300) = force restante

3. **2 seuils doivent passer (Conservative)**
   - Confiance ≥ 50%
   - Danger ≥ 50%

4. **3 zones de minute**
   - [30-45] ✅ Zone 1
   - (45-75) ❌ Zone morte
   - [75-90] ✅ Zone 2

5. **Penalty = signal moins fiable**
   - Marché suspendu pendant 120s
   - Confiance × 0.5 pendant cette période

---

Veux-tu **tester le debugger** avec des valeurs personnalisées ?

```bash
python scoring_debugger.py
# puis choisir: 1, 2, 3, 4, 5 ou 'custom'
```
