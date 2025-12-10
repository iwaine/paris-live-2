#!/usr/bin/env python3
"""
Simulation du message Telegram enrichi pour un match live Australia A-League
"""
from telegram_formatter_enriched import format_telegram_alert_enriched

# Données simulées pour un match en live (minute 88, intervalle 76-90)
match_data = {
    'home_team': 'Sydney FC',
    'away_team': 'Melbourne Victory',
    'current_minute': 88,
    'score_home': 2,
    'score_away': 2,
    'league': 'Australia - A-League',
    'live_stats': {
        'possession_home': 51,
        'possession_away': 49,
        'corners_home': 5,
        'corners_away': 6,
        'shots_home': 14,
        'shots_away': 15,
        'shots_on_target_home': 7,
        'shots_on_target_away': 8,
        'attacks_home': 100,
        'attacks_away': 105,
        'dangerous_attacks_home': 35,
        'dangerous_attacks_away': 38
    }
}
prediction_home = {
    'interval_name': '76-90',
    'probability_final': 62.5,
    'probability_historical': 38.0,
    'confidence_level': 'EXCELLENT',
    'recurrence_last_5': 0.85,
    'avg_minute': 84.2,
    'std_minute': 5.9,
    'sem_minute': 2.6,
    'iqr_q1': 79,
    'iqr_q3': 89,
    'momentum_boost': 15,
    'saturation_factor': 1.00,
    'any_goal_total': 12,
    'goals_scored': 7,
    'goals_conceded': 5,
    'freq_any_goal': 0.38,
    'total_matches': 32,
    'avg_goals_first_half': 1.3,
    'avg_goals_second_half': 1.8,
    'avg_goals_full_match': 3.1
}
prediction_away = {
    'interval_name': '76-90',
    'probability_final': 65.2,
    'probability_historical': 40.0,
    'confidence_level': 'BON',
    'recurrence_last_5': 0.70,
    'avg_minute': 86.0,
    'std_minute': 6.2,
    'sem_minute': 2.9,
    'iqr_q1': 80,
    'iqr_q3': 90,
    'momentum_boost': 18,
    'saturation_factor': 1.00,
    'any_goal_total': 13,
    'goals_scored': 8,
    'goals_conceded': 5,
    'freq_any_goal': 0.40,
    'total_matches': 33,
    'avg_goals_first_half': 1.2,
    'avg_goals_second_half': 1.9,
    'avg_goals_full_match': 3.1
}
combined_prob = 0.68

message = format_telegram_alert_enriched(match_data, prediction_home, prediction_away, combined_prob)
print("\n=== SIMULATION MESSAGE TELEGRAM LIVE AUSTRALIA ===\n")
print(message)
