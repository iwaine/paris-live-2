#!/usr/bin/env python3
"""
Signal Telegram pour Benfica vs Sporting CP
"""

import json
import requests
import sqlite3
from datetime import datetime

# Charger config Telegram
with open("/workspaces/paris-live/telegram_config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config['bot_token']
CHAT_ID = config['chat_id']

# Charger whitelist Portugal
with open("/workspaces/paris-live/football-live-prediction/whitelists/portugal_whitelist.json", "r", encoding="utf-8") as f:
    whitelist = json.load(f)

# Infos match
match_info = {
    'home': 'Benfica',
    'away': 'Sporting CP',
    'minute': 86,
    'score_home': 1,
    'score_away': 1,
    'league': 'Portugal - Liga Portugal'
}

# Récupérer patterns depuis whitelist ET all_stats (même si < 65%)
benfica_home_76_90 = None
for t in whitelist['qualified_teams']:
    if t['team'] == 'Benfica' and t['location'] == 'HOME' and t['interval'] == '76-90':
        benfica_home_76_90 = t
        break

if not benfica_home_76_90:
    print("❌ Pattern Benfica HOME 76-90 non trouvé dans whitelist")
    exit(1)

# Chercher Sporting CP AWAY 76-90 (même si < 65%)
sporting_away_76_90 = None
for t in whitelist['all_stats']:
    if t['team'] == 'Sporting CP' and t['location'] == 'AWAY' and t['interval'] == '76-90':
        sporting_away_76_90 = t
        break

# Connexion DB pour récurrence récente et stats complètes
conn = sqlite3.connect("/workspaces/paris-live/football-live-prediction/data/predictions.db")
cursor = conn.cursor()

# Si Sporting CP trouvé dans all_stats, calculer les détails depuis DB
if sporting_away_76_90:
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
    
    sporting_prob = sporting_away_76_90['probability']
else:
    sporting_total_matches = 0
    sporting_matches_with_goal = 0
    sporting_total_goals = 0
    sporting_prob = 0

# Récupérer les 3 derniers matchs HOME de Benfica
cursor.execute("""
    SELECT match_id, team, opponent, goal_times, goal_times_conceded
    FROM soccerstats_scraped_matches
    WHERE team = 'Benfica' AND is_home = 1
    ORDER BY match_id DESC
    LIMIT 3
""")

recent_matches = cursor.fetchall()

# Calculer récurrence récente (buts marqués + encaissés)
recent_with_goal = 0
recent_total_goals = 0
for match in recent_matches:
    goal_times_for = match[3]  # buts marqués
    goal_times_against = match[4]  # buts encaissés
    
    has_goal_in_interval = False
    
    # Buts marqués
    if goal_times_for:
        goals_for = [int(g.strip()) for g in goal_times_for.split(',') if g.strip().isdigit()]
        goals_for_interval = [g for g in goals_for if 76 <= g <= 90]
        recent_total_goals += len(goals_for_interval)
        if goals_for_interval:
            has_goal_in_interval = True
    
    # Buts encaissés
    if goal_times_against:
        goals_against = [int(g.strip()) for g in goal_times_against.split(',') if g.strip().isdigit()]
        goals_against_interval = [g for g in goals_against if 76 <= g <= 90]
        recent_total_goals += len(goals_against_interval)
        if goals_against_interval:
            has_goal_in_interval = True
    
    if has_goal_in_interval:
        recent_with_goal += 1

recent_total = len(recent_matches)
recent_recurrence = (recent_with_goal / recent_total * 100) if recent_total > 0 else 0

conn.close()

# Déterminer tendance
if recent_recurrence >= 80:
    trend = "🟢"
elif recent_recurrence >= 50:
    trend = "🟡"
else:
    trend = "🔴"

# Construire message
probability = benfica_home_76_90['probability']

message = f"""🚨 SIGNAL V2.0 - PORTUGAL

⚽ {match_info['home']} vs {match_info['away']}
🏆 {match_info['league']}
⏱️ {match_info['minute']}' | Score: {match_info['score_home']}-{match_info['score_away']}

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

print(message)
print()

# Envoyer sur Telegram
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    'chat_id': CHAT_ID,
    'text': message
}

try:
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    print("✅ Message envoyé sur Telegram avec succès !")
except Exception as e:
    print(f"❌ Erreur envoi Telegram: {e}")
