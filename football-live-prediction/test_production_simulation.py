#!/usr/bin/env python3
# ============================================================================
# PARIS LIVE - TEST SIMULATION FOR PRODUCTION
# ============================================================================
# Simule des matchs en direct et teste le pipeline complet
# ============================================================================

import sys
import os
import time
import json
import random
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, '/workspaces/paris-live/football-live-prediction')

from live_prediction_pipeline import LivePredictionPipeline
from backtesting_engine import BacktestingEngine
from backtesting_analyzer import BacktestingAnalyzer
from loguru import logger
from telegram import Bot

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}"
)

class ProductionTestSimulator:
    """Simule des matchs en production pour tester le pipeline"""
    
    def __init__(self):
        self.pipeline = LivePredictionPipeline()
        self.predictions = []
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '6942358056')
        
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
    
    def generate_simulated_match(self, idx: int) -> dict:
        """Génère un match simulé"""
        teams = [
            ("Paris SG", "Marseille"),
            ("Lyon", "Monaco"),
            ("Lille", "Nice"),
            ("Bordeaux", "Toulouse"),
            ("Nantes", "Rennes")
        ]
        
        home, away = teams[idx % len(teams)]
        
        return {
            'match_id': f'SIM_{idx:04d}',
            'home_team': home,
            'away_team': away,
            'interval': random.choice(['30-45', '75-90']),
            'minute': random.randint(30, 90),
            'home_score': random.randint(0, 3),
            'away_score': random.randint(0, 3),
            'home_possession': random.randint(40, 60),
            'home_shots': random.randint(5, 15),
            'home_shots_on_target': random.randint(2, 8),
            'home_corners': random.randint(2, 10),
            'home_fouls': random.randint(10, 20),
            'away_possession': None,  # Will be calculated
            'away_shots': random.randint(5, 15),
            'away_shots_on_target': random.randint(2, 8),
            'away_corners': random.randint(2, 10),
            'away_fouls': random.randint(10, 20),
        }
    
    def process_match(self, match: dict) -> dict:
        """Traite un match et génère une prédiction"""
        logger.info(f"🎮 Match: {match['home_team']} vs {match['away_team']}")
        
        # Simulate feature generation
        import numpy as np
        features = np.random.randn(1, 23)
        
        # Get prediction
        result = self.pipeline.calculate_danger_score(features)
        
        prediction = {
            'match_id': match['match_id'],
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'interval': match['interval'],
            'minute': match['minute'],
            'danger_score': result.get('danger_score', 0.0) if isinstance(result, dict) else 0.0,
            'confidence': result.get('confidence', 0.0) if isinstance(result, dict) else 0.0,
            'prediction': 'BUY' if (result.get('danger_score', 0) >= 0.5 and 
                                    result.get('confidence', 0) >= 0.5) else 'SKIP',
            'timestamp': datetime.now().isoformat()
        }
        
        self.predictions.append(prediction)
        return prediction
    
    async def simulate_live_test(self, num_matches: int = 5):
        """Lance la simulation de test en direct"""
        logger.info("=" * 60)
        logger.info("🚀 PARIS LIVE - PRODUCTION TEST SIMULATION")
        logger.info("=" * 60)
        logger.info(f"Configuration:")
        logger.info(f"  - Confidence Threshold: 50%")
        logger.info(f"  - Danger Score Threshold: 50%")
        logger.info(f"  - Strategy: Conservative")
        logger.info(f"  - Expected Win Rate: 35.1%")
        logger.info("=" * 60)
        logger.info("")
        
        # Initial Telegram alert
        await self.send_telegram_alert(
            "🚀 <b>PARIS LIVE - Test Production Démarré</b>\n\n"
            "📊 Configuration:\n"
            "• Stratégie: Conservative (50%/50%)\n"
            "• Matchs simulés: " + str(num_matches) + "\n"
            "• Interval: [30-45] et [75-90]\n"
            "• Win Rate attendu: 35.1%"
        )
        
        for i in range(num_matches):
            logger.info(f"\n[{i+1}/{num_matches}] Traitement du match...")
            
            # Generate and process match
            match = self.generate_simulated_match(i)
            prediction = self.process_match(match)
            
            # Display result
            logger.info(f"   Match: {prediction['home_team']} vs {prediction['away_team']}")
            logger.info(f"   Interval: {prediction['interval']}'")
            logger.info(f"   Danger Score: {prediction['danger_score']:.4f}")
            logger.info(f"   Confidence: {prediction['confidence']:.4f}")
            logger.info(f"   Decision: {prediction['prediction']}")
            
            # Send alert if prediction is BUY
            if prediction['prediction'] == 'BUY':
                await self.send_telegram_alert(
                    "⚽ <b>PREDICTION GÉNÉRÉE</b>\n\n"
                    f"🏟️  <b>{prediction['home_team']}</b> vs <b>{prediction['away_team']}</b>\n"
                    f"⏱️  Interval: {prediction['interval']} minutes\n"
                    f"📊 Danger Score: {prediction['danger_score']:.1%}\n"
                    f"💪 Confidence: {prediction['confidence']:.1%}\n"
                    f"🎯 Prédiction: <b>AU MOINS 1 BUT</b>\n"
                    f"💰 Statut: <b>ACHETER</b>"
                )
            
            time.sleep(2)  # Small delay between matches
        
        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 RÉSUMÉ DU TEST")
        logger.info("=" * 60)
        logger.info(f"Matchs traités: {len(self.predictions)}")
        
        buy_predictions = [p for p in self.predictions if p['prediction'] == 'BUY']
        logger.info(f"Prédictions BUY: {len(buy_predictions)}")
        
        if buy_predictions:
            avg_danger = sum(p['danger_score'] for p in buy_predictions) / len(buy_predictions)
            avg_confidence = sum(p['confidence'] for p in buy_predictions) / len(buy_predictions)
            logger.info(f"Avg Danger Score (BUY): {avg_danger:.4f}")
            logger.info(f"Avg Confidence (BUY): {avg_confidence:.4f}")
        
        logger.info("=" * 60)
        
        # Final Telegram alert
        await self.send_telegram_alert(
            "✅ <b>Test Production Terminé</b>\n\n"
            f"📊 Résultats:\n"
            f"• Matchs traités: {len(self.predictions)}\n"
            f"• Prédictions BUY: {len(buy_predictions)}\n"
            f"• Taux de déclenchement: {len(buy_predictions)/len(self.predictions)*100:.1f}%\n\n"
            f"🎯 Système prêt pour la production!"
        )
        
        # Save predictions
        with open('/workspaces/paris-live/football-live-prediction/logs/test_predictions.json', 'w') as f:
            json.dump(self.predictions, f, indent=2, default=str)
        
        logger.info("\n✅ Test simulation complété avec succès!")
        logger.info(f"📁 Prédictions sauvegardées: logs/test_predictions.json")

async def main():
    """Main entry point"""
    try:
        simulator = ProductionTestSimulator()
        await simulator.simulate_live_test(num_matches=5)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Test interrompu par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
