#!/usr/bin/env python3
"""
ÉTAPE 3: Scrape + Analyze All Leagues
Lance le scraping et l'analyse pour toutes les ligues configurées
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from scrapers.soccerstats_match_history_scraper import SoccerStatsHistoricalScraper
from scrapers.historical_data_loader import HistoricalDataLoader
from predictors.recurrence_analyzer import RecurrenceAnalyzer
from utils.database_manager import DatabaseManager
from loguru import logger


def main():
    print("\n" + "="*80)
    print("🚀 ÉTAPE 3: SCRAPE + ANALYZE ALL LEAGUES")
    print("="*80)

    # Configuration
    DEMO_MODE = True  # Mode démo rapide (pas besoin internet)
    MATCHES_PER_LEAGUE = 30  # 30 matchs par ligue = ~600 matchs total

    # Ligues à scraper
    ligues = [
        "england", "spain", "france", "germany", "italy",
        "norway6", "iceland2", "cyprus", "estonia", "bolivia",
        "portugal", "portugal2"
    ]

    # PHASE 1: SCRAPING
    print("\n📊 PHASE 1: SCRAPING LEAGUES")
    print("-"*80)

    scraper = SoccerStatsHistoricalScraper(demo_mode=DEMO_MODE)
    total_matches_scraped = 0

    for league in ligues:
        try:
            count = scraper.scrape_league_history(league, max_matches=MATCHES_PER_LEAGUE)
            total_matches_scraped += count
            print(f"  ✅ {league:15s} → {count} matches")
        except Exception as e:
            logger.error(f"Error scraping {league}: {e}")
            print(f"  ❌ {league:15s} → Failed")

    print(f"\n✓ Total matches scraped: {total_matches_scraped}")

    # Get all unique teams from DB
    loader = HistoricalDataLoader()
    teams = loader.get_teams_in_db()
    print(f"✓ Total unique teams: {len(teams)}")

    # PHASE 2: ANALYSIS
    print("\n\n📈 PHASE 2: ANALYZING PATTERNS")
    print("-"*80)

    analyzer = RecurrenceAnalyzer()

    print(f"Analyzing {len(teams)} teams...")
    analyzer.analyze_and_save_all(teams)

    # PHASE 3: STATS & SUMMARY
    print("\n\n📊 PHASE 3: SUMMARY")
    print("-"*80)

    stats = loader.get_match_stats()
    print(f"\n✓ Database Statistics:")
    print(f"  • Total matches: {stats.get('total_matches', 0)}")
    print(f"  • Total goals: {stats.get('total_goals', 0)}")
    print(f"  • Unique teams: {stats.get('total_teams', 0)}")

    # Get some sample predictions
    print(f"\n\n🎯 SAMPLE PREDICTIONS (Testing)")
    print("-"*80)

    from predictors.recurrence_predictor import RecurrencePredictor

    predictor = RecurrencePredictor()

    # Test cases from different leagues
    test_cases = [
        ("Arsenal", "Chelsea", 38, 0.62, "England"),
        ("Real Madrid", "Barcelona", 42, 0.58, "Spain"),
        ("PSG", "Marseille", 39, 0.65, "France"),
        ("Bayern Munich", "Borussia Dortmund", 81, 0.55, "Germany"),
        ("AC Milan", "Juventus", 35, 0.60, "Italy"),
        ("Molde", "Viking", 40, 0.58, "Norway"),
        ("APOEL", "Olympiakos Nicosia", 38, 0.62, "Cyprus"),
    ]

    print("\nLive predictions at key minutes:\n")

    for home, away, minute, poss, league in test_cases:
        prediction = predictor.predict_at_minute(
            home_team=home,
            away_team=away,
            current_minute=minute,
            home_possession=poss
        )

        if "error" not in prediction:
            danger = prediction['danger_score_percentage']
            status = "✅ PARIER" if danger >= 65 else "⚠️  CONSIDÉRER" if danger >= 50 else "❌ SKIP"

            print(f"  {status:15s} | {home:20s} vs {away:20s} @ min {minute:2d}")
            print(f"                  | Danger: {danger:5.1f}% | Data: {prediction['data_summary']['home_matches_total']} + {prediction['data_summary']['away_matches_total']} matches | {league}")
            print()

    print("="*80)
    print("✅ ÉTAPE 3 COMPLÉTÉE!")
    print("="*80)
    print("\n📌 Next: Backtesting (Étape 4)")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
