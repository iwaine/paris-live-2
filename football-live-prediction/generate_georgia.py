"""Génération rapide des profils Géorgie"""
from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
from analyzers.pattern_analyzer import PatternAnalyzer

print("="*70)
print("🇬🇪 GÉNÉRATION PROFILS GÉORGIE - LIGUE 2")
print("="*70)

scraper = SoccerStatsHistoricalScraper()
analyzer = PatternAnalyzer()

league_code = "georgia2"
league_name = "Erovnuli Liga 2"

print(f"\n🔄 Scraping {league_name}...")

# Scraper toutes les équipes
timing_data = scraper.scrape_timing_stats_all_venues(league_code)

if timing_data and 'overall' in timing_data:
    teams = list(timing_data['overall'].keys())
    print(f"\n✅ {len(teams)} équipes trouvées")
    
    profiles = []
    
    for i, team_name in enumerate(teams, 1):
        print(f"\n[{i}/{len(teams)}] {team_name}...")
        
        try:
            team_stats = scraper.scrape_team_stats(team_name, league_code)
            
            if team_stats:
                analysis = analyzer.analyze_team_profile(team_stats)
                analyzer.save_team_profile(analysis)
                profiles.append(analysis)
                print(f"  ✅ Profil créé")
            else:
                print(f"  ❌ Pas de stats")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    print(f"\n{'='*70}")
    print(f"✅ {len(profiles)} profils générés pour {league_name}")
    print(f"{'='*70}")
else:
    print("❌ Échec du scraping")

scraper.cleanup()
