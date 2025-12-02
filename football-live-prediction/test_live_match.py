"""Test avec le match live en Géorgie"""
import sys
sys.path.insert(0, 'scrapers')
from soccerstats_live import SoccerStatsLiveScraper

# URL du match LIVE
live_url = "https://www.soccerstats.com/pmatch.asp?league=georgia2&stats=263-5-4-2025"

print("="*70)
print("🔴 TEST AVEC MATCH LIVE EN GÉORGIE")
print("="*70)

scraper = SoccerStatsLiveScraper()

# Scraping unique
print("\n📊 Scraping des données live...")
match_data = scraper.scrape_live_match(live_url)

if match_data:
    print(f"\n✅ DONNÉES EXTRAITES:")
    print(f"  🏠 Domicile: {match_data.get('home_team', 'N/A')}")
    print(f"  ✈️  Extérieur: {match_data.get('away_team', 'N/A')}")
    print(f"  ⚽ Score: {match_data.get('score', 'N/A')}")
    print(f"  ⏱️  Minute: {match_data.get('current_minute', 'N/A')}'")
    print(f"  📡 Statut: {match_data.get('status', 'N/A')}")
    
    stats = match_data.get('stats', {})
    if stats:
        print(f"\n📊 STATISTIQUES LIVE ({len(stats)} catégories):")
        for stat_name, values in stats.items():
            print(f"  {stat_name:25s}: {values['home']:6s} vs {values['away']:6s}")
    else:
        print("\n⚠️  Aucune stat extraite")
    
    # Si le match est live, proposer la surveillance
    if match_data.get('status') == 'Live':
        print("\n" + "="*70)
        response = input("🔴 Surveiller ce match en continu ? (o/n): ")
        
        if response.lower() in ['o', 'oui', 'y', 'yes']:
            def callback(data):
                print(f"\n⚡ UPDATE [{data.get('scraped_at', 'N/A')}]")
                print(f"   Score: {data.get('score', 'N/A')} @ {data.get('current_minute', 'N/A')}'")
                print(f"   Statut: {data.get('status', 'N/A')}")
                
                # Afficher changements de stats
                new_stats = data.get('stats', {})
                if 'Possession' in new_stats:
                    print(f"   Possession: {new_stats['Possession']['home']} vs {new_stats['Possession']['away']}")
                if 'Total shots' in new_stats:
                    print(f"   Tirs: {new_stats['Total shots']['home']} vs {new_stats['Total shots']['away']}")
            
            scraper.monitor_match(live_url, interval=45, callback=callback)
    else:
        print(f"\n⚠️  Match pas en live (statut: {match_data.get('status')})")
else:
    print("\n❌ Échec de l'extraction")

print("\n" + "="*70)
