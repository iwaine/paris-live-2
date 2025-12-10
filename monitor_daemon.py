#!/usr/bin/env python3
"""Prototype de daemon pour détecter et monitorer automatiquement les matches live.

Fonctions principales:
 - boucle de détection toutes les N secondes (par défaut 15s)
 - cache TTL pour éviter relancer plusieurs fois le même match
 - démarre un monitor par match (thread) qui scrape périodiquement
 - option --dry-run pour exécuter une détection unique et sortir

Usage:
  python3 monitor_daemon.py [--detect-interval 15] [--match-interval 8] [--filter england|spain] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import threading
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from soccerstats_live_selector import get_live_matches
from soccerstats_live_scraper import SoccerStatsLiveScraper

DEFAULT_DETECT_INTERVAL = 15
DEFAULT_MATCH_INTERVAL = 8
CACHE_TTL = 60 * 60  # 1 heure par défaut


class MatchMonitor(threading.Thread):
    def __init__(self, url: str, match_interval: int = DEFAULT_MATCH_INTERVAL):
        super().__init__(daemon=True)
        self.url = url
        self.match_interval = match_interval
        self.scraper = SoccerStatsLiveScraper()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            try:
                data = self.scraper.scrape_match(self.url)
                if data:
                    d = data.to_dict() if hasattr(data, 'to_dict') else data
                    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{ts}] MONITOR {self.url} | {d.get('home_team')} {d.get('score_home')}:{d.get('score_away')} {d.get('away_team')} | min={d.get('minute')}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] MONITOR {self.url} | no data")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] MONITOR {self.url} | error: {e}")
            # sleep between scrapes for this match
            time.sleep(self.match_interval)


def main():
    p = argparse.ArgumentParser(description='Daemon prototype: detect and monitor live matches')
    p.add_argument('--detect-interval', type=int, default=DEFAULT_DETECT_INTERVAL, help='Intervalle (s) entre détections')
    p.add_argument('--match-interval', type=int, default=DEFAULT_MATCH_INTERVAL, help='Intervalle (s) de scraping par match')
    p.add_argument('--filter', type=str, default=None, help='Regex pour filtrer les URLs/ligues (ex: england|spain)')
    p.add_argument('--dry-run', action='store_true', help='Détecte une fois et affiche les candidats puis sort')
    args = p.parse_args()

    seen_cache: Dict[str, datetime] = {}
    monitors: Dict[str, MatchMonitor] = {}

    def should_monitor(url: str) -> bool:
        # appliquer filtre si fourni
        if args.filter:
            if not re.search(args.filter, url, re.I):
                return False
        # TTL cache
        t = seen_cache.get(url)
        if t and datetime.now() - t < timedelta(seconds=CACHE_TTL):
            return False
        return True

    try:
        # single detection (dry-run)
        candidates = get_live_matches(debug=False)
        if args.dry_run:
            print(f"Dry-run: found {len(candidates)} candidates")
            for c in candidates:
                print(f" - {c['url']} minute={c.get('minute')} snippet={c.get('snippet')[:140]}")
            return 0

        print("Starting monitor daemon. Press Ctrl-C to stop.")
        while True:
            try:
                candidates = get_live_matches(debug=False)
            except Exception as e:
                print(f"Detection error: {e}")
                candidates = []

            for c in candidates:
                url = c['url']
                if not should_monitor(url):
                    continue
                # start monitor thread
                print(f"Starting monitor for {url} (minute={c.get('minute')})")
                m = MatchMonitor(url, match_interval=args.match_interval)
                m.start()
                monitors[url] = m
                seen_cache[url] = datetime.now()

            # cleanup finished monitors (if any)
            for url, m in list(monitors.items()):
                if not m.is_alive():
                    monitors.pop(url, None)

            time.sleep(args.detect_interval)

    except KeyboardInterrupt:
        print('Stopping daemon...')
        for m in monitors.values():
            m.stop()
        return 0


if __name__ == '__main__':
    exit(main())
