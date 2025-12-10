"""
Configuration Telegram Bot pour alertes live
⚠️ NE PAS COMMIT CE FICHIER SUR GITHUB !
"""

# Configuration Bot Telegram
TELEGRAM_BOT_TOKEN = "8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c"
TELEGRAM_CHAT_ID = "6942358056"

# Seuils d'alerte (ajustables)
ALERT_THRESHOLD_COMBINED = 0.80  # Alerte si probabilité combinée ≥ 80%
ALERT_THRESHOLD_SINGLE = 0.75    # Alerte si une équipe seule ≥ 75%

# Activer/désactiver les alertes
ALERTS_ENABLED = True

# Intervalle minimum entre alertes pour le même match (minutes)
MIN_ALERT_INTERVAL_MINUTES = 5
