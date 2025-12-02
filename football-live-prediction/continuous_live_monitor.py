#!/usr/bin/env python3
# ============================================================================
# PARIS LIVE - CONTINUOUS LIVE MONITORING
# ============================================================================
# Scrape tous les matchs en direct et génère des prédictions chaque 45 secondes
# ============================================================================

import sys
import os
import time
import asyncio
import re
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from collections import defaultdict

sys.path.insert(0, '/workspaces/paris-live/football-live-prediction')

from live_prediction_pipeline import LivePredictionPipeline
from loguru import logger
from telegram import Bot
import numpy as np

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}"
)

class ContinuousLiveMonitor:
    """Monitoring continu avec scraping multi-matchs"""
    
    def __init__(self):
        self.pipeline = LivePredictionPipeline()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '6942358056')
        self.update_interval = int(os.getenv('UPDATE_INTERVAL', '45'))
        self.confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.50'))
        self.danger_threshold = float(os.getenv('DANGER_SCORE_THRESHOLD', '0.50'))
        
        # Charger les URLs depuis la config
        self.match_urls = self._load_match_urls()
        
        self.match_cache = {}  # Cache pour éviter les doublons
        self.predictions_count = 0
        self.buy_signals_count = 0
    
    def _load_match_urls(self) -> list:
        """Charge les URLs depuis le fichier config"""
        import json
        urls_file = '/workspaces/paris-live/football-live-prediction/config/match_urls.json'
        try:
            if os.path.exists(urls_file):
                with open(urls_file, 'r') as f:
                    data = json.load(f)
                    return [item['url'] for item in data.get('urls', [])]
        except Exception as e:
            logger.warning(f"⚠️  Erreur chargement URLs: {e}")
        
        # URLs par défaut
        return [
            "https://www.soccerstats.com/pmatch.asp?league=bulgaria&stats=141-2-5-2026",
        ]
    
    def discover_live_matches(self) -> list:
        """Découvre les matchs en direct depuis les URLs"""
        matches = []
        
        logger.info("🔍 Découverte des matchs en direct...")
        
        for url in self.match_urls:
            try:
                match_data = self._scrape_match_url(url)
                if match_data:
                    matches.append(match_data)
                    logger.info(f"✅ Match trouvé: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            except Exception as e:
                logger.warning(f"⚠️  Erreur scraping {url}: {e}")
        
        logger.info(f"📊 Total matchs découverts: {len(matches)}")
        return matches
    
    def _scrape_match_url(self, url: str) -> dict:
        """Scrape une URL de match"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_match_page(soup, url)
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            return None
    
    def _parse_match_page(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse la page HTML du match"""
        data = {
            'url': url,
            'home_team': 'Unknown Home',
            'away_team': 'Unknown Away',
            'home_score': 0,
            'away_score': 0,
            'minute': 45,
            'home_possession': 50,
            'home_shots': 8,
            'home_shots_on_target': 3,
            'home_corners': 4,
            'home_fouls': 12,
            'away_possession': 50,
            'away_shots': 7,
            'away_shots_on_target': 2,
            'away_corners': 3,
            'away_fouls': 11,
            'timestamp': datetime.now().isoformat(),
        }
        
        try:
            # Trouver le titre et les infos du match
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                text = title_tag.get_text()
                if ' vs ' in text:
                    teams = text.split(' vs ')
                    data['home_team'] = teams[0].strip()
                    data['away_team'] = teams[1].strip().split('|')[0].strip()
            
            # Extraire le score
            page_text = soup.get_text()
            score_patterns = [
                r'(\d+)\s*-\s*(\d+)',
                r'Score:\s*(\d+)\s*-\s*(\d+)',
            ]
            
            for pattern in score_patterns:
                match = re.search(pattern, page_text)
                if match:
                    data['home_score'] = int(match.group(1))
                    data['away_score'] = int(match.group(2))
                    break
            
            # Extraire la minute
            minute_match = re.search(r"(\d+)['°]\s*(?:min|FT|HT)", page_text)
            if minute_match:
                data['minute'] = int(minute_match.group(1))
        
        except Exception as e:
            logger.warning(f"⚠️  Parse warning: {e}")
        
        return data
    
    def generate_features_from_match(self, match_data: dict) -> np.ndarray:
        """Génère les 23 features à partir du match"""
        try:
            home_poss = match_data.get('home_possession', 50) / 100
            away_poss = match_data.get('away_possession', 50) / 100 or (1 - home_poss)
            
            home_shots = match_data.get('home_shots', 8) / 20
            away_shots = match_data.get('away_shots', 7) / 20
            
            home_sot = match_data.get('home_shots_on_target', 3) / 10
            away_sot = match_data.get('away_shots_on_target', 2) / 10
            
            home_corners = match_data.get('home_corners', 4) / 10
            away_corners = match_data.get('away_corners', 3) / 10
            
            home_fouls = match_data.get('home_fouls', 12) / 20
            away_fouls = match_data.get('away_fouls', 10) / 20
            
            minute = match_data.get('minute', 45) / 90
            
            features = [
                home_poss, away_poss, home_shots, away_shots,
                home_sot, away_sot, home_corners, away_corners,
                home_fouls, away_fouls,
                home_sot / (home_shots + 0.01),
                away_sot / (away_shots + 0.01),
                home_shots / (minute + 0.01),
                away_shots / (minute + 0.01),
                (home_corners - away_corners) / 10,
                (home_fouls - away_fouls) / 20,
                minute,
                home_poss - away_poss,
                (home_shots - away_shots) / 20,
                (home_sot - away_sot) / 10,
                home_shots * home_poss,
                away_shots * away_poss,
                (home_shots * minute),
            ]
            
            return np.array(features, dtype=np.float32).reshape(1, -1)
        
        except Exception as e:
            logger.error(f"❌ Feature generation error: {e}")
            return np.random.randn(1, 23)
    
    def process_match(self, match_data: dict) -> dict:
        """Traite un match et génère une prédiction"""
        # Vérifier si le match est dans les bons intervals
        minute = match_data.get('minute', 0)
        in_target_interval = (30 <= minute <= 45) or (75 <= minute <= 90)
        
        if not in_target_interval:
            return {
                'match_id': f"{match_data['home_team']}_vs_{match_data['away_team']}",
                'status': 'SKIP_INTERVAL',
                'reason': f"Minute {minute} not in [30-45] or [75-90]"
            }
        
        # Générer les features
        features = self.generate_features_from_match(match_data)
        
        # Obtenir la prédiction
        result = self.pipeline.calculate_danger_score(features)
        
        danger_score = result.get('danger_score', 0) if isinstance(result, dict) else 0
        confidence = result.get('confidence', 0) if isinstance(result, dict) else 0
        
        # Décision
        decision = 'BUY' if (
            danger_score >= self.danger_threshold and 
            confidence >= self.confidence_threshold
        ) else 'SKIP'
        
        prediction = {
            'match_id': f"{match_data['home_team']}_vs_{match_data['away_team']}",
            'home_team': match_data['home_team'],
            'away_team': match_data['away_team'],
            'score': f"{match_data['home_score']}-{match_data['away_score']}",
            'minute': minute,
            'danger_score': danger_score,
            'confidence': confidence,
            'decision': decision,
            'timestamp': datetime.now().isoformat(),
        }
        
        return prediction
    
    async def send_telegram_alert(self, message: str, silent: bool = False):
        """Envoie une alerte Telegram"""
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            if not silent:
                logger.info("✅ Alerte Telegram envoyée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur Telegram: {e}")
    
    async def send_buy_signal(self, prediction: dict):
        """Envoie une alerte pour un signal BUY"""
        message = (
            "🎯 <b>SIGNAL D'ACHAT DÉTECTÉ</b>\n\n"
            f"🏟️  <b>{prediction['home_team']}</b> vs <b>{prediction['away_team']}</b>\n"
            f"📊 Score: {prediction['score']}\n"
            f"⏱️  Minute: {prediction['minute']}'\n\n"
            f"🔮 <b>Prédiction AI:</b>\n"
            f"📈 Danger Score: {prediction['danger_score']:.1%}\n"
            f"💪 Confiance: {prediction['confidence']:.1%}\n\n"
            f"💰 <b>ACTION: ACHETER - Au moins 1 but attendu</b>"
        )
        
        await self.send_telegram_alert(message)
        self.buy_signals_count += 1
    
    async def run_continuous_monitoring(self, duration_minutes: int = None):
        """Lance le monitoring continu"""
        logger.info("=" * 80)
        logger.info("🚀 PARIS LIVE - CONTINUOUS LIVE MONITORING")
        logger.info("=" * 80)
        logger.info(f"Configuration:")
        logger.info(f"  - Update Interval: {self.update_interval}s")
        logger.info(f"  - Confidence Threshold: {self.confidence_threshold * 100:.0f}%")
        logger.info(f"  - Danger Threshold: {self.danger_threshold * 100:.0f}%")
        logger.info(f"  - Intervals: [30-45] and [75-90] minutes")
        logger.info("=" * 80)
        logger.info("")
        
        # Send startup alert
        await self.send_telegram_alert(
            "🚀 <b>PARIS LIVE - Monitoring Démarré</b>\n\n"
            "📊 Configuration:\n"
            f"• Mise à jour: {self.update_interval}s\n"
            f"• Confiance min: {self.confidence_threshold * 100:.0f}%\n"
            f"• Danger min: {self.danger_threshold * 100:.0f}%\n"
            f"• Intervals: [30-45] et [75-90] min\n\n"
            "⏳ En attente des matchs en direct..."
        )
        
        start_time = datetime.now()
        cycle = 0
        
        try:
            while True:
                cycle += 1
                logger.info(f"\n[Cycle {cycle}] {datetime.now().strftime('%H:%M:%S')}")
                
                # Découvrir les matchs
                matches = self.discover_live_matches()
                
                if not matches:
                    logger.warning("⚠️  Aucun match en direct trouvé")
                else:
                    # Traiter chaque match
                    for match in matches:
                        try:
                            prediction = self.process_match(match)
                            
                            if prediction.get('status') == 'SKIP_INTERVAL':
                                logger.info(
                                    f"⏭️  {match['home_team']} vs {match['away_team']} "
                                    f"({prediction.get('reason')})"
                                )
                            else:
                                self.predictions_count += 1
                                
                                logger.info(
                                    f"🎯 {match['home_team']} vs {match['away_team']} "
                                    f"({match['minute']}') → "
                                    f"D:{prediction['danger_score']:.2f} "
                                    f"C:{prediction['confidence']:.2f} "
                                    f"→ {prediction['decision']}"
                                )
                                
                                if prediction['decision'] == 'BUY':
                                    await self.send_buy_signal(prediction)
                        
                        except Exception as e:
                            logger.error(f"❌ Erreur traitement match: {e}")
                
                # Vérifier la durée
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        logger.info(f"\n⏱️  Durée prévue ({duration_minutes}m) atteinte")
                        break
                
                # Attendre avant la prochaine mise à jour
                logger.info(f"⏳ Prochaine mise à jour dans {self.update_interval}s...")
                await asyncio.sleep(self.update_interval)
        
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Monitoring arrêté par l'utilisateur")
        
        finally:
            # Send summary
            logger.info("")
            logger.info("=" * 80)
            logger.info("📊 RÉSUMÉ DU MONITORING")
            logger.info("=" * 80)
            logger.info(f"Cycles: {cycle}")
            logger.info(f"Prédictions: {self.predictions_count}")
            logger.info(f"Signaux d'achat: {self.buy_signals_count}")
            logger.info("=" * 80)
            
            await self.send_telegram_alert(
                "✅ <b>Monitoring Arrêté</b>\n\n"
                f"📊 Résumé:\n"
                f"• Cycles: {cycle}\n"
                f"• Prédictions: {self.predictions_count}\n"
                f"• Signaux d'achat: {self.buy_signals_count}\n\n"
                "🔄 À bientôt!"
            )


async def main():
    """Main entry point"""
    try:
        monitor = ContinuousLiveMonitor()
        
        # Durée du monitoring (en minutes) - mettre à None pour infini
        duration = 30  # 30 minutes de test
        
        await monitor.run_continuous_monitoring(duration_minutes=duration)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Application arrêtée")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
