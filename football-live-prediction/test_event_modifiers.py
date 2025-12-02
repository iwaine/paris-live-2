from predictors.interval_predictor import IntervalPredictor


def make_profile(scored=1.0, conceded=1.0):
    # Minimal profile structure expected by calculate_danger_score
    return {
        'team': 'TEST',
        'home': {
            'goals_by_interval': {'61-75': {'scored': scored, 'conceded': conceded}},
            'games_played': 4,
            'total_scored': int(scored * 4),
            'recent_form': {'avg_goals_scored': scored}
        },
        'away': {
            'goals_by_interval': {'61-75': {'scored': scored, 'conceded': conceded}},
            'games_played': 4,
            'total_scored': int(scored * 4),
            'recent_form': {'avg_goals_scored': scored}
        }
    }


def test_no_events_modifier_default():
    p = IntervalPredictor()
    home = make_profile(scored=1.0, conceded=1.0)['home']
    away = make_profile(scored=1.0, conceded=1.0)['away']

    danger, details = p.calculate_danger_score(home_profile={'team': 'H', 'home': home},
                                               away_profile={'team': 'A', 'away': away},
                                               interval='61-75',
                                               current_score=(0, 0),
                                               current_minute=65,
                                               live_stats=None)

    assert details['home_event_modifier'] == 1.0
    assert details['away_event_modifier'] == 1.0


def test_home_red_card_reduces_home_modifier_and_danger():
    p = IntervalPredictor()
    home = make_profile(scored=1.5, conceded=0.5)['home']
    away = make_profile(scored=1.0, conceded=1.0)['away']

    base_danger, base_details = p.calculate_danger_score(home_profile={'team': 'H', 'home': home},
                                                         away_profile={'team': 'A', 'away': away},
                                                         interval='61-75',
                                                         current_score=(1, 1),
                                                         current_minute=65,
                                                         live_stats=None)

    # Apply one red card to home
    live = {'red_cards': {'home': 1, 'away': 0}}
    new_danger, new_details = p.calculate_danger_score(home_profile={'team': 'H', 'home': home},
                                                       away_profile={'team': 'A', 'away': away},
                                                       interval='61-75',
                                                       current_score=(1, 1),
                                                       current_minute=65,
                                                       live_stats=live)

    # modifier expected: max(0.4, 1 - 0.3*1) => 0.7
    assert abs(new_details['home_event_modifier'] - 0.7) < 1e-6
    assert new_danger < base_danger


def test_away_penalty_increases_away_modifier_and_danger():
    p = IntervalPredictor()
    home = make_profile(scored=1.0, conceded=1.0)['home']
    away = make_profile(scored=2.0, conceded=0.5)['away']

    base_danger, base_details = p.calculate_danger_score(home_profile={'team': 'H', 'home': home},
                                                         away_profile={'team': 'A', 'away': away},
                                                         interval='61-75',
                                                         current_score=(0, 0),
                                                         current_minute=65,
                                                         live_stats=None)

    live = {'penalties': {'home': 0, 'away': 1}}
    new_danger, new_details = p.calculate_danger_score(home_profile={'team': 'H', 'home': home},
                                                       away_profile={'team': 'A', 'away': away},
                                                       interval='61-75',
                                                       current_score=(0, 0),
                                                       current_minute=65,
                                                       live_stats=live)

    # modifier expected for away: min(2.0, 1 + 0.4*1) => 1.4
    assert abs(new_details['away_event_modifier'] - 1.4) < 1e-6
    assert new_danger != base_danger


def test_injuries_reduce_modifier():
    p = IntervalPredictor()
    home = make_profile(scored=1.2, conceded=0.8)['home']
    away = make_profile(scored=1.0, conceded=1.0)['away']

    live = {'injuries': {'home': 2, 'away': 0}}
    new_danger, new_details = p.calculate_danger_score(home_profile={'team': 'H', 'home': home},
                                                       away_profile={'team': 'A', 'away': away},
                                                       interval='61-75',
                                                       current_score=(0, 0),
                                                       current_minute=65,
                                                       live_stats=live)

    # home_inj_mod = max(0.6, 1 - 0.15*2) => max(0.6, 0.7) => 0.7
    assert abs(new_details['home_event_modifier'] - 0.7) < 1e-6
    assert new_details['home_event_modifier'] <= 1.0
