#!/usr/bin/env python3
"""
MONITORING LIVE GERMANY2 (BUNDESLIGA 2)
Système complet pour prise de décision avec :
- Patterns historiques Germany2 (80%)
- Contexte live temps réel (20%)
- Alertes uniquement dans intervalles critiques 31-47 et 76-95
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "football-live-prediction"))

from soccerstats_live_selector import get_live_matches
from soccerstats_live_scraper import SoccerStatsLiveScraper

try:
    from predictors.live_goal_probability_predictor import predict_goal
except ImportError:
    from football_live_prediction.predictors.live_goal_probability_predictor import predict_goal

# Configuration
LEAGUE = 'germany2'
SCAN_INTERVAL = 10  # secondes entre chaque scan
GOAL_PROBABILITY_THRESHOLD = 0.45  # 45% = seuil d'alerte
HIGH_THRESHOLD = 0.60  # 60% = forte probabilité
CRITICAL_THRESHOLD = 0.70  # 70% = très forte probabilité

# Intervalles critiques
CRITICAL_INTERVALS = [
    (31, 47),  # 31-45 + temps additionnel
    (76, 95),  # 76-90 + temps additionnel
]

def is_in_critical_interval(minute):
    """Vérifie si on est dans un intervalle critique"""
    for min_start, min_end in CRITICAL_INTERVALS:
        if min_start <= minute <= min_end:
            return True, f"{min_start}-{min_end}"
    return False, None

def format_alert(match_str, minute, goal_prob, danger_level, match_data, prediction, is_critical_interval):
    """Formate une alerte détaillée pour décision"""
    
    details = prediction.get('details', {})
    
    lines = []
    lines.append("\n" + "="*120)
    lines.append(f"🚨 {'ALERTE CRITIQUE' if goal_prob >= CRITICAL_THRESHOLD else 'ALERTE BUT'} - GERMANY2")
    lines.append("="*120)
    
    lines.append(f"\n⚽ MATCH: {match_str}")
    lines.append(f"⏱️  MINUTE: {minute}' {'🔥 INTERVALLE CRITIQUE' if is_critical_interval else ''}")
    lines.append(f"📊 SCORE ACTUEL: {match_data.get('score_home')}-{match_data.get('score_away')}")
    
    lines.append(f"\n🎯 PROBABILITÉ DE BUT: {goal_prob*100:.1f}%")
    lines.append(f"⚠️  NIVEAU: {danger_level}")
    
    # Composantes du calcul (80/20)
    base_rate = details.get('base_rate', 0)
    historical_comp = details.get('historical_component', base_rate)
    live_mult = details.get('live_multiplier', 1.0)
    live_adj = details.get('live_adjustment', 0)
    
    lines.append(f"\n📈 COMPOSANTES DU CALCUL (80% HISTORIQUE + 20% LIVE):")
    lines.append("-"*120)
    
    lines.append(f"\n🏛️  HISTORIQUE (80%):")
    lines.append(f"   • Base rate GERMANY2: {base_rate*100:.1f}%")
    lines.append(f"   • Récurrence patterns {match_data.get('home_team')} + {match_data.get('away_team')}")
    lines.append(f"   • Intervalle: {details.get('interval', 'N/A')}")
    lines.append(f"   ➜ Composante historique: {historical_comp*100:.1f}%")
    
    lines.append(f"\n📡 LIVE (20%):")
    lines.append(f"   • Possession: {match_data.get('possession_home')}% - {match_data.get('possession_away')}% "
                 f"(factor: {details.get('possession_factor', 1):.2f}x)")
    lines.append(f"   • Attaques: {match_data.get('attacks_home')} - {match_data.get('attacks_away')}")
    lines.append(f"   • Attaques dangereuses: {match_data.get('dangerous_attacks_home')} - {match_data.get('dangerous_attacks_away')} "
                 f"(factor: {details.get('dangerous_attacks_factor', 1):.2f}x)")
    lines.append(f"   • Tirs cadrés: {match_data.get('shots_on_target_home')} - {match_data.get('shots_on_target_away')} "
                 f"(factor: {details.get('shots_on_target_factor', 1):.2f}x)")
    lines.append(f"   • Cartes rouges: {match_data.get('red_cards_home', 0)} - {match_data.get('red_cards_away', 0)}")
    lines.append(f"   ➜ Multiplicateur live: {live_mult:.2f}x")
    lines.append(f"   ➜ Ajustement (20%): {live_adj*100:+.1f}%")
    
    lines.append(f"\n🎲 FORMULE:")
    lines.append(f"   Probabilité = {base_rate*100:.1f}% × (1 + {(live_mult-1)*100:+.1f}% × 0.20)")
    lines.append(f"   Probabilité = {goal_prob*100:.1f}%")
    
    lines.append(f"\n💡 DÉCISION RECOMMANDÉE:")
    if goal_prob >= CRITICAL_THRESHOLD:
        lines.append("   🔴 TRÈS FORTE PROBABILITÉ (≥70%)")
        lines.append("   ➜ Patterns historiques solides + contexte live favorable")
        lines.append("   ➜ ⚠️  CONSIDÉRER FORTEMENT LE PARI")
        lines.append("   ➜ Risque: FAIBLE | Opportunité: EXCELLENTE")
    elif goal_prob >= HIGH_THRESHOLD:
        lines.append("   🟠 FORTE PROBABILITÉ (60-70%)")
        lines.append("   ➜ Bons patterns confirmés par le live")
        lines.append("   ➜ ✅ BONNE OPPORTUNITÉ")
        lines.append("   ➜ Risque: MODÉRÉ | Opportunité: BONNE")
    elif goal_prob >= GOAL_PROBABILITY_THRESHOLD:
        lines.append("   🟡 PROBABILITÉ MODÉRÉE (45-60%)")
        lines.append("   ➜ Patterns corrects, contexte à surveiller")
        lines.append("   ➜ 📊 SURVEILLER L'ÉVOLUTION")
        lines.append("   ➜ Risque: MOYEN | Opportunité: ACCEPTABLE")
    
    lines.append("\n" + "="*120 + "\n")
    
    return "\n".join(lines)

def monitor_match(url, match_info):
    """Monitore un match spécifique"""
    
    scraper = SoccerStatsLiveScraper()
    last_minute = None
    alerts_sent = set()
    
    print(f"\n🟢 MONITORING: {match_info}")
    print(f"🔗 URL: {url}")
    print(f"⏱️  Scan toutes les {SCAN_INTERVAL}s")
    print(f"🎯 Seuil alerte: {GOAL_PROBABILITY_THRESHOLD*100}%")
    print("-"*120)
    
    try:
        while True:
            try:
                data = scraper.scrape_match(url)
                if not data:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Pas de données")
                    time.sleep(SCAN_INTERVAL)
                    continue
                
                d = data.to_dict()
                d['url'] = url
                
                current_minute = d.get('minute', 0)
                
                # Vérifier intervalle critique
                in_critical, interval_name = is_in_critical_interval(current_minute)
                
                # Affichage uniquement si minute change
                if current_minute != last_minute:
                    last_minute = current_minute
                    
                    match_str = f"{d.get('home_team')} {d.get('score_home')}:{d.get('score_away')} {d.get('away_team')}"
                    ts = datetime.now().strftime("%H:%M:%S")
                    
                    if not in_critical:
                        print(f"[{ts}] ⏸️  {match_str} | min={current_minute}' | "
                              f"Hors intervalle critique (31-47 ou 76-95) | "
                              f"Poss={d.get('possession_home')}%-{d.get('possession_away')}%")
                        time.sleep(SCAN_INTERVAL)
                        continue
                    
                    # Dans intervalle critique → Prédire
                    prediction = predict_goal(None, d.get('home_team'), d.get('away_team'), d)
                    goal_prob = prediction.get('goal_probability', 0) / 100
                    danger_level = prediction.get('danger_level', 'LOW')
                    
                    details = prediction.get('details', {})
                    base_rate = details.get('base_rate', 0)
                    historical_comp = details.get('historical_component', base_rate)
                    live_mult = details.get('live_multiplier', 1.0)
                    
                    # Icône selon danger
                    if danger_level == 'CRITICAL':
                        icon = "🔴"
                    elif danger_level == 'HIGH':
                        icon = "🟠"
                    elif danger_level == 'MEDIUM':
                        icon = "🟡"
                    else:
                        icon = "🟢"
                    
                    print(f"[{ts}] {icon} {match_str} | min={current_minute}' [{interval_name}] | "
                          f"Prob={goal_prob*100:.1f}% [{danger_level}] | "
                          f"Hist={historical_comp*100:.1f}% (80%) | Live={live_mult:.2f}x (20%) | "
                          f"Poss={d.get('possession_home')}%-{d.get('possession_away')}% | "
                          f"DA={d.get('dangerous_attacks_home')}-{d.get('dangerous_attacks_away')} | "
                          f"SOT={d.get('shots_on_target_home')}-{d.get('shots_on_target_away')}")
                    
                    # Alerte si seuil atteint
                    if goal_prob >= GOAL_PROBABILITY_THRESHOLD:
                        alert_key = f"{current_minute}_{int(goal_prob*10)}"
                        if alert_key not in alerts_sent:
                            print(format_alert(match_str, current_minute, goal_prob, danger_level, d, prediction, in_critical))
                            alerts_sent.add(alert_key)
                
                time.sleep(SCAN_INTERVAL)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Erreur: {e}")
                time.sleep(SCAN_INTERVAL)
    
    except KeyboardInterrupt:
        print(f"\n\n🛑 Arrêt du monitoring {match_info}")

def main():
    """Lance le monitoring Germany2"""
    
    print("\n" + "="*120)
    print("🇩🇪 PARIS LIVE - MONITORING GERMANY2 (BUNDESLIGA 2)")
    print("="*120)
    print(f"📊 Ligue: Bundesliga 2")
    print(f"🎯 Seuils: {GOAL_PROBABILITY_THRESHOLD*100}% alerte | {HIGH_THRESHOLD*100}% fort | {CRITICAL_THRESHOLD*100}% critique")
    print(f"⏱️  Intervalles: 31-47 (fin 1ère MT) | 76-95 (fin match)")
    print(f"📈 Calcul: 80% patterns historiques + 20% contexte live")
    print("="*120)
    
    # Détecter matches Germany2 live
    print("\n🔍 Détection des matches live...")
    all_matches = get_live_matches()
    
    germany2_matches = [m for m in all_matches if 'germany2' in m['url'].lower()]
    
    if not germany2_matches:
        print("❌ Aucun match Germany2 live actuellement")
        return
    
    print(f"✅ {len(germany2_matches)} match(s) Germany2 détecté(s):\n")
    
    for i, match in enumerate(germany2_matches, 1):
        print(f"{i}. {match.get('snippet', 'Match inconnu')} - Minute {match.get('minute', '?')}'")
    
    if len(germany2_matches) == 1:
        print(f"\n🎯 Monitoring automatique du match unique...")
        monitor_match(germany2_matches[0]['url'], germany2_matches[0].get('snippet', 'Match 1'))
    else:
        print(f"\n📝 Choisir le match à monitorer (1-{len(germany2_matches)}) ou 'all' pour tous: ", end='')
        choice = input().strip().lower()
        
        if choice == 'all':
            print("⚠️  Mode multi-match non implémenté, monitoring du premier match...")
            monitor_match(germany2_matches[0]['url'], germany2_matches[0].get('snippet', 'Match 1'))
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(germany2_matches):
                    monitor_match(germany2_matches[idx]['url'], germany2_matches[idx].get('snippet', f'Match {choice}'))
                else:
                    print("❌ Choix invalide")
            except ValueError:
                print("❌ Choix invalide")

if __name__ == "__main__":
    main()
