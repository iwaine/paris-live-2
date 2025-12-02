#!/usr/bin/env python3
"""
Démonstration du Bot Telegram
Montre comment le bot envoie les alertes sur Telegram
"""
import sys
import os

# Aller dans le répertoire football-live-prediction
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(script_dir, 'football-live-prediction')
os.chdir(project_dir)

# Ajouter le répertoire courant aux imports
sys.path.insert(0, project_dir)

from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env racine
load_dotenv(os.path.join(script_dir, '.env'))

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

print("=" * 70)
print("🤖 DÉMONSTRATION BOT TELEGRAM")
print("=" * 70)

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("\n⚠️  VARIABLES D'ENVIRONNEMENT MANQUANTES")
    print("\nPour configurer le bot Telegram, exécutez:")
    print("\n  export TELEGRAM_BOT_TOKEN='votre_token_ici'")
    print("  export TELEGRAM_CHAT_ID='votre_chat_id_ici'")
    print("\n📝 Guide complet:")
    print("  1. Trouvez @BotFather sur Telegram")
    print("  2. Tapez /newbot")
    print("  3. Suivez les instructions pour obtenir votre TOKEN")
    print("  4. Trouvez @userinfobot sur Telegram")
    print("  5. Tapez /start pour obtenir votre USER ID")
    print("\n" + "=" * 70)
    exit(1)

print(f"\n✅ Configuration trouvée:")
print(f"   Token: {TELEGRAM_BOT_TOKEN[:20]}...")
print(f"   Chat ID: {TELEGRAM_CHAT_ID}")

# Importer après avoir vérifié les variables
from utils.telegram_bot import TelegramNotifier

def test_notifications():
    """Teste les notifications Telegram"""
    
    notifier = TelegramNotifier()
    
    if not notifier.bot:
        print("\n❌ Bot Telegram non initialisé")
        print("Vérifiez vos variables d'environnement !")
        return
    
    print("\n" + "=" * 70)
    print("📤 ENVOI DE NOTIFICATIONS DE TEST")
    print("=" * 70)
    
    # Test 1: Alerte simple (sans événements)
    print("\n1️⃣  Envoi d'une alerte simple...")
    result1 = notifier.send_match_alert({
        'home_team': 'Arsenal',
        'away_team': 'Manchester City',
        'current_minute': 35,
        'current_interval': '31-45',
        'danger_score': 4.62,
        'interpretation': 'ULTRA-DANGEREUX 🔴',
        'details': {
            'home_event_modifier': 1.0,
            'away_event_modifier': 1.0,
            'red_cards_home': 0,
            'red_cards_away': 0,
            'penalties_home': 0,
            'penalties_away': 0,
            'injuries_home': 0,
            'injuries_away': 0
        }
    })
    print(f"   Résultat: {'✅ Succès' if result1 else '❌ Échec'}")
    
    # Test 2: Alerte avec événements
    print("\n2️⃣  Envoi d'une alerte avec CARTON ROUGE...")
    result2 = notifier.send_match_alert({
        'home_team': 'Arsenal',
        'away_team': 'Manchester City',
        'current_minute': 50,
        'current_interval': '46-60',
        'danger_score': 3.85,
        'interpretation': 'DANGEREUX 🟠',
        'details': {
            'home_event_modifier': 0.7,
            'away_event_modifier': 1.0,
            'red_cards_home': 1,
            'red_cards_away': 0,
            'penalties_home': 0,
            'penalties_away': 0,
            'injuries_home': 0,
            'injuries_away': 0
        }
    })
    print(f"   Résultat: {'✅ Succès' if result2 else '❌ Échec'}")
    
    # Test 3: Notification de but
    print("\n3️⃣  Envoi d'une notification de BUT...")
    result3 = notifier.send_goal_notification(
        match_data={
            'home_team': 'Arsenal',
            'away_team': 'Manchester City',
            'score': '2-1',
            'live_stats': {
                'red_cards': {'home': 1, 'away': 0},
                'penalties': {'home': 0, 'away': 1},
                'injuries': {'home': 0, 'away': 0}
            }
        },
        team='Arsenal',
        minute=65
    )
    print(f"   Résultat: {'✅ Succès' if result3 else '❌ Échec'}")
    
    print("\n" + "=" * 70)
    print("✅ Tests de notification terminés!")
    print("=" * 70)


if __name__ == '__main__':
    print("\n⏳ Envoi des notifications...")
    test_notifications()
    print("\n💡 Les messages devraient maintenant apparaître sur votre Telegram!")
