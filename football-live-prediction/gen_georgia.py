from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
from analyzers.pattern_analyzer import PatternAnalyzer

print("="*70)
print("GENERATION PROFILS GEORGIE - LIGUE 2")
print("="*70)

scraper = SoccerStatsHistoricalScraper()
analyzer = PatternAnalyzer()

league_code = "georgia2"
league_name = "Erovnuli Liga 2"

print(f"\nScraping {league_name}...")

timing_data = scraper.scrape_timing_stats_all_venues(league_code)

if timing_data and 'overall' in timing_data:
    overall_df = timing_data['overall']
    
    if 'team' in overall_df.columns:
        teams = overall_df['team'].tolist()
    else:
        teams = overall_df[overall_df.columns[0]].tolist()
    
    print(f"\n{len(teams)} equipes trouvees:")
    for team in teams:
        print(f"   - {team}")
    
    profiles = []
    
    for i, team_name in enumerate(teams, 1):
        print(f"\n[{i}/{len(teams)}] {team_name}...")
        
        try:
            team_stats = scraper.scrape_team_stats(team_name, league_code)
            
            if team_stats:
                analysis = analyzer.analyze_team_profile(team_stats)
                analyzer.save_team_profile(analysis)
                profiles.append(analysis)
                print(f"  OK")
            else:
                print(f"  Pas de stats")
        except Exception as e:
            print(f"  Erreur: {e}")
    
    print(f"\n{'='*70}")
    print(f"{len(profiles)} profils generes")
else:
    print("Echec du scraping")

scraper.cleanup()
