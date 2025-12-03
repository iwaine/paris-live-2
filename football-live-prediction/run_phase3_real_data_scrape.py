#!/usr/bin/env python3
"""
SCRAPE REAL DATA FROM SOCCERSTATS.COM
Récupère les vraies données historiques (pas mode démo)
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from scrapers.soccerstats_match_history_scraper import SoccerStatsHistoricalScraper
from scrapers.historical_data_loader import HistoricalDataLoader
from predictors.recurrence_analyzer import RecurrenceAnalyzer
from loguru import logger


def main():
    print("\n" + "="*80)
    print("🌐 SCRAPING REAL DATA FROM SOCCERSTATS.COM")
    print("="*80)

    # Configuration - REAL MODE (no demo)
    DEMO_MODE = False  # Scraper les vraies données
    MATCHES_PER_LEAGUE = 50  # 50 matchs par ligue

    # Ligues à scraper (12 au total)
    ligues = [
        "england", "spain", "france", "germany", "italy",
        "norway6", "iceland2", "cyprus", "estonia", "bolivia",
        "portugal", "portugal2"
    ]

    print("\n🌐 REAL DATA SCRAPING")
    print("-"*80)
    print("Mode: REAL DATA (not demo)")
    print("Fallback: Auto-fallback to demo if internet unavailable")
    print()

    # Initialize scraper in REAL mode
    scraper = SoccerStatsHistoricalScraper(demo_mode=DEMO_MODE)
    total_matches_scraped = 0

    # Scrape each league
    for league in ligues:
        try:
            print(f"Scraping {league}...", end=" ", flush=True)
            count = scraper.scrape_league_history(league, max_matches=MATCHES_PER_LEAGUE)
            total_matches_scraped += count
            print(f"✅ {count} matches")
        except Exception as e:
            logger.error(f"Error scraping {league}: {e}")
            print(f"❌ Failed")

    print(f"\n✓ Total matches scraped: {total_matches_scraped}")

    # Analyze all teams
    print("\n📈 ANALYZING PATTERNS")
    print("-"*80)

    loader = HistoricalDataLoader()
    teams = loader.get_teams_in_db()
    print(f"Analyzing {len(teams)} unique teams...")

    analyzer = RecurrenceAnalyzer()
    analyzer.analyze_and_save_all(teams)

    # Show results
    print("\n\n📊 FINAL STATISTICS")
    print("-"*80)

    stats = loader.get_match_stats()
    print(f"\n✓ Database Statistics:")
    print(f"  • Total matches: {stats.get('total_matches', 0)}")
    print(f"  • Total goals: {stats.get('total_goals', 0)}")
    print(f"  • Unique teams: {stats.get('total_teams', 0)}")
    print(f"  • Avg goals/match: {stats.get('total_goals', 0) / max(stats.get('total_matches', 1), 1):.1f}")

    print("\n" + "="*80)
    print("✅ REAL DATA SCRAPING COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
