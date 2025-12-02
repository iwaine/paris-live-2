#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
import json

scraper = SoccerStatsHistoricalScraper()

print("\n" + "="*60)
print("🔍 DEBUG : STRUCTURE DES DONNÉES")
print("="*60 + "\n")

# Tester avec Manchester City
print("📊 Test avec Manchester City...\n")

team_stats = scraper.scrape_team_stats("Manchester City", "england")

if team_stats:
    print("✅ Données reçues!\n")
    print("📋 Structure des données:")
    print("-" * 60)
    print(json.dumps(team_stats, indent=2, default=str))
    print("-" * 60)
    
    print("\n🔑 Clés disponibles:")
    for key in team_stats.keys():
        print(f"   • {key}")
else:
    print("❌ Aucune donnée reçue")

scraper.cleanup()
