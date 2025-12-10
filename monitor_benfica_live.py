#!/usr/bin/env python3
"""
Monitoring en direct Benfica vs Sporting CP
Rafraîchit toutes les 30 secondes
"""

import time
import json
import requests
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

# Config
TELEGRAM_CONFIG = "/workspaces/paris-live/telegram_config.json"
DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
WHITELIST_PATH = "/workspaces/paris-live/football-live-prediction/whitelists/portugal_whitelist.json"

# Charger config
with open(TELEGRAM_CONFIG, "r") as f:
    telegram_config = json.load(f)

with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
    whitelist = json.load(f)

BOT_TOKEN = telegram_config['bot_token']
CHAT_ID = telegram_config['chat_id']

# URL à tester (flashscore style)
MATCH_URL = "https://www.soccerstats.com/latest.asp?league=portugal"

print("🚀 MONITORING BENFICA vs SPORTING CP")
print("="*70)
print(f"⏰ Démarré à {datetime.now().strftime('%H:%M:%S')}")
print("🔄 Rafraîchissement toutes les 30 secondes")
print("❌ Ctrl+C pour arrêter")
print("="*70)
print()

last_minute_sent = None

def send_telegram_alert(minute, score_home, score_away):
    """Envoyer alerte Telegram"""
    
    # Récupérer patterns
    benfica_home_76_90 = None
    for t in whitelist['qualified_teams']:
        if t['team'] == 'Benfica' and t['location'] == 'HOME' and t['interval'] == '76-90':
            benfica_home_76_90 = t
            break
    
    if not benfica_home_76_90:
        return False
    
    # Stats Sporting CP
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT match_id, goal_times
        FROM soccerstats_scraped_matches
        WHERE team = 'Sporting CP' AND is_home = 0
    """)
    
    sporting_matches = cursor.fetchall()
    sporting_total_matches = len(sporting_matches)
    sporting_matches_with_goal = 0
    sporting_total_goals = 0
    
    for match in sporting_matches:
        goal_times = match[1]
        if goal_times:
            goals = [int(g.strip()) for g in goal_times.split(',') if g.strip().isdigit()]
            goals_in_interval = [g for g in goals if 76 <= g <= 90]
            sporting_total_goals += len(goals_in_interval)
            if goals_in_interval:
                sporting_matches_with_goal += 1
    
    sporting_prob = (sporting_matches_with_goal / sporting_total_matches * 100) if sporting_total_matches > 0 else 0
    
    # Récurrence récente Benfica
    cursor.execute("""
        SELECT match_id, team, opponent, goal_times, goal_times_conceded
        FROM soccerstats_scraped_matches
        WHERE team = 'Benfica' AND is_home = 1
        ORDER BY match_id DESC
        LIMIT 3
    """)
    
    recent_matches = cursor.fetchall()
    recent_with_goal = 0
    recent_total_goals = 0
    
    for match in recent_matches:
        goal_times_for = match[3]
        goal_times_against = match[4]
        
        has_goal = False
        
        if goal_times_for:
            goals_for = [int(g.strip()) for g in goal_times_for.split(',') if g.strip().isdigit()]
            goals_for_interval = [g for g in goals_for if 76 <= g <= 90]
            recent_total_goals += len(goals_for_interval)
            if goals_for_interval:
                has_goal = True
        
        if goal_times_against:
            goals_against = [int(g.strip()) for g in goal_times_against.split(',') if g.strip().isdigit()]
            goals_against_interval = [g for g in goals_against if 76 <= g <= 90]
            recent_total_goals += len(goals_against_interval)
            if goals_against_interval:
                has_goal = True
        
        if has_goal:
            recent_with_goal += 1
    
    recent_total = len(recent_matches)
    recent_recurrence = (recent_with_goal / recent_total * 100) if recent_total > 0 else 0
    
    conn.close()
    
    # Tendance
    if recent_recurrence >= 80:
        trend = "🟢"
    elif recent_recurrence >= 50:
        trend = "🟡"
    else:
        trend = "🔴"
    
    # Message
    probability = benfica_home_76_90['probability']
    
    message = f"""🚨 SIGNAL V2.0 - PORTUGAL

⚽ Benfica vs Sporting CP
🏆 Portugal - Liga Portugal
⏱️ {minute}' | Score: {score_home}-{score_away}

📊 INTERVALLE: 76-90 minutes
🎯 PROBABILITÉ: {probability:.1f}%

📈 FORMULA MAX:
• Benfica À DOMICILE:
  → Récurrence: {probability:.1f}% ({benfica_home_76_90['matches_with_goal']}/{benfica_home_76_90['matches']} matchs)
  → {benfica_home_76_90['total_goals']} buts marqués dans intervalle

• Sporting CP À L'EXTÉRIEUR:
  → Récurrence: {sporting_prob:.1f}% ({sporting_matches_with_goal}/{sporting_total_matches} matchs) {'❌ < 65%' if sporting_prob < 65 else '✅'}
  → {sporting_total_goals} buts marqués dans intervalle

🔢 RÉCURRENCE RÉCENTE (3 derniers matchs):
• Benfica HOME 76-90: {recent_recurrence:.1f}% ({recent_with_goal}/{recent_total} matchs) - {recent_total_goals} buts (marqués + encaissés)
• Tendance: {trend}

✅ SIGNAL VALIDÉ
Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Envoyer
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message}
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except:
        return False

try:
    iteration = 0
    
    while True:
        iteration += 1
        now = datetime.now().strftime('%H:%M:%S')
        
        print(f"[{now}] Itération #{iteration}")
        
        # Vous devez fournir manuellement la minute actuelle
        print("⚠️  Mode manuel : Entrez la minute actuelle (ou 'q' pour quitter)")
        print("    Format : minute,score_home,score_away")
        print("    Exemple : 88,1,1")
        
        user_input = input(">>> ").strip()
        
        if user_input.lower() == 'q':
            print("\n✋ Monitoring arrêté")
            break
        
        if ',' in user_input:
            try:
                parts = user_input.split(',')
                minute = int(parts[0])
                score_home = int(parts[1])
                score_away = int(parts[2])
                
                print(f"✓ Match détecté : {minute}' | {score_home}-{score_away}")
                
                # Vérifier si on est dans l'intervalle 76-90
                if 76 <= minute <= 90:
                    print(f"  🎯 Dans l'intervalle 76-90 !")
                    
                    # Envoyer alerte seulement si nouvelle minute
                    if last_minute_sent != minute:
                        print(f"  📤 Envoi alerte Telegram...")
                        
                        if send_telegram_alert(minute, score_home, score_away):
                            print(f"  ✅ Alerte envoyée avec succès")
                            last_minute_sent = minute
                        else:
                            print(f"  ❌ Échec envoi Telegram")
                    else:
                        print(f"  ⏭️  Alerte déjà envoyée pour minute {minute}")
                else:
                    print(f"  ⏸️  Hors intervalle (attente 76-90')")
                
            except (ValueError, IndexError):
                print("❌ Format invalide")
        
        print()

except KeyboardInterrupt:
    print("\n\n✋ Monitoring interrompu par l'utilisateur")
    print("="*70)
