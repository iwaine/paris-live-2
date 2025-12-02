"""
Test simple du main_live_predictor.py
Simule les données d'un match live sans web scraping
"""
import sys
sys.path.insert(0, 'scrapers')
sys.path.insert(0, 'predictors')

from interval_predictor import IntervalPredictor

print("="*70)
print("🧪 TEST MAIN PREDICTOR - Simulation Match Live")
print("="*70)

# Initialiser le prédicteur
predictor = IntervalPredictor()

# Données de match simulées
home_team = "Arsenal"
away_team = "Manchester City"
current_minute = 65
current_score = "1-1"

print(f"\n📋 Match simulé:")
print(f"   {home_team} vs {away_team}")
print(f"   Minute: {current_minute}'")
print(f"   Score: {current_score}")

# Stats de match
stats = {
    'shots': {'home': '8', 'away': '6'},
    'shots_on_target': {'home': '4', 'away': '3'},
    'possession': {'home': '55%', 'away': '45%'},
    'fouls': {'home': '12', 'away': '10'},
}

print(f"\n📊 Stats live du match:")
for stat_name, values in stats.items():
    print(f"   {stat_name:20s}: {values['home']:6s} vs {values['away']:6s}")

# PRÉDICTION
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
    print(f"\n✅ Prédiction réussie!")
    print(f"\n⏱️  Intervalle ACTUEL: {prediction['current_interval']}")
    print(f"🎯 Danger Score: {prediction['danger_score']:.2f}")
    print(f"📊 Interprétation: {prediction['interpretation']}")
    
    details = prediction.get('details', {})
    print(f"\n📈 DÉTAILS:")
    print(f"   Attaque {home_team}: {details.get('home_attack_rate', 0):.2f} buts/match")
    print(f"   Défense adverse: {details.get('away_defense_weakness', 0):.2f} buts/match")
    print(f"   Boost forme {home_team}: {details.get('home_form_boost', 1.0):.2f}x")
    print(f"   Saturation: {details.get('saturation_factor', 1.0):.2f}x")
    
    bet = prediction['bet_recommendation']
    print(f"\n💰 RECOMMANDATION:")
    print(f"   Confiance: {bet['confidence']}")
    print(f"   Action: {bet['action']}")
    print(f"   Type: {bet['over_under']}")
    print(f"   Buteur probable: {bet['likely_scorer']}")
    print(f"   Prob. but {home_team}: {bet['home_goal_prob']}")
    print(f"   Prob. but {away_team}: {bet['away_goal_prob']}")
    print(f"   Minutes restantes: {bet['minutes_left_in_interval']}")
else:
    print(f"\n❌ Erreur: {prediction.get('error')}")

print(f"\n{'='*70}")
print("✅ Test terminé avec succès!")
print(f"{'='*70}")
