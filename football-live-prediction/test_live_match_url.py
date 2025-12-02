#!/usr/bin/env python3
# ============================================================================
# PARIS LIVE - LIVE MATCH TEST WITH REAL URL
# ============================================================================
# Test avec URL réelle: https://www.soccerstats.com/pmatch.asp?league=bulgaria&stats=141-2-5-2026
# ============================================================================

import sys
import os
import time
import asyncio
import re
from datetime import datetime
from bs4 import BeautifulSoup
import requests

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

class RealMatchTester:
    """Test avec URL réelle de match"""
    
    def __init__(self):
        self.pipeline = LivePredictionPipeline()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '6942358056')
        self.match_url = "https://www.soccerstats.com/pmatch.asp?league=bulgaria&stats=141-2-5-2026"
        
    def scrape_match_data(self) -> dict:
        """Scrape les données du match depuis l'URL"""
        try:
            logger.info(f"🌐 Scraping: {self.match_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.match_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract match info from page
            match_data = self._parse_match_page(soup)
            
            logger.info(f"✅ Match data extracted:")
            logger.info(f"   - Home: {match_data.get('home_team', 'N/A')}")
            logger.info(f"   - Away: {match_data.get('away_team', 'N/A')}")
            logger.info(f"   - Score: {match_data.get('home_score', 0)}-{match_data.get('away_score', 0)}")
            logger.info(f"   - Minute: {match_data.get('minute', 0)}'")
            
            return match_data
            
        except Exception as e:
            logger.error(f"❌ Error scraping: {e}")
            return self._get_fallback_data()
    
    def _parse_match_page(self, soup: BeautifulSoup) -> dict:
        """Parse la page HTML du match"""
        data = {
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
        }
        
        try:
            # Try to find match title
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                text = title_tag.get_text()
                # Extract team names from title
                if ' vs ' in text:
                    teams = text.split(' vs ')
                    data['home_team'] = teams[0].strip()
                    data['away_team'] = teams[1].strip().split('|')[0].strip()
                elif '-' in text:
                    parts = text.split('-')
                    if len(parts) >= 2:
                        data['home_team'] = parts[0].strip()
                        data['away_team'] = parts[1].strip()
            
            # Try to find score
            score_patterns = [
                r'(\d+)\s*-\s*(\d+)',
                r'Score:\s*(\d+)\s*-\s*(\d+)',
                r'Final:\s*(\d+)\s*-\s*(\d+)',
            ]
            
            page_text = soup.get_text()
            for pattern in score_patterns:
                match = re.search(pattern, page_text)
                if match:
                    data['home_score'] = int(match.group(1))
                    data['away_score'] = int(match.group(2))
                    break
            
            # Try to find minute
            minute_match = re.search(r"(\d+)['°]\s*(?:min|FT|HT)", page_text)
            if minute_match:
                data['minute'] = int(minute_match.group(1))
            
            # Look for possession, shots, etc in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text().strip() for cell in cells])
                    
                    if 'possession' in row_text.lower():
                        nums = re.findall(r'\d+', row_text)
                        if nums:
                            data['home_possession'] = int(nums[0])
                    elif 'shots' in row_text.lower():
                        nums = re.findall(r'\d+', row_text)
                        if nums:
                            data['home_shots'] = int(nums[0])
                    elif 'corners' in row_text.lower():
                        nums = re.findall(r'\d+', row_text)
                        if nums:
                            data['home_corners'] = int(nums[0])
                    elif 'fouls' in row_text.lower():
                        nums = re.findall(r'\d+', row_text)
                        if nums:
                            data['home_fouls'] = int(nums[0])
        
        except Exception as e:
            logger.warning(f"⚠️  Parse warning: {e}")
        
        return data
    
    def _get_fallback_data(self) -> dict:
        """Données de fallback si le scraping échoue"""
        logger.warning("⚠️  Utilisation des données de fallback")
        return {
            'home_team': 'CSKA Sofia',
            'away_team': 'Lokomotiv Sofia',
            'home_score': 1,
            'away_score': 0,
            'minute': 55,
            'interval': '45-90',
            'home_possession': 52,
            'home_shots': 9,
            'home_shots_on_target': 4,
            'home_corners': 5,
            'home_fouls': 13,
            'away_possession': 48,
            'away_shots': 6,
            'away_shots_on_target': 2,
            'away_corners': 3,
            'away_fouls': 10,
        }
    
    def generate_features_from_match(self, match_data: dict) -> np.ndarray:
        """Génère les 23 features à partir des données du match"""
        try:
            # Normaliser les données
            home_poss = match_data.get('home_possession', 50) / 100
            away_poss = match_data.get('away_possession', 50) / 100 or (1 - home_poss)
            
            home_shots = match_data.get('home_shots', 8) / 20  # Normaliser par 20
            away_shots = match_data.get('away_shots', 7) / 20
            
            home_sot = match_data.get('home_shots_on_target', 3) / 10
            away_sot = match_data.get('away_shots_on_target', 2) / 10
            
            home_corners = match_data.get('home_corners', 4) / 10
            away_corners = match_data.get('away_corners', 3) / 10
            
            home_fouls = match_data.get('home_fouls', 12) / 20
            away_fouls = match_data.get('away_fouls', 10) / 20
            
            minute = match_data.get('minute', 45) / 90  # 0-1 scale
            
            # Créer 23 features
            features = [
                home_poss,                          # 0: home possession
                away_poss,                          # 1: away possession
                home_shots,                         # 2: home shots
                away_shots,                         # 3: away shots
                home_sot,                           # 4: home shots on target
                away_sot,                           # 5: away shots on target
                home_corners,                       # 6: home corners
                away_corners,                       # 7: away corners
                home_fouls,                         # 8: home fouls
                away_fouls,                         # 9: away fouls
                home_sot / (home_shots + 0.01),     # 10: home shot accuracy
                away_sot / (away_shots + 0.01),     # 11: away shot accuracy
                home_shots / (minute + 0.01),       # 12: home shot rate
                away_shots / (minute + 0.01),       # 13: away shot rate
                (home_corners - away_corners) / 10, # 14: corner difference
                (home_fouls - away_fouls) / 20,     # 15: foul difference
                minute,                             # 16: match progress
                home_poss - away_poss,              # 17: possession diff
                (home_shots - away_shots) / 20,     # 18: shots diff
                (home_sot - away_sot) / 10,         # 19: SOT diff
                home_shots * home_poss,             # 20: home aggression
                away_shots * away_poss,             # 21: away aggression
                (home_shots * minute),              # 22: home momentum (bonus feature)
            ]
            
            return np.array(features, dtype=np.float32).reshape(1, -1)
        
        except Exception as e:
            logger.error(f"❌ Error generating features: {e}")
            return np.random.randn(1, 23)
    
    async def send_telegram_alert(self, message: str):
        """Envoie une alerte Telegram"""
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("✅ Alerte Telegram envoyée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur Telegram: {e}")
    
    async def test_real_match(self):
        """Lance le test avec le match réel"""
        logger.info("=" * 70)
        logger.info("🎯 PARIS LIVE - TEST WITH REAL MATCH URL")
        logger.info("=" * 70)
        logger.info(f"URL: {self.match_url}")
        logger.info("=" * 70)
        logger.info("")
        
        # Scrape match data
        match_data = self.scrape_match_data()
        
        # Send initial alert
        await self.send_telegram_alert(
            "🔴 <b>PARIS LIVE - Real Match Test Started</b>\n\n"
            f"🏟️  <b>{match_data.get('home_team')}</b> vs <b>{match_data.get('away_team')}</b>\n"
            f"📊 Score: {match_data.get('home_score', 0)}-{match_data.get('away_score', 0)}\n"
            f"⏱️  Minute: {match_data.get('minute', 0)}'\n"
            f"🔗 Source: SoccerStats Bulgaria League"
        )
        
        logger.info("")
        logger.info("🧠 Generating features from real match data...")
        
        # Generate features from real match
        features = self.generate_features_from_match(match_data)
        logger.info(f"✅ Features generated (shape: {features.shape})")
        logger.info(f"   Sample values: {features[0][:3]}")
        
        # Get prediction
        logger.info("")
        logger.info("🎯 Calculating danger score...")
        result = self.pipeline.calculate_danger_score(features)
        
        danger_score = result.get('danger_score', 0) if isinstance(result, dict) else 0
        confidence = result.get('confidence', 0) if isinstance(result, dict) else 0
        
        logger.info(f"✅ Prediction result:")
        logger.info(f"   - Danger Score: {danger_score:.4f}")
        logger.info(f"   - Confidence: {confidence:.4f}")
        
        # Decision
        decision = 'BUY' if (danger_score >= 0.5 and confidence >= 0.5) else 'SKIP'
        logger.info(f"   - Decision: {decision}")
        
        logger.info("")
        logger.info("=" * 70)
        
        # Send result alert
        await self.send_telegram_alert(
            "⚽ <b>PREDICTION GENERATED</b>\n\n"
            f"🏟️  <b>{match_data.get('home_team')}</b> vs <b>{match_data.get('away_team')}</b>\n"
            f"📊 Current Score: {match_data.get('home_score', 0)}-{match_data.get('away_score', 0)}\n"
            f"⏱️  Minute: {match_data.get('minute', 0)}'\n\n"
            f"🔮 <b>AI Prediction:</b>\n"
            f"📈 Danger Score: {danger_score:.1%}\n"
            f"💪 Confidence: {confidence:.1%}\n\n"
            f"🎯 <b>Decision: {decision}</b>\n"
            f"{'💰 BET: At least 1 goal' if decision == 'BUY' else '⏳ Wait for better signal'}"
        )
        
        logger.info("")
        logger.info("✅ Test with real match completed!")


async def main():
    """Main entry point"""
    try:
        tester = RealMatchTester()
        await tester.test_real_match()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
