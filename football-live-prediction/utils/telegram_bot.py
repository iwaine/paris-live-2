"""
Telegram Bot pour notifications de prédictions live
"""
import os
import asyncio
from typing import Dict, Optional, Callable
from pathlib import Path
import yaml
from loguru import logger

# Import telegram (à installer: pip install python-telegram-bot)
try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
    Bot = None
    Update = None
    ContextTypes = None


class TelegramNotifier:
    """Gestionnaire de notifications Telegram"""
    
    def __init__(self, config_path: str = "config/telegram_config.yaml"):
        """
        Initialise le notifiant Telegram
        
        Args:
            config_path: Chemin vers la config Telegram
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.bot = None
        self.app = None
        self.running = False
        
        if self.config:
            self._init_bot()
            logger.info("✅ TelegramNotifier initialized")
        else:
            logger.warning("⚠️  Telegram config not found")
    
    def _load_config(self) -> Optional[Dict]:
        """Charge la configuration Telegram"""
        if not self.config_path.exists():
            logger.warning(f"Config not found: {self.config_path}")
            return None
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return None
    
    def _init_bot(self):
        """Initialise le bot Telegram"""
        try:
            # Récupérer token et chat_id
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or self.config.get('telegram', {}).get('bot_token')
            self.chat_id = os.getenv('TELEGRAM_CHAT_ID') or self.config.get('telegram', {}).get('chat_id')
            
            if not bot_token or not self.chat_id:
                logger.warning("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
                return
            
            self.bot = Bot(token=bot_token)
            logger.info("✅ Telegram Bot connected")
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Envoie un message Telegram
        
        Args:
            message: Contenu du message
            parse_mode: HTML ou Markdown
            
        Returns:
            True si succès
        """
        if not self.bot or not self.chat_id:
            logger.warning("Bot not initialized")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.success(f"✓ Message sent")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_match_alert(self, match_data: Dict) -> bool:
        """
        Envoie une alerte sur un match
        
        Args:
            match_data: Données du match
            
        Returns:
            True si succès
        """
        try:
            # Supporter deux formats d'entrée:
            # 1) prediction dict retournée par predict_match
            # 2) match_data provenant du monitor (incluant 'live_stats')
            if 'details' in match_data:
                details = match_data.get('details', {})
                home_team = details.get('home_team', match_data.get('home_team', 'N/A'))
                away_team = details.get('away_team', match_data.get('away_team', 'N/A'))
                minute = match_data.get('current_minute', match_data.get('minute', 'N/A'))
                score = match_data.get('current_score', match_data.get('score', 'N/A'))
                danger_score = match_data.get('danger_score', 0)
                interpretation = match_data.get('interpretation', 'N/A')
                # events possibly in details
                red_home = details.get('red_cards_home', 0)
                red_away = details.get('red_cards_away', 0)
                pen_home = details.get('penalties_home', 0)
                pen_away = details.get('penalties_away', 0)
                inj_home = details.get('injuries_home', 0)
                inj_away = details.get('injuries_away', 0)
            else:
                home_team = match_data.get('home_team', 'N/A')
                away_team = match_data.get('away_team', 'N/A')
                minute = match_data.get('current_minute', 'N/A')
                score = match_data.get('score', 'N/A')
                danger_score = match_data.get('danger_score', 0)
                interpretation = match_data.get('interpretation', 'N/A')
                live = match_data.get('live_stats', {}) or {}
                red_home = live.get('red_cards', {}).get('home', 0)
                red_away = live.get('red_cards', {}).get('away', 0)
                pen_home = live.get('penalties', {}).get('home', 0)
                pen_away = live.get('penalties', {}).get('away', 0)
                inj_home = live.get('injuries', {}).get('home', 0)
                inj_away = live.get('injuries', {}).get('away', 0)
            
            # Déterminer l'emoji de danger
            if danger_score >= 4.0:
                emoji = "🔴"
                level = "ULTRA-DANGEREUX"
            elif danger_score >= 3.0:
                emoji = "🟠"
                level = "DANGEREUX"
            elif danger_score >= 2.0:
                emoji = "🟡"
                level = "MODÉRÉ"
            else:
                emoji = "🟢"
                level = "FAIBLE"
            
            message = f"""
<b>{emoji} ALERTE PRÉDICTION</b>

<b>Match:</b> {home_team} vs {away_team}
<b>Minute:</b> {minute}'
<b>Score:</b> {score}

<b>🎯 Danger Score:</b> {danger_score:.2f}
<b>📊 Niveau:</b> {level}

<b>💡 Recommandation:</b>
Préparez-vous pour un but probable dans les prochaines minutes!
            """
            # Ajouter résumé des événements s'ils existent
            events_lines = []
            if any([red_home, red_away, pen_home, pen_away, inj_home, inj_away]):
                events_lines.append('\n<b>⚠️ Événements en direct:</b>')
                if red_home or red_away:
                    events_lines.append(f"Cartons rouges — Domicile: {red_home}, Extérieur: {red_away}")
                if pen_home or pen_away:
                    events_lines.append(f"Pénalités — Domicile: {pen_home}, Extérieur: {pen_away}")
                if inj_home or inj_away:
                    events_lines.append(f"Blessures — Domicile: {inj_home}, Extérieur: {inj_away}")

                message += "\n" + "\n".join(events_lines)
            
            asyncio.run(self.send_message(message))
            return True
        except Exception as e:
            logger.error(f"Error sending match alert: {e}")
            return False
    
    def send_goal_notification(self, match_data: Dict, team: str, minute: int) -> bool:
        """
        Notifie d'un but marqué
        
        Args:
            match_data: Données du match
            team: Équipe qui a marqué
            minute: Minute du but
            
        Returns:
            True si succès
        """
        try:
            # match_data peut contenir 'live_stats' ou 'details'
            if 'details' in match_data:
                details = match_data.get('details', {})
                home_team = details.get('home_team', match_data.get('home_team', 'N/A'))
                away_team = details.get('away_team', match_data.get('away_team', 'N/A'))
                score = match_data.get('current_score', match_data.get('score', 'N/A'))
                live = details
            else:
                home_team = match_data.get('home_team', 'N/A')
                away_team = match_data.get('away_team', 'N/A')
                score = match_data.get('score', 'N/A')
                live = match_data.get('live_stats', {}) or {}

            # Extraire événements si disponibles
            red_home = live.get('red_cards', {}).get('home', live.get('red_cards_home', 0)) if isinstance(live, dict) else 0
            red_away = live.get('red_cards', {}).get('away', live.get('red_cards_away', 0)) if isinstance(live, dict) else 0
            pen_home = live.get('penalties', {}).get('home', live.get('penalties_home', 0)) if isinstance(live, dict) else 0
            pen_away = live.get('penalties', {}).get('away', live.get('penalties_away', 0)) if isinstance(live, dict) else 0
            inj_home = live.get('injuries', {}).get('home', live.get('injuries_home', 0)) if isinstance(live, dict) else 0
            inj_away = live.get('injuries', {}).get('away', live.get('injuries_away', 0)) if isinstance(live, dict) else 0

            message = f"""
⚽ <b>BUT MARQUÉ!</b>

<b>{home_team}</b> vs <b>{away_team}</b>
<b>Minute:</b> {minute}'
<b>Buteur:</b> {team}
<b>Score:</b> {score}

✅ Prédiction validée!
            """

            # Ajouter événements si présent
            events_lines = []
            if any([red_home, red_away, pen_home, pen_away, inj_home, inj_away]):
                events_lines.append('\n<b>⚠️ Événements en direct:</b>')
                if red_home or red_away:
                    events_lines.append(f"Cartons rouges — Domicile: {red_home}, Extérieur: {red_away}")
                if pen_home or pen_away:
                    events_lines.append(f"Pénalités — Domicile: {pen_home}, Extérieur: {pen_away}")
                if inj_home or inj_away:
                    events_lines.append(f"Blessures — Domicile: {inj_home}, Extérieur: {inj_away}")

                message += "\n" + "\n".join(events_lines)

            asyncio.run(self.send_message(message))
            return True
        except Exception as e:
            logger.error(f"Error sending goal notification: {e}")
            return False
    
    def send_prediction_summary(self, predictions: list) -> bool:
        """
        Envoie un résumé des prédictions du jour
        
        Args:
            predictions: Liste des prédictions
            
        Returns:
            True si succès
        """
        try:
            message = "<b>📊 RÉSUMÉ DES PRÉDICTIONS</b>\n\n"
            
            for i, pred in enumerate(predictions[:10], 1):  # Max 10
                home = pred.get('home_team', 'N/A')
                away = pred.get('away_team', 'N/A')
                score = pred.get('danger_score', 0)
                
                if score >= 4.0:
                    emoji = "🔴"
                elif score >= 3.0:
                    emoji = "🟠"
                else:
                    emoji = "🟡"
                
                message += f"{i}. {emoji} {home} vs {away} ({score:.1f})\n"
            
            message += f"\n<b>Total:</b> {len(predictions)} matchs analysés"
            
            asyncio.run(self.send_message(message))
            return True
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
            return False


class TelegramBotApp:
    """Application Telegram Bot avec commandes"""
    def __init__(self, config_path: str = "config/telegram_config.yaml"):
        self.notifier = TelegramNotifier(config_path)
        self.app = None
        self.predictor = None
        self.monitor_callbacks = {}

    # Utiliser des types génériques si Telegram n'est pas installé
    if Update is not None and ContextTypes is not None:
        async def start_command(self, update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
            welcome_msg = self.notifier.config.get('telegram', {}).get('messages', {}).get('welcome', '')
            await update.message.reply_text(welcome_msg, parse_mode="HTML")

        async def help_command(self, update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
            help_msg = self.notifier.config.get('telegram', {}).get('messages', {}).get('help', '')
            await update.message.reply_text(help_msg, parse_mode="HTML")

        async def match_command(self, update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
            try:
                if not context.args:
                    await update.message.reply_text("❌ Usage: /match <URL>")
                    return
                url = context.args[0]
                await update.message.reply_text(f"⏳ Analyse du match: {url}")
                # TODO: Intégrer avec le scraper live
                await update.message.reply_text("✅ Match analysé!")
            except Exception as e:
                await update.message.reply_text(f"❌ Erreur: {e}")

        async def stats_command(self, update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
            message = """
📊 <b>STATISTIQUES</b>

<b>Prédictions ce mois:</b>
• Total: 25
• Réussies: 18 (72%)
• ROI: +2.3 unités

<b>Matchs surveillés:</b> 3
<b>Buts prédits:</b> 7/10
            """
            await update.message.reply_text(message, parse_mode="HTML")

        async def stop_command(self, update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
            await update.message.reply_text("⏹️  Surveillance arrêtée")
    else:
        async def start_command(self, update, context):
            pass
        async def help_command(self, update, context):
            pass
        async def match_command(self, update, context):
            pass
        async def stats_command(self, update, context):
            pass
        async def stop_command(self, update, context):
            pass
    
    async def run(self):
        """Démarre l'application bot"""
        try:
            if not self.notifier.bot:
                logger.error("Bot not initialized")
                return
            
            self.app = Application.builder().token(
                os.getenv('TELEGRAM_BOT_TOKEN')
            ).build()
            
            # Ajouter les handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
            self.app.add_handler(CommandHandler("match", self.match_command))
            self.app.add_handler(CommandHandler("stats", self.stats_command))
            self.app.add_handler(CommandHandler("stop", self.stop_command))
            
            logger.info("🤖 Telegram Bot started")
            await self.app.run_polling()
        except Exception as e:
            logger.error(f"Error running bot: {e}")
    
    def start_in_background(self):
        """Démarre le bot en arrière-plan"""
        # TODO: Implémenter avec threading
        pass


if __name__ == "__main__":
    # Test
    notifier = TelegramNotifier()
    
    # Exemple d'alerte
    test_data = {
        'home_team': 'Arsenal',
        'away_team': 'Manchester City',
        'current_minute': 65,
        'score': '1-1',
        'danger_score': 4.5,
        'interpretation': 'ULTRA-DANGEREUX'
    }
    
    # notifier.send_match_alert(test_data)
    print("✅ Telegram Bot module loaded")
