"""
Système de prédiction live complet
Combine le scraper live + les profils historiques + le prédicteur
"""
import sys
sys.path.insert(0, 'scrapers')
sys.path.insert(0, 'predictors')

from soccerstats_live import SoccerStatsLiveScraper
from interval_predictor import IntervalPredictor
import time


def main():
    print("="*70)
    print("🎯 SYSTÈME DE PRÉDICTION LIVE")
    print("="*70)

    # Initialiser
    scraper = SoccerStatsLiveScraper()
    predictor = IntervalPredictor()

    # URL du match (à adapter)
    match_url = input("\n📋 Entrez l'URL du match live: ").strip()

    print(f"\n🔄 Scraping initial...")

    # Premier scraping
    match_data = scraper.scrape_live_match(match_url)

    if not match_data:
        print("❌ Échec du scraping")
        return

    home_team = match_data.get('home_team')
    away_team = match_data.get('away_team')
    current_minute = match_data.get('current_minute')
    status = match_data.get('status')

    print(f"\n{'='*70}")
    print(f"🏆 MATCH: {home_team} vs {away_team}")
    print(f"⏱️  Minute: {current_minute}' | Statut: {status}")
    print(f"⚽ Score: {match_data.get('score')}")
    print(f"{'='*70}")

    # Afficher stats live
    stats = match_data.get('stats', {})
    if stats:
        print(f"\n📊 STATS LIVE:")
        for stat_name, values in stats.items():
            print(f"  {stat_name:25s}: {values['home']:6s} vs {values['away']:6s}")

    # PRÉDICTION
    if status == 'Live' and current_minute:
        print(f"\n{'='*70}")
        print("🎯 GÉNÉRATION DE LA PRÉDICTION")
        print(f"{'='*70}")
        
        prediction = predictor.predict_match(
            home_team=home_team,
            away_team=away_team,
            current_minute=current_minute,
            live_stats=stats
        )
        
        if prediction.get('success'):
            print(f"\n⏱️  Intervalle ACTUEL: {prediction['current_interval']}")
            print(f"🎯 Danger Score: {prediction['danger_score']}")
            print(f"📊 {prediction['interpretation']}")
            
            bet = prediction['bet_recommendation']
            print(f"\n💰 RECOMMANDATION:")
            print(f"   Confiance: {bet['confidence']}")
            print(f"   {bet['action']}")
            print(f"   Type: {bet['over_under']}")
            print(f"   Buteur probable: {bet['likely_scorer']}")
            print(f"   Prob. but domicile: {bet['home_goal_prob']}")
            print(f"   Prob. but extérieur: {bet['away_goal_prob']}")
        else:
            print(f"\n⚠️  {prediction.get('error')}")
    else:
        print(f"\n⚠️  Match pas en live ou minute non disponible")

    # Surveillance continue ?
    print(f"\n{'='*70}")
    response = input("🔴 Surveiller ce match en continu avec prédictions ? (o/n): ").strip().lower()

    if response in ['o', 'oui', 'y', 'yes']:
        def callback_with_prediction(data):
            minute = data.get('current_minute')
            status = data.get('status')
            score = data.get('score')
            
            print(f"\n{'='*70}")
            print(f"⚡ UPDATE [{data.get('scraped_at')}]")
            print(f"   Score: {score} @ {minute}' | Statut: {status}")
            
            # Prédiction si live
            if status == 'Live' and minute:
                pred = predictor.predict_match(home_team, away_team, minute, data.get('stats'))
                
                if pred.get('success'):
                    print(f"\n   🎯 Danger Score: {pred['danger_score']}")
                    print(f"   📊 {pred['interpretation']}")
                    print(f"   💰 {pred['bet_recommendation']['action']}")
            
            print(f"{'='*70}")
        
        scraper.monitor_match(match_url, interval=45, callback=callback_with_prediction)

    print("\n✅ Session terminée")


if __name__ == '__main__':
    main()
