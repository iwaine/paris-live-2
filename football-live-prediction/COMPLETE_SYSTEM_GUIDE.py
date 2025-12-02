"""
Guide d'utilisation du système complet
avec Telegram Bot + Surveillance Live + Base de Données
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     FOOTBALL LIVE PREDICTION - GUIDE COMPLET                ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 NOUVELLE ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Telegram Bot (utils/telegram_bot.py)
   • TelegramNotifier: Envoi de messages
   • TelegramBotApp: Bot interactif avec commandes
   
   Configuration: config/telegram_config.yaml
   Commandes:
   - /start: Démarrer
   - /help: Aide
   - /match URL: Analyser un match
   - /stats: Voir statistiques
   - /stop: Arrêter surveillance

🔄 Surveillance Live (utils/match_monitor.py)
   • MatchMonitor: Surveille 1 match en continu
   • MultiMatchMonitor: Surveille plusieurs matchs
   
   Scrape toutes les 30 secondes par défaut
   Détecte: nouveaux buts, danger scores élevés
   Envoie callbacks pour notifications

💾 Base de Données (utils/database_manager.py)
   • DatabaseManager: Gère SQLite
   
   Tables:
   - matches: Historique des matchs
   - predictions: Toutes les prédictions
   - notifications: Logs des notifications
   - stats: Statistiques par date
   
   Suivi des données: cartons rouges, pénalités, blessures


📚 INSTALLATION REQUISE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Installer les packages Telegram:
   pip install python-telegram-bot

2. Créer un bot Telegram:
   • Ouvrez Telegram et trouvez @BotFather
   • Tapez /newbot et suivez les instructions
   • Copiez le token

3. Configurer les variables d'environnement:
   export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstUVwxyz"
   export TELEGRAM_CHAT_ID="987654321"

4. Déployer la BD:
   python -c "from utils.database_manager import DatabaseManager; DatabaseManager()"


🎯 CAS D'USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAS 1: Prédiction simple (sans surveillance)
────────────────────────────────────────────

    from predictors.interval_predictor import IntervalPredictor
    
    predictor = IntervalPredictor()
    result = predictor.predict_match(
        home_team="Arsenal",
        away_team="Manchester City",
        current_minute=65
    )
    
    print(result['danger_score'])  # 4.86
    print(result['interpretation'])  # ULTRA-DANGEREUX


CAS 2: Surveillance avec notifications Telegram
───────────────────────────────────────────────

    from utils.telegram_bot import TelegramNotifier
    from utils.match_monitor import MatchMonitor, create_telegram_callbacks
    from utils.database_manager import DatabaseManager
    
    # Initialiser
    notifier = TelegramNotifier()
    db = DatabaseManager()
    monitor = MatchMonitor(match_url="http://example.com/match")
    
    # Créer callbacks
    callbacks = create_telegram_callbacks(notifier)
    monitor.set_callbacks(**callbacks)
    
    # Insérer match en BD
    match_id = db.insert_match({
        'home_team': 'Arsenal',
        'away_team': 'Manchester City',
        'match_url': 'http://example.com/match'
    })
    
    # Commencer surveillance
    monitor.monitor()
    
    db.close()


CAS 3: Analyser historique et optimiser poids
──────────────────────────────────────────────

    from utils.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    # Récupérer stats
    stats = db.get_stats(days=30)
    print(f"Accuracy: {stats['accuracy']}%")
    
    # Par intervalle
    by_interval = db.get_accuracy_by_interval()
    for interval, data in by_interval.items():
        print(f"{interval}: {data['accuracy']}% (n={data['total']})")
    
    db.close()


🔧 CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: config/telegram_config.yaml

telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"
  
  notifications:
    danger_threshold: 3.5        # Alerte si > 3.5
    update_interval_minutes: 15  # Maj toutes les 15 min
    
    types:
      match_start: true
      danger_alert: true
      goal: true
      match_end: true

Danger Levels:
  🔴 4.0+ : ULTRA-DANGEREUX (parier maintenant!)
  🟠 3.0-4.0: DANGEREUX (haute probabilité)
  🟡 2.0-3.0: MODÉRÉ (surveiller)
  🟢 <2.0: FAIBLE (passer)


📊 INTÉGRATION COMPLÈTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Exemple complet avec tous les composants:

    from utils.telegram_bot import TelegramNotifier
    from utils.match_monitor import MatchMonitor, create_telegram_callbacks
    from utils.database_manager import DatabaseManager
    
    class CompleteLiveSystem:
        def __init__(self, match_url):
            self.notifier = TelegramNotifier()
            self.db = DatabaseManager()
            self.monitor = MatchMonitor(match_url)
            
            self.monitor.set_callbacks(
                **create_telegram_callbacks(self.notifier)
            )
        
        def run(self):
            # Créer entrée BD
            match = self.db.insert_match({...})
            
            # Lancer surveillance
            self.monitor.monitor()
            
            # Récupérer résultats
            predictions = self.db.get_predictions_for_match(match)
            print(f"Prédictions: {len(predictions)}")
            
            self.db.close()
    
    system = CompleteLiveSystem("http://example.com/match")
    system.run()


🎯 PROCHAINES ÉTAPES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✅ Telegram Bot: COMPLÉTÉ
2. ✅ Surveillance Live: COMPLÉTÉ
3. ✅ Base de Données: COMPLÉTÉ
4. 🔄 Optimisation des poids (E):
   - Analyser accuracy par intervalle
   - Intégrer données: cartons rouges, pénalités
   - Recalculer coefficients d'attaque/défense
   - Valider sur historique

5. Futures améliorations:
   - API REST pour dashboard web
   - Machine Learning pour prédictions
   - Multi-langue pour notifications
   - Support de plusieurs bourses de paris


💡 TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Toujours tester sur quelques matchs avant de déployer
• Vérifier les logs: tail -f logs/telegram_bot.log
• Analyser les stats par intervalle pour optimiser
• Ne parier que si confidence >= "HAUTE"
• Suivre le ROI sur au moins 30 matchs

╚══════════════════════════════════════════════════════════════════════════════╝
""")
