
#!/usr/bin/env python3
"""
Workflow complet : extraction live + prédiction + message Telegram (affichage console)
"""
import sys
sys.path.append('./football-live-prediction')
from soccerstats_live_scraper import scrape_live_match
from predictors.live_goal_probability_predictor import LiveGoalProbabilityPredictor
from telegram_formatter_enriched import format_telegram_alert_enriched

# URL du match live Australia A-League
url = "https://www.soccerstats.com/pmatch.asp?league=australia&stats=41-11-2-2026"
live_data = scrape_live_match(url)
if not live_data:
    print("❌ Aucune donnée extraite pour ce match.")
    exit(1)
match_dict = live_data.to_dict()

# Prédiction home
predictor = LiveGoalProbabilityPredictor()
prediction_home = predictor.predict_goal_probability(
    home_team=match_dict['home_team'],
    away_team=match_dict['away_team'],
    current_minute=match_dict['minute'],
    home_possession=match_dict['possession_home'],
    away_possession=match_dict['possession_away'],
    home_attacks=match_dict['attacks_home'],
    away_attacks=match_dict['attacks_away'],
    home_dangerous_attacks=match_dict['dangerous_attacks_home'],
    away_dangerous_attacks=match_dict['dangerous_attacks_away'],
    home_shots_on_target=match_dict['shots_on_target_home'],
    away_shots_on_target=match_dict['shots_on_target_away'],
    score_home=match_dict['score_home'],
    score_away=match_dict['score_away'],
    league="australia"
)
details_home = prediction_home.get('details', {})
for k in [
    'any_goal_total', 'goals_scored', 'goals_conceded', 'freq_any_goal', 'total_matches',
    'avg_goals_first_half', 'avg_goals_second_half', 'avg_goals_full_match',
]:
    prediction_home[k] = prediction_home.get(k, 0)
prediction_home['interval_name'] = details_home.get('interval', '')
prediction_home['probability_final'] = details_home.get('final_probability', 0) * 100
prediction_home['probability_historical'] = details_home.get('historical_component', 0) * 100
prediction_home['confidence_level'] = details_home.get('danger_level', '')
prediction_home['recurrence_last_5'] = 0.7  # Valeur fictive si non calculée
prediction_home['avg_minute'] = 0
prediction_home['sem_minute'] = 0
prediction_home['iqr_q1'] = 0
prediction_home['iqr_q3'] = 0
# Prédiction away
prediction_away = predictor.predict_goal_probability(
    home_team=match_dict['away_team'],
    away_team=match_dict['home_team'],
    current_minute=match_dict['minute'],
    home_possession=match_dict['possession_away'],
    away_possession=match_dict['possession_home'],
    home_attacks=match_dict['attacks_away'],
    away_attacks=match_dict['attacks_home'],
    home_dangerous_attacks=match_dict['dangerous_attacks_away'],
    away_dangerous_attacks=match_dict['dangerous_attacks_home'],
    home_shots_on_target=match_dict['shots_on_target_away'],
    away_shots_on_target=match_dict['shots_on_target_home'],
    score_home=match_dict['score_away'],
    score_away=match_dict['score_home'],
    league="australia"
)
details_away = prediction_away.get('details', {})
for k in [
    'any_goal_total', 'goals_scored', 'goals_conceded', 'freq_any_goal', 'total_matches',
    'avg_goals_first_half', 'avg_goals_second_half', 'avg_goals_full_match',
]:
    prediction_away[k] = prediction_away.get(k, 0)
prediction_away['interval_name'] = details_away.get('interval', '')
prediction_away['probability_final'] = details_away.get('final_probability', 0) * 100
prediction_away['probability_historical'] = details_away.get('historical_component', 0) * 100
prediction_away['confidence_level'] = details_away.get('danger_level', '')
prediction_away['recurrence_last_5'] = 0.7  # Valeur fictive si non calculée
prediction_away['avg_minute'] = 0
prediction_away['sem_minute'] = 0
prediction_away['iqr_q1'] = 0
prediction_away['iqr_q3'] = 0

# Probabilité combinée (max des deux)
combined_prob = max(prediction_home['goal_probability'], prediction_away['goal_probability']) / 100

# Générer le message Telegram
if 'current_minute' not in match_dict and 'minute' in match_dict:
    match_dict['current_minute'] = match_dict['minute']
message = format_telegram_alert_enriched(match_dict, prediction_home, prediction_away, combined_prob)
print("\n=== MESSAGE TELEGRAM LIVE AUSTRALIA ===\n")
print(message)
