#!/usr/bin/env python3
"""
Phase 3: Scrape TOUTES les données historiques RÉELLES de SoccerStats
Aucune donnée de démo - que du vrai

Cible: 100+ matches par ligue × 15 ligues = 1500+ matches avec données réelles
"""

import sys
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from utils.database_manager import DatabaseManager
from scrapers.match_history_scraper import MatchHistoryScraper

# Ligues à scraper (configuration globale)
LEAGUES_CONFIG = {
    "england": {"code": "england", "max_matches": 150},
    "spain": {"code": "spain", "max_matches": 150},
    "france": {"code": "france", "max_matches": 150},
    "germany": {"code": "germany", "max_matches": 150},
    "italy": {"code": "italy", "max_matches": 150},
    "scotland": {"code": "scotland", "max_matches": 100},
    "netherlands": {"code": "netherlands", "max_matches": 100},
    "belgium": {"code": "belgium", "max_matches": 100},
    "portugal": {"code": "portugal", "max_matches": 100},
    "austria": {"code": "austria", "max_matches": 100},
    "norway": {"code": "norway6", "max_matches": 100},
    "iceland": {"code": "iceland2", "max_matches": 80},
    "cyprus": {"code": "cyprus", "max_matches": 80},
    "estonia": {"code": "estonia", "max_matches": 80},
    "bolivia": {"code": "bolivia", "max_matches": 80},
}

DEMO_MODE = False  # ⚠️ IMPORTANT: VRAIS DONNÉES SEULEMENT


def main():
    print("\n" + "=" * 80)
    print("PHASE 3: SCRAPE REAL SOCCERSTATS HISTORICAL DATA")
    print("=" * 80)
    print(f"Mode DEMO: {DEMO_MODE}")
    print(f"Ligues à scraper: {len(LEAGUES_CONFIG)}")
    print(f"Target: ~{sum(c['max_matches'] for c in LEAGUES_CONFIG.values())} matches")
    print("=" * 80 + "\n")

    # Initialiser DB et scraper
    db = DatabaseManager(db_path="data/predictions.db")
    scraper = MatchHistoryScraper()

    total_matches = 0
    total_goals = 0
    total_teams = set()

    # Scraper chaque ligue
    for league_name, league_config in LEAGUES_CONFIG.items():
        league_code = league_config["code"]
        max_matches = league_config["max_matches"]

        print(f"\n🔄 Scraping {league_name.upper()} ({league_code})...")
        print(f"   Target: {max_matches} matches")

        try:
            matches = scraper.scrape_league_matches(league_code, max_matches=max_matches)

            if not matches:
                print(f"   ❌ Aucun match scrappé pour {league_name}")
                continue

            print(f"   ✅ {len(matches)} matches scrappés")

            # Insérer dans la base
            for match in matches:
                try:
                    # Insérer le match
                    match_id = db.insert_match({
                        "home_team": match.get("home_team"),
                        "away_team": match.get("away_team"),
                        "league": league_code,
                        "match_date": match.get("match_date"),
                        "final_score": match.get("final_score"),
                        "home_goals": match.get("home_goals"),
                        "away_goals": match.get("away_goals"),
                    })
                    
                    if match_id:
                        total_matches += 1
                        total_goals += match.get("home_goals", 0) + match.get("away_goals", 0)
                        total_teams.add(match.get("home_team"))
                        total_teams.add(match.get("away_team"))

                except Exception as e:
                    print(f"   ⚠️ Erreur insertion {match.get('home_team')} vs {match.get('away_team')}: {e}")
                    continue

            print(f"   📊 Cumul: {total_matches} matches, {total_goals} buts, {len(total_teams)} équipes")

            # Throttle respectueux
            time.sleep(2)

        except Exception as e:
            print(f"   ❌ Erreur scraping {league_name}: {e}")
            continue

    print("\n" + "=" * 80)
    print("PHASE 3 COMPLETE")
    print(f"✅ Total matches scrappés: {total_matches}")
    print(f"✅ Total buts: {total_goals}")
    print(f"✅ Total équipes: {len(total_teams)}")
    print("=" * 80)

    print("\n✅ Phase 3 finished. Historical data is now available for predictions.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(2)
