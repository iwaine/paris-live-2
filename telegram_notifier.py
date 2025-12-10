"""
Module d'envoi de notifications Telegram
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Gestionnaire de notifications Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_alerts = {}  # match_url -> timestamp
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Envoyer un message Telegram.
        
        Args:
            message: Texte du message
            parse_mode: Format (HTML ou Markdown)
            
        Returns:
            True si envoi réussi, False sinon
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Message Telegram envoyé avec succès")
                return True
            else:
                logger.error(f"❌ Erreur Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception lors de l'envoi Telegram: {e}")
            return False
    
    def format_alert_message(self, analysis: Dict, championship: str = "Bulgarie") -> str:
        """
        Formater le message d'alerte.
        
        Args:
            analysis: Dictionnaire avec context, predictions, match_data
            championship: Nom du championnat
            
        Returns:
            Message formaté en HTML
        """
        context = analysis['context']
        predictions = analysis['predictions']
        
        # Récupérer les prédictions
        home_pred = predictions.get('home_active')
        away_pred = predictions.get('away_active')
        combined = predictions.get('combined_active')
        
        if not home_pred or not away_pred or not combined:
            return None
        
        # Émoji selon le championnat
        flag = "🇧🇬" if championship.lower() == "bulgarie" else "🇳🇱"
        
        # Déterminer le signal
        combined_prob = combined['probability']
        if combined_prob >= 0.90:
            signal = "🟢 SIGNAL TRÈS FORT"
            recommendation = "Pari fortement recommandé"
        elif combined_prob >= 0.75:
            signal = "🟡 SIGNAL FORT"
            recommendation = "Pari modéré possible"
        else:
            signal = "⚪ SIGNAL MOYEN"
            recommendation = "Prudence recommandée"
        
        # Construire le message
        message = f"""
🚨 <b>ALERTE {championship.upper()}</b> {flag}

<b>{context.home_team} vs {context.away_team}</b>
⏱️ Minute <b>{context.current_minute}</b> | Score: <b>{context.home_score}-{context.away_score}</b>

⚡ <b>INTERVALLE {home_pred.interval_name} ACTIF</b>

📊 <b>PROBABILITÉS:</b>
  🏡 {context.home_team}: <b>{home_pred.probability*100:.1f}%</b>
     • Confiance: {home_pred.confidence_level}
     • Historique: {home_pred.matches_with_goal}/{home_pred.total_matches} matches
"""
        
        if home_pred.recurrence_last_5:
            message += f"     • Récurrence: {home_pred.recurrence_last_5*100:.0f}%\n"
        
        message += f"""
  ✈️ {context.away_team}: <b>{away_pred.probability*100:.1f}%</b>
     • Confiance: {away_pred.confidence_level}
     • Historique: {away_pred.matches_with_goal}/{away_pred.total_matches} matches
"""
        
        if away_pred.recurrence_last_5:
            message += f"     • Récurrence: {away_pred.recurrence_last_5*100:.0f}%\n"
        
        message += f"""
  🎯 <b>COMBINÉ: {combined_prob*100:.1f}%</b>

{signal}
💡 {recommendation}

🔗 <a href="{analysis.get('url', '#')}">Voir le match live</a>
"""
        
        return message
    
    def should_send_alert(self, match_url: str, min_interval_minutes: int = 5) -> bool:
        """
        Vérifier si on peut envoyer une alerte (éviter spam).
        
        Args:
            match_url: URL du match
            min_interval_minutes: Intervalle minimum entre alertes
            
        Returns:
            True si on peut envoyer, False sinon
        """
        now = datetime.now()
        
        if match_url in self.last_alerts:
            last_alert = self.last_alerts[match_url]
            elapsed = (now - last_alert).total_seconds() / 60
            
            if elapsed < min_interval_minutes:
                logger.info(f"⏸️ Alerte trop récente pour {match_url} ({elapsed:.1f}min)")
                return False
        
        self.last_alerts[match_url] = now
        return True
    
    def send_alert(self, analysis: Dict, championship: str = "Bulgarie", 
                   min_interval_minutes: int = 5) -> bool:
        """
        Envoyer une alerte complète.
        
        Args:
            analysis: Analyse du match
            championship: Nom du championnat
            min_interval_minutes: Intervalle minimum entre alertes
            
        Returns:
            True si envoyé, False sinon
        """
        match_url = analysis.get('url', 'unknown')
        
        # Vérifier si on peut envoyer
        if not self.should_send_alert(match_url, min_interval_minutes):
            return False
        
        # Formater le message
        message = self.format_alert_message(analysis, championship)
        
        if not message:
            logger.warning("⚠️ Impossible de formater le message")
            return False
        
        # Envoyer
        return self.send_message(message)
    
    def send_test_message(self) -> bool:
        """Envoyer un message de test."""
        test_message = """
🧪 <b>TEST ALERTE TELEGRAM</b>

✅ Configuration réussie !
✅ Bot opérationnel

Vous recevrez désormais des alertes quand :
• Intervalle critique actif (31-45 ou 75-90)
• Probabilité combinée ≥ 80%

🚀 Système prêt !
"""
        return self.send_message(test_message)


def test_telegram_connection():
    """Tester la connexion Telegram."""
    try:
        from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
        print("📡 Test de connexion Telegram...")
        success = notifier.send_test_message()
        
        if success:
            print("✅ Test réussi ! Vérifiez votre Telegram.")
        else:
            print("❌ Test échoué. Vérifiez votre configuration.")
        
        return success
        
    except ImportError:
        print("❌ Fichier telegram_config.py introuvable")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    test_telegram_connection()
