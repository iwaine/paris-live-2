# 📚 COMPRENDRE LE SYSTÈME PARIS LIVE

## En 5 Minutes

### Ce que fait PARIS LIVE
1. **Scrape les matchs en direct** → Récupère stats live toutes les 45 secondes
2. **Calcule 30 features** → Possession, tirs, corners, cartons, etc.
3. **Modèle ML LightGBM** → Prédit probabilité d'au moins 1 but
4. **Applique décroissance TTL** → Signal perd de la force avec le temps
5. **Filtre strictement** → Confiance & Danger > seuils
6. **Envoie alerte Telegram** → Si signal passe TOUS les filtres

### Le Résultat
```
BUY ✅ → Alerte Telegram "Au moins 1 but attendu"
SKIP ❌ → Rien (attendre)
```

---

## Les 8 Étapes (Détaillées)

### [ÉTAPE 1] DONNÉES BRUTES DU MATCH
```
Input: Stats live (minute, tirs, possession, corners, etc.)
Output: Données structurées
```

### [ÉTAPE 2] VÉRIFICATION DE L'INTERVALLE
```
Condition: minute ∈ [30-45] ou [75-90]
Si NON → STOP, décision = SKIP
Si OUI → Continue
```

### [ÉTAPE 3] EXTRACTION DE 30 FEATURES
```
Features extraites:
  - minute, score, possession
  - tirs, tirs cadrés, corners
  - cartons, Elo des équipes
  - évolution en 5 dernières minutes
  
Output: Vecteur de 30 valeurs
```

### [ÉTAPE 4] NORMALISATION (StandardScaler)
```
Transformation: Chaque feature centrée-réduite
Raison: Modèle ML fonctionne mieux avec données normalisées
```

### [ÉTAPE 5] MODÈLE LightGBM
```
Input: 30 features normalisées
Processing: 100+ arbres de décision
Output: Probabilité P(≥1 but) ∈ [0.0, 1.0]
```

### [ÉTAPE 6] DANGER SCORE
```
Formula: danger_score = probability × 100
Example: 0.68 × 100 = 68%
```

### [ÉTAPE 7] DÉCROISSANCE TTL
```
Formula: freshness = e^(-age / 300)
Effect: Signal s'affaiblit exponentiellement
       → Après 300s: Signal à 36.8% de force
       → Après 600s: Signal presque mort
```

### [ÉTAPE 8] VÉRIFICATION DES FILTRES
```
5 filtres doivent tous passer:
1. ✅ Minute dans [30-45] ou [75-90]
2. ✅ Pas de penalty actif
3. ✅ Signal age < 300s
4. ✅ Confidence > 50%
5. ✅ Danger > 50%

Si OUI à tous: BUY ✅
Si NON à l'un: SKIP ❌
```

---

## Cas d'Usage Réel

### Cas 1: SIGNAL BON (BUY) ✅

```
PSG 2-1 Marseille
├─ Minute: 38 ✅ (dans [30-45])
├─ Tirs: 9 vs 6 ✅ (PSG domine)
├─ Possession: 55% vs 45% ✅ (PSG domine)
├─ Corners: 4 vs 2 ✅ (PSG domine)
├─ Signal age: 15s ✅ (très frais)
└─ Pas de penalty ✅

Modèle ML → Probabilité: 68%
Danger Score: 68% ✅ (> 50%)
TTL Decay: 68% × 0.9512 = 64.7% ✅ (> 50%)

DÉCISION: BUY ✅
ACTION: Alerte Telegram
```

### Cas 2: SIGNAL FAIBLE (SKIP) ❌

```
Lyon 1-0 Monaco
├─ Minute: 42 ✅ (dans [30-45])
├─ Tirs: 5 vs 5 ❌ (équilibré)
├─ Possession: 48% vs 52% ❌ (Monaco domine!)
├─ Corners: 2 vs 2 ❌ (équilibré)
├─ Signal age: 45s ✅ (frais)
└─ Pas de penalty ✅

Modèle ML → Probabilité: 35%
Danger Score: 35% ❌ (< 50%)
TTL Decay: 35% × 0.942 = 33% ❌ (< 50%)

DÉCISION: SKIP ❌ (signal trop faible)
RAISON: LOW_DANGER (35% < 50%)
```

### Cas 3: SIGNAL ANCIEN (SKIP) ❌

```
Real 2-1 Barcelona
├─ Minute: 38 ✅ (dans [30-45])
├─ Tirs: 8 vs 7 ✅ (Real domine)
├─ Possession: 60% vs 40% ✅ (Real domine)
├─ Signal age: 350s ❌ (TROP VIEUX!)
└─ Pas de penalty ✅

Modèle ML → Probabilité: 65%
Danger Score: 65%
TTL Decay: 65% × 0.314 = 20.4% ❌ (< 50%)

DÉCISION: SKIP ❌ (signal trop ancien)
RAISON: SIGNAL_STALE (350s > 300s TTL)
```

---

## Les 30 Features Expliquées

### Groupe 1: TEMPS (2 features)
- `minute` : Minute du match
- `minute_bucket` : Catégorie (30-35, 35-40, etc.)

### Groupe 2: SCORE (4 features)
- `score_home / score_away` : Buts
- `goal_diff` : Différence
- `recent_goals_5m` : Buts dernières 5 min

### Groupe 3: POSSESSION (2 features)
- `possession_home / away` : % possession

### Groupe 4: TIRS (8 features)
- `shots / sot` : Tirs totaux et cadrés
- `accuracy` : % de tirs cadrés
- `delta_5m` : Tirs dernières 5 min

### Groupe 5: CORNERS (6 features)
- `corners` : Totaux
- `delta_5m` : Dernières 5 min
- `sot_delta_5m` : Tirs cadrés en transition

### Groupe 6: CARTONS (4 features)
- `red / yellow cards` : Pour chaque équipe

### Groupe 7: FORCE (4 features)
- `team_elo` : Rating force de chaque équipe
- `elo_diff` : Avantage
- `saturation_score` : Intensité du jeu

---

## Formules Clés

### Danger Score
```
danger_score (%) = P(≥1 but) × 100
```

### TTL Decay (Décroissance)
```
freshness_factor = e^(-signal_age / 300)
confidence = danger_score × freshness_factor
```

### Exemple Complet
```
P(≥1 but) = 0.68
danger_score = 68%
signal_age = 15s
freshness = e^(-15/300) = 0.9512
confidence = 68% × 0.9512 = 64.7%

BUY si: confidence > 50% AND danger > 50%
→ 64.7% > 50% ✅ ET 68% > 50% ✅
→ DECISION: BUY ✅
```

---

## Seuils (Strategy Conservative)

```
confidence_threshold = 50%
danger_score_threshold = 50%

→ Moins de faux positifs
→ Win rate: 35.1% (backtesting)
→ Bets: 22.9% déclenchés
```

Comparaison:
- Conservative (50%/50%): 35.1% win rate ⭐ (MEILLEUR)
- Moderate (30%/35%): 32.0% win rate
- Aggressive (20%/25%): ~28% win rate (risqué)

---

## Outils pour Comprendre

### 1. Visualiser le Système
```bash
python SCORING_EXPLANATION.py
```

### 2. Tester Interactivement
```bash
python scoring_debugger.py
# Choisir exemple 1-5 ou custom
```

### 3. Voir Trace Complète
```bash
cat COMPLETE_TRACE_EXAMPLE.txt
```

### 4. Lire Documentation
```bash
cat SCORING_AND_DECISION_GUIDE.md
```

---

## Questions Fréquentes

### Q: Pourquoi 30 features?
R: Parce que le modèle a besoin de contexte riche:
- Possession seule ne suffit pas
- Tirs seuls ne suffisent pas
- Besoin d'histoire (5 dernières min)
- Besoin de contexte (Elo, cartons)

### Q: Pourquoi TTL de 300s?
R: C'est l'équilibre entre:
- < 300s: Signal trop restrictif
- > 300s: Signal devient bruit
- 300s (5 min): Optimal en backtesting

### Q: Pourquoi seuil 50% Conservative?
R: Backtesting de 6000 décisions montre:
- 50%/50%: 35.1% win rate ✅
- 30%/35%: 32.0% win rate
- 20%/25%: ~28% win rate
→ 50%/50% est le meilleur

### Q: Pourquoi intervals [30-45] et [75-90] seulement?
R: Parce que:
- [0-30): Match peu prévisible au démarrage
- [30-45]: Pattern établi + impulsivité croissante
- [45-75): Zone morte (transitions instables)
- [75-90]: Fatigue + urgence = plus de buts
- [90+]: Temps compensation imprévisible

### Q: Comment le modèle apprend?
R: Sur 1000 matchs historiques:
```
Entraînement (80%): 800 matchs
Test (20%): 200 matchs

Pour chaque match historique:
- Features extraites au moment du but
- Label = but marqué (1) ou non (0)
- Modèle apprend patterns = probabilités
```

### Q: Quand le signal est rejeté?
R: Si l'une de ces conditions:
1. Hors interval [30-45] et [75-90]
2. Penalty actif (marché suspendu)
3. Signal > 300s (trop vieux)
4. Confidence < 50%
5. Danger < 50%

---

## Résumé Ultra-Rapide

```
MATCH EN DIRECT
      ↓
      (Extract 30 features)
      ↓
      LightGBM Model (Trained on 1000 matches)
      ↓
      Probability of ≥1 goal (0-100%)
      ↓
      Apply TTL Decay (Signal freshness)
      ↓
      Check 5 Filters (All must pass)
      ↓
      BUY ✅ or SKIP ❌
      ↓
      Telegram Alert or Silence
```

Win Rate: 35.1% (Better than 32%)

---

## Pour Aller Plus Loin

1. **Code Source Principal**
   - `live_prediction_pipeline.py` - Pipeline complet
   - `feature_extractor.py` - Extraction des features
   - `signal_ttl_manager.py` - Gestion TTL

2. **Tests & Debugging**
   - `scoring_debugger.py` - Debug interactif
   - `backtesting_engine.py` - Validation historique

3. **Documentation**
   - `SCORING_AND_DECISION_GUIDE.md` - Ce document détaillé
   - `COMPLETE_TRACE_EXAMPLE.txt` - Trace d'exécution

---

**Créé par**: GitHub Copilot  
**Date**: 2 décembre 2025  
**Version**: 2.0 Production
