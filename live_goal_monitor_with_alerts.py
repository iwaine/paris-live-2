#!/usr/bin/env python3
"""
Intégration complète: MONITOR DAEMON + GOAL PROBABILITY PREDICTOR + TELEGRAM ALERTS

Ce script:
1. Lance le daemon de détection de matches live
2. Pour chaque match, scrape les données live
3. Prédit la probabilité de but
4. Envoie une alerte Telegram si probabilité > seuil
"""

import sys
import time
import threading
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

# Ajouter les chemins
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "football-live-prediction"))

from soccerstats_live_selector import get_live_matches
from soccerstats_live_scraper import SoccerStatsLiveScraper

try:
    from predictors.live_goal_probability_predictor import predict_goal
except ImportError:
    # Fallback
    from football_live_prediction.predictors.live_goal_probability_predictor import predict_goal

try:
    from utils.telegram_bot import TelegramBot
    TELEGRAM_AVAILABLE = True
except ImportError:
    try:
        from football_live_prediction.utils.telegram_bot import TelegramBot
        TELEGRAM_AVAILABLE = True
    except ImportError:
        TELEGRAM_AVAILABLE = False
        print("⚠️ TelegramBot non disponible - les alertes ne seront pas envoyées")

DEFAULT_DETECTION_INTERVAL = 15  # secondes entre détections
DEFAULT_MATCH_INTERVAL = 8  # secondes entre scrapes par match
GOAL_PROBABILITY_THRESHOLD = 0.60  # 60% = seuil d'alerte


class LiveGoalMonitor(threading.Thread):
    """Monitor un match et envoie des alertes quand il y a risque de but"""

    def __init__(
        self,
        url: str,
        match_interval: int = DEFAULT_MATCH_INTERVAL,
        telegram_bot: Optional[object] = None,
        threshold: float = GOAL_PROBABILITY_THRESHOLD,
    ):
        super().__init__(daemon=True)
        self.url = url
        self.match_interval = match_interval
        self.scraper = SoccerStatsLiveScraper()
        self.telegram = telegram_bot
        self.threshold = threshold
        self._stop = threading.Event()
        self.last_alert_time = {}  # {match_key: timestamp} pour éviter spam

    def stop(self):
        self._stop.set()

    def run(self):
        """Boucle de monitoring"""
        while not self._stop.is_set():
            try:
                data = self.scraper.scrape_match(self.url)
                if data:
                    d = data.to_dict() if hasattr(data, "to_dict") else data
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Prédire la probabilité de but
                    try:
                        prediction = predict_goal(None, d.get("home_team"), d.get("away_team"), d)
                        goal_prob = prediction.get("goal_probability", 0) / 100
                        danger_level = prediction.get("danger_level", "LOW")

                        # Affichage console
                        match_str = f"{d.get('home_team')} {d.get('score_home')}:{d.get('score_away')} {d.get('away_team')}"
                        print(
                            f"[{ts}] {match_str} | min={d.get('minute')} | Goal Prob={goal_prob*100:.1f}% [{danger_level}]"
                        )

                        # Vérifier si alerte nécessaire
                        match_key = self.url
                        if goal_prob >= self.threshold:
                            time_since_last_alert = time.time() - self.last_alert_time.get(
                                match_key, 0
                            )
                            # Limiter les alertes: max 1 par 2 minutes pour le même match
                            if time_since_last_alert > 120:
                                self._send_alert(match_str, goal_prob, danger_level, d)
                                self.last_alert_time[match_key] = time.time()

                    except Exception as e:
                        print(f"[{ts}] Erreur prédiction: {e}")

                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] MONITOR {self.url} | no data")

            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] MONITOR {self.url} | error: {e}")

            time.sleep(self.match_interval)

    def _send_alert(
        self, match_str: str, goal_prob: float, danger_level: str, live_data: Dict
    ):
        """Envoie une alerte Telegram"""
        if not self.telegram:
            return

        # Construire le message avec TOUTES les stats disponibles
        message_lines = [
            f"⚽ *BUT POTENTIEL IMMINENT*\n",
            f"🔥 *{match_str}*",
            f"⏱️ Minute: {live_data.get('minute')}",
            f"📊 Score: {live_data.get('score_home', 0)}-{live_data.get('score_away', 0)}",
            f"📈 Probabilité de but: *{goal_prob*100:.1f}%*",
            f"🎯 Niveau: *{danger_level}*\n",
            f"📊 *STATS LIVE:*"
        ]
        
        # Ajouter toutes les stats disponibles
        if live_data.get('possession_home') is not None or live_data.get('possession_away') is not None:
            message_lines.append(f"🏟️ Possession: {live_data.get('possession_home', 0):.0f}% / {live_data.get('possession_away', 0):.0f}%")
        
        if live_data.get('corners_home') is not None or live_data.get('corners_away') is not None:
            message_lines.append(f"🚩 Corners: {live_data.get('corners_home', 0)} / {live_data.get('corners_away', 0)}")
        
        if live_data.get('shots_home') is not None or live_data.get('shots_away') is not None:
            message_lines.append(f"⚽ Total shots: {live_data.get('shots_home', 0)} / {live_data.get('shots_away', 0)}")
        
        if live_data.get('shots_on_target_home') is not None or live_data.get('shots_on_target_away') is not None:
            message_lines.append(f"🎯 Shots on target: {live_data.get('shots_on_target_home', 0)} / {live_data.get('shots_on_target_away', 0)}")
        
        if live_data.get('attacks_home') is not None or live_data.get('attacks_away') is not None:
            message_lines.append(f"⚔️ Attacks: {live_data.get('attacks_home', 0)} / {live_data.get('attacks_away', 0)}")
        
        if live_data.get('dangerous_attacks_home') is not None or live_data.get('dangerous_attacks_away') is not None:
            message_lines.append(f"🔥 Dangerous attacks: {live_data.get('dangerous_attacks_home', 0)} / {live_data.get('dangerous_attacks_away', 0)}")
        
        message = "\n".join(message_lines)

        try:
            self.telegram.send_message(message)
            print(f"✅ Alerte Telegram envoyée pour {match_str}")
        except Exception as e:
            print(f"❌ Erreur envoi Telegram: {e}")


def main():
    """Daemon principal"""
    import argparse

    p = argparse.ArgumentParser(description="Live goal monitor with Telegram alerts")
    p.add_argument(
        "--detect-interval", type=int, default=DEFAULT_DETECTION_INTERVAL, help="Intervalle détection (s)"
    )
    p.add_argument(
        "--match-interval", type=int, default=DEFAULT_MATCH_INTERVAL, help="Intervalle scrape (s)"
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=GOAL_PROBABILITY_THRESHOLD,
        help="Seuil de probabilité de but (0-1)",
    )
    p.add_argument("--dry-run", action="store_true", help="Détecte une fois et affiche")
    args = p.parse_args()

    # Initialiser Telegram (optionnel)
    telegram = None
    if TELEGRAM_AVAILABLE:
        try:
            telegram = TelegramBot()
            print("✅ Telegram connecté")
        except Exception as e:
            print(f"⚠️ Telegram non configuré: {e}")

    seen_cache = {}
    monitors = {}

    try:
        print("🚀 Starting Live Goal Monitor. Press Ctrl-C to stop.")

        if args.dry_run:
            candidates = get_live_matches(debug=False)
            print(f"\n📊 Dry-run: {len(candidates)} matches détectés\n")
            for c in candidates:
                print(f"- {c['url']} | minute={c.get('minute')} | snippet={c.get('snippet')[:100]}")
            return 0

        while True:
            try:
                candidates = get_live_matches(debug=False)
            except Exception as e:
                print(f"Detection error: {e}")
                candidates = []

            for c in candidates:
                url = c["url"]
                if url in seen_cache:
                    continue  # Déjà en cours de monitoring

                print(f"🎯 Starting monitor for {c.get('snippet')[:80]} (min={c.get('minute')})")
                m = LiveGoalMonitor(
                    url,
                    match_interval=args.match_interval,
                    telegram_bot=telegram,
                    threshold=args.threshold,
                )
                m.start()
                monitors[url] = m
                seen_cache[url] = datetime.now()

            # Cleanup finished monitors
            for url in list(monitors.keys()):
                if not monitors[url].is_alive():
                    del monitors[url]

            time.sleep(args.detect_interval)

    except KeyboardInterrupt:
        print("\n⏹️ Stopping Live Goal Monitor...")
        for m in monitors.values():
            m.stop()
        return 0


if __name__ == "__main__":
    sys.exit(main())
