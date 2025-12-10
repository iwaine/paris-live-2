#!/usr/bin/env python3
"""
Monitoring manuel - Vous entrez les infos du match
"""

import json
import requests
import sqlite3

# Configuration
TELEGRAM_CONFIG = "telegram_config.json"
DB_PATH = "football-live-prediction/data/predictions.db"

# Charger config Telegram
with open(TELEGRAM_CONFIG, "r") as f:
    config = json.load(f)

BOT_TOKEN = config['bot_token']
CHAT_ID = config['chat_id']

# ÉTAPE 1 : Entrer les infos du match
print("="*70)
print("🎯 MONITORING MANUEL - ENTREZ LES INFOS DU MATCH")
print("="*70)

league = input("Ligue (ex: portugal, france, germany) : ")
home_team = input("Équipe domicile (ex: Benfica) : ")
away_team = input("Équipe extérieure (ex: Sporting CP) : ")
minute = int(input("Minute actuelle (ex: 86) : "))
score_home = int(input("Buts domicile (ex: 1) : "))
score_away = int(input("Buts extérieur (ex: 1) : "))

# ÉTAPE 2 : Déterminer l'intervalle actif
if 31 <= minute <= 45:
    interval = "31-45"
elif 76 <= minute <= 90:
    interval = "76-90"
else:
    print(f"\n⚠️  Minute {minute} hors des intervalles surveillés (31-45 ou 76-90)")
    print("Aucun signal à envoyer.")
    exit()

print(f"\n✅ Intervalle actif : {interval}")

# ÉTAPE 3 : Charger la whitelist
whitelist_path = f"whitelists/{league}_whitelist.json"

try:
    with open(whitelist_path, "r", encoding="utf-8") as f:
        whitelist = json.load(f)
except FileNotFoundError:
    print(f"\n❌ Whitelist non trouvée : {whitelist_path}")
    print(f"Générez-la avec : python3 generate_top_teams_whitelist.py --league {league}")
    exit()

# ÉTAPE 4 : Récupérer les patterns
home_pattern = None
away_pattern = None

for team in whitelist['qualified_teams']:
    if team['team'] == home_team and team['location'] == 'HOME' and team['interval'] == interval:
        home_pattern = team
    if team['team'] == away_team and team['location'] == 'AWAY' and team['interval'] == interval:
        away_pattern = team

# Chercher aussi dans all_stats si pas dans qualified
if not away_pattern:
    for team in whitelist.get('all_stats', []):
        if team['team'] == away_team and team['location'] == 'AWAY' and team['interval'] == interval:
            away_pattern = team
            break

# ÉTAPE 5 : Calculer stats complètes pour away_team
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

if away_pattern:
    cursor.execute("""
        SELECT match_id, goal_times
        FROM soccerstats_scraped_matches
        WHERE team = ? AND is_home = 0
    """, (away_team,))
    
    away_matches = cursor.fetchall()
    away_total = len(away_matches)
    away_with_goal = 0
    away_goals = 0
    
    interval_min, interval_max = map(int, interval.split('-'))
    
    for match in away_matches:
        if match[1]:
            goals = [int(g.strip()) for g in match[1].split(',') if g.strip().isdigit()]
            interval_goals = [g for g in goals if interval_min <= g <= interval_max]
            away_goals += len(interval_goals)
            if interval_goals:
                away_with_goal += 1
    
    away_prob = (away_with_goal / away_total * 100) if away_total > 0 else 0
else:
    away_total = 0
    away_with_goal = 0
    away_goals = 0
    away_prob = 0

# ÉTAPE 6 : Calculer récurrence récente HOME
cursor.execute("""
    SELECT match_id, goal_times, goal_times_conceded
    FROM soccerstats_scraped_matches
    WHERE team = ? AND is_home = 1
    ORDER BY match_id DESC
    LIMIT 3
""", (home_team,))

recent_matches = cursor.fetchall()
recent_with_goal = 0
recent_total_goals = 0
interval_min, interval_max = map(int, interval.split('-'))

for match in recent_matches:
    has_goal = False
    
    # Buts marqués
    if match[1]:
        goals_for = [int(g.strip()) for g in match[1].split(',') if g.strip().isdigit()]
        interval_goals = [g for g in goals_for if interval_min <= g <= interval_max]
        recent_total_goals += len(interval_goals)
        if interval_goals:
            has_goal = True
    
    # Buts encaissés
    if match[2]:
        goals_against = [int(g.strip()) for g in match[2].split(',') if g.strip().isdigit()]
        interval_goals = [g for g in goals_against if interval_min <= g <= interval_max]
        recent_total_goals += len(interval_goals)
        if interval_goals:
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

# ÉTAPE 7 : Afficher résultats
print("\n" + "="*70)
print("📊 ANALYSE DES PATTERNS")
print("="*70)

if home_pattern:
    print(f"\n✅ {home_team} HOME {interval}:")
    print(f"   Récurrence: {home_pattern['probability']:.1f}%")
    print(f"   Matchs: {home_pattern['matches_with_goal']}/{home_pattern['matches']}")
    print(f"   Buts: {home_pattern['total_goals']}")
    home_prob = home_pattern['probability']
else:
    print(f"\n❌ {home_team} HOME {interval}: Aucun pattern")
    home_prob = 0

print(f"\n{'✅' if away_prob >= 65 else '⚠️'} {away_team} AWAY {interval}:")
print(f"   Récurrence: {away_prob:.1f}%")
print(f"   Matchs: {away_with_goal}/{away_total}")
print(f"   Buts: {away_goals}")

print(f"\n📈 FORMULA MAX:")
max_prob = max(home_prob, away_prob)
print(f"   MAX({home_prob:.1f}%, {away_prob:.1f}%) = {max_prob:.1f}%")

print(f"\n🔢 RÉCURRENCE RÉCENTE ({home_team} HOME):")
print(f"   {recent_recurrence:.1f}% ({recent_with_goal}/{recent_total} matchs)")
print(f"   {recent_total_goals} buts - Tendance: {trend}")

# ÉTAPE 8 : Décision
print("\n" + "="*70)
if max_prob >= 65:
    print("✅ SIGNAL VALIDÉ (≥ 65%)")
    print("="*70)
    
    # ÉTAPE 9 : Construire message Telegram
    if home_pattern:
        message = f"""🚨 SIGNAL V2.0 - {league.upper()}

⚽ {home_team} vs {away_team}
⏱️ {minute}' | Score: {score_home}-{score_away}

📊 INTERVALLE: {interval} minutes
🎯 PROBABILITÉ: {max_prob:.1f}%

📈 FORMULA MAX:
• {home_team} À DOMICILE:
  → Récurrence: {home_prob:.1f}% ({home_pattern['matches_with_goal']}/{home_pattern['matches']} matchs)
  → {home_pattern['total_goals']} buts marqués dans intervalle

• {away_team} À L'EXTÉRIEUR:
  → Récurrence: {away_prob:.1f}% ({away_with_goal}/{away_total} matchs) {'❌ < 65%' if away_prob < 65 else '✅'}
  → {away_goals} buts marqués dans intervalle

🔢 RÉCURRENCE RÉCENTE (3 derniers matchs):
• {home_team} HOME {interval}: {recent_recurrence:.1f}% ({recent_with_goal}/{recent_total} matchs) - {recent_total_goals} buts (marqués + encaissés)
• Tendance: {trend}

✅ SIGNAL VALIDÉ
"""
    
        # ÉTAPE 10 : Envoyer sur Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': message}
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            print("\n✅ Message envoyé sur Telegram !")
        except Exception as e:
            print(f"\n❌ Erreur Telegram: {e}")
    else:
        print("\n❌ Pattern HOME manquant, impossible d'envoyer le signal")
else:
    print(f"❌ SIGNAL REJETÉ (< 65%)")
    print("="*70)
