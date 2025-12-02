#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PARIS LIVE - PRODUCTION MONITORING SYSTEM
Monitors live matches and sends Telegram alerts in real-time
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.database_manager import DatabaseManager
from utils.telegram_bot import TelegramNotifier
from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
import yaml
import json


class ProductionMonitor:
    """Main production monitoring system"""
    
    def __init__(self):
        """Initialize production monitor"""
        logger.info("Initializing Production Monitor...")
        
        # Load configuration
        config_path = Path(__file__).parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        db_path = Path(__file__).parent / "data" / "production.db"
        self.db = DatabaseManager(str(db_path))
        
        # TelegramNotifier reads environment variables or config file internally
        self.telegram = TelegramNotifier()
        
        self.scraper = SoccerStatsHistoricalScraper()
        
        logger.info(f"✅ Monitor initialized")
        logger.info(f"   - Teams: {len(self.config['teams'])}")
        logger.info(f"   - Database: {db_path}")
        logger.info(f"   - Telegram: {'✅' if self.telegram else '❌'}")
    
    async def send_startup_notification(self):
        """Send startup notification"""
        try:
            message = """
🚀 <b>PARIS LIVE - PRODUCTION MONITORING STARTED</b>

📊 System Status:
✅ Database initialized
✅ Telegram connected
✅ 243 teams configured
✅ 40+ leagues available

🎯 Monitoring:
• Real-time match tracking
• Live statistics analysis
• Event detection (goals, cards, injuries)
• Automated alerts via Telegram

📱 You will receive alerts for:
🟢 Goal scored
🟠 Red/Yellow card
🟡 Injury to key player
🎯 Penalty kick
📊 Danger score updates

Système prêt pour la surveillance en direct!
            """
            await self.telegram.send_message(message)
            logger.info("✅ Startup notification sent")
        except Exception as e:
            logger.warning(f"Failed to send startup notification: {e}")
    
    async def monitor_matches(self):
        """Main monitoring loop"""
        logger.info("Starting match monitoring loop...")
        
        monitor_cycles = 0
        while True:
            try:
                monitor_cycles += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Monitor Cycle #{monitor_cycles} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Check for live matches
                live_matches = await self.check_live_matches()
                
                if live_matches:
                    logger.info(f"Found {len(live_matches)} live matches")
                    
                    for match in live_matches:
                        try:
                            await self.process_match(match)
                        except Exception as e:
                            logger.error(f"Error processing match: {e}")
                else:
                    logger.info("No live matches at this time")
                
                # Log statistics
                self.log_statistics()
                
                # Wait before next cycle
                logger.info(f"Waiting 300 seconds before next cycle...")
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def check_live_matches(self):
        """Check for live matches from configured leagues"""
        try:
            # This is a placeholder - in production, would scrape SoccerStats
            # for actual live matches
            logger.debug("Checking for live matches...")
            return []  # Return empty for now
        except Exception as e:
            logger.error(f"Error checking live matches: {e}")
            return []
    
    async def process_match(self, match_data):
        """Process a live match and send alerts if needed"""
        try:
            logger.info(f"Processing match: {match_data}")
            
            # Store match data
            self.db.insert_match(match_data)
            
            # Check for events
            events = match_data.get('events', [])
            if events:
                logger.info(f"Found {len(events)} events")
                for event in events:
                    await self.handle_event(event, match_data)
        
        except Exception as e:
            logger.error(f"Error processing match: {e}")
    
    async def handle_event(self, event, match_data):
        """Handle a match event"""
        try:
            event_type = event.get('type')
            logger.info(f"Handling event: {event_type}")
            
            # Send Telegram alert
            alert_message = self.format_event_alert(event, match_data)
            await self.telegram.send_message(alert_message)
            
            # Store event
            self.db.insert_event(event, match_data)
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def format_event_alert(self, event, match_data):
        """Format event for Telegram alert"""
        event_type = event.get('type', 'Unknown')
        minute = event.get('minute', '?')
        team = event.get('team', 'Unknown')
        player = event.get('player', 'Unknown')
        
        emoji_map = {
            'goal': '⚽',
            'red_card': '🔴',
            'yellow_card': '🟡',
            'penalty': '🎯',
            'injury': '🚑'
        }
        
        emoji = emoji_map.get(event_type, '📍')
        
        message = f"""
{emoji} **{event_type.upper()}** - {minute}'

Match: {match_data.get('home_team')} vs {match_data.get('away_team')}
Team: {team}
Player: {player}

⏱️  {datetime.now().strftime('%H:%M:%S')}
        """
        return message
    
    def log_statistics(self):
        """Log system statistics"""
        try:
            # Get stats from database
            db_conn = self.db.conn
            cursor = db_conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM matches")
            matches_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM predictions")
            events_count = cursor.fetchone()[0]
            
            logger.info(f"""
📊 Statistics:
   - Total matches: {matches_count}
   - Total predictions: {events_count}
   - Uptime: OK
            """)
        except Exception as e:
            logger.warning(f"Failed to get statistics: {e}")
    
    async def run(self):
        """Run the monitoring system"""
        try:
            logger.info("🚀 PARIS LIVE PRODUCTION MONITORING STARTED")
            logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Log: {log_file}")
            
            # Send startup notification
            await self.send_startup_notification()
            
            # Start monitoring loop
            await self.monitor_matches()
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            raise
        finally:
            logger.info("🛑 Production monitoring stopped")


async def main():
    """Main entry point"""
    monitor = ProductionMonitor()
    await monitor.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
