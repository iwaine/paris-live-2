#!/usr/bin/env python3
# ============================================================================
# PARIS LIVE - SCORING & DECISION LOGIC EXPLANATION
# ============================================================================
# Guide complet sur le calcul du score et la prise de décision
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    PARIS LIVE - SYSTÈME DE SCORING                        │
│                                                                             │
│  INPUT → FEATURES → ML MODEL → DANGER SCORE → FRESHNESS DECAY → DECISION  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘


=== ÉTAPE 1: ENTRÉE (INPUT) ===
─────────────────────────────────

Les données du match en direct (live stats):

    {
        'match_id': 'PSG_vs_OM_20251202',
        'home_team': 'Paris SG',
        'away_team': 'Marseille',
        'minute': 38,                      # ← MINUTE CLÉE (30-45 ou 75-90)
        'home_score': 2,
        'away_score': 1,
        'home_possession': 55,             # %
        'home_shots': 9,
        'home_shots_on_target': 5,
        'away_possession': 45,             # %
        'away_shots': 6,
        'away_shots_on_target': 2,
        'home_corners': 4,
        'away_corners': 2,
        'signal_age_seconds': 15           # ← ÂGE DU SIGNAL
    }


=== ÉTAPE 2: EXTRACTION DES FEATURES (23 features) ===
──────────────────────────────────────────────────────

Les features sont calculées à partir des stats live:

┌──────────────────────────────────────┐
│ FEATURES DE BASE (Minute & Intervalle)
├──────────────────────────────────────┤
│ 1. minute = 38 (35-45 window)
│ 2. minute_bucket = "35-40"
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ FEATURES DE SCORE & BUT
├──────────────────────────────────────┤
│ 3. score_home = 2
│ 4. score_away = 1
│ 5. goal_diff = 2 - 1 = 1 (home devant)
│ 6. recent_goal_count_5m = 0 (pas de but dernières 5 min)
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ FEATURES DE POSSESSION
├──────────────────────────────────────┤
│ 7. possession_home = 0.55 (55%)
│ 8. possession_away = 0.45 (45%)
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ FEATURES DE TIRS
├──────────────────────────────────────┤
│ 9.  shots_home = 9
│ 10. shots_away = 6
│ 11. sot_home = 5 (shots on target)
│ 12. sot_away = 2
│ 13. shot_accuracy_home = 5/9 = 0.556
│ 14. shot_accuracy_away = 2/6 = 0.333
│ 15. shots_delta_5m_home = 2 (2 tirs en dernières 5 min)
│ 16. shots_delta_5m_away = 1
│ 17. sot_delta_5m_home = 1
│ 18. sot_delta_5m_away = 0
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ FEATURES DE CORNERS
├──────────────────────────────────────┤
│ 19. corners_home = 4
│ 20. corners_away = 2
│ 21. corners_delta_5m_home = 1 (1 corner dernières 5 min)
│ 22. corners_delta_5m_away = 0
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ FEATURES DE CARTONS
├──────────────────────────────────────┤
│ 23. red_cards_home = 0
│ 24. red_cards_away = 0
│ 25. yellow_cards_home = 2
│ 26. yellow_cards_away = 1
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ FEATURES D'ELO & SATURATION
├──────────────────────────────────────┤
│ 27. team_elo_home = 1750 (PSG très fort)
│ 28. team_elo_away = 1600 (OM fort)
│ 29. elo_diff = 150 (avantage PSG)
│ 30. saturation_score = 1.2 (intensité de jeu)
└──────────────────────────────────────┘


=== ÉTAPE 3: MODÈLE ML (LightGBM) ===
─────────────────────────────────────

Le modèle LightGBM prend les 30 features en entrée:

    Entrée: [38, "35-40", 2, 1, 1, 0.55, 0.45, 9, 6, 5, 2, 0.556, 0.333, ...]
            ↓
    StandardScaler (normalisation)
            ↓
    LightGBM Classifier
            ↓
    Sortie: probability (0.0 - 1.0)

EXEMPLE DE RÉSULTAT:
    Probability = 0.68
    → "Il y a 68% de chance qu'au moins 1 but soit marqué dans cet interval"


=== ÉTAPE 4: CALCUL DU DANGER SCORE ===
───────────────────────────────────────

danger_score = probability × 100

    Probability = 0.68
    Danger Score = 0.68 × 100 = 68%

INTERPRÉTATION:
    • 0-20%:  Très faible risque de but
    • 20-40%: Faible risque
    • 40-60%: Moyen risque
    • 60-80%: Risque élevé ⚠️
    • 80-100%: Très haut risque 🔴


=== ÉTAPE 5: APPLICATION DES PÉNALITÉS ===
───────────────────────────────────────────

A) PÉNALITÉ MARCHÉ SUSPENDU (Penalty):
   Si penalty détecté → danger_score *= 0.5
   
   Exemple: 68% → 34% (signal moins fiable après un penalty)

B) PÉNALITÉ MARCHÉ NORMAL:
   Aucune pénalité appliquée
   
   danger_score reste: 68%


=== ÉTAPE 6: DÉCROISSANCE EXPONENTIELLE TTL ===
────────────────────────────────────────────────

TTL = Time To Live = 300 secondes
signal_age = âge actuel du signal

freshness_factor = e^(-signal_age / TTL)
confidence = danger_score × freshness_factor

EXEMPLES:
┌─────────────────────────────────────────────────────────┐
│ signal_age (sec) │ freshness_factor │ confidence résult │
├─────────────────────────────────────────────────────────┤
│        0         │      1.000       │  68% × 1.000 = 68%
│       30         │      0.905       │  68% × 0.905 = 61%
│       60         │      0.819       │  68% × 0.819 = 56%
│      150         │      0.606       │  68% × 0.606 = 41%
│      300         │      0.368       │  68% × 0.368 = 25%
│      450         │      0.223       │  68% × 0.223 = 15%
└─────────────────────────────────────────────────────────┘

INTERPRÉTATION:
    Le signal perd de la force avec le temps (exponentiellement)
    Après 5 minutes (300s): signal à 36.8% de sa force
    Après 10 minutes (600s): signal pratiquement mort


=== ÉTAPE 7: VÉRIFICATION DES SEUILS & FILTRES ===
──────────────────────────────────────────────────

3 filtres doivent passer pour un BET (dans cet ordre):

FILTRE 1 - INTERVAL DE MINUTE
┌────────────────────────────────┐
│ Minute doit être dans:         │
│ • [30-45] (première moitié)   │
│ • OU [75-90] (fin du match)   │
├────────────────────────────────┤
│ ✅ EXEMPLE: minute=38 PASS     │
│ ❌ EXEMPLE: minute=50 FAIL     │
└────────────────────────────────┘

FILTRE 2 - MARCHÉ SUSPENDU (PENALTY)?
┌────────────────────────────────┐
│ Si penalty active:             │
│ → Rejeter (pénalité appliquée) │
├────────────────────────────────┤
│ ✅ EXEMPLE: pas de penalty     │
│ ❌ EXEMPLE: penalty active -15s│
└────────────────────────────────┘

FILTRE 3 - ÂGE DU SIGNAL
┌────────────────────────────────┐
│ Si signal_age > 300s:          │
│ → Rejeter (trop vieux)         │
├────────────────────────────────┤
│ ✅ EXEMPLE: signal_age=15s     │
│ ❌ EXEMPLE: signal_age=400s    │
└────────────────────────────────┘

FILTRE 4 - CONFIANCE MINIMALE (Threshold)
┌────────────────────────────────┐
│ Seuil Conservative: 50%        │
│ Si confidence < 50%:           │
│ → Rejeter (signal faible)      │
├────────────────────────────────┤
│ ✅ EXEMPLE: conf=61% > 50%     │
│ ❌ EXEMPLE: conf=41% < 50%     │
└────────────────────────────────┘

FILTRE 5 - DANGER MINIMALE (Threshold)
┌────────────────────────────────┐
│ Seuil Conservative: 50%        │
│ Si danger_score < 50%:         │
│ → Rejeter (danger trop bas)    │
├────────────────────────────────┤
│ ✅ EXEMPLE: danger=68% > 50%   │
│ ❌ EXEMPLE: danger=35% < 50%   │
└────────────────────────────────┘


=== ÉTAPE 8: PRISE DE DÉCISION FINALE ===
──────────────────────────────────────────

CAS 1 - SIGNAL REJETÉ
┌────────────────────────────────────┐
│ Raison possible:                   │
│ • Minute 50 (hors interval)       │
│ • ou confidence 41% < 50%          │
│ ou danger 35% < 50%                │
│                                    │
│ → DÉCISION: SKIP (attendre)       │
│ → ACTION: Aucune alerte Telegram  │
└────────────────────────────────────┘

CAS 2 - SIGNAL ACCEPTÉ ✅
┌────────────────────────────────────┐
│ Tous les filtres passés:           │
│ ✅ minute = 38 (dans [30-45])     │
│ ✅ pas de penalty                 │
│ ✅ signal_age = 15s (< 300s)      │
│ ✅ confidence = 61% > 50%         │
│ ✅ danger = 68% > 50%             │
│                                    │
│ → DÉCISION: BUY ✅                │
│ → ACTION: Alerte Telegram envoyée  │
│ → MESSAGE: "Au moins 1 but attendu"
└────────────────────────────────────┘


=== RÉSUMÉ COMPLET EXEMPLE ===
──────────────────────────────

ENTRÉE MATCH:
    PSG 2-1 Marseille (Minute 38, tirs 9-6, possession 55-45)

ÉTAPE 1: Features extraction (30 features calculées)
ÉTAPE 2: Normalisation StandardScaler
ÉTAPE 3: LightGBM → Probability = 0.68
ÉTAPE 4: Danger Score = 68%
ÉTAPE 5: Pas de pénalité → 68% inchangé
ÉTAPE 6: TTL decay (15s) → confidence = 68% × 0.95 = 64.6%
ÉTAPE 7: Filtres:
    ✅ Minute 38 dans [30-45]
    ✅ Pas de penalty
    ✅ Signal age 15s < 300s
    ✅ Confidence 64.6% > 50%
    ✅ Danger 68% > 50%
ÉTAPE 8: DÉCISION = BUY ✅

RÉSULTAT FINAL:
    {
        'should_bet': True,
        'reason': 'BETTING_SIGNAL_ACTIVE',
        'danger_score': 68.0,
        'confidence': 64.6,
        'freshness_factor': 0.95,
        'market_suspended': False,
        'minute': 38,
        'interval': (30, 45)
    }

→ Alerte Telegram envoyée!


=== THRESHOLDS STRATÉGIES ===
────────────────────────────

CONSERVATIVE (Actuelle - Recommandée):
    confidence_threshold = 50%
    danger_score_threshold = 50%
    → Moins de faux positifs
    → Win rate: 35.1% (backtesting)

MODERATE:
    confidence_threshold = 30%
    danger_score_threshold = 35%
    → Plus de signaux
    → Win rate: 32.0% (backtesting)

AGGRESSIVE:
    confidence_threshold = 20%
    danger_score_threshold = 25%
    → Beaucoup de signaux (bruit)
    → Win rate: ~28% (risqué)


=== NOTES IMPORTANTES ===
────────────────────────

1. FRESHNESS DECAY (TTL):
   - Signal perd sa force exponentiellement
   - e^(-t/300) = force du signal à temps t
   - Après 5 min: 36.8% de force restante

2. PENALTY SUSPENSION:
   - Quand penalty détecté → marché suspendu
   - Confiance divisée par 2 pendant 120 secondes
   - Évite les faux positifs après événements

3. INTERVAL RESTRICTION:
   - BET uniquement [30-45] et [75-90]
   - Éviite les transitions difficiles

4. DANGER SCORE vs CONFIDENCE:
   - Danger Score = probabilité brute du modèle
   - Confidence = danger score après décroissance TTL
   - Les deux doivent être > threshold

5. BACKTEST VALIDATION:
   - 6000 décisions historiques testées
   - Conservative: 35.1% win rate
   - Supérieur à Moderate de 3.1%

"""

if __name__ == '__main__':
    print(__doc__)
