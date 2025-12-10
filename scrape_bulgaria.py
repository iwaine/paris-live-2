#!/usr/bin/env python3
"""
Script rapide pour scraper les données historiques de la Bulgarie
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "football-live-prediction"))

from utils.database_manager import DatabaseManager
from scrapers.match_history_scraper import MatchHistoryScraper

def main():
    print("\n" + "=" * 80)
    print("🇧🇬 SCRAPING BULGARIA - Parva Liga")
    print("=" * 80)

    # Initialiser DB et scraper
    db = DatabaseManager(db_path="football-live-prediction/data/predictions.db")
    scraper = MatchHistoryScraper()

    league_code = "bulgaria"
    max_matches = 100  # Suffisant pour créer des patterns

    print(f"\n🔄 Scraping Bulgaria ({league_code})...")
    print(f"   Target: {max_matches} matches\n")

    try:
        matches = scraper.scrape_league_matches(league_code, max_matches=max_matches)

        if not matches:
            print(f"   ❌ Aucun match scrappé pour Bulgaria")
            return

        print(f"   ✅ {len(matches)} matches scrappés")

        # Insérer dans la base
        total_inserted = 0
        total_goals = 0
        teams = set()

        for i, match in enumerate(matches, 1):
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
                    total_inserted += 1
                    total_goals += match.get("home_goals", 0) + match.get("away_goals", 0)
                    teams.add(match.get("home_team"))
                    teams.add(match.get("away_team"))

                    if i % 10 == 0:
                        print(f"   Progression: {i}/{len(matches)} matches insérés...")

            except Exception as e:
                print(f"   ⚠️ Erreur insertion {match.get('home_team')} vs {match.get('away_team')}: {e}")
                continue

        print(f"\n   📊 RÉSULTAT:")
        print(f"      Matches insérés: {total_inserted}")
        print(f"      Buts totaux: {total_goals}")
        print(f"      Équipes uniques: {len(teams)}")
        print(f"      Équipes: {', '.join(sorted(teams)[:10])}...")

        print("\n✅ SCRAPING TERMINÉ!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
