#!/usr/bin/env python3
"""
🔄 MONITORING CONTINU AUTOMATIQUE
Détecte les matchs live et les suit avec mises à jour toutes les 60 secondes
Utilise SoccerStatsLiveScraper pour extraire les données
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import os
from datetime import datetime
import re

# Ajouter le chemin du module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'football-live-prediction'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'football-live-prediction/predictors'))
from live_goal_probability_predictor import LiveGoalProbabilityPredictor

# Importer le scraper live
try:
    from scrape_live_soccerstats import SoccerStatsLiveScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    print("⚠️  scrape_live_soccerstats.py non trouvé, scraping basique activé")
    SCRAPER_AVAILABLE = False

# Configuration des ligues suivies avec leurs IDs et URLs SoccerStats
LEAGUES_CONFIG = {
    'france': {
        'id': 1,
        'name': 'France Ligue 1',
        'whitelist': 'whitelists/france_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=france',
        'keywords': ['france', 'ligue 1', 'psg', 'marseille', 'lyon']
    },
    'germany': {
        'id': 2,
        'name': 'Germany Bundesliga',
        'whitelist': 'whitelists/germany_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=germany',
        'keywords': ['bundesliga', 'bayern', 'dortmund', 'leipzig']
    },
    'germany2': {
        'id': 3,
        'name': 'Germany 2.Bundesliga',
        'whitelist': 'whitelists/germany2_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=germany2',
        'keywords': ['2.bundesliga', '2. bundesliga']
    },
    'england': {
        'id': 4,
        'name': 'England Premier League',
        'whitelist': 'whitelists/england_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=england',
        'keywords': ['premier league', 'england', 'manchester', 'liverpool', 'chelsea']
    },
    'netherlands2': {
        'id': 12,
        'name': 'Netherlands Eerste Divisie',
        'whitelist': 'whitelists/netherlands2_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=netherlands2',
        'keywords': ['eerste divisie', 'netherlands']
    },
    'bolivia': {
        'id': 94,
        'name': 'Bolivia Division Profesional',
        'whitelist': 'whitelists/bolivia_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=bolivia',
        'keywords': ['bolivia', 'bolivar', 'strongest']
    },
    'bulgaria': {
        'id': 18,
        'name': 'Bulgaria First League',
        'whitelist': 'whitelists/bulgaria_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=bulgaria',
        'keywords': ['bulgaria', 'ludogorets', 'cska sofia']
    },
    'portugal': {
        'id': 8,
        'name': 'Portugal Liga',
        'whitelist': 'whitelists/portugal_whitelist.json',
        'soccerstats_url': 'https://www.soccerstats.com/latest.asp?league=portugal',
        'keywords': ['portugal', 'benfica', 'porto', 'sporting']
    }
}

# Intervalles à surveiller
INTERVALS = [
    {'start': 31, 'end': 45, 'period': '31-45'},
    {'start': 76, 'end': 90, 'period': '76-90'}
]

# Fréquence de mise à jour (secondes)
UPDATE_INTERVAL = 60

class ContinuousLiveMonitor:
    def __init__(self):
        self.predictor = LiveGoalProbabilityPredictor()
        self.telegram_config = self.load_telegram_config()
        self.tracked_matches = {}  # {match_id: {data, last_alert, interval}}
        self.alert_history = {}  # {match_id_period: [probabilities]}
        
        # Initialiser le scraper robuste si disponible
        if SCRAPER_AVAILABLE:
            self.live_scraper = SoccerStatsLiveScraper(throttle_seconds=3)
            print("✅ SoccerStatsLiveScraper initialisé")
        else:
            self.live_scraper = None
            print("⚠️  Mode scraping basique")
        
    def load_telegram_config(self):
        """Charge la configuration Telegram"""
        try:
            with open('telegram_config.json', 'r') as f:
                return json.load(f)
        except:
            print("⚠️  telegram_config.json non trouvé")
            return None
    
    def send_telegram(self, message):
        """Envoie un message Telegram"""
        if not self.telegram_config:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            data = {
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def scrape_live_matches(self):
        """Scrape les pages de ligues pour détecter les matchs live"""
        print("\n🔍 Scraping des matchs live...")
        
        all_live_matches = []
        
        for league_key, league_info in LEAGUES_CONFIG.items():
            try:
                # Scraper la page "latest" de chaque ligue
                url = league_info['soccerstats_url']
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Chercher les matchs "In-play" (en cours)
                # Structure SoccerStats: liens avec "pmatch.asp" et indicateur "In-play" ou minute
                links = soup.find_all('a', href=re.compile(r'pmatch\.asp'))
                
                for link in links:
                    # Vérifier si le match est live (chercher indicateur de minute dans les parents)
                    parent_row = link.find_parent('tr')
                    if not parent_row:
                        continue
                    
                    row_text = parent_row.get_text()
                    
                    # Détecter si en cours: "'" ou "In-play" ou "Live"
                    if "'" not in row_text and 'In-play' not in row_text and 'Live' not in row_text:
                        continue
                    
                    # Extraire l'URL complète du match
                    match_url = link.get('href')
                    if not match_url.startswith('http'):
                        match_url = f"https://www.soccerstats.com/{match_url}"
                    
                    # Scraper les détails du match avec le scraper robuste
                    if SCRAPER_AVAILABLE and self.live_scraper:
                        match_data = self.live_scraper.scrape_match(match_url)
                        
                        if match_data:
                            # Convertir en format compatible
                            live_match = {
                                'league': league_key,
                                'home_team': match_data.home_team,
                                'away_team': match_data.away_team,
                                'home_score': match_data.score_home,
                                'away_score': match_data.score_away,
                                'minute': match_data.minute or 0,
                                'match_url': match_url
                            }
                            all_live_matches.append(live_match)
                            print(f"   ✅ {league_info['name']}: {match_data.home_team} {match_data.score_home}-{match_data.score_away} {match_data.away_team} ({match_data.minute}')")
                
            except Exception as e:
                print(f"   ⚠️  {league_key}: {e}")
                continue
        
        return all_live_matches
    
    def check_interval(self, minute):
        """Vérifie si la minute est dans un intervalle à surveiller"""
        for interval in INTERVALS:
            if interval['start'] <= minute <= interval['end']:
                return interval['period']
        return None
    
    def get_match_id(self, match):
        """Génère un ID unique pour un match"""
        return f"{match['league']}_{match['home_team']}_{match['away_team']}"
    
    def analyze_and_track_match(self, match):
        """Analyse un match et le suit en continu s'il est dans un intervalle"""
        
        # Vérifier l'intervalle
        period = self.check_interval(match['minute'])
        if not period:
            return  # Hors intervalle
        
        match_id = self.get_match_id(match)
        match_period_id = f"{match_id}_{period}"
        
        # Charger la whitelist de la ligue
        try:
            with open(LEAGUES_CONFIG[match['league']]['whitelist'], 'r') as f:
                whitelist = json.load(f)
        except:
            print(f"   ❌ Whitelist non trouvée pour {match['league']}")
            return
        
        # Analyser avec le predictor
        result = self.predictor.predict_live_match(
            league_name=match['league'],
            home_team=match['home_team'],
            away_team=match['away_team'],
            current_minute=match['minute'],
            current_home_goals=match['home_score'],
            current_away_goals=match['away_score'],
            whitelist_data=whitelist
        )
        
        if not result:
            return
        
        # Initialiser l'historique si nouveau match
        if match_period_id not in self.alert_history:
            self.alert_history[match_period_id] = []
            # Premier signal pour ce match dans cet intervalle
            print(f"\n🆕 NOUVEAU MATCH DÉTECTÉ:")
            print(f"   {match['home_team']} vs {match['away_team']}")
            print(f"   Ligue: {LEAGUES_CONFIG[match['league']]['name']}")
            print(f"   Intervalle: {period}")
            print(f"   ➡️  Suivi activé (MAJ toutes les 60s)")
        
        # Afficher les résultats actuels
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"\n📊 [{current_time}] {match['home_team']} vs {match['away_team']}")
        print(f"   Minute: {match['minute']}' | Score: {match['home_score']}-{match['away_score']}")
        print(f"   Probabilité: {result['probability']:.1f}% | Intervalle: {period}")
        
        # Vérifier si changement significatif ou première alerte
        should_send_alert = False
        
        if len(self.alert_history[match_period_id]) == 0:
            # Première analyse de ce match dans cet intervalle
            if result['probability'] >= 65.0:
                should_send_alert = True
                print(f"   ✅ PREMIER SIGNAL (≥65%)")
        else:
            # Vérifier si changement significatif (±5% ou changement de seuil 65%)
            last_prob = self.alert_history[match_period_id][-1]
            prob_change = abs(result['probability'] - last_prob)
            
            # Alerte si:
            # 1. Passe au-dessus de 65% (était en dessous)
            # 2. Passe en dessous de 65% (était au-dessus)
            # 3. Changement ≥5% et toujours ≥65%
            crossed_threshold_up = last_prob < 65.0 and result['probability'] >= 65.0
            crossed_threshold_down = last_prob >= 65.0 and result['probability'] < 65.0
            significant_change = prob_change >= 5.0 and result['probability'] >= 65.0
            
            if crossed_threshold_up:
                should_send_alert = True
                print(f"   📈 SIGNAL ACTIVÉ ({last_prob:.1f}% → {result['probability']:.1f}%)")
            elif crossed_threshold_down:
                should_send_alert = True
                print(f"   📉 SIGNAL DÉSACTIVÉ ({last_prob:.1f}% → {result['probability']:.1f}%)")
            elif significant_change:
                should_send_alert = True
                print(f"   🔄 MAJ SIGNIFICATIVE (+{prob_change:.1f}%)")
            else:
                print(f"   ⏸️  Stable ({prob_change:.1f}% de variation)")
        
        # Ajouter à l'historique
        self.alert_history[match_period_id].append(result['probability'])
        
        # Envoyer l'alerte si nécessaire
        if should_send_alert:
            self.send_detailed_alert(match, result, period)
        
        # Mettre à jour le tracking
        self.tracked_matches[match_id] = {
            'match': match,
            'period': period,
            'last_update': datetime.now()
        }
    
    def send_detailed_alert(self, match, result, period):
        """Envoie une alerte Telegram détaillée"""
        
        # Récurrence totale
        rt_text = "N/A"
        if result['recurrence_totale']:
            rt = result['recurrence_totale']
            rt_text = f"{rt['buts']}/{rt['total_matches']} matchs ({rt['taux']:.1f}%)"
        
        # Récurrence récente
        rr_text = "N/A"
        if result['recurrence_recente']:
            rr = result['recurrence_recente']
            rr_text = f"{rr['total_buts']} buts sur 3 matchs ({rr['taux']:.1f}%)"
        
        # Saturation
        sat_text = ""
        if result['saturation_factor'] < 1.0:
            sat_text = f"\n⚠️ <b>Saturation:</b> {result['saturation_factor']:.2f}"
        
        # Statut du signal
        if result['probability'] >= 65.0:
            status = "✅ SIGNAL VALIDÉ"
            emoji = "🚨"
        else:
            status = "⚠️ SIGNAL DÉSACTIVÉ"
            emoji = "📉"
        
        # Historique de probabilité
        match_period_id = f"{self.get_match_id(match)}_{period}"
        history = self.alert_history.get(match_period_id, [])
        if len(history) > 1:
            history_text = f"\n📈 <b>Évolution:</b> {' → '.join([f'{p:.1f}%' for p in history[-3:]])}"
        else:
            history_text = ""
        
        message = f"""
{emoji} <b>MONITORING CONTINU - MAJ</b> {emoji}

⚽ <b>Match:</b> {match['home_team']} vs {match['away_team']}
🏆 <b>Ligue:</b> {LEAGUES_CONFIG[match['league']]['name']}
⏱ <b>Minute:</b> {match['minute']}' (Intervalle {period})
📊 <b>Score actuel:</b> {match['home_score']}-{match['away_score']}

🎯 <b>PROBABILITÉ: {result['probability']:.1f}%</b>

📈 <b>Équipe qualifiée:</b> {result['qualified_team']}
🏠 <b>Contexte:</b> {result['context']}

📊 <b>Récurrence Totale:</b> {rt_text}
🔥 <b>Récurrence Récente:</b> {rr_text}{sat_text}{history_text}

{status}
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        
        if self.send_telegram(message):
            print(f"   📱 Alerte Telegram envoyée !")
        else:
            print(f"   ⚠️  Échec envoi Telegram")
    
    def cleanup_finished_matches(self):
        """Nettoie les matchs qui ont quitté les intervalles surveillés"""
        to_remove = []
        for match_id, data in self.tracked_matches.items():
            match = data['match']
            period = self.check_interval(match['minute'])
            
            # Si le match n'est plus dans un intervalle surveillé
            if not period:
                to_remove.append(match_id)
                print(f"\n   ⏹️  Arrêt suivi: {match['home_team']} vs {match['away_team']} (hors intervalle)")
        
        for match_id in to_remove:
            del self.tracked_matches[match_id]
    
    def run_continuous(self, duration_minutes=None):
        """Lance le monitoring continu"""
        print("\n" + "="*70)
        print("🔄 MONITORING CONTINU AUTOMATIQUE")
        print("="*70)
        print(f"🕐 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Ligues: {len(LEAGUES_CONFIG)}")
        print(f"📊 Intervalles: 31-45' et 76-90'")
        print(f"🔄 Fréquence MAJ: {UPDATE_INTERVAL}s")
        print(f"✅ Seuil: ≥65%")
        if duration_minutes:
            print(f"⏱️  Durée: {duration_minutes} minutes")
        else:
            print(f"⏱️  Durée: Illimité (Ctrl+C pour arrêter)")
        print("="*70)
        
        start_time = datetime.now()
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                print(f"\n🔍 SCAN #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 70)
                
                # Scraper les matchs live
                live_matches = self.scrape_live_matches()
                
                if live_matches:
                    print(f"✅ {len(live_matches)} match(s) live détecté(s)")
                    
                    # Analyser et suivre chaque match
                    for match in live_matches:
                        try:
                            self.analyze_and_track_match(match)
                        except Exception as e:
                            print(f"❌ Erreur: {e}")
                else:
                    print("❌ Aucun match live pour nos ligues")
                
                # Nettoyer les matchs terminés
                self.cleanup_finished_matches()
                
                # Afficher le résumé
                if self.tracked_matches:
                    print(f"\n📌 {len(self.tracked_matches)} match(s) en suivi actif")
                
                # Vérifier la durée si limitée
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        print(f"\n⏱️  Durée atteinte ({duration_minutes} min)")
                        break
                
                # Attendre avant le prochain scan
                print(f"\n⏳ Prochain scan dans {UPDATE_INTERVAL}s...")
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Arrêt demandé (Ctrl+C)")
        
        # Résumé final
        print("\n" + "="*70)
        print("📊 RÉSUMÉ DE LA SESSION")
        print("="*70)
        print(f"🔍 Scans effectués: {scan_count}")
        print(f"⏱️  Durée totale: {(datetime.now() - start_time).total_seconds() / 60:.1f} min")
        print(f"⚽ Matchs suivis: {len(self.alert_history)}")
        
        if self.alert_history:
            print("\n📈 Historique des matchs:")
            for match_period_id, probs in self.alert_history.items():
                print(f"   • {match_period_id}: {len(probs)} mises à jour")
                if probs:
                    print(f"     Probabilité: {probs[0]:.1f}% → {probs[-1]:.1f}%")
        
        print("="*70)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring continu automatique')
    parser.add_argument('--duration', type=int, help='Durée en minutes (illimité par défaut)')
    args = parser.parse_args()
    
    monitor = ContinuousLiveMonitor()
    monitor.run_continuous(duration_minutes=args.duration)

if __name__ == "__main__":
    main()
