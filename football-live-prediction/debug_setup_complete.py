#!/usr/bin/env python3
"""Test du setup_profiles corrigé"""

import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path("/home/claude/football-live-prediction")
sys.path.insert(0, str(project_root))

from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
from analyzers.pattern_analyzer import PatternAnalyzer
from utils.config_loader import get_config

print("\n" + "=" * 60)
print("TEST SETUP_PROFILES - MÉTHODES DISPONIBLES")
print("=" * 60 + "\n")

# Charger config
config = get_config()

# Créer instances
scraper = SoccerStatsHistoricalScraper()
analyzer = PatternAnalyzer()

print("✅ Config chargée")
print("✅ Scraper créé")
print("✅ Analyzer créé\n")

# Test 1: Charger test_teams
print("=" * 60)
print("TEST 1: Charger test_teams")
print("=" * 60)
test_teams = config.get_test_teams()
print(f"✓ {len(test_teams)} équipes de test chargées")
for team in test_teams:
    # Gérer les deux formats possibles
    team_name = team.get('name', team.get('team_name', str(team)))
    league_code = team.get('league_code', 'unknown')
    print(f"   • {team_name} (league_code: {league_code})")

# Test 2: Vérifier méthode scrape_team_stats
print("\n" + "=" * 60)
print("TEST 2: Vérifier scrape_team_stats")
print("=" * 60)
if hasattr(scraper, 'scrape_team_stats'):
    print("✅ scrape_team_stats() existe")
else:
    print("❌ scrape_team_stats() manquante")
    sys.exit(1)

# Test 3: Essayer de scraper une équipe
print("\n" + "=" * 60)
print("TEST 3: Scraper une équipe (Manchester United)")
print("=" * 60)
print("⏳ Cela va prendre ~5 secondes...")

try:
    team_stats = scraper.scrape_team_stats("Manchester United", "england")
    
    if team_stats:
        print("✅ Scraping réussi!")
        print(f"   • Équipe: {team_stats.get('team', 'N/A')}")
        print(f"   • Matchs: {team_stats.get('gp', 'N/A')}")
        print(f"   • Intervalles: {len(team_stats.get('goals_by_interval', {}))}")
    else:
        print("⚠️  Scraping retourné None")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Tester l'analyzer
print("\n" + "=" * 60)
print("TEST 4: Analyzer")
print("=" * 60)

team_stats = None
if team_stats and team_stats:
    try:
        analysis = analyzer.analyze_team_profile(team_stats)
        print("✅ Analyse réussie!")
        print(f"   • Équipe: {analysis.get('team', 'N/A')}")
        print(f"   • Zones de danger: {len(analysis.get('danger_zones', []))}")
        print(f"   • Style: {analysis.get('play_style', {}).get('summary', 'N/A')}")
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")

# Cleanup
scraper.cleanup()

print("\n" + "=" * 60)
print("✅ TESTS TERMINÉS")
print("=" * 60 + "\n")
