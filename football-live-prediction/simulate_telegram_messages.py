"""
Simulateur : affiche les messages Telegram avec événements (sans envoi réseau)
Génère des prédictions avec live_stats et affiche les messages d'alerte formatés
Usage: python simulate_telegram_messages.py
"""
from predictors.interval_predictor import IntervalPredictor
from utils.telegram_bot import TelegramNotifier
from unittest.mock import patch
import asyncio


def display_message_header(title: str):
    """Affiche un en-tête pour chaque message"""
    print('\n' + '='*70)
    print(f"📱 MESSAGE TELEGRAM: {title}")
    print('='*70)


def display_message_content(message: str):
    """Affiche le contenu du message formaté"""
    print(message)
    print('-'*70)


async def mock_send_async(message):
    """Mock async send qui capture le message"""
    return message


def run_telegram_simulator():
    """Simule l'envoi de messages Telegram avec différents scénarios"""
    p = IntervalPredictor()

    # Load profiles
    home = p.load_team_profile('Arsenal')
    away = p.load_team_profile('Manchester City')

    if not home or not away:
        print("⚠️  Profiles manquants — exécutez d'abord le scraper d'historique")
        return

    notifier = TelegramNotifier()

    # Scénarios avec différents événements
    scenarios = [
        {
            'name': 'Alerte danger : Aucun événement',
            'live_stats': {
                'red_cards': {'home': 0, 'away': 0},
                'penalties': {'home': 0, 'away': 0},
                'injuries': {'home': 0, 'away': 0}
            },
            'minute': 65,
            'score': (1, 1)
        },
        {
            'name': 'Alerte danger : Carton rouge domicile',
            'live_stats': {
                'red_cards': {'home': 1, 'away': 0},
                'penalties': {'home': 0, 'away': 0},
                'injuries': {'home': 0, 'away': 0}
            },
            'minute': 65,
            'score': (1, 1)
        },
        {
            'name': 'Alerte danger : Penalty extérieur',
            'live_stats': {
                'red_cards': {'home': 0, 'away': 0},
                'penalties': {'home': 0, 'away': 1},
                'injuries': {'home': 0, 'away': 0}
            },
            'minute': 65,
            'score': (1, 1)
        },
        {
            'name': 'Notification de but avec carton rouge',
            'live_stats': {
                'red_cards': {'home': 1, 'away': 0},
                'penalties': {'home': 0, 'away': 0},
                'injuries': {'home': 0, 'away': 0}
            },
            'minute': 68,
            'score': (2, 1),
            'goal': True
        },
        {
            'name': 'Alerte danger : Événements multiples',
            'live_stats': {
                'red_cards': {'home': 2, 'away': 1},
                'penalties': {'home': 1, 'away': 2},
                'injuries': {'home': 2, 'away': 1}
            },
            'minute': 72,
            'score': (2, 2)
        }
    ]

    for scenario in scenarios:
        display_message_header(scenario['name'])

        minute = scenario.get('minute', 65)
        score = scenario.get('score', (1, 1))
        live_stats = scenario.get('live_stats', {})

        # Calculer la prédiction
        interval = p.determine_current_interval(minute)
        danger, details = p.calculate_danger_score(
            home_profile=home,
            away_profile=away,
            interval=interval,
            current_score=score,
            current_minute=minute,
            live_stats=live_stats
        )

        # Construire un dict de prédiction complet
        prediction = {
            'success': True,
            'current_minute': minute,
            'current_interval': interval,
            'current_score': f"{score[0]}-{score[1]}",
            'danger_score': danger,
            'interpretation': p._interpret_danger_score(danger),
            'details': details,
            'bet_recommendation': p._generate_bet_recommendation(danger, details, p._interpret_danger_score(danger), minute)
        }

        # Mock send_message pour capturer le message
        with patch.object(notifier, 'send_message', side_effect=mock_send_async) as mock_send:
            if scenario.get('goal'):
                # Afficher notification de but
                match_data = {
                    'home_team': home.get('team'),
                    'away_team': away.get('team'),
                    'score': f"{score[0]}-{score[1]}",
                    'live_stats': live_stats
                }
                notifier.send_goal_notification(match_data, home.get('team'), minute)
            else:
                # Afficher alerte danger
                notifier.send_match_alert(prediction)

            if mock_send.called:
                message = mock_send.call_args[0][0]
                display_message_content(message)

        print(f"📊 Danger score: {danger:.2f} | Interpretation: {p._interpret_danger_score(danger)}")
        print(f"🎯 Home modifier: {details.get('home_event_modifier')} | Away modifier: {details.get('away_event_modifier')}")


if __name__ == '__main__':
    run_telegram_simulator()
    print('\n✅ Simulateur Telegram terminé!')
