"""
🌐 DASHBOARD WEB TEMPS RÉEL
Interface web pour visualiser les matchs live et les probabilités
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import os
import sys
from datetime import datetime
from threading import Thread, Lock
import time
import requests
from bs4 import BeautifulSoup
import re

# Ajouter le chemin du module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'football-live-prediction'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'football-live-prediction/predictors'))

try:
    from live_goal_probability_predictor import LiveGoalProbabilityPredictor
    from scrape_live_soccerstats import SoccerStatsLiveScraper
    PREDICTORS_AVAILABLE = True
except ImportError:
    PREDICTORS_AVAILABLE = False
    print("⚠️  Modules de prédiction non disponibles")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'paris-live-dashboard-secret-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# État global du dashboard
dashboard_state = {
    'live_matches': [],
    'signals_history': [],
    'monitoring_active': False,
    'last_update': None,
    'stats': {
        'total_scans': 0,
        'matches_detected': 0,
        'signals_sent': 0,
        'avg_probability': 0
    }
}
state_lock = Lock()

# Configuration des ligues
LEAGUES_CONFIG = {
    'australia': {'name': 'Australia A-League', 'whitelist': 'whitelists/australia_whitelist.json'},
    'france': {'name': 'France Ligue 1', 'whitelist': 'whitelists/france_whitelist.json'},
    'germany': {'name': 'Germany Bundesliga', 'whitelist': 'whitelists/germany_whitelist.json'},
    'germany2': {'name': 'Germany 2.Bundesliga', 'whitelist': 'whitelists/germany2_whitelist.json'},
    'england': {'name': 'England Premier League', 'whitelist': 'whitelists/england_whitelist.json'},
    'netherlands2': {'name': 'Netherlands Eerste Divisie', 'whitelist': 'whitelists/netherlands2_whitelist.json'},
    'bolivia': {'name': 'Bolivia Division Profesional', 'whitelist': 'whitelists/bolivia_whitelist.json'},
    'bulgaria': {'name': 'Bulgaria First League', 'whitelist': 'whitelists/bulgaria_whitelist.json'},
    'portugal': {'name': 'Portugal Liga', 'whitelist': 'whitelists/portugal_whitelist.json'}
}

class DashboardMonitor:
    """Monitoring en arrière-plan pour le dashboard"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        if PREDICTORS_AVAILABLE:
            self.predictor = LiveGoalProbabilityPredictor()
            self.scraper = SoccerStatsLiveScraper(throttle_seconds=3)
        else:
            self.predictor = None
            self.scraper = None
    
    def start(self):
        """Démarre le monitoring"""
        if self.running:
            return False
        
        self.running = True
        self.thread = Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop(self):
        """Arrête le monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Boucle de monitoring principale"""
        global dashboard_state
        
        while self.running:
            try:
                with state_lock:
                    dashboard_state['stats']['total_scans'] += 1
                
                # Scraper les matchs live (simulation pour l'instant)
                live_matches = self._scan_live_matches()
                
                with state_lock:
                    dashboard_state['live_matches'] = live_matches
                    dashboard_state['last_update'] = datetime.now().isoformat()
                    dashboard_state['stats']['matches_detected'] = len(live_matches)
                
                # Émettre mise à jour via WebSocket
                socketio.emit('matches_update', {
                    'matches': live_matches,
                    'timestamp': datetime.now().isoformat(),
                    'stats': dashboard_state['stats']
                })
                
                # Attendre 60 secondes
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Erreur monitoring: {e}")
                time.sleep(5)
    
    def _scan_live_matches(self):
        """Scanne les matchs live avec le vrai scraper SoccerStats"""
        matches = []
        
        if not self.scraper or not self.predictor:
            return matches
        
        # Scraper chaque ligue
        for league_key, league_info in LEAGUES_CONFIG.items():
            try:
                # Scraper la page "latest" de la ligue
                url = f"https://www.soccerstats.com/latest.asp?league={league_key}"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                
                response = requests.get(url, headers=headers, timeout=15)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Chercher les matchs "In-play"
                import re
                links = soup.find_all('a', href=re.compile(r'pmatch\.asp'))
                
                for link in links:
                    parent_row = link.find_parent('tr')
                    if not parent_row:
                        continue
                    
                    row_text = parent_row.get_text()
                    
                    # Détecter si en cours
                    if "'" not in row_text and 'In-play' not in row_text and 'Live' not in row_text:
                        continue
                    
                    # Extraire l'URL du match
                    match_url = link.get('href')
                    if not match_url.startswith('http'):
                        match_url = f"https://www.soccerstats.com/{match_url}"
                    
                    # Scraper le match complet
                    match_data = self.scraper.scrape_match(match_url)
                    
                    if match_data and match_data.minute:
                        # Vérifier l'intervalle
                        interval = None
                        if 31 <= match_data.minute <= 45:
                            interval = '31-45'
                        elif 76 <= match_data.minute <= 90:
                            interval = '76-90'
                        
                        if interval:
                            # Charger whitelist
                            try:
                                with open(league_info['whitelist'], 'r') as f:
                                    whitelist = json.load(f)
                                
                                # Analyser avec le predictor
                                result = self.predictor.predict_live_match(
                                    league_name=league_key,
                                    home_team=match_data.home_team,
                                    away_team=match_data.away_team,
                                    current_minute=match_data.minute,
                                    current_home_goals=match_data.score_home,
                                    current_away_goals=match_data.score_away,
                                    whitelist_data=whitelist
                                )
                                
                                if result:
                                    match_id = f"{league_key}_{match_data.home_team}_{match_data.away_team}".replace(' ', '_')
                                    matches.append({
                                        'id': match_id,
                                        'league': league_key,
                                        'league_name': league_info['name'],
                                        'home_team': match_data.home_team,
                                        'away_team': match_data.away_team,
                                        'home_score': match_data.score_home,
                                        'away_score': match_data.score_away,
                                        'minute': match_data.minute,
                                        'probability': result['probability'],
                                        'interval': interval,
                                        'status': 'qualified' if result['probability'] >= 65 else 'monitoring',
                                        'last_update': datetime.now().isoformat()
                                    })
                            except Exception as e:
                                print(f"⚠️ Erreur analyse {match_data.home_team}: {e}")
                                continue
                            
            except Exception as e:
                print(f"⚠️ Erreur scraping {league_key}: {e}")
                continue
        
        return matches

# Instance du moniteur
monitor = DashboardMonitor()

@app.route('/')
def index():
    """Page principale du dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API: État du système"""
    with state_lock:
        return jsonify({
            'monitoring_active': dashboard_state['monitoring_active'],
            'last_update': dashboard_state['last_update'],
            'stats': dashboard_state['stats'],
            'predictors_available': PREDICTORS_AVAILABLE
        })

@app.route('/api/matches')
def api_matches():
    """API: Liste des matchs live"""
    with state_lock:
        return jsonify({
            'matches': dashboard_state['live_matches'],
            'count': len(dashboard_state['live_matches'])
        })

@app.route('/api/signals')
def api_signals():
    """API: Historique des signaux"""
    with state_lock:
        return jsonify({
            'signals': dashboard_state['signals_history'][-50:],  # 50 derniers
            'count': len(dashboard_state['signals_history'])
        })

@app.route('/api/whitelists')
def api_whitelists():
    """API: Statistiques des whitelists"""
    whitelists_stats = {}
    
    for league_key, league_info in LEAGUES_CONFIG.items():
        try:
            with open(league_info['whitelist'], 'r') as f:
                whitelist = json.load(f)
                whitelists_stats[league_key] = {
                    'name': league_info['name'],
                    'teams_count': len(whitelist.get('qualified_teams', [])),
                    'threshold': whitelist.get('threshold', 65),
                    'min_matches': whitelist.get('min_matches', 4)
                }
        except:
            whitelists_stats[league_key] = {
                'name': league_info['name'],
                'teams_count': 0,
                'error': 'Non trouvée'
            }
    
    return jsonify(whitelists_stats)

@socketio.on('connect')
def handle_connect():
    """WebSocket: Connexion client"""
    print(f"🔌 Client connecté: {request.sid}")
    emit('connected', {'message': 'Connecté au dashboard'})
    
    # Envoyer l'état actuel
    with state_lock:
        emit('matches_update', {
            'matches': dashboard_state['live_matches'],
            'timestamp': datetime.now().isoformat(),
            'stats': dashboard_state['stats']
        })

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket: Déconnexion client"""
    print(f"🔌 Client déconnecté: {request.sid}")

@socketio.on('start_monitoring')
def handle_start_monitoring():
    """WebSocket: Démarrer le monitoring"""
    global dashboard_state
    
    if monitor.start():
        with state_lock:
            dashboard_state['monitoring_active'] = True
        emit('monitoring_status', {'active': True, 'message': 'Monitoring démarré'}, broadcast=True)
        print("✅ Monitoring démarré")
    else:
        emit('monitoring_status', {'active': False, 'message': 'Monitoring déjà actif'})

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """WebSocket: Arrêter le monitoring"""
    global dashboard_state
    
    monitor.stop()
    with state_lock:
        dashboard_state['monitoring_active'] = False
    emit('monitoring_status', {'active': False, 'message': 'Monitoring arrêté'}, broadcast=True)
    print("⏹️  Monitoring arrêté")

@socketio.on('add_signal')
def handle_add_signal(data):
    """WebSocket: Ajouter un signal à l'historique"""
    global dashboard_state
    
    signal = {
        'timestamp': datetime.now().isoformat(),
        'match': data.get('match', ''),
        'probability': data.get('probability', 0),
        'interval': data.get('interval', ''),
        'result': data.get('result', 'pending')
    }
    
    with state_lock:
        dashboard_state['signals_history'].append(signal)
        dashboard_state['stats']['signals_sent'] += 1
        
        # Calculer probabilité moyenne
        if dashboard_state['signals_history']:
            avg = sum(s['probability'] for s in dashboard_state['signals_history']) / len(dashboard_state['signals_history'])
            dashboard_state['stats']['avg_probability'] = round(avg, 1)
    
    emit('signal_added', signal, broadcast=True)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌐 DASHBOARD WEB - Démarrage")
    print("="*70)
    print(f"📡 URL: http://localhost:5000")
    print(f"🔄 WebSocket: Activé")
    print(f"🎯 Ligues: {len(LEAGUES_CONFIG)}")
    print(f"✅ Prédicteurs: {'Disponibles' if PREDICTORS_AVAILABLE else 'Indisponibles'}")
    print("="*70)
    print("\n💡 Ouvrez http://localhost:5000 dans votre navigateur")
    print("⏸️  Ctrl+C pour arrêter\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
