import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper

scraper = SoccerStatsHistoricalScraper()

print("\n" + "="*60)
print("ÉQUIPES DISPONIBLES PAR LIGUE")
print("="*60)

leagues = [
    ('england', 'Premier League'),
    ('france', 'Ligue 1'),
    ('spain', 'La Liga')
]

for code, name in leagues:
    print(f"\n🏆 {name} ({code}):")
    df = scraper.scrape_timing_stats(code)
    if df is not None and not df.empty:
        teams = df['team'].tolist()
        for i, team in enumerate(teams, 1):
            print(f"   {i:2d}. {team}")
    else:
        print("   ❌ Aucune donnée")

scraper.cleanup()
