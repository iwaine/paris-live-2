#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper

scraper = SoccerStatsHistoricalScraper()

leagues = [
    ('england', 'Premier League'),
    ('france', 'Ligue 1'), 
    ('spain', 'La Liga')
]

for code, name in leagues:
    print(f"\n{'='*60}")
    print(f"🏆 {name} ({code})")
    print('='*60)
    
    df = scraper.scrape_timing_stats(code)
    if df is not None and not df.empty:
        teams = sorted(df['team'].tolist())
        for i, team in enumerate(teams, 1):
            print(f"{i:2d}. {team}")
    else:
        print("❌ Erreur")

scraper.cleanup()
