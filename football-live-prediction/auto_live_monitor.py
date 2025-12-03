#!/usr/bin/env python3
"""
Système de Surveillance Automatique Multi-Ligues
Détecte automatiquement tous les matchs live et les surveille en temps réel
"""

import time
import yaml
from pathlib import Path
from typing import List, Dict
from loguru import logger
from datetime import datetime

# Imports du projet
import sys
sys.path.insert(0, 'scrapers')
sys.path.insert(0, 'predictors')
sys.path.insert(0, 'utils')

from live_match_detector import LiveMatchDetector
from soccerstats_live_scraper import SoccerStatsLiveScraper
from interval_predictor import IntervalPredictor
from match_monitor import MatchMonitor, create_telegram_callbacks
from database_manager import DatabaseManager

# Optional: Telegram
try:
    from telegram_bot import TelegramNotifier
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("⚠️  Telegram not available (install python-telegram-bot)")


class AutoLiveMonitor:
    """
    Système automatique de surveillance multi-ligues

    Fonctionnalités:
    1. Détecte automatiquement tous les matchs live (44+ ligues)
    2. Extrait les données complètes de chaque match
    3. Fait des prédictions en temps réel
    4. Envoie des alertes Telegram
    5. Stocke tout en base de données
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        detection_interval: int = 300,  # Scan toutes les 5 min
        monitor_interval: int = 60,     # Update match toutes les 60s
        enable_telegram: bool = True,
        enable_database: bool = True
    ):
        """
        Initialise le système automatique

        Args:
            config_path: Chemin vers config.yaml
            detection_interval: Intervalle de détection en secondes
            monitor_interval: Intervalle de surveillance par match en secondes
            enable_telegram: Activer Telegram
            enable_database: Activer la base de données
        """
        self.config_path = config_path
        self.detection_interval = detection_interval
        self.monitor_interval = monitor_interval

        # Charger la configuration
        self.leagues = self._load_config()

        # Initialiser les composants
        self.detector = LiveMatchDetector()
        self.scraper = SoccerStatsLiveScraper()
        self.predictor = IntervalPredictor()

        # Base de données
        self.db = None
        if enable_database:
            try:
                self.db = DatabaseManager()
                logger.success("✅ Database connected")
            except Exception as e:
                logger.warning(f"⚠️  Database not available: {e}")

        # Telegram
        self.notifier = None
        if enable_telegram and TELEGRAM_AVAILABLE:
            try:
                self.notifier = TelegramNotifier()
                if self.notifier.bot:
                    logger.success("✅ Telegram connected")
                else:
                    self.notifier = None
            except Exception as e:
                logger.warning(f"⚠️  Telegram not available: {e}")

        # État
        self.active_matches: Dict[str, Dict] = {}  # URL -> match_info
        self.monitored_urls = set()  # URLs déjà surveillées
        self.running = False

        logger.info("="*70)
        logger.info("🚀 AUTO LIVE MONITOR INITIALIZED")
        logger.info("="*70)
        logger.info(f"📊 Leagues: {len(self.leagues)}")
        logger.info(f"🔍 Detection interval: {detection_interval}s")
        logger.info(f"👁️  Monitor interval: {monitor_interval}s")
        logger.info(f"💾 Database: {'✅' if self.db else '❌'}")
        logger.info(f"📱 Telegram: {'✅' if self.notifier else '❌'}")
        logger.info("="*70)

    def _load_config(self) -> List[Dict]:
        """Charge la configuration des ligues"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                leagues = config.get('leagues', [])
                logger.info(f"📋 Loaded {len(leagues)} leagues from config")
                return leagues
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return []

    def detect_all_live_matches(self) -> List[Dict]:
        """
        Détecte tous les matchs live sur toutes les ligues

        Returns:
            Liste de tous les matchs live détectés
        """
        logger.info("\n" + "="*70)
        logger.info(f"🔍 SCANNING {len(self.leagues)} LEAGUES FOR LIVE MATCHES")
        logger.info("="*70)

        all_matches = []

        for i, league in enumerate(self.leagues, 1):
            league_name = league.get('name', 'Unknown')
            league_url = league.get('url')

            if not league_url:
                continue

            logger.info(f"[{i}/{len(self.leagues)}] Scanning: {league_name}")

            try:
                matches = self.detector.scrape(league_url, league_name)

                if matches:
                    logger.success(f"   ✅ Found {len(matches)} live match(es)")
                    all_matches.extend(matches)
                else:
                    logger.debug(f"   ⚪ No live matches")

                # Petit délai pour ne pas surcharger
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"   ❌ Error: {e}")

        logger.info("="*70)
        logger.success(f"🎯 TOTAL LIVE MATCHES FOUND: {len(all_matches)}")
        logger.info("="*70)

        return all_matches

    def extract_complete_match_data(self, match_url: str) -> Dict:
        """
        Extrait les données complètes d'un match (équipes, score, stats)

        Args:
            match_url: URL du match

        Returns:
            MatchData complet ou None
        """
        try:
            match_data = self.scraper.scrape_match(match_url)

            if match_data:
                logger.info(f"✅ Data extracted: {match_data.home_team} {match_data.score_home}-{match_data.score_away} {match_data.away_team} ({match_data.minute}')")
                return match_data
            else:
                logger.warning(f"⚠️  Failed to extract data from: {match_url}")
                return None

        except Exception as e:
            logger.error(f"❌ Error extracting data: {e}")
            return None

    def store_match_in_db(self, match_data) -> int:
        """
        Stocke le match en base de données

        Args:
            match_data: MatchData object

        Returns:
            match_id ou None
        """
        if not self.db:
            return None

        try:
            match_dict = {
                'home_team': match_data.home_team,
                'away_team': match_data.away_team,
                'league': 'auto-detected',
                'final_score': f"{match_data.score_home}-{match_data.score_away}",
                'red_cards_home': 0,
                'red_cards_away': 0,
                'penalties_home': 0,
                'penalties_away': 0,
                'injuries_home': '',
                'injuries_away': '',
                'status': 'live'
            }

            match_id = self.db.insert_match(match_dict)
            logger.info(f"💾 Match stored in DB (ID: {match_id})")
            return match_id

        except Exception as e:
            logger.error(f"❌ Failed to store match: {e}")
            return None

    def make_prediction(self, match_data, match_id: int = None):
        """
        Fait une prédiction et l'envoie/stocke

        Args:
            match_data: MatchData object
            match_id: ID du match en BD
        """
        try:
            # Prédiction
            prediction = self.predictor.predict_match(
                home_team=match_data.home_team,
                away_team=match_data.away_team,
                current_minute=match_data.minute,
                live_stats={
                    'score': f"{match_data.score_home}-{match_data.score_away}",
                    'red_cards': {'home': 0, 'away': 0},
                    'penalties': {'home': 0, 'away': 0},
                    'injuries': {'home': 0, 'away': 0}
                }
            )

            if not prediction.get('success'):
                logger.warning(f"⚠️  Prediction failed for {match_data.home_team} vs {match_data.away_team}")
                return

            danger_score = prediction.get('danger_score', 0)
            interpretation = prediction.get('interpretation', 'N/A')
            confidence = prediction.get('confidence', 'N/A')

            logger.info(f"📊 Prediction: Danger={danger_score:.2f} ({interpretation}) | Confidence={confidence}")

            # Stocker en BD
            if self.db and match_id:
                try:
                    pred_dict = {
                        'match_id': match_id,
                        'minute': match_data.minute,
                        'interval': prediction.get('interval', '?'),
                        'danger_score': danger_score,
                        'interpretation': interpretation,
                        'confidence': confidence,
                        'result_correct': None,
                        'result_notes': None
                    }
                    pred_id = self.db.insert_prediction(pred_dict)
                    logger.info(f"💾 Prediction stored (ID: {pred_id})")
                except Exception as e:
                    logger.error(f"❌ Failed to store prediction: {e}")

            # Alerte Telegram si danger élevé
            if danger_score >= 3.5 and self.notifier:
                try:
                    alert_data = {
                        'home_team': match_data.home_team,
                        'away_team': match_data.away_team,
                        'current_minute': match_data.minute,
                        'score': f"{match_data.score_home}-{match_data.score_away}",
                        'danger_score': danger_score,
                        'interpretation': interpretation,
                        'confidence': confidence,
                        'details': prediction.get('details', {})
                    }
                    self.notifier.send_match_alert(alert_data)
                    logger.success("📱 Telegram alert sent")
                except Exception as e:
                    logger.error(f"❌ Failed to send Telegram alert: {e}")

        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")

    def monitor_match_once(self, match_url: str, league_name: str):
        """
        Surveille un match une seule fois (extrait données + prédiction)

        Args:
            match_url: URL du match
            league_name: Nom de la ligue
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"👁️  MONITORING MATCH: {league_name}")
        logger.info(f"🔗 URL: {match_url}")
        logger.info(f"{'='*70}")

        # Extraire les données complètes
        match_data = self.extract_complete_match_data(match_url)

        if not match_data:
            logger.warning("⚠️  Skipping match (no data)")
            return

        # Stocker en BD
        match_id = self.store_match_in_db(match_data)

        # Faire une prédiction
        self.make_prediction(match_data, match_id)

        # Notifier Telegram du nouveau match
        if self.notifier:
            try:
                message = f"""
🏟️  <b>NOUVEAU MATCH LIVE DÉTECTÉ</b>

<b>Ligue:</b> {league_name}
<b>Match:</b> {match_data.home_team} vs {match_data.away_team}
<b>Score:</b> {match_data.score_home}-{match_data.score_away}
<b>Minute:</b> {match_data.minute}'

📊 Surveillance en cours...
                """
                # self.notifier.send_message(message)  # Décommenter si méthode existe
            except:
                pass

    def run_detection_cycle(self):
        """
        Lance un cycle de détection complet

        1. Détecte tous les matchs live
        2. Pour chaque nouveau match: extraire données + prédiction
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 DETECTION CYCLE STARTED - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'='*70}")

        # Détecter tous les matchs live
        live_matches = self.detect_all_live_matches()

        if not live_matches:
            logger.info("⚪ No live matches found")
            return

        # Traiter chaque match
        for i, match in enumerate(live_matches, 1):
            match_url = match['url']
            league_name = match['league']
            status = match['status']

            # Vérifier si déjà surveillé dans ce cycle
            if match_url in self.active_matches:
                logger.debug(f"[{i}/{len(live_matches)}] Already active: {league_name} ({status})")
                continue

            # Nouveau match!
            logger.info(f"\n[{i}/{len(live_matches)}] 🆕 NEW LIVE MATCH DETECTED")

            # Surveiller une fois
            self.monitor_match_once(match_url, league_name)

            # Ajouter aux matchs actifs
            self.active_matches[match_url] = {
                'league': league_name,
                'status': status,
                'first_detected': datetime.now(),
                'last_checked': datetime.now()
            }

        # Nettoyage: retirer les matchs qui ne sont plus live
        self._cleanup_finished_matches(live_matches)

    def _cleanup_finished_matches(self, current_live_matches: List[Dict]):
        """
        Retire les matchs terminés de active_matches

        Args:
            current_live_matches: Liste des matchs actuellement live
        """
        current_urls = {m['url'] for m in current_live_matches}
        finished_urls = set(self.active_matches.keys()) - current_urls

        for url in finished_urls:
            match_info = self.active_matches[url]
            logger.info(f"✅ Match finished: {match_info['league']}")
            del self.active_matches[url]

    def run(self, max_cycles: int = None):
        """
        Lance la surveillance automatique en continu

        Args:
            max_cycles: Nombre maximum de cycles (None = infini)
        """
        logger.info("\n" + "="*70)
        logger.success("🚀 AUTO LIVE MONITOR STARTED")
        logger.info("="*70)
        logger.info(f"Detection interval: {self.detection_interval}s")
        logger.info(f"Max cycles: {max_cycles or 'Unlimited'}")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*70 + "\n")

        self.running = True
        cycle_count = 0

        try:
            while self.running:
                cycle_count += 1

                if max_cycles and cycle_count > max_cycles:
                    logger.info(f"✅ Max cycles ({max_cycles}) reached")
                    break

                # Lancer un cycle de détection
                self.run_detection_cycle()

                # Attendre avant le prochain cycle
                logger.info(f"\n💤 Sleeping {self.detection_interval}s before next cycle...")
                logger.info(f"Active matches: {len(self.active_matches)}")

                time.sleep(self.detection_interval)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopping auto monitor...")
            self.running = False

        finally:
            self.cleanup()

    def cleanup(self):
        """Nettoie les ressources"""
        logger.info("\n🧹 Cleaning up...")

        if self.detector:
            self.detector.cleanup()

        if self.db:
            self.db.close()

        logger.success("✅ AUTO LIVE MONITOR STOPPED")


def main():
    """Point d'entrée principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Auto Live Monitor - Surveillance automatique multi-ligues')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--detection-interval', type=int, default=300, help='Detection interval in seconds (default: 300s = 5min)')
    parser.add_argument('--monitor-interval', type=int, default=60, help='Monitor interval in seconds (default: 60s)')
    parser.add_argument('--max-cycles', type=int, default=None, help='Max detection cycles (default: unlimited)')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram notifications')
    parser.add_argument('--no-database', action='store_true', help='Disable database storage')
    parser.add_argument('--test', action='store_true', help='Run one detection cycle only (for testing)')

    args = parser.parse_args()

    # Créer le moniteur
    monitor = AutoLiveMonitor(
        config_path=args.config,
        detection_interval=args.detection_interval,
        monitor_interval=args.monitor_interval,
        enable_telegram=not args.no_telegram,
        enable_database=not args.no_database
    )

    # Mode test: un seul cycle
    if args.test:
        logger.info("🧪 TEST MODE: Running one detection cycle only")
        monitor.run_detection_cycle()
        monitor.cleanup()
    else:
        # Mode normal: surveillance continue
        monitor.run(max_cycles=args.max_cycles)


if __name__ == "__main__":
    main()
