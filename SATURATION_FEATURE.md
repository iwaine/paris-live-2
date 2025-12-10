# 🎯 Fonctionnalité SATURATION DE BUTS

## Vue d'ensemble

Le système intègre désormais un **ajustement de saturation** qui module les probabilités de but selon le nombre de buts déjà marqués par rapport à la moyenne attendue. Cette fonctionnalité enrichit le modèle hybride (80% historique + 20% momentum) avec une intelligence contextuelle sur le rythme de buts du match.

---

## Concept

### Principe

Plus un match produit de buts par rapport à la moyenne, moins il est probable qu'il en produise davantage (saturation). Inversement, un match pauvre en buts peut "rattraper" la moyenne (boost).

### Formule

**IMPORTANT** : La saturation est **personnalisée pour chaque rencontre**.

```
Moyenne attendue = (Moyenne HOME dans config HOME + Moyenne AWAY dans config AWAY) / 2

Ratio saturation = Buts actuels / Moyenne attendue
```

**Exemple concret** :
- **Spartak Varna (HOME)** : Moyenne 1ère MT = 1.33 buts
- **Slavia Sofia (AWAY)** : Moyenne 1ère MT = 0.75 buts
- **→ Moyenne pour CE match** : (1.33 + 0.75) / 2 = **1.04 buts**

Chaque paire d'équipes a son propre seuil de saturation !

### Ajustements progressifs

| Ratio saturation | Ajustement probabilité | Interprétation |
|-----------------|------------------------|----------------|
| **< 0.75** | **+5%** | Boost (match sous la moyenne) |
| **≥ 0.75** | **-5%** | Légère saturation |
| **≥ 1.00** | **-10%** | Saturation modérée (moyenne atteinte) |
| **≥ 1.25** | **-15%** | Saturation élevée |
| **≥ 1.50** | **-20%** | Saturation maximale (50%+ au-dessus moyenne) |

---

## Implémentation technique

### 1. Extension base de données

**Table** : `team_critical_intervals`

**Nouvelles colonnes** :
```sql
avg_goals_full_match REAL     -- Moyenne buts total (90min)
avg_goals_first_half REAL     -- Moyenne buts 1ère mi-temps (0-45)
avg_goals_second_half REAL    -- Moyenne buts 2nde mi-temps (46-90)
```

**Calcul** :
- **Full match** : `goals_for + goals_against` (colonnes directes)
- **Par mi-temps** : Parse `goal_times` et compte buts dans intervalle 0-45 ou 46-90

**Fichier** : `build_critical_interval_recurrence.py`

### 2. Fonction calcul moyennes

```python
def _calculate_goal_averages(self, team_name, is_home):
    """
    Calcule moyennes buts pour une équipe dans configuration donnée.
    
    Returns:
        (avg_full_match, avg_first_half, avg_second_half)
    """
    # Total match : requête directe sur goals_for/against
    # Par mi-temps : parse goal_times avec filtrage [0-45] et [46-90]
```

**Important** : La fonction `_parse_goal_times` filtre les zéros (padding JSON) pour obtenir seulement les buts réels.

### 3. Fonction ajustement saturation

**Fichier** : `live_predictor_v2.py`

```python
def _calculate_saturation_adjustment(context, pattern_home, pattern_away, interval_name):
    """
    Calculer ajustement saturation basé sur buts actuels vs moyenne attendue.
    
    Logique :
    - Intervalle 31-45+ : Utilise avg_goals_first_half
    - Intervalle 75-90+ :
        - Si minute < 46 : Utilise avg_goals_full_match
        - Si minute ≥ 46 : Utilise avg_goals_second_half
    
    Returns:
        Ajustement entre -0.20 et +0.05
    """
```

**Détermination moyenne** :
- **31-45+** (1ère mi-temps) → `avg_goals_first_half`
- **75-90+** avant 46ème minute → `avg_goals_full_match`
- **75-90+** après 46ème minute → `avg_goals_second_half`

### 4. Intégration dans pipeline prédiction

**Signature étendue** :
```python
def _calculate_probability(freq_any, rec5, confidence, is_active,
                          momentum_score=None,
                          saturation_adjustment=0.0):  # ← NOUVEAU
```

**Ordre d'application** :
```
1. Probabilité pattern historique (freq_any)
2. Ajustements récurrence
3. Ajustements confiance
4. Boost intervalle actif
5. AJUSTEMENT SATURATION ← APPLIQUÉ ICI
6. Limitation [0, 1]
7. Combinaison avec momentum (80/20)
```

**Formule finale** :
```python
historical_prob = freq_any + ajust_recurrence + ajust_confiance + ajust_intervalle
historical_prob += saturation_adjustment  # ← NOUVEAU

# Limiter entre 0 et 1
historical_prob = max(0.0, min(1.0, historical_prob))

# Hybride 80/20
final_probability = 0.80 * historical_prob + 0.20 * momentum_score
```

---

## Exemples concrets

### Personnalisation par rencontre

**CHAQUE MATCH A SON PROPRE SEUIL DE SATURATION** basé sur les moyennes des deux équipes.

#### Exemple 1 : Spartak Varna vs Slavia Sofia

**Moyennes individuelles** :
- Spartak Varna (HOME) : 1.33 buts en 1ère MT
- Slavia Sofia (AWAY) : 0.75 buts en 1ère MT

**Moyenne combinée pour CETTE rencontre** :
```
Moyenne attendue = (1.33 + 0.75) / 2 = 1.04 buts
```

**Scénarios** :

| Score | Buts actuels | Ratio | Ajustement | Explication |
|-------|--------------|-------|------------|-------------|
| 0-0 | 0 | 0.00 | **+5%** | Aucun but, boost car sous moyenne |
| 1-0 | 1 | 0.96 | **-5%** | Proche moyenne (96%) |
| 1-1 | 2 | 1.92 | **-20%** | Saturation max (192% de moyenne) |
| 3-2 | 5 | 4.80 | **-20%** | Forte saturation (480% !) |

---

#### Exemple 2 : Match avec moyennes différentes

**Hypothèse** :
- Équipe A (HOME) : 2.50 buts en 1ère MT
- Équipe B (AWAY) : 1.50 buts en 1ère MT

**Moyenne combinée** :
```
Moyenne attendue = (2.50 + 1.50) / 2 = 2.00 buts
```

**Comparaison avec Spartak vs Slavia** :
- Spartak/Slavia : Seuil saturation = 1.04 buts
- Équipe A/B : Seuil saturation = **2.00 buts** (presque 2× plus élevé)

→ **Le même score 2-1 (3 buts)** donne :
- Dans Spartak/Slavia : Ratio 2.88 → **Saturation -20%**
- Dans Équipe A/B : Ratio 1.50 → **Saturation -20%**

→ Mais **score 1-1 (2 buts)** donne :
- Dans Spartak/Slavia : Ratio 1.92 → Saturation -20%
- Dans Équipe A/B : Ratio 1.00 → Saturation **-10%** (léger)

---

### Scénario 1 : Match pauvre en buts

**Configuration** :
- **Équipes** : Spartak Varna (HOME) vs Slavia Sofia (AWAY)
- **Intervalle** : 31-45+ (1ère mi-temps)
- **Moyenne attendue** : (1.33 + 0.75) / 2 = **1.04 buts**

**Contexte live** :
- **Minute** : 32
- **Score** : 0-0
- **Buts actuels** : 0

**Calcul** :
```
Ratio = 0 / 1.04 = 0.00
Ajustement = +5% (boost, ratio < 0.75)
```

**Résultat** :
- Probabilité AVANT saturation : 95.0%
- Probabilité APRÈS saturation : **100.0%** ✅
- **Impact** : +5% (encourage prédiction BUT car match sous moyenne)

---

### Scénario 2 : Match avec saturation modérée

**Configuration** :
- Même équipes, même intervalle
- **Moyenne attendue** : 1.04 buts

**Contexte live** :
- **Minute** : 32
- **Score** : 2-1
- **Buts actuels** : 3

**Calcul** :
```
Ratio = 3 / 1.04 = 2.88
Ajustement = -20% (saturation max, ratio ≥ 1.50)
```

**Résultat** :
- Probabilité AVANT saturation : 100.0%
- Probabilité APRÈS saturation : **90.2%** ✅
- **Impact** : -9.8% (réduit probabilité car déjà beaucoup de buts)

---

### Scénario 3 : 2nde mi-temps avec saturation

**Configuration** :
- Spartak Varna vs Slavia Sofia
- **Intervalle** : 75-90+
- **Moyenne 2nde mi-temps** : (1.78 + 1.50) / 2 = **1.64 buts**

**Contexte live** :
- **Minute** : 76
- **Score** : 3-2 (5 buts déjà marqués)
- **Buts actuels** : 5

**Calcul** :
```
Ratio = 5 / 1.64 = 3.05
Ajustement = -20% (saturation max)
```

**Impact** :
Probabilité réduite de 20% pour refléter la saturation de buts dans le match.

---

## Tests et validation

### Script de test

**Fichier** : `test_saturation_final.py`

**Commande** :
```bash
python3 test_saturation_final.py
```

**Output attendu** :
```
Scénario                  | Buts | Ratio | Ajust Sat | Prob AVANT | Prob APRÈS | Réduction
Match sans buts           |    0 |  0.00 |  +0.05  |    95.0%  |   100.0%  |    -5.3%
1 but marqué              |    1 |  0.96 |  -0.05  |   100.0%  |    97.6%  |     2.4%
2 buts (moyenne)          |    2 |  1.92 |  -0.20  |   100.0%  |    90.2%  |     9.8%
```

✅ **Validation** : Ajustements appliqués correctement selon ratio

---

## Impact sur prédictions

### Cas d'usage typiques

**1. Match serré 0-0 à la mi-temps**
- Ratio faible → **Boost +5%**
- Raisonnement : Match peut "exploser" dans intervalles critiques

**2. Match spectaculaire 3-2 en cours**
- Ratio élevé → **Réduction -20%**
- Raisonnement : Beaucoup de buts déjà, probabilité saturée

**3. Match moyen 1-1**
- Ratio proche de 1.0 → **Réduction -10%**
- Raisonnement : Moyenne atteinte, légère saturation

### Complémentarité avec momentum

Le système hybride final combine :
- **80% Pattern historique** (+ saturation)
- **20% Momentum live**

Exemple :
```
Pattern : 70% → +5% (saturation boost) = 75%
Momentum : 60%
Final = 0.80 × 75% + 0.20 × 60% = 60% + 12% = 72%
```

---

## Configuration patterns

### Moyennes typiques observées

**Bulgarie (9 matches/équipe)** :

| Équipe | Config | Full | 1ère MT | 2nde MT |
|--------|--------|------|---------|---------|
| Spartak Varna | HOME | 3.11 | 1.33 | 1.78 |
| Spartak Varna | AWAY | 1.78 | 0.78 | 1.00 |
| Slavia Sofia | HOME | 2.40 | 1.40 | 1.00 |
| Slavia Sofia | AWAY | 2.25 | 0.75 | 1.50 |

**Observations** :
- Moyenne full match : **1.8 à 3.1 buts** (réaliste)
- Moyenne 1ère mi-temps : **0.75 à 1.40 buts**
- Moyenne 2nde mi-temps : **1.00 à 1.78 buts**

### Seuils saturation pratiques

Avec moyenne ~1.0 but par mi-temps :
- **1 but** → Ratio ~1.0 → Ajustement -10%
- **2 buts** → Ratio ~2.0 → Ajustement -20% (max)
- **0 buts** → Ratio 0.0 → Ajustement +5% (boost)

---

## Régénération base de données

### Commandes

```bash
# Supprimer table existante
sqlite3 data/predictions.db "DROP TABLE IF EXISTS team_critical_intervals;"

# Régénérer avec nouvelles colonnes
python3 build_critical_interval_recurrence.py
```

### Vérification

```bash
# Checker moyennes calculées
sqlite3 data/predictions.db << EOF
SELECT 
    team_name,
    is_home,
    interval_name,
    ROUND(avg_goals_full_match, 2) as avg_full,
    ROUND(avg_goals_first_half, 2) as avg_1st,
    ROUND(avg_goals_second_half, 2) as avg_2nd,
    total_matches
FROM team_critical_intervals
WHERE team_name = 'Spartak Varna'
ORDER BY is_home, interval_name;
EOF
```

**Output attendu** :
```
Spartak Varna | 0 | 31-45+ | 1.78 | 0.78 | 1.00 | 9
Spartak Varna | 0 | 75-90+ | 1.78 | 0.78 | 1.00 | 9
Spartak Varna | 1 | 31-45+ | 3.11 | 1.33 | 1.78 | 9
Spartak Varna | 1 | 75-90+ | 3.11 | 1.33 | 1.78 | 9
```

---

## Problèmes résolus

### Bug 1 : Moyennes incorrectes (20 buts/match)

**Symptôme** : `avg_goals_first_half = 18.5` (impossible)

**Cause** : Fonction `_parse_goal_times` retournait JSON complet avec zéros de padding
```python
# BUGUÉ
goal_times = "[12, 0, 0, 0, 0, 0, 0, 0, 0, 0]"  # 1 but à la 12ème
parsed = json.loads(goal_times)  # [12, 0, 0, 0, ...]
len(parsed)  # 10 ❌ (compte les zéros)
```

**Fix** :
```python
def _parse_goal_times(self, goal_times_str):
    if goal_times_str.startswith('['):
        times = json.loads(goal_times_str)
        return [t for t in times if t > 0]  # ✅ Filtrer zéros
```

### Bug 2 : Calcul full_match incorrect

**Symptôme** : Utilisait `len(goal_times)` pour total match

**Fix** : Utiliser colonnes directes `goals_for + goals_against`
```python
# AVANT (bugué)
total = len(scored) + len(conceded)  # Compte minutes

# APRÈS (correct)
total = goals_for + goals_against  # Buts réels
```

---

## Maintenance

### Mise à jour moniteurs en production

```bash
# Arrêter processus actuels
kill <PID_monitor_1> <PID_monitor_2>

# Relancer avec nouveau code
./start_live_alerts.sh both
```

### Tests après modification

1. Vérifier moyennes : `sqlite3 ... SELECT avg_goals...`
2. Tester saturation : `python3 test_saturation_final.py`
3. Valider prédictions live : `python3 validate_live_system.py`

---

## Auteurs & Historique

**Implémentation** : Décembre 2024  
**Version** : 1.0  
**Statut** : ✅ Opérationnel

**Modifications** :
- 2024-12-04 : Implémentation initiale
- 2024-12-04 : Fix parsing goal_times (filtrage zéros)
- 2024-12-04 : Fix calcul full_match (goals_for/against)
- 2024-12-04 : Tests validation + documentation
