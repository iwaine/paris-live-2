"""
Tests unitaires pour les alertes Telegram
Vérifie le formatage des messages avec événements sans envoyer sur le réseau
"""
from utils.telegram_bot import TelegramNotifier
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio


def test_send_match_alert_with_no_events():
    """Teste le formatage d'alerte sans événements"""
    notifier = TelegramNotifier()
    
    # Mock pour éviter l'envoi réel (async)
    async def mock_send_async(*args, **kwargs):
        return True
    
    with patch.object(notifier, 'send_message', side_effect=mock_send_async) as mock_send:
        match_data = {
            'home_team': 'Arsenal',
            'away_team': 'Manchester City',
            'current_minute': 65,
            'score': '1-1',
            'danger_score': 4.5,
            'interpretation': 'ULTRA-DANGEREUX',
            'live_stats': {
                'red_cards': {'home': 0, 'away': 0},
                'penalties': {'home': 0, 'away': 0},
                'injuries': {'home': 0, 'away': 0}
            }
        }
        
        result = notifier.send_match_alert(match_data)
        
        assert result == True
        assert mock_send.called
        message = mock_send.call_args[0][0]  # First positional argument
        assert '🔴 ALERTE PRÉDICTION' in message
        assert 'Arsenal' in message
        assert 'Manchester City' in message
        assert '65' in message
        assert '4.5' in message or '4.50' in message
        assert '⚠️ Événements en direct:' not in message  # Pas d'événements


def test_send_match_alert_with_red_card_events():
    """Teste le formatage d'alerte avec cartons rouges"""
    notifier = TelegramNotifier()
    
    async def mock_send_async(*args, **kwargs):
        return True
    
    with patch.object(notifier, 'send_message', side_effect=mock_send_async) as mock_send:
        match_data = {
            'home_team': 'Arsenal',
            'away_team': 'Manchester City',
            'current_minute': 65,
            'score': '1-1',
            'danger_score': 3.85,
            'interpretation': 'DANGEREUX',
            'live_stats': {
                'red_cards': {'home': 1, 'away': 0},
                'penalties': {'home': 0, 'away': 0},
                'injuries': {'home': 0, 'away': 0}
            }
        }
        
        result = notifier.send_match_alert(match_data)
        
        assert result == True
        message = mock_send.call_args[0][0]
        assert '⚠️ Événements en direct:' in message
        assert 'Cartons rouges' in message
        assert 'Domicile: 1' in message
        assert 'Extérieur: 0' in message


def test_send_match_alert_with_penalty_events():
    """Teste le formatage d'alerte avec pénalités"""
    notifier = TelegramNotifier()
    
    async def mock_send_async(*args, **kwargs):
        return True
    
    with patch.object(notifier, 'send_message', side_effect=mock_send_async) as mock_send:
        match_data = {
            'home_team': 'Arsenal',
            'away_team': 'Manchester City',
            'current_minute': 65,
            'score': '1-1',
            'danger_score': 5.44,
            'interpretation': 'ULTRA-DANGEREUX',
            'live_stats': {
                'red_cards': {'home': 0, 'away': 0},
                'penalties': {'home': 0, 'away': 1},
                'injuries': {'home': 0, 'away': 0}
            }
        }
        
        result = notifier.send_match_alert(match_data)
        
        assert result == True
        message = mock_send.call_args[0][0]
        assert '⚠️ Événements en direct:' in message
        assert 'Pénalités' in message
        assert 'Domicile: 0' in message
        assert 'Extérieur: 1' in message


def test_send_match_alert_with_multiple_events():
    """Teste le formatage d'alerte avec événements multiples"""
    notifier = TelegramNotifier()
    
    async def mock_send_async(*args, **kwargs):
        return True
    
    with patch.object(notifier, 'send_message', side_effect=mock_send_async) as mock_send:
        match_data = {
            'home_team': 'Arsenal',
            'away_team': 'Manchester City',
            'current_minute': 65,
            'score': '1-1',
            'danger_score': 3.2,
            'interpretation': 'MODÉRÉ',
            'live_stats': {
                'red_cards': {'home': 2, 'away': 1},
                'penalties': {'home': 1, 'away': 2},
                'injuries': {'home': 2, 'away': 1}
            }
        }
        
        result = notifier.send_match_alert(match_data)
        
        assert result == True
        message = mock_send.call_args[0][0]
        assert '⚠️ Événements en direct:' in message
        assert 'Cartons rouges' in message
        assert 'Pénalités' in message
        assert 'Blessures' in message
        assert 'Domicile: 2' in message
        assert 'Domicile: 1' in message  # injuries_home


def test_send_goal_notification_with_events():
    """Teste le formatage de notification de but avec événements"""
    notifier = TelegramNotifier()
    
    async def mock_send_async(*args, **kwargs):
        return True
    
    with patch.object(notifier, 'send_message', side_effect=mock_send_async) as mock_send:
        match_data = {
            'home_team': 'Arsenal',
            'away_team': 'Manchester City',
            'score': '2-1',
            'live_stats': {
                'red_cards': {'home': 1, 'away': 0},
                'penalties': {'home': 0, 'away': 0},
                'injuries': {'home': 0, 'away': 0}
            }
        }
        
        result = notifier.send_goal_notification(match_data, 'Arsenal', 68)
        
        assert result == True
        message = mock_send.call_args[0][0]
        assert '⚽ <b>BUT MARQUÉ!</b>' in message
        assert 'Arsenal' in message
        assert 'Manchester City' in message
        assert '68' in message
        assert '2-1' in message
        assert '⚠️ Événements en direct:' in message
        assert 'Cartons rouges' in message


def test_send_match_alert_prediction_format():
    """Teste le formatage d'alerte au format prédiction (avec 'details')"""
    notifier = TelegramNotifier()
    
    async def mock_send_async(*args, **kwargs):
        return True
    
    with patch.object(notifier, 'send_message', side_effect=mock_send_async) as mock_send:
        # Format retourné par predict_match
        prediction = {
            'success': True,
            'current_minute': 65,
            'current_interval': '61-75',
            'current_score': '1-1',
            'danger_score': 4.62,
            'interpretation': 'ULTRA-DANGEREUX',
            'details': {
                'home_team': 'Arsenal',
                'away_team': 'Manchester City',
                'red_cards_home': 0,
                'red_cards_away': 0,
                'penalties_home': 0,
                'penalties_away': 1,
                'injuries_home': 0,
                'injuries_away': 0
            },
            'bet_recommendation': {}
        }
        
        result = notifier.send_match_alert(prediction)
        
        assert result == True
        message = mock_send.call_args[0][0]
        assert '🔴 ALERTE PRÉDICTION' in message
        assert 'Arsenal' in message
        assert 'Manchester City' in message
        assert '65' in message
        assert 'Pénalités' in message


if __name__ == '__main__':
    # Run tests
    test_send_match_alert_with_no_events()
    test_send_match_alert_with_red_card_events()
    test_send_match_alert_with_penalty_events()
    test_send_match_alert_with_multiple_events()
    test_send_goal_notification_with_events()
    test_send_match_alert_prediction_format()
    print("✅ All Telegram alert tests passed!")
