"""
Simulateur rapide pour injecter `live_stats` et observer l'effet sur calculate_danger_score
Usage: python test_simulate_events.py
"""
from predictors.interval_predictor import IntervalPredictor


def run_simulation():
    p = IntervalPredictor()

    # Teams exist in data/team_profiles after previous integration test
    home = p.load_team_profile('Arsenal')
    away = p.load_team_profile('Manchester City')

    if not home or not away:
        print("Profiles manquants — exécutez d'abord le scraper d'historique")
        return

    scenarios = [
        ('No events', None),
        ('Home 1 red card', {'red_cards': {'home': 1, 'away': 0}}),
        ('Away 1 penalty', {'penalties': {'home': 0, 'away': 1}}),
        ('Home 2 injuries', {'injuries': {'home': 2, 'away': 0}}),
        ('Home RC + Away penalty', {'red_cards': {'home': 1, 'away': 0}, 'penalties': {'home': 0, 'away': 1}}),
        ('Multiple events (extreme)', {'red_cards': {'home': 2, 'away': 1}, 'penalties': {'home': 1, 'away': 2}, 'injuries': {'home': 2, 'away': 1}})
    ]

    minute = 65

    for name, live in scenarios:
        print('\n' + '='*60)
        print(f"Scenario: {name}")
        print('-'*60)

        danger, details = p.calculate_danger_score(
            home_profile=home,
            away_profile=away,
            interval=p.determine_current_interval(minute),
            current_score=(1,1),
            current_minute=minute,
            live_stats=live
        )

        print(f"Danger score: {danger:.2f} ({details.get('danger_score')})")
        print(f"Home event modifier: {details.get('home_event_modifier')}")
        print(f"Away event modifier: {details.get('away_event_modifier')}")
        print(f"Home prob: {details.get('home_goal_probability')} | Away prob: {details.get('away_goal_probability')}")
        print('Details (events):', {k: details.get(k) for k in ['red_cards_home','red_cards_away','penalties_home','penalties_away','injuries_home','injuries_away']})


if __name__ == '__main__':
    run_simulation()
