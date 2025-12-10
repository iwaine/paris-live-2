#!/usr/bin/env python3
"""
Test affichage Telegram enrichi pour 31-45+ et 76-90+
"""
from telegram_formatter_enriched import format_telegram_alert_enriched

# Données factices pour 31-45+
match_data_31 = {
    'home_team': 'Sydney FC',
    'away_team': 'Melbourne Victory',
    'current_minute': 44,
    'score_home': 1,
    'score_away': 2,
    'league': 'Australia - A-League',
    'live_stats': {
        'possession_home': 52,
        'possession_away': 48,
        'corners_home': 2,
        'corners_away': 3,
        'shots_home': 7,
        'shots_away': 8,
        'shots_on_target_home': 3,
        'shots_on_target_away': 4,
        'attacks_home': 60,
        'attacks_away': 65,
        'dangerous_attacks_home': 18,
        'dangerous_attacks_away': 22
    }
}
prediction_home_31 = {
    'interval_name': '31-45',
    'probability_final': 41.2,
    'probability_historical': 35.0,
    'confidence_level': 'BON',
    'recurrence_last_5': 0.60,
    'avg_minute': 39.5,
    'std_minute': 4.2,
    'sem_minute': 2.1,
    'iqr_q1': 36,
    'iqr_q3': 43,
    'momentum_boost': 5,
    'saturation_factor': 1.00,
    'any_goal_total': 8,
    'goals_scored': 5,
    'goals_conceded': 3,
    'freq_any_goal': 0.35,
    'total_matches': 23,
    'avg_goals_first_half': 1.2,
    'avg_goals_second_half': 1.5,
    'avg_goals_full_match': 2.7
}
prediction_away_31 = {
    'interval_name': '31-45',
    'probability_final': 38.7,
    'probability_historical': 32.0,
    'confidence_level': 'MOYEN',
    'recurrence_last_5': 0.40,
    'avg_minute': 41.0,
    'std_minute': 5.0,
    'sem_minute': 2.5,
    'iqr_q1': 37,
    'iqr_q3': 45,
    'momentum_boost': 3,
    'saturation_factor': 1.00,
    'any_goal_total': 7,
    'goals_scored': 4,
    'goals_conceded': 3,
    'freq_any_goal': 0.32,
    'total_matches': 22,
    'avg_goals_first_half': 1.1,
    'avg_goals_second_half': 1.4,
    'avg_goals_full_match': 2.5
}
combined_prob_31 = 0.40

message_31 = format_telegram_alert_enriched(match_data_31, prediction_home_31, prediction_away_31, combined_prob_31)
print("\n=== TEST 31-45+ ===\n")
print(message_31)

# Données factices pour 76-90+
match_data_76 = {
    'home_team': 'Sydney FC',
    'away_team': 'Melbourne Victory',
    'current_minute': 85,
    'score_home': 2,
    'score_away': 2,
    'league': 'Australia - A-League',
    'live_stats': {
        'possession_home': 50,
        'possession_away': 50,
        'corners_home': 4,
        'corners_away': 5,
        'shots_home': 12,
        'shots_away': 13,
        'shots_on_target_home': 6,
        'shots_on_target_away': 7,
        'attacks_home': 90,
        'attacks_away': 95,
        'dangerous_attacks_home': 30,
        'dangerous_attacks_away': 32
    }
}
prediction_home_76 = {
    'interval_name': '76-90',
    'probability_final': 55.8,
    'probability_historical': 38.0,
    'confidence_level': 'EXCELLENT',
    'recurrence_last_5': 0.80,
    'avg_minute': 83.2,
    'std_minute': 6.1,
    'sem_minute': 2.8,
    'iqr_q1': 78,
    'iqr_q3': 89,
    'momentum_boost': 10,
    'saturation_factor': 1.00,
    'any_goal_total': 10,
    'goals_scored': 6,
    'goals_conceded': 4,
    'freq_any_goal': 0.38,
    'total_matches': 26,
    'avg_goals_first_half': 1.3,
    'avg_goals_second_half': 1.7,
    'avg_goals_full_match': 3.0
}
prediction_away_76 = {
    'interval_name': '76-90',
    'probability_final': 60.2,
    'probability_historical': 40.0,
    'confidence_level': 'BON',
    'recurrence_last_5': 0.60,
    'avg_minute': 85.0,
    'std_minute': 7.0,
    'sem_minute': 3.0,
    'iqr_q1': 80,
    'iqr_q3': 90,
    'momentum_boost': 12,
    'saturation_factor': 1.00,
    'any_goal_total': 11,
    'goals_scored': 7,
    'goals_conceded': 4,
    'freq_any_goal': 0.40,
    'total_matches': 27,
    'avg_goals_first_half': 1.2,
    'avg_goals_second_half': 1.8,
    'avg_goals_full_match': 3.0
}
combined_prob_76 = 0.59

message_76 = format_telegram_alert_enriched(match_data_76, prediction_home_76, prediction_away_76, combined_prob_76)
print("\n=== TEST 76-90+ ===\n")
print(message_76)
