#!/usr/bin/env python3
"""
MONITOR LIVE avec PATTERNS HISTORIQUES + TELEGRAM ALERTS

Ce script:
1. Détecte les matches live des ligues suivies
2. Scrape les données en temps réel
3. Prédit la probabilité de but avec patterns historiques
4. Envoie des alertes Telegram enrichies pour prise de décision

Ligues suivies:
- france (Ligue 1)
- germany (Bundesliga)
- germany2 (Bundesliga 2)
- england (Premier League)
- spain (La Liga)
- italy (Serie A)
- bulgaria (Parva Liga)
- bolivia
- netherlands2
"""

import sys
import time
import threading
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

# Ajouter les chemins
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "football-live-prediction"))

from soccerstats_live_selector import get_live_matches
from soccerstats_live_scraper import SoccerStatsLiveScraper

try:
    from predictors.live_goal_probability_predictor import predict_goal
except ImportError:
    from football_live_prediction.predictors.live_goal_probability_predictor import predict_goal

# Configuration
FOLLOWED_LEAGUES = ['france', 'germany', 'germany2', 'england', 'spain', 'italy', 'bulgaria', 'bolivia', 'netherlands2']
DETECTION_INTERVAL = 30  # secondes entre détections de nouveaux matches
MATCH_INTERVAL = 10  # secondes entre scrapes par match
GOAL_PROBABILITY_THRESHOLD = 0.50  # 50% = seuil d'alerte
CRITICAL_THRESHOLD = 0.70  # 70% = alerte critique

# INTERVALLES CRITIQUES (patterns validés)
CRITICAL_INTERVALS = [
    (31, 47),  # 31-45 + temps additionnel (jusqu'à 47')
    (76, 95),  # 76-90 + temps additionnel (jusqu'à 95')
]


class MatchMonitor(threading.Thread):
    """Monitor un match spécifique et affiche les prédictions"""

    def __init__(self, url: str, match_info: str, league: str):
        super().__init__(daemon=True)
        self.url = url
        self.match_info = match_info
        self.league = league
        self.scraper = SoccerStatsLiveScraper()
        self._stop = threading.Event()
        self.last_minute = None
        self.alert_sent = {}

    def stop(self):
        self._stop.set()

    def run(self):
        """Boucle de monitoring"""
        print(f"🟢 Monitor démarré: {self.match_info}")
        
        while not self._stop.is_set():
            try:
                data = self.scraper.scrape_match(self.url)
                if data:
                    d = data.to_dict()
                    d['url'] = self.url
                    
                    current_minute = d.get('minute', 0)
                    
                    # VÉRIFIER SI ON EST DANS UN INTERVALLE CRITIQUE
                    in_critical_interval = False
                    for min_start, min_end in CRITICAL_INTERVALS:
                        if min_start <= current_minute <= min_end:
                            in_critical_interval = True
                            break
                    
                    # Ne monitorer QUE les intervalles critiques (31-47 et 76-95)
                    if not in_critical_interval:
                        # Pas dans intervalle critique, attendre
                        if current_minute != self.last_minute:
                            self.last_minute = current_minute
                            ts = datetime.now().strftime("%H:%M:%S")
                            match_str = f"{d.get('home_team')} {d.get('score_home')}:{d.get('score_away')} {d.get('away_team')}"
                            print(f"[{ts}] ⏸️  {match_str} | min={current_minute}' | Hors intervalle critique (31-47 ou 76-95)")
                        time.sleep(MATCH_INTERVAL)
                        continue
                    
                    # Ne prédire que si la minute a changé (éviter spam)
                    if current_minute != self.last_minute:
                        self.last_minute = current_minute
                        
                        # Prédire la probabilité de but
                        prediction = predict_goal(None, d.get('home_team'), d.get('away_team'), d)
                        goal_prob = prediction.get('goal_probability', 0) / 100
                        danger_level = prediction.get('danger_level', 'LOW')
                        
                        # Affichage console
                        ts = datetime.now().strftime("%H:%M:%S")
                        match_str = f"{d.get('home_team')} {d.get('score_home')}:{d.get('score_away')} {d.get('away_team')}"
                        
                        # Couleurs selon niveau de danger
                        if danger_level == 'CRITICAL':
                            icon = "🔴"
                        elif danger_level == 'HIGH':
                            icon = "🟠"
                        elif danger_level == 'MEDIUM':
                            icon = "🟡"
                        else:
                            icon = "🟢"
                        
                        details = prediction.get('details', {})
                        base_rate = details.get('base_rate', 0)
                        historical_comp = details.get('historical_component', base_rate)
                        live_mult = details.get('live_multiplier', 1.0)
                        
                        print(f"[{ts}] {icon} {match_str} | min={current_minute}' | "
                              f"Prob={goal_prob*100:.1f}% [{danger_level}] | "
                              f"Hist={historical_comp*100:.1f}% (80%) | Live={live_mult:.2f}x (20%) | "
                              f"Poss={d.get('possession_home')}%-{d.get('possession_away')}% | "
                              f"DA={d.get('dangerous_attacks_home')}-{d.get('dangerous_attacks_away')}")
                        
                        # Alerte si seuil atteint
                        if goal_prob >= GOAL_PROBABILITY_THRESHOLD:
                            alert_key = f"{current_minute}_{int(goal_prob*100)}"
                            if alert_key not in self.alert_sent:
                                self._send_alert(match_str, current_minute, goal_prob, danger_level, d, prediction)
                                self.alert_sent[alert_key] = time.time()
                
                time.sleep(MATCH_INTERVAL)
                
            except Exception as e:
                print(f"⚠️ Erreur monitor {self.match_info}: {e}")
                time.sleep(MATCH_INTERVAL)

    def _send_alert(self, match_str: str, minute: int, goal_prob: float, danger_level: str, 
                    match_data: Dict, prediction: Dict):
        """Affiche une alerte détaillée"""
        print("\n" + "="*100)
        print(f"🚨 ALERTE BUT - {danger_level}")
        print("="*100)
        print(f"⚽ Match: {match_str}")
        print(f"⏱️  Minute: {minute}'")
        print(f"🔥 Probabilité de but: {goal_prob*100:.1f}%")
        print(f"🎯 Niveau de danger: {danger_level}")
        
        details = prediction.get('details', {})
        
        print(f"\n📊 ANALYSE DÉTAILLÉE (80% HISTORIQUE + 20% LIVE):")
        print("-"*100)
        
        # Composante historique (80%)
        base_rate = details.get('base_rate', 0)
        historical_comp = details.get('historical_component', base_rate)
        print(f"\n🏛️  COMPOSANTE HISTORIQUE (80% du calcul):")
        print(f"   • Base rate patterns {self.league.upper()}: {base_rate*100:.1f}%")
        print(f"   • Récurrence historique intervalle {details.get('interval', 'N/A')}")
        print(f"   • Données: {match_data.get('home_team')} + {match_data.get('away_team')}")
        print(f"   ➜ Impact historique: {historical_comp*100:.1f}%")
        
        # Composante live (20%)
        live_mult = details.get('live_multiplier', 1.0)
        live_adj = details.get('live_adjustment', 0)
        print(f"\n📡 COMPOSANTE LIVE (20% du calcul):")
        print(f"   • Possession: {match_data.get('possession_home')}% - {match_data.get('possession_away')}% (factor: {details.get('possession_factor', 1):.2f}x)")
        print(f"   • Attaques dangereuses: {match_data.get('dangerous_attacks_home')} - {match_data.get('dangerous_attacks_away')} (factor: {details.get('dangerous_attacks_factor', 1):.2f}x)")
        print(f"   • Tirs cadrés: {match_data.get('shots_on_target_home')} - {match_data.get('shots_on_target_away')} (factor: {details.get('shots_on_target_factor', 1):.2f}x)")
        print(f"   • Saturation: {details.get('saturation_factor', 1):.2f}x")
        print(f"   ➜ Multiplicateur live combiné: {live_mult:.2f}x")
        print(f"   ➜ Ajustement live (20%): {live_adj*100:+.1f}%")
        
        print(f"\n🎲 FORMULE FINALE:")
        print(f"   Probabilité = Base historique × (1 + Ajustement live × 0.20)")
        print(f"   Probabilité = {base_rate*100:.1f}% × (1 + {(live_mult-1)*100:+.1f}% × 0.20)")
        print(f"   Probabilité = {goal_prob*100:.1f}%")
        
        print(f"\n💡 DÉCISION RECOMMANDÉE:")
        if goal_prob >= CRITICAL_THRESHOLD:
            print("   🔴 TRÈS FORTE PROBABILITÉ (≥70%)")
            print("   ➜ Patterns historiques + contexte live alignés")
            print("   ➜ CONSIDÉRER FORTEMENT LE PARI")
        elif goal_prob >= 0.60:
            print("   🟠 FORTE PROBABILITÉ (60-70%)")
            print("   ➜ Bons patterns historiques confirmés par le live")
            print("   ➜ BONNE OPPORTUNITÉ")
        elif goal_prob >= GOAL_PROBABILITY_THRESHOLD:
            print("   🟡 PROBABILITÉ MODÉRÉE (50-60%)")
            print("   ➜ Patterns historiques corrects")
            print("   ➜ SURVEILLER L'ÉVOLUTION")
        
        print("="*100 + "\n")


def main():
    """Fonction principale de monitoring"""
    print("\n" + "="*100)
    print("🚀 PARIS LIVE - MONITORING AVEC PATTERNS HISTORIQUES")
    print("="*100)
    print(f"📊 Ligues suivies: {', '.join(FOLLOWED_LEAGUES)}")
    print(f"⏱️  Interval détection: {DETECTION_INTERVAL}s")
    print(f"🎯 Seuil alerte: {GOAL_PROBABILITY_THRESHOLD*100}%")
    print(f"🔥 Seuil critique: {CRITICAL_THRESHOLD*100}%")
    print("="*100 + "\n")
    
    active_monitors = {}
    
    try:
        while True:
            try:
                # Détecter les matches live
                all_matches = get_live_matches()
                
                if not all_matches:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Aucun match live détecté")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(all_matches)} match(s) live détecté(s)")
                
                # Filtrer les matches de nos ligues suivies
                for match in all_matches:
                    url = match['url']
                    
                    # Extraire le code ligue
                    league = None
                    if 'league=' in url:
                        import re
                        m = re.search(r'league=([a-z0-9]+)', url)
                        if m:
                            league = m.group(1)
                    
                    # Vérifier si ligue suivie
                    if league and league in FOLLOWED_LEAGUES:
                        if url not in active_monitors:
                            # Démarrer un nouveau monitor
                            match_info = match.get('snippet', 'Match inconnu')
                            monitor = MatchMonitor(url, match_info, league)
                            monitor.start()
                            active_monitors[url] = monitor
                            print(f"✅ Nouveau match suivi: [{league.upper()}] {match_info}")
                
                # Nettoyer les monitors terminés (matches finis)
                finished = [url for url, mon in active_monitors.items() if not mon.is_alive()]
                for url in finished:
                    print(f"⏹️  Match terminé: {active_monitors[url].match_info}")
                    del active_monitors[url]
                
                time.sleep(DETECTION_INTERVAL)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"⚠️ Erreur dans la boucle principale: {e}")
                time.sleep(DETECTION_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du monitoring...")
        for monitor in active_monitors.values():
            monitor.stop()
        print("✅ Monitoring arrêté proprement")


if __name__ == "__main__":
    main()
