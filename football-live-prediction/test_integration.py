"""
Test d'intégration - Arsenal vs Man City avec forme récente
"""
from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
from scrapers.recent_form_complete import RecentFormCompleteScraper
from predictors.interval_predictor import IntervalPredictor
from utils.display_helper import display_prediction_result
import json

print("="*80)
print("🧪 TEST INTÉGRATION COMPLÈTE")
print("="*80)

# 1. Scraper historique
print("\n📊 Étape 1: Stats historiques...")
hist_scraper = SoccerStatsHistoricalScraper()

arsenal_hist = hist_scraper.scrape_team_stats('Arsenal', 'england')
mancity_hist = hist_scraper.scrape_team_stats('Manchester City', 'england')

if not arsenal_hist or not mancity_hist:
    print("❌ Erreur scraping historique")
    exit(1)

print("✅ Stats historiques chargées")

# 2. Scraper forme récente
print("\n📊 Étape 2: Forme récente par intervalle...")
form_scraper = RecentFormCompleteScraper()

arsenal_recent_home = form_scraper.scrape_team_recent_matches(
    'Arsenal', 'england', 'home', 4, 'u324'
)

mancity_recent_away = form_scraper.scrape_team_recent_matches(
    'Manchester City', 'england', 'away', 4, 'u321'
)

print(f"✅ Arsenal: {len(arsenal_recent_home)} matchs home")
print(f"✅ Man City: {len(mancity_recent_away)} matchs away")

# 3. Construire les profils complets
print("\n📊 Étape 3: Construction des profils...")

def build_complete_profile(hist_data, recent_matches, team_name):
    """Construit un profil complet avec forme récente"""
    profile = {
        'team': team_name,
        'league': 'England - Premier League',
        'overall': hist_data.get('overall', {}),
        'home': hist_data.get('home', {}),
        'away': hist_data.get('away', {})
    }
    
    # Ajouter forme récente par intervalle
    if recent_matches:
        aggregated = {}
        for interval in ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90']:
            total_scored = sum(m['scored_by_interval'].get(interval, 0) for m in recent_matches)
            total_conceded = sum(m['conceded_by_interval'].get(interval, 0) for m in recent_matches)
            
            aggregated[interval] = {
                'scored': total_scored,
                'conceded': total_conceded,
                'scored_avg': total_scored / len(recent_matches),
                'conceded_avg': total_conceded / len(recent_matches),
                'matches': len(recent_matches)
            }
        
        # Déterminer le venue
        venue = 'home' if recent_matches[0].get('venue') != 'away' else 'away'
        profile[venue]['recent_form_by_interval'] = aggregated
    
    return profile

arsenal_profile = build_complete_profile(arsenal_hist, arsenal_recent_home, 'Arsenal')
mancity_profile = build_complete_profile(mancity_hist, mancity_recent_away, 'Manchester City')

print("✅ Profils construits")

# 4. Sauvegarder les profils
print("\n📊 Étape 4: Sauvegarde...")
with open('data/team_profiles/arsenal_profile.json', 'w') as f:
    json.dump(arsenal_profile, f, indent=2)

with open('data/team_profiles/manchester_city_profile.json', 'w') as f:
    json.dump(mancity_profile, f, indent=2)

print("✅ Profils sauvegardés")

# 5. Test de prédiction
print("\n" + "="*80)
print("🎯 TEST DE PRÉDICTION")
print("="*80)

predictor = IntervalPredictor(profiles_dir='data/team_profiles')

live_stats = {'score': '1-1', 'minute': 65}

result = predictor.predict_match(
    home_team='Arsenal',
    away_team='Manchester City',
    current_minute=65,
    live_stats=live_stats
)

display_prediction_result(result, 'Arsenal', 'Manchester City')

# 6. Afficher les détails de forme récente
print("\n" + "="*80)
print("📊 FORME RÉCENTE PAR INTERVALLE")
print("="*80)

if 'recent_form_by_interval' in arsenal_profile['home']:
    print("\n🔴 Arsenal (Home) - Intervalle 61-75:")
    interval_data = arsenal_profile['home']['recent_form_by_interval']['61-75']
    print(f"   Marqués: {interval_data['scored']} buts ({interval_data['scored_avg']:.2f}/match)")
    print(f"   Encaissés: {interval_data['conceded']} buts ({interval_data['conceded_avg']:.2f}/match)")
    print(f"   Sur {interval_data['matches']} matchs")

if 'recent_form_by_interval' in mancity_profile['away']:
    print("\n🔵 Man City (Away) - Intervalle 61-75:")
    interval_data = mancity_profile['away']['recent_form_by_interval']['61-75']
    print(f"   Marqués: {interval_data['scored']} buts ({interval_data['scored_avg']:.2f}/match)")
    print(f"   Encaissés: {interval_data['conceded']} buts ({interval_data['conceded_avg']:.2f}/match)")
    print(f"   Sur {interval_data['matches']} matchs")

print("\n✅ TEST COMPLET TERMINÉ")
