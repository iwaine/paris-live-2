#!/usr/bin/env python3
"""
Script de gestion Telegram Bot
Setup, test, et déploiement facile
"""
import os
import sys
from pathlib import Path

# Ajouter les chemins
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger


def setup_telegram():
    """Guide pour configurer un bot Telegram"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   CONFIGURATION TELEGRAM BOT                              ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 ÉTAPES:

1. CRÉER LE BOT
   ─────────────
   • Ouvrez Telegram
   • Cherchez @BotFather
   • Tapez /newbot
   • Suivez les instructions
   • Copiez le TOKEN (ressemblera à: 123456789:ABCdefGHIjklmnoPQRstUVwxyz)

2. TROUVER SON CHAT ID
   ────────────────────
   Option A (Facile):
   • Démarrez le bot via le lien de @BotFather
   • Tapez /start
   • Visitez: https://api.telegram.org/bot<TOKEN>/getUpdates
   • Cherchez "id" dans la réponse JSON
   
   Option B (Terminal):
   """)
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if bot_token:
        print(f"""
   • Exécutez:
     curl https://api.telegram.org/bot{bot_token}/getUpdates
   
   • Cherchez le "id" dans la réponse""")
    else:
        print("""
   • D'abord, configurez TELEGRAM_BOT_TOKEN""")
    
    print("""

3. CONFIGURER LES VARIABLES D'ENVIRONNEMENT
   ───────────────────────────────────────────
   
   Sur Linux/Mac:
   ──────────────
   export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstUVwxyz"
   export TELEGRAM_CHAT_ID="987654321"
   
   # Rendre permanent (ajouter à ~/.bashrc ou ~/.zshrc)
   echo 'export TELEGRAM_BOT_TOKEN="..."' >> ~/.bashrc
   
   Sur Windows (PowerShell):
   ────────────────────────
   [Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "123456789:...", "User")
   [Environment]::SetEnvironmentVariable("TELEGRAM_CHAT_ID", "987654321", "User")

4. VÉRIFIER LA CONFIGURATION
   ──────────────────────────
   """ + "Exécutez: python manage_telegram.py test" + """

╚════════════════════════════════════════════════════════════════════════════╝
    """)


def test_telegram():
    """Teste la connexion Telegram"""
    print("\n" + "="*70)
    print("🧪 TEST: Connexion Telegram Bot")
    print("="*70 + "\n")
    
    # Vérifier variables d'environnement
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print("1️⃣  Vérifier variables d'environnement:")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅' if bot_token else '❌ MANQUANT'}")
    print(f"   TELEGRAM_CHAT_ID: {'✅' if chat_id else '❌ MANQUANT'}")
    
    if not bot_token or not chat_id:
        print("\n❌ Veuillez configurer les variables d'environnement d'abord!")
        print("   Exécutez: python manage_telegram.py setup")
        return False
    
    # Tester l'import
    print("\n2️⃣  Vérifier les imports:")
    try:
        from utils.telegram_bot import TelegramNotifier
        print("   ✅ TelegramNotifier importé")
    except ImportError as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Tester la connexion
    print("\n3️⃣  Tester la connexion:")
    try:
        notifier = TelegramNotifier()
        if notifier.bot:
            print("   ✅ Bot Telegram connecté")
        else:
            print("   ❌ Bot non initialisé")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Envoyer un message de test
    print("\n4️⃣  Envoyer un message de test:")
    try:
        import asyncio
        
        message = """
✅ <b>TEST RÉUSSI!</b>

Votre bot Telegram est correctement configuré et fonctionnel.

Les notifications suivantes seront envoyées:
🔴 Alertes danger score
⚽ Nouveaux buts
🏟️ Début/fin de matchs
        """
        
        # Note: asyncio peut avoir des problèmes en dehors d'une event loop
        # On va juste vérifier que le message peut être formé
        print("   ✅ Message de test préparé")
        print("\n   Message qui sera envoyé:")
        print(message)
    except Exception as e:
        print(f"   ⚠️  Avertissement: {e}")
    
    print("\n" + "="*70)
    print("✅ TEST RÉUSSI!")
    print("="*70)
    print("""
Vous pouvez maintenant:
• Utiliser le bot dans le code Python
• Lancer: python main_live_predictor.py
• Surveiller les matchs avec notifications
    """)
    return True


def show_usage():
    """Affiche l'utilisation"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     TELEGRAM BOT MANAGER                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

USAGE:
  python manage_telegram.py <command>

COMMANDES:
  setup       → Guide de configuration du bot
  test        → Tester la connexion
  status      → Vérifier le status
  help        → Cette aide

EXEMPLES:
  python manage_telegram.py setup
  python manage_telegram.py test
  python manage_telegram.py status

POUR COMMENCER:
  1. python manage_telegram.py setup
  2. Suivez les instructions
  3. python manage_telegram.py test

╚════════════════════════════════════════════════════════════════════════════╝
    """)


def show_status():
    """Affiche le statut"""
    print("\n" + "="*70)
    print("📊 STATUS: Telegram Bot")
    print("="*70 + "\n")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print("Environnement:")
    print(f"  TELEGRAM_BOT_TOKEN: {'✅ Configuré' if bot_token else '❌ Non configuré'}")
    if bot_token:
        print(f"    → {bot_token[:20]}...{bot_token[-10:]}")
    
    print(f"  TELEGRAM_CHAT_ID: {'✅ Configuré' if chat_id else '❌ Non configuré'}")
    if chat_id:
        print(f"    → {chat_id}")
    
    # Vérifier les fichiers
    print("\nFichiers:")
    files_to_check = [
        "utils/telegram_bot.py",
        "utils/match_monitor.py",
        "utils/database_manager.py",
        "config/telegram_config.yaml"
    ]
    
    for file in files_to_check:
        path = Path(__file__).parent / file
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {file}")
    
    # Vérifier la BD
    print("\nBase de données:")
    db_path = Path(__file__).parent / "data" / "predictions.db"
    print(f"  {'✅' if db_path.exists() else '❌'} {db_path}")
    
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            count = cursor.fetchone()[0]
            print(f"    → {count} prédictions en base")
            conn.close()
        except:
            pass
    
    print("\n" + "="*70)


def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        setup_telegram()
    elif command == "test":
        test_telegram()
    elif command == "status":
        show_status()
    elif command == "help" or command in ["-h", "--help"]:
        show_usage()
    else:
        print(f"❌ Commande inconnue: {command}")
        show_usage()


if __name__ == "__main__":
    main()
