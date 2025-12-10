#!/usr/bin/env python3
"""Batch test: détecte matches live depuis plusieurs pages et scrape chaque match.

Usage: python3 run_selector_batch.py
"""
from __future__ import annotations

import sys
import time
from typing import List

from soccerstats_live_selector import get_live_matches

try:
    from soccerstats_live_scraper import SoccerStatsLiveScraper
except Exception:
    SoccerStatsLiveScraper = None

INDEX_PAGES: List[str] = [
    "https://www.soccerstats.com/",
    "https://www.soccerstats.com/matches.asp",
]


def main():
    print("Batch detection + scrape start")
    all_detected = []
    for idx in INDEX_PAGES:
        print(f"\nScanning index: {idx}")
        try:
            detected = get_live_matches(idx, timeout=15, debug=False)
        except Exception as e:
            print(f"  Error fetching {idx}: {e}")
            detected = []
        print(f"  Found {len(detected)} candidate(s)")
        for d in detected:
            print(f"   - {d['url']} (minute={d.get('minute')}) snippet={d.get('snippet')[:120]}")
        all_detected.extend(detected)

    # dedupe
    unique_urls = {}
    for d in all_detected:
        unique_urls[d['url']] = d

    print(f"\nTotal unique detected matches: {len(unique_urls)}")

    if SoccerStatsLiveScraper is None:
        print("SoccerStatsLiveScraper not available in environment. Skipping scrape tests.")
        return 0

    scraper = SoccerStatsLiveScraper()
    successes = 0
    failures = 0
    for url, d in unique_urls.items():
        print(f"\nScraping {url} ...")
        try:
            data = scraper.scrape_match(url)
            if data:
                # LiveMatchData uses score_home/score_away
                print(f"  OK: {data.home_team} {data.score_home}:{data.score_away} {data.away_team} minute={data.minute}")
                successes += 1
            else:
                print("  WARN: no data returned")
                failures += 1
        except Exception as e:
            print(f"  FAIL: exception during scrape: {e}")
            failures += 1
        # be polite
        time.sleep(1)

    print(f"\nBatch complete. Successes={successes} Failures={failures}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
