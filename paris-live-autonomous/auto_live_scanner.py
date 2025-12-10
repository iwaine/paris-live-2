#!/usr/bin/env python3
"""
🔍 AUTO LIVE SCANNER - Monitoring Automatique SoccerStats
Scrape automatiquement les matchs live et applique nos conditions
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import os
from datetime import datetime

# Ajouter le chemin du module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'football-live-prediction'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'football-live-prediction/predictors'))
from live_goal_probability_predictor import LiveGoalProbabilityPredictor

# Configuration des ligues suivies avec leurs IDs SoccerStats
LEAGUES_CONFIG = {
    'france': {
        'id': 1,
        'name': 'France Ligue 1',
        'whitelist': 'whitelists/france_whitelist.json'
    },
    'germany': {
        'id': 2,
        'name': 'Germany Bundesliga',
        'whitelist': 'whitelists/germany_whitelist.json'
    },
    'germany2': {
        'id': 3,
        'name': 'Germany 2.Bundesliga',
        'whitelist': 'whitelists/germany2_whitelist.json'
    },
    'england': {
        'id': 4,
        'name': 'England Premier League',
        'whitelist': 'whitelists/england_whitelist.json'
    },
    'netherlands2': {
        'id': 12,
        'name': 'Netherlands Eerste Divisie',
        'whitelist': 'whitelists/netherlands2_whitelist.json'
    },
    'bolivia': {
        'id': 94,
        'name': 'Bolivia Division Profesional',
        'whitelist': 'whitelists/bolivia_whitelist.json'
    },
    'bulgaria': {
        'id': 18,
        'name': 'Bulgaria First League',
        'whitelist': 'whitelists/bulgaria_whitelist.json'
    },
    'portugal': {
        'id': 8,
        'name': 'Portugal Liga',
        'whitelist': 'whitelists/portugal_whitelist.json'
    }
}

# Intervalles à surveiller
INTERVALS = [
    {'start': 31, 'end': 45, 'period': '31-45'},
    {'start': 76, 'end': 90, 'period': '76-90'}
]

class AutoLiveScanner:
    def __init__(self):
        self.predictor = LiveGoalProbabilityPredictor()
        self.telegram_config = self.load_telegram_config()
        self.monitored_matches = set()  # Éviter les doublons
        
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
        """Scrape la page d'accueil SoccerStats pour détecter les matchs live"""
        print("\n🔍 Scraping des matchs live sur SoccerStats...")
        
        try:
            url = "https://www.soccerstats.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            live_matches = []
            
            # Chercher les matchs avec classe "live" ou contenant la minute
            # Structure type: <tr class="live"> ou texte contenant "45'" ou "87'"
            rows = soup.find_all('tr', class_=['live', 'inplay'])
            
            if not rows:
                # Alternative: chercher tous les rows et filtrer ceux avec une minute
                all_rows = soup.find_all('tr')
                for row in all_rows:
                    text = row.get_text()
                    # Détecter format minute: "87'" ou "45'" ou "HT" ou "2H 87'"
                    if "'" in text or 'HT' in text or '2H' in text:
                        rows.append(row)
            
            print(f"   Trouvé {len(rows)} lignes potentielles")
            
            for row in rows:
                try:
                    match_data = self.parse_live_match_row(row)
                    if match_data:
                        live_matches.append(match_data)
                except Exception as e:
                    continue
            
            return live_matches
            
        except Exception as e:
            print(f"❌ Erreur scraping: {e}")
            return []
    
    def parse_live_match_row(self, row):
        """Parse une ligne de match live"""
        cells = row.find_all('td')
        if len(cells) < 4:
            return None
        
        text = row.get_text()
        
        # Extraire la minute
        minute = None
        if "'" in text:
            # Format: "87'" ou "2H 87'"
            import re
            minute_match = re.search(r'(\d+)\'', text)
            if minute_match:
                minute = int(minute_match.group(1))
        
        if not minute:
            return None
        
        # Extraire équipes et score
        # Structure typique: [Ligue] [Équipe Domicile] [Score] [Équipe Extérieure] [Minute]
        home_team = None
        away_team = None
        home_score = 0
        away_score = 0
        league_name = None
        
        # Chercher les liens des équipes
        team_links = row.find_all('a', href=True)
        if len(team_links) >= 2:
            home_team = team_links[0].get_text(strip=True)
            away_team = team_links[1].get_text(strip=True)
        
        # Chercher le score (format: "2-1" ou "0-0")
        score_match = re.search(r'(\d+)\s*-\s*(\d+)', text)
        if score_match:
            home_score = int(score_match.group(1))
            away_score = int(score_match.group(2))
        
        # Identifier la ligue
        for league_key, league_info in LEAGUES_CONFIG.items():
            if league_info['name'].lower() in text.lower():
                league_name = league_key
                break
        
        if not home_team or not away_team or not league_name:
            return None
        
        return {
            'league': league_name,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'minute': minute
        }
    
    def check_interval(self, minute):
        """Vérifie si la minute est dans un intervalle à surveiller"""
        for interval in INTERVALS:
            if interval['start'] <= minute <= interval['end']:
                return interval['period']
        return None
    
    def analyze_match(self, match):
        """Analyse un match et envoie une alerte si conditions remplies"""
        
        # Vérifier l'intervalle
        period = self.check_interval(match['minute'])
        if not period:
            print(f"   ⏭️  {match['home_team']} vs {match['away_team']} - Minute {match['minute']} hors intervalles")
            return
        
        # Créer un ID unique pour éviter les doublons
        match_id = f"{match['league']}_{match['home_team']}_{match['away_team']}_{period}"
        if match_id in self.monitored_matches:
            return  # Déjà analysé
        
        print(f"\n⚽ ANALYSE: {match['home_team']} vs {match['away_team']}")
        print(f"   Ligue: {LEAGUES_CONFIG[match['league']]['name']}")
        print(f"   Minute: {match['minute']} (Intervalle {period})")
        print(f"   Score: {match['home_score']}-{match['away_score']}")
        
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
            print("   ❌ Analyse impossible")
            return
        
        # Afficher les résultats
        print(f"\n   📊 RÉSULTATS:")
        print(f"   • Probabilité: {result['probability']:.1f}%")
        print(f"   • Intervalle: {result['period']}")
        print(f"   • Équipe qualifiée: {result['qualified_team']}")
        print(f"   • Contexte: {result['context']}")
        
        # Récurrence totale
        if result['recurrence_totale']:
            rt = result['recurrence_totale']
            print(f"\n   📈 Récurrence Totale:")
            print(f"   • {rt['buts']}/{rt['total_matches']} matchs = {rt['taux']:.1f}%")
        
        # Récurrence récente
        if result['recurrence_recente']:
            rr = result['recurrence_recente']
            print(f"\n   🔥 Récurrence Récente (3 derniers matchs):")
            print(f"   • Buts marqués: {rr['buts_marques']}")
            print(f"   • Buts encaissés: {rr['buts_encaisses']}")
            print(f"   • Total buts: {rr['total_buts']}")
            print(f"   • Taux: {rr['taux']:.1f}%")
        
        # Saturation
        if result['saturation_factor'] < 1.0:
            print(f"\n   ⚠️  Saturation: {result['saturation_factor']:.2f} (total buts: {match['home_score'] + match['away_score']})")
        
        # Si probabilité ≥65% → Envoyer alerte Telegram
        if result['probability'] >= 65.0:
            print(f"\n   ✅ SIGNAL VALIDÉ ! (≥65%)")
            self.send_alert(match, result)
            self.monitored_matches.add(match_id)
        else:
            print(f"\n   ❌ Signal non qualifié ({result['probability']:.1f}% < 65%)")
    
    def send_alert(self, match, result):
        """Envoie une alerte Telegram formatée"""
        
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
        
        message = f"""
🚨 <b>SIGNAL DÉTECTÉ AUTOMATIQUEMENT</b> 🚨

⚽ <b>Match:</b> {match['home_team']} vs {match['away_team']}
🏆 <b>Ligue:</b> {LEAGUES_CONFIG[match['league']]['name']}
⏱ <b>Minute:</b> {match['minute']}' (Intervalle {result['period']})
📊 <b>Score actuel:</b> {match['home_score']}-{match['away_score']}

🎯 <b>PROBABILITÉ: {result['probability']:.1f}%</b>

📈 <b>Équipe qualifiée:</b> {result['qualified_team']}
🏠 <b>Contexte:</b> {result['context']}

📊 <b>Récurrence Totale:</b> {rt_text}
🔥 <b>Récurrence Récente:</b> {rr_text}{sat_text}

✅ <b>Signal validé ≥65%</b>
🕐 Détecté à {datetime.now().strftime('%H:%M:%S')}
"""
        
        if self.send_telegram(message):
            print("   📱 Alerte Telegram envoyée !")
        else:
            print("   ⚠️  Échec envoi Telegram")
    
    def run_scan(self):
        """Lance un scan complet"""
        print("\n" + "="*70)
        print("🚀 AUTO LIVE SCANNER - Démarrage")
        print("="*70)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Ligues surveillées: {len(LEAGUES_CONFIG)}")
        print(f"📊 Intervalles: 31-45' et 76-90'")
        print(f"✅ Seuil: ≥65%")
        print("="*70)
        
        # Scraper les matchs live
        live_matches = self.scrape_live_matches()
        
        if not live_matches:
            print("\n❌ Aucun match live détecté pour nos ligues")
            print("   Les matchs seront détectés quand ils seront en cours")
            return
        
        print(f"\n✅ {len(live_matches)} match(s) live détecté(s)\n")
        
        # Analyser chaque match
        for match in live_matches:
            try:
                self.analyze_match(match)
            except Exception as e:
                print(f"❌ Erreur analyse {match['home_team']} vs {match['away_team']}: {e}")
        
        print("\n" + "="*70)
        print("✅ Scan terminé")
        print("="*70)

def main():
    scanner = AutoLiveScanner()
    scanner.run_scan()

if __name__ == "__main__":
    main()
