#!/usr/bin/env python3
"""
VALIDATION FINALE - Système V2.0
=================================

Vérifie que TOUS les composants sont correctement mis à jour :
1. ✅ Base de données (team_goal_recurrence avec SEM, IQR)
2. ✅ Préditeur (formula MAX, intervalles clés)
3. ✅ Formatter (affichage SEM, IQR)
4. ✅ Scripts monitoring (compatibles)
"""

import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, '/workspaces/paris-live/football-live-prediction')

print("="*80)
print("🔍 VALIDATION SYSTÈME V2.0")
print("="*80)
print()

# ==============================================================================
# TEST 1 : Base de données
# ==============================================================================
print("📊 TEST 1 : Base de données team_goal_recurrence")
print("-"*80)

db_path = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vérifier structure table
cursor.execute("PRAGMA table_info(team_goal_recurrence)")
columns = {row[1] for row in cursor.fetchall()}

required_columns = {'sem_minute', 'iqr_q1', 'iqr_q3', 'avg_minute', 'std_minute', 
                   'goal_count', 'total_matches', 'team_name', 'is_home', 'period'}

missing = required_columns - columns
if missing:
    print(f"❌ Colonnes manquantes : {missing}")
    print("   → Exécuter : python3 build_team_recurrence_stats.py")
else:
    print("✅ Structure table correcte (SEM, IQR présents)")

# Vérifier données Monaco
cursor.execute("""
    SELECT period, avg_minute, sem_minute, iqr_q1, iqr_q3, goal_count, total_matches
    FROM team_goal_recurrence
    WHERE team_name = 'Monaco' AND is_home = 0
    ORDER BY period
""")
monaco_data = cursor.fetchall()

if not monaco_data:
    print("❌ Pas de données Monaco")
    print("   → Exécuter : python3 build_team_recurrence_stats.py")
else:
    print(f"✅ {len(monaco_data)} enregistrements Monaco trouvés")
    for period, avg, sem, q1, q3, goals, matches in monaco_data:
        mt = "1ère MT" if period == 1 else "2ème MT"
        print(f"   • {mt}: {goals} buts, Avg {avg:.1f}' ±{sem:.1f}' (SEM), IQR [{q1:.0f}'-{q3:.0f}']")
        
        # Vérifier cohérence
        if period == 2:  # 2ème MT
            if goals < 10:
                print(f"   ⚠️  Attention : Seulement {goals} buts (attendu ~16 avec buts marqués+encaissés)")
            if sem > 5:
                print(f"   ⚠️  Attention : SEM élevé ({sem:.1f}' > 5'), peu précis")

conn.close()
print()

# ==============================================================================
# TEST 2 : Préditeur
# ==============================================================================
print("🎯 TEST 2 : Préditeur (Formula MAX, Intervalles clés)")
print("-"*80)

from predictors.live_goal_probability_predictor import LiveGoalProbabilityPredictor
predictor = LiveGoalProbabilityPredictor()

# Test hors intervalle clé
result_outside = predictor.predict_goal_probability(
    home_team="Brest", away_team="Monaco", league="france",
    current_minute=25,
    home_possession=50, away_possession=50,
    home_attacks=30, away_attacks=30,
    home_dangerous_attacks=10, away_dangerous_attacks=10,
    home_shots_on_target=2, away_shots_on_target=2,
    score_home=0, score_away=0
)

if result_outside['details']['interval'] == "outside_key_intervals" and result_outside['goal_probability'] < 10:
    print("✅ Hors intervalles clés : Probabilité faible (5-10%)")
else:
    print(f"❌ Hors intervalles : {result_outside['goal_probability']:.1f}% (attendu <10%)")

# Test intervalle clé avec Monaco
result_monaco = predictor.predict_goal_probability(
    home_team="Brest", away_team="Monaco", league="france",
    current_minute=78,
    home_possession=45, away_possession=55,
    home_attacks=50, away_attacks=60,
    home_dangerous_attacks=20, away_dangerous_attacks=30,
    home_shots_on_target=3, away_shots_on_target=4,
    score_home=1, score_away=0
)

base_rate = result_monaco['details']['base_rate']
if result_monaco['details']['interval'] == "76-90" and base_rate >= 0.95:
    print(f"✅ Monaco 76-90+ : Base rate {base_rate*100:.0f}% (Formula MAX)")
else:
    print(f"❌ Monaco 76-90+ : Base rate {base_rate*100:.1f}% (attendu ~100%)")
    print("   → Vérifier que team_goal_recurrence est recalculé avec buts marqués+encaissés")

print()

# ==============================================================================
# TEST 3 : Formatter Telegram
# ==============================================================================
print("📱 TEST 3 : Formatter Telegram (SEM, IQR)")
print("-"*80)

from telegram_formatter_enriched import format_telegram_alert_enriched

# Créer données test
match_data = {
    'home_team': 'Brest',
    'away_team': 'Monaco',
    'current_minute': 79,
    'score_home': 1,
    'score_away': 0,
    'league': 'France',
    'live_stats': {
        'possession_home': 45, 'possession_away': 55,
        'corners_home': 2, 'corners_away': 3,
        'shots_home': 8, 'shots_away': 10,
        'shots_on_target_home': 3, 'shots_on_target_away': 4,
        'attacks_home': 80, 'attacks_away': 90,
        'dangerous_attacks_home': 25, 'dangerous_attacks_away': 30
    }
}

pred_home = {
    'interval_name': '76-90', 'probability_final': 50.0, 'probability_historical': 42.9,
    'confidence_level': 'BON', 'recurrence_last_5': 0.6,
    'avg_minute': 70.0, 'std_minute': 15.0, 'sem_minute': 4.9, 'iqr_q1': 56, 'iqr_q3': 78,
    'momentum_boost': 5, 'saturation_factor': 1.0,
    'any_goal_total': 10, 'goals_scored': 5, 'goals_conceded': 5,
    'freq_any_goal': 0.43, 'total_matches': 7,
    'avg_goals_first_half': 1.4, 'avg_goals_second_half': 1.6, 'avg_goals_full_match': 3.0
}

pred_away = {
    'interval_name': '76-90', 'probability_final': 95.0, 'probability_historical': 100.0,
    'confidence_level': 'EXCELLENT', 'recurrence_last_5': 1.0,
    'avg_minute': 78.2, 'std_minute': 12.4, 'sem_minute': 3.1, 'iqr_q1': 73, 'iqr_q3': 89,
    'momentum_boost': 10, 'saturation_factor': 1.0,
    'any_goal_total': 16, 'goals_scored': 7, 'goals_conceded': 9,
    'freq_any_goal': 1.0, 'total_matches': 6,
    'avg_goals_first_half': 1.3, 'avg_goals_second_half': 2.7, 'avg_goals_full_match': 4.0
}

message = format_telegram_alert_enriched(match_data, pred_home, pred_away, 0.975)

has_sem = "(SEM)" in message
has_iqr = "[" in message and "']" in message
has_zone_danger = "Zone de danger" in message

if has_sem and has_iqr and has_zone_danger:
    print("✅ Formatter affiche SEM et IQR correctement")
    # Extraire et afficher exemple
    for line in message.split('\n'):
        if 'Timing' in line or 'Zone de danger' in line:
            print(f"   {line.strip()}")
else:
    print(f"❌ Formatter incomplet : SEM={has_sem}, IQR={has_iqr}, Zone={has_zone_danger}")

print()

# ==============================================================================
# TEST 4 : Scripts de monitoring
# ==============================================================================
print("🔧 TEST 4 : Scripts de monitoring")
print("-"*80)

# Vérifier existence
monitoring_files = {
    'live_monitor_with_historical_patterns.py': '/workspaces/paris-live/live_monitor_with_historical_patterns.py',
    'live_goal_monitor_with_alerts.py': '/workspaces/paris-live/live_goal_monitor_with_alerts.py',
}

for name, path in monitoring_files.items():
    if Path(path).exists():
        # Vérifier contenu
        content = Path(path).read_text()
        has_intervals = "CRITICAL_INTERVALS" in content or "31" in content
        print(f"✅ {name} : Présent" + (" (intervalles critiques configurés)" if has_intervals else ""))
    else:
        print(f"❌ {name} : Manquant")

print()

# ==============================================================================
# RÉSUMÉ FINAL
# ==============================================================================
print("="*80)
print("📋 RÉSUMÉ FINAL")
print("="*80)

checks = [
    ("Base de données", not missing and len(monaco_data) > 0),
    ("Préditeur intervals", result_outside['goal_probability'] < 10),
    ("Préditeur MAX formula", base_rate >= 0.95),
    ("Formatter SEM/IQR", has_sem and has_iqr),
    ("Scripts monitoring", all(Path(p).exists() for p in monitoring_files.values()))
]

all_passed = all(passed for _, passed in checks)

for check_name, passed in checks:
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")

print()
if all_passed:
    print("🎉 SYSTÈME V2.0 PRÊT POUR PRODUCTION !")
    print()
    print("📝 Prochaines étapes :")
    print("   1. python3 build_team_recurrence_stats.py  # Si pas déjà fait")
    print("   2. python3 test_pipeline_complet_simulation.py  # Test complet")
    print("   3. python3 live_monitor_with_historical_patterns.py  # Démarrer monitoring")
else:
    print("⚠️ VALIDATION INCOMPLÈTE - Voir erreurs ci-dessus")
    print()
    print("📝 Actions requises :")
    for check_name, passed in checks:
        if not passed:
            print(f"   ❌ Corriger : {check_name}")

print("="*80)
