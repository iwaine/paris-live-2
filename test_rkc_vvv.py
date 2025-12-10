#!/usr/bin/env python3
"""
Test du système V2.0 avec match réel : RKC Waalwijk vs VVV
Netherlands - Eerste Divisie
Score actuel : 0-1
"""

import sys
sys.path.insert(0, '/workspaces/paris-live/football-live-prediction')

from predictors.live_goal_probability_predictor import LiveGoalProbabilityPredictor
from telegram_formatter_enriched import format_telegram_alert_enriched

print("="*80)
print("🔍 TEST MATCH : RKC Waalwijk vs VVV (Netherlands - Eerste Divisie)")
print("="*80)
print()

# Initialiser préditeur
predictor = LiveGoalProbabilityPredictor()

# Données du match
match_data = {
    'home_team': 'RKC Waalwijk',
    'away_team': 'VVV',
    'current_minute': 35,  # Test dans intervalle 31-45+
    'score_home': 0,
    'score_away': 1,
    'league': 'Netherlands - Eerste Divisie',
    'live_stats': {
        'possession_home': 55,
        'possession_away': 45,
        'corners_home': 3,
        'corners_away': 2,
        'shots_home': 8,
        'shots_away': 6,
        'shots_on_target_home': 3,
        'shots_on_target_away': 2,
        'attacks_home': 45,
        'attacks_away': 35,
        'dangerous_attacks_home': 18,
        'dangerous_attacks_away': 12
    }
}

# Test plusieurs minutes clés
test_minutes = [
    (10, "Début match (hors intervalle)"),
    (35, "1ère MT - Fin de mi-temps (31-45+)"),
    (42, "1ère MT - Dernières minutes (31-45+)"),
    (55, "2ème MT - Début (hors intervalle)"),
    (78, "2ème MT - Fin de mi-temps (76-90+)"),
    (85, "2ème MT - Money time (76-90+)"),
    (92, "Temps additionnel (76-90+)")
]

print("📊 RÉSULTATS PAR MINUTE")
print("-"*80)

for minute, description in test_minutes:
    print(f"\n⏰ MINUTE {minute} - {description}")
    print("-"*80)
    
    # Prédiction
    result = predictor.predict_goal_probability(
        home_team="RKC Waalwijk",
        away_team="VVV",
        league="Netherlands - Eerste Divisie",
        current_minute=minute,
        home_possession=55, away_possession=45,
        home_attacks=45, away_attacks=35,
        home_dangerous_attacks=18, away_dangerous_attacks=12,
        home_shots_on_target=3, away_shots_on_target=2,
        score_home=0, score_away=1
    )
    
    interval = result['details']['interval']
    proba = result['goal_probability']
    base_rate = result['details']['base_rate']
    
    print(f"Intervalle détecté : {interval}")
    print(f"Probabilité finale : {proba:.1f}%")
    print(f"Base rate (historical) : {base_rate*100:.1f}%")
    
    # Analyser patterns historiques
    home_pattern = result['details'].get('home_team_pattern')
    away_pattern = result['details'].get('away_team_pattern')
    
    if home_pattern:
        print(f"\n🏠 RKC Waalwijk (domicile) - {interval}")
        print(f"   Récurrence : {home_pattern.get('freq_any_goal', 0)*100:.0f}% ({home_pattern.get('any_goal_total', 0)} buts / {home_pattern.get('total_matches', 0)} matchs)")
        if 'avg_minute' in home_pattern and home_pattern['avg_minute']:
            sem = home_pattern.get('sem_minute', 0)
            q1 = home_pattern.get('iqr_q1', 0)
            q3 = home_pattern.get('iqr_q3', 0)
            print(f"   Timing : {home_pattern['avg_minute']:.1f}' ±{sem:.1f}' (SEM)")
            if q1 and q3:
                print(f"   Zone IQR : [{q1:.0f}' - {q3:.0f}']")
    
    if away_pattern:
        print(f"\n✈️  VVV (extérieur) - {interval}")
        print(f"   Récurrence : {away_pattern.get('freq_any_goal', 0)*100:.0f}% ({away_pattern.get('any_goal_total', 0)} buts / {away_pattern.get('total_matches', 0)} matchs)")
        if 'avg_minute' in away_pattern and away_pattern['avg_minute']:
            sem = away_pattern.get('sem_minute', 0)
            q1 = away_pattern.get('iqr_q1', 0)
            q3 = away_pattern.get('iqr_q3', 0)
            print(f"   Timing : {away_pattern['avg_minute']:.1f}' ±{sem:.1f}' (SEM)")
            if q1 and q3:
                print(f"   Zone IQR : [{q1:.0f}' - {q3:.0f}']")
    
    # Décision signal
    is_key_interval = interval in ["31-45", "76-90"]
    should_signal = proba >= 65 and is_key_interval
    
    print(f"\n{'🚨' if should_signal else '⭕'} DÉCISION : {'SIGNAL TELEGRAM' if should_signal else 'PAS DE SIGNAL'}")
    if not is_key_interval:
        print(f"   Raison : Hors intervalles clés (31-45+, 76-90+)")
    elif proba < 65:
        print(f"   Raison : Probabilité < 65% (seuil minimum)")

print("\n" + "="*80)
print("📱 EXEMPLE SIGNAL TELEGRAM (Minute 78)")
print("="*80)
print()

# Générer signal pour minute 78 (si données suffisantes)
result_78 = predictor.predict_goal_probability(
    home_team="RKC Waalwijk",
    away_team="VVV",
    league="Netherlands - Eerste Divisie",
    current_minute=78,
    home_possession=55, away_possession=45,
    home_attacks=70, away_attacks=50,
    home_dangerous_attacks=30, away_dangerous_attacks=20,
    home_shots_on_target=5, away_shots_on_target=3,
    score_home=0, score_away=1
)

if result_78['goal_probability'] >= 65:
    # Formatter les données pour Telegram
    home_pattern = result_78['details'].get('home_team_pattern', {})
    away_pattern = result_78['details'].get('away_team_pattern', {})
    
    # Construire données enrichies
    pred_home = {
        'interval_name': result_78['details']['interval'],
        'probability_final': result_78['goal_probability'],
        'probability_historical': home_pattern.get('freq_any_goal', 0) * 100,
        'confidence_level': 'EXCELLENT' if result_78['goal_probability'] >= 85 else 'BON',
        'recurrence_last_5': home_pattern.get('freq_any_goal', 0),
        'avg_minute': home_pattern.get('avg_minute', 0),
        'std_minute': home_pattern.get('std_minute', 0),
        'sem_minute': home_pattern.get('sem_minute', 0),
        'iqr_q1': home_pattern.get('iqr_q1', 0),
        'iqr_q3': home_pattern.get('iqr_q3', 0),
        'momentum_boost': result_78['details'].get('live_adjustment', 0),
        'saturation_factor': 1.0,
        'any_goal_total': home_pattern.get('any_goal_total', 0),
        'goals_scored': home_pattern.get('goals_scored', 0),
        'goals_conceded': home_pattern.get('goals_conceded', 0),
        'freq_any_goal': home_pattern.get('freq_any_goal', 0),
        'total_matches': home_pattern.get('total_matches', 0),
        'avg_goals_first_half': home_pattern.get('avg_goals_first_half', 1.0),
        'avg_goals_second_half': home_pattern.get('avg_goals_second_half', 1.5),
        'avg_goals_full_match': home_pattern.get('avg_goals_full_match', 2.5)
    }
    
    pred_away = {
        'interval_name': result_78['details']['interval'],
        'probability_final': result_78['goal_probability'],
        'probability_historical': away_pattern.get('freq_any_goal', 0) * 100,
        'confidence_level': 'EXCELLENT' if result_78['goal_probability'] >= 85 else 'BON',
        'recurrence_last_5': away_pattern.get('freq_any_goal', 0),
        'avg_minute': away_pattern.get('avg_minute', 0),
        'std_minute': away_pattern.get('std_minute', 0),
        'sem_minute': away_pattern.get('sem_minute', 0),
        'iqr_q1': away_pattern.get('iqr_q1', 0),
        'iqr_q3': away_pattern.get('iqr_q3', 0),
        'momentum_boost': result_78['details'].get('live_adjustment', 0),
        'saturation_factor': 1.0,
        'any_goal_total': away_pattern.get('any_goal_total', 0),
        'goals_scored': away_pattern.get('goals_scored', 0),
        'goals_conceded': away_pattern.get('goals_conceded', 0),
        'freq_any_goal': away_pattern.get('freq_any_goal', 0),
        'total_matches': away_pattern.get('total_matches', 0),
        'avg_goals_first_half': away_pattern.get('avg_goals_first_half', 1.0),
        'avg_goals_second_half': away_pattern.get('avg_goals_second_half', 1.5),
        'avg_goals_full_match': away_pattern.get('avg_goals_full_match', 2.5)
    }
    
    match_data['current_minute'] = 78
    
    telegram_message = format_telegram_alert_enriched(
        match_data, pred_home, pred_away, result_78['goal_probability']/100
    )
    
    print(telegram_message)
else:
    print("❌ Probabilité insuffisante pour générer un signal Telegram")
    print(f"   Probabilité : {result_78['goal_probability']:.1f}% < 65%")

print()
print("="*80)
