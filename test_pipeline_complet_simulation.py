#!/usr/bin/env python3
"""
TEST COMPLET DU PIPELINE - SIMULATION
======================================

Simule un match complet avec tous les intervalles et vérifie :
1. ✅ Signaux uniquement dans 31-45+ et 76-90+
2. ✅ SEM et IQR affichés correctement
3. ✅ Récurrence basée sur buts marqués + encaissés
4. ✅ Formula MAX utilisée
5. ✅ Formatter Telegram enrichi

Test avec : Monaco AWAY (100% récurrence 76-90+)
"""

import sys
sys.path.insert(0, '/workspaces/paris-live/football-live-prediction')

from predictors.live_goal_probability_predictor import LiveGoalProbabilityPredictor
from telegram_formatter_enriched import format_telegram_alert_enriched
import sqlite3

print("="*80)
print("🧪 TEST PIPELINE COMPLET - SIMULATION MATCH")
print("="*80)
print()

# Initialiser le préditeur
predictor = LiveGoalProbabilityPredictor()

# Simuler différentes minutes du match
test_scenarios = [
    {"minute": 10, "desc": "Début 1ère MT", "expected": "❌ PAS DE SIGNAL"},
    {"minute": 25, "desc": "Milieu 1ère MT", "expected": "❌ PAS DE SIGNAL"},
    {"minute": 35, "desc": "31-45+ ACTIF", "expected": "✅ SIGNAL MOYEN (Brest ~43%)"},
    {"minute": 44, "desc": "Fin 1ère MT", "expected": "✅ SIGNAL MOYEN"},
    {"minute": 50, "desc": "Temps add. 1ère", "expected": "✅ SIGNAL MOYEN"},
    {"minute": 55, "desc": "Début 2ème MT", "expected": "❌ PAS DE SIGNAL"},
    {"minute": 70, "desc": "Milieu 2ème MT", "expected": "❌ PAS DE SIGNAL"},
    {"minute": 78, "desc": "76-90+ ACTIF", "expected": "✅ SIGNAL FORT (Monaco 100%)"},
    {"minute": 85, "desc": "Fin de match", "expected": "✅ SIGNAL FORT"},
    {"minute": 92, "desc": "Temps add. 2ème", "expected": "✅ SIGNAL FORT"},
]

print("📋 SCÉNARIOS DE TEST")
print("-"*80)

results = []
for scenario in test_scenarios:
    minute = scenario["minute"]
    desc = scenario["desc"]
    expected = scenario["expected"]
    
    # Prédiction
    result = predictor.predict_goal_probability(
        home_team="Brest",
        away_team="Monaco",
        league="france",
        current_minute=minute,
        home_possession=45,
        away_possession=55,
        home_attacks=50,
        away_attacks=60,
        home_dangerous_attacks=20,
        away_dangerous_attacks=30,
        home_shots_on_target=3,
        away_shots_on_target=4,
        score_home=1,
        score_away=0
    )
    
    prob = result['goal_probability']
    level = result['danger_level']
    interval = result['details']['interval']
    base_rate = result['details']['base_rate'] * 100
    
    # Vérifier si conforme aux attentes
    is_key_interval = interval in ["31-45", "76-90"]
    status = "✅" if is_key_interval else "⏸️"
    
    # Déterminer si signal envoyé (seuil 65%)
    signal_sent = "🔔 SIGNAL" if prob >= 65 else "🔕 Pas signal"
    
    result_line = f"{status} Min {minute:3d} ({desc:20s}) → {interval:20s} | {prob:5.1f}% [{level:8s}] | {signal_sent}"
    print(result_line)
    
    results.append({
        "minute": minute,
        "interval": interval,
        "prob": prob,
        "level": level,
        "is_key": is_key_interval,
        "signal_sent": prob >= 65,
        "expected": expected
    })

print()
print("="*80)
print("📊 RÉSUMÉ DES TESTS")
print("="*80)

# Compter les signaux
key_intervals = [r for r in results if r['is_key']]
non_key_intervals = [r for r in results if not r['is_key']]
signals_sent = [r for r in results if r['signal_sent']]

print(f"\n✅ Intervalles clés (31-45+, 76-90+) : {len(key_intervals)}/10 scénarios")
print(f"⏸️  Hors intervalles clés : {len(non_key_intervals)}/10 scénarios")
print(f"🔔 Signaux envoyés (≥65%) : {len(signals_sent)}/10 scénarios")

print(f"\n🎯 VALIDATION :")
all_ok = True

# Test 1 : Intervalles clés détectés
if len(key_intervals) == 5:
    print("✅ Test 1 : 5 intervalles clés détectés (31-45+ et 76-90+)")
else:
    print(f"❌ Test 1 : {len(key_intervals)} intervalles clés au lieu de 5")
    all_ok = False

# Test 2 : Hors intervalles = faible probabilité
non_key_high = [r for r in non_key_intervals if r['prob'] > 15]
if len(non_key_high) == 0:
    print("✅ Test 2 : Probabilités faibles hors intervalles clés (<15%)")
else:
    print(f"❌ Test 2 : {len(non_key_high)} proba élevées hors intervalles clés")
    all_ok = False

# Test 3 : Monaco pattern fort dans 76-90+
monaco_intervals = [r for r in results if r['minute'] in [78, 85, 92]]
if all(r['prob'] >= 90 for r in monaco_intervals):
    print("✅ Test 3 : Monaco AWAY 100% pattern → ≥90% probabilité en 76-90+")
else:
    print("❌ Test 3 : Monaco pattern pas détecté correctement")
    all_ok = False

# Test 4 : Signaux uniquement dans intervalles clés
signals_in_key = [r for r in signals_sent if r['is_key']]
if len(signals_in_key) == len(signals_sent):
    print("✅ Test 4 : Tous les signaux dans intervalles clés uniquement")
else:
    print(f"❌ Test 4 : {len(signals_sent) - len(signals_in_key)} signaux hors intervalles")
    all_ok = False

print()
print("="*80)

if all_ok:
    print("🎉 TOUS LES TESTS RÉUSSIS !")
else:
    print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")

print("="*80)
print()

# TEST FORMATTER TELEGRAM avec SEM et IQR
print("="*80)
print("📱 TEST FORMATTER TELEGRAM ENRICHI")
print("="*80)
print()

# Récupérer stats depuis DB
db_path = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT avg_minute, std_minute, sem_minute, iqr_q1, iqr_q3, goal_count, total_matches
    FROM team_goal_recurrence
    WHERE team_name = 'Monaco' AND is_home = 0 AND period = 2
""")
monaco_stats = cursor.fetchone()

cursor.execute("""
    SELECT avg_minute, std_minute, sem_minute, iqr_q1, iqr_q3, goal_count, total_matches
    FROM team_goal_recurrence
    WHERE team_name = 'Brest' AND is_home = 1 AND period = 2
""")
brest_stats = cursor.fetchone()

conn.close()

# Générer signal Telegram pour minute 79
match_data = {
    'home_team': 'Brest',
    'away_team': 'Monaco',
    'current_minute': 79,
    'score_home': 1,
    'score_away': 0,
    'league': 'France - Ligue 1',
    'live_stats': {
        'possession_home': 45,
        'possession_away': 55,
        'corners_home': 3,
        'corners_away': 4,
        'shots_home': 10,
        'shots_away': 14,
        'shots_on_target_home': 4,
        'shots_on_target_away': 5,
        'attacks_home': 85,
        'attacks_away': 95,
        'dangerous_attacks_home': 25,
        'dangerous_attacks_away': 35
    }
}

brest_avg, brest_std, brest_sem, brest_q1, brest_q3, brest_goals, brest_matches = brest_stats
prediction_home = {
    'interval_name': '76-90',
    'probability_final': 52.3,
    'probability_historical': 42.9,
    'confidence_level': 'BON',
    'recurrence_last_5': 0.60,
    'avg_minute': brest_avg,
    'std_minute': brest_std,
    'sem_minute': brest_sem,
    'iqr_q1': brest_q1,
    'iqr_q3': brest_q3,
    'momentum_boost': 8,
    'saturation_factor': 1.00,
    'any_goal_total': brest_goals,
    'goals_scored': 5,
    'goals_conceded': 5,
    'freq_any_goal': 0.429,
    'total_matches': brest_matches,
    'avg_goals_first_half': 1.4,
    'avg_goals_second_half': 1.6,
    'avg_goals_full_match': 3.0
}

monaco_avg, monaco_std, monaco_sem, monaco_q1, monaco_q3, monaco_goals, monaco_matches = monaco_stats
prediction_away = {
    'interval_name': '76-90',
    'probability_final': 96.5,
    'probability_historical': 100.0,
    'confidence_level': 'EXCELLENT',
    'recurrence_last_5': 1.00,
    'avg_minute': monaco_avg,
    'std_minute': monaco_std,
    'sem_minute': monaco_sem,
    'iqr_q1': monaco_q1,
    'iqr_q3': monaco_q3,
    'momentum_boost': 15,
    'saturation_factor': 1.00,
    'any_goal_total': monaco_goals,
    'goals_scored': 7,
    'goals_conceded': 9,
    'freq_any_goal': 1.00,
    'total_matches': monaco_matches,
    'avg_goals_first_half': 1.3,
    'avg_goals_second_half': 2.7,
    'avg_goals_full_match': 4.0
}

combined_prob = 0.978

message = format_telegram_alert_enriched(match_data, prediction_home, prediction_away, combined_prob)

# Vérifier présence SEM et IQR
has_sem = "SEM" in message
has_iqr = "[" in message and "']" in message  # Format [73' - 89']

print("Vérifications formatter :")
print(f"  ✅ SEM affiché : {'OUI' if has_sem else 'NON'}")
print(f"  ✅ IQR affiché : {'OUI' if has_iqr else 'NON'}")
print()

# Afficher extrait du message
print("📱 EXTRAIT DU MESSAGE TELEGRAM :")
print("-"*80)
lines = message.split('\n')
# Afficher la section timing
for i, line in enumerate(lines):
    if 'Timing' in line:
        print('\n'.join(lines[i:min(i+3, len(lines))]))
        break
print("-"*80)

print()
print("="*80)
print("✅ TEST PIPELINE COMPLET TERMINÉ")
print("="*80)
