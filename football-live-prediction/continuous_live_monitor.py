#!/usr/bin/env python3
"""
🎯 CONTINUOUS LIVE MATCH MONITOR
Integrates RecurrencePredictor for real-time betting signals

Phase 5: Live Monitoring with Recurrence-Based Predictions
- Scrapes live match data every N seconds
- Makes predictions using RecurrencePredictor (minute-exact analysis)
- Alerts when danger_score >= 65% (high confidence betting signal)
- Supports multiple simultaneous matches
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

sys.path.insert(0, 'scrapers')
sys.path.insert(0, 'predictors')

from soccerstats_live import SoccerStatsLiveScraper
from recurrence_predictor import RecurrencePredictor
from loguru import logger


@dataclass
class BettingSignal:
    """Betting signal output"""
    match_id: str
    home_team: str
    away_team: str
    minute: int
    current_score: str
    danger_score: float
    danger_level: str  # "HIGH", "MODERATE", "LOW"
    should_bet: bool
    prediction_data: Dict
    timestamp: datetime
    signal_reason: str

    def display(self) -> str:
        """Pretty print the signal"""
        emoji = "🎯" if self.should_bet else "⚠️ "
        bet_indicator = "PARIER" if self.should_bet else "CONSIDÉRER"
        return f"{emoji} {bet_indicator} | {self.home_team} vs {self.away_team} @ min {self.minute} | Danger: {self.danger_score:.1f}% | Score: {self.current_score}"


class ContinuousLiveMonitor:
    """Continuous live match monitoring with recurrence-based predictions"""

    def __init__(self, telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
        """
        Initialize the monitor

        Args:
            telegram_token: Telegram bot token for alerts
            telegram_chat_id: Telegram chat ID for alerts
        """
        self.scraper = SoccerStatsLiveScraper()
        self.predictor = RecurrencePredictor()
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id

        # Monitoring state
        self.active_matches: Dict[str, Dict] = {}
        self.signals_history: List[BettingSignal] = []
        self.high_danger_signals: List[BettingSignal] = []

        # Configuration
        self.DANGER_THRESHOLD_HIGH = 65  # Alert when >= 65%
        self.DANGER_THRESHOLD_MODERATE = 50
        self.POLLING_INTERVAL = 30  # seconds
        self.MATCH_TIMEOUT = 3600  # Stop monitoring after 1 hour of no updates

        logger.info("ContinuousLiveMonitor initialized")

    def add_match(self, match_url: str, match_id: str) -> bool:
        """Add a match to monitoring"""
        try:
            match_data = self.scraper.scrape_live_match(match_url)
            if not match_data:
                logger.error(f"Failed to scrape match: {match_id}")
                return False

            self.active_matches[match_id] = {
                'url': match_url,
                'data': match_data,
                'last_update': datetime.now(),
                'last_minute': match_data.get('current_minute', 0),
                'signals_count': 0,
            }

            logger.info(f"✅ Added match: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            return True
        except Exception as e:
            logger.error(f"Error adding match {match_id}: {e}")
            return False

    def remove_match(self, match_id: str):
        """Remove a match from monitoring"""
        if match_id in self.active_matches:
            del self.active_matches[match_id]
            logger.info(f"Removed match: {match_id}")

    def process_match(self, match_id: str) -> Optional[List[BettingSignal]]:
        """
        Process a single match and generate predictions

        Returns:
            List of BettingSignal or None if error
        """
        if match_id not in self.active_matches:
            return None

        match_info = self.active_matches[match_id]
        match_url = match_info['url']

        # Scrape latest data
        try:
            match_data = self.scraper.scrape_live_match(match_url)
            if not match_data:
                logger.warning(f"Failed to scrape match {match_id}")
                return None
        except Exception as e:
            logger.error(f"Error scraping match {match_id}: {e}")
            return None

        # Update match info
        match_info['data'] = match_data
        match_info['last_update'] = datetime.now()

        current_minute = match_data.get('current_minute')
        status = match_data.get('status')
        score = match_data.get('score', 'N/A')
        home_team = match_data.get('home_team', 'HOME')
        away_team = match_data.get('away_team', 'AWAY')

        # Only process live matches
        if status != 'Live' or not current_minute:
            return None

        signals = []

        # Generate predictions for each target interval [31-45] and [76-90]
        if 31 <= current_minute <= 45 or 76 <= current_minute <= 90:
            try:
                # Get possession (fallback to 50% neutral)
                live_stats = match_data.get('stats', {})
                home_possession = 50
                if 'Possession' in live_stats:
                    poss_str = live_stats['Possession'].get('home', '50')
                    try:
                        home_possession = float(poss_str.rstrip('%'))
                    except:
                        home_possession = 50

                # Make prediction
                prediction = self.predictor.predict_at_minute(
                    home_team=home_team,
                    away_team=away_team,
                    current_minute=current_minute,
                    home_possession=home_possession
                )

                if 'error' not in prediction:
                    danger_score = prediction['danger_score_percentage']

                    # Determine danger level
                    if danger_score >= self.DANGER_THRESHOLD_HIGH:
                        danger_level = "HIGH"
                        should_bet = True
                        signal_reason = f"HIGH DANGER ({danger_score:.1f}%)"
                    elif danger_score >= self.DANGER_THRESHOLD_MODERATE:
                        danger_level = "MODERATE"
                        should_bet = False
                        signal_reason = f"MODERATE ({danger_score:.1f}%)"
                    else:
                        danger_level = "LOW"
                        should_bet = False
                        signal_reason = f"LOW DANGER ({danger_score:.1f}%)"

                    # Create signal
                    signal = BettingSignal(
                        match_id=match_id,
                        home_team=home_team,
                        away_team=away_team,
                        minute=current_minute,
                        current_score=score,
                        danger_score=danger_score,
                        danger_level=danger_level,
                        should_bet=should_bet,
                        prediction_data=prediction,
                        timestamp=datetime.now(),
                        signal_reason=signal_reason,
                    )

                    signals.append(signal)
                    self.signals_history.append(signal)

                    if should_bet:
                        self.high_danger_signals.append(signal)
                        logger.warning(f"🎯 HIGH DANGER SIGNAL: {signal.display()}")
                    else:
                        logger.info(f"⚠️ {signal.display()}")

                    match_info['signals_count'] += 1

            except Exception as e:
                logger.error(f"Error generating prediction for {match_id}: {e}")
                return None

        return signals

    def monitor_all_matches(self, interval_seconds: int = 30, max_duration_seconds: Optional[int] = None):
        """
        Continuously monitor all active matches

        Args:
            interval_seconds: Polling interval in seconds
            max_duration_seconds: Maximum monitoring duration (None = infinite)
        """
        start_time = time.time()
        poll_count = 0

        print("\n" + "="*80)
        print("🔴 LIVE MONITORING STARTED")
        print("="*80)
        print(f"Polling interval: {interval_seconds}s")
        if max_duration_seconds:
            print(f"Max duration: {max_duration_seconds}s")
        print("="*80 + "\n")

        try:
            while True:
                # Check duration
                if max_duration_seconds and (time.time() - start_time) > max_duration_seconds:
                    logger.info("Max duration reached, stopping monitor")
                    break

                if not self.active_matches:
                    logger.warning("No active matches to monitor")
                    time.sleep(interval_seconds)
                    continue

                poll_count += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n⏰ [{current_time}] Poll #{poll_count}")
                print("-" * 80)

                # Process each match
                for match_id in list(self.active_matches.keys()):
                    match_info = self.active_matches[match_id]
                    match_data = match_info['data']

                    # Check if match timed out
                    time_since_update = (datetime.now() - match_info['last_update']).total_seconds()
                    if time_since_update > self.MATCH_TIMEOUT:
                        logger.info(f"Match {match_id} timed out, removing from monitoring")
                        self.remove_match(match_id)
                        continue

                    # Process match
                    signals = self.process_match(match_id)

                    if signals:
                        for signal in signals:
                            print(f"  {signal.display()}")

                            # Send Telegram alert for high danger signals
                            if signal.should_bet and self.telegram_token and self.telegram_chat_id:
                                self._send_telegram_alert(signal)

                # Sleep before next poll
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self._print_summary()

    def _send_telegram_alert(self, signal: BettingSignal):
        """Send Telegram alert for high danger signal"""
        if not self.telegram_token or not self.telegram_chat_id:
            return

        try:
            import requests

            message = f"""
🎯 BETTING SIGNAL ALERT

Match: {signal.home_team} vs {signal.away_team}
Minute: {signal.minute}'
Score: {signal.current_score}
Danger: {signal.danger_score:.1f}%

Action: PARIER (High Confidence)
Time: {signal.timestamp.strftime('%H:%M:%S')}
            """.strip()

            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            params = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                logger.success(f"✅ Telegram alert sent for {signal.match_id}")
            else:
                logger.warning(f"Failed to send Telegram alert: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")

    def _print_summary(self):
        """Print monitoring summary"""
        print("\n" + "="*80)
        print("📊 MONITORING SUMMARY")
        print("="*80)
        print(f"Total signals generated: {len(self.signals_history)}")
        print(f"High danger signals: {len(self.high_danger_signals)}")

        if self.high_danger_signals:
            print(f"\n🎯 HIGH DANGER SIGNALS:")
            for signal in self.high_danger_signals:
                print(f"  • {signal.home_team} vs {signal.away_team} @ {signal.minute}' - {signal.danger_score:.1f}%")

        print("="*80 + "\n")

    def get_statistics(self) -> Dict:
        """Get monitoring statistics"""
        return {
            'total_signals': len(self.signals_history),
            'high_danger_signals': len(self.high_danger_signals),
            'active_matches': len(self.active_matches),
            'trigger_rate': len(self.high_danger_signals) / len(self.signals_history) if self.signals_history else 0,
        }


def demo_monitor():
    """Demo: Monitor sample matches"""

    print("\n" + "="*80)
    print("🎯 LIVE MONITORING DEMO")
    print("="*80 + "\n")

    monitor = ContinuousLiveMonitor()

    # Add sample matches (URL must be valid for actual scraping)
    print("Note: Add live match URLs to monitor")
    print("Example: https://www.soccerstats.com/match_detail.asp?...")

    # In demo, we'll show the system is ready
    print("\n✅ Live monitoring system initialized and ready")
    print("   - RecurrencePredictor integrated")
    print("   - Danger score threshold: 65%")
    print("   - Polling interval: 30s")
    print("   - Supports Telegram alerts")
    print("   - Ready for Phase 5 live monitoring @ 12h")
    print("\n" + "="*80)


if __name__ == '__main__':
    demo_monitor()
