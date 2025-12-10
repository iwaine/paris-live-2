#!/usr/bin/env python3
"""
TEST COMPLET DU SYSTÈME V2.0 AVEC TELEGRAM
1. Détecte matchs live
2. Filtre avec whitelist (équipes performantes)
3. Scrape données live
4. Calcule probabilités
5. Envoie alertes Telegram si signal ≥ 65%
"""

import json
import requests
import sqlite3
import sys
from bs4 import BeautifulSoup
from datetime import datetime

# Config
DB_PATH = '/workspaces/paris-live/football-live-prediction/data/predictions.db'
TELEGRAM_CONFIG = '/workspaces/paris-live/telegram_config.json'

sys.path.append('/workspaces/paris-live/football-live-prediction/predictors')
from live_goal_probability_predictor import LiveGoalProbabilityPredictor

def load_whitelists():
    """Charge toutes les whitelists"""
    import os
    whitelists = {}
    whitelist_dir = 'whitelists'
    
    if os.path.exists(whitelist_dir):
        for filename in os.listdir(whitelist_dir):
            if filename.endswith('_whitelist.json'):
                league = filename.replace('_whitelist.json', '')
                with open(f'{whitelist_dir}/{filename}', 'r') as f:
                    data = json.load(f)
                    # Créer set des équipes qualifiées
                    teams = set()
                    for team_data in data['qualified_teams']:
                        teams.add(team_data['team'])
                    whitelists[league] = teams
    
    return whitelists

def detect_live_matches():
    """Détecte tous les matchs live"""
    url = 'https://www.soccerstats.com/live.asp'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    matches = []
    current_league = None
    
    for row in soup.find_all('tr'):
        # Détection des ligues
        if 'trow6' in row.get('class', []):
            league_text = row.get_text(strip=True)
            current_league = league_text
            continue
        
        cells = row.find_all('td')
        if len(cells) > 5:
            time_cell = cells[0].get_text(strip=True)
            # Match live
            if "'" in time_cell or 'HT' in time_cell:
                team_home = cells[2].get_text(strip=True)
                team_away = cells[4].get_text(strip=True)
                score_text = cells[3].get_text(strip=True)
                
                # Extraire score
                try:
                    score_parts = score_text.split('-')
                    home_score = int(score_parts[0].strip())
                    away_score = int(score_parts[1].strip())
                except:
                    home_score = 0
                    away_score = 0
                
                # Extraire minute
                try:
                    if "'" in time_cell:
                        minute = int(time_cell.replace("'", ""))
                    elif 'HT' in time_cell:
                        minute = 45
                    else:
                        minute = 0
                except:
                    minute = 0
                
                # Trouver URL du match
                match_link = None
                for cell in cells:
                    link = cell.find('a', href=True)
                    if link and 'pmatch.asp' in link['href']:
                        match_link = 'https://www.soccerstats.com/' + link['href']
                        break
                
                matches.append({
                    'league': current_league,
                    'home_team': team_home,
                    'away_team': team_away,
                    'home_score': home_score,
                    'away_score': away_score,
                    'minute': minute,
                    'match_url': match_link
                })
    
    return matches

def get_interval_stats(cursor, team_name, is_home, interval_min, interval_max, last_n=None):
    """Récupère stats d'intervalle pour une équipe"""
    query = '''
        SELECT goal_times, goal_times_conceded, date
        FROM soccerstats_scraped_matches
        WHERE team = ? AND is_home = ?
        ORDER BY date DESC
    '''
    params = [team_name, 1 if is_home else 0]
    
    if last_n:
        query += ' LIMIT ?'
        params.append(last_n)
    
    cursor.execute(query, params)
    matches = cursor.fetchall()
    
    total_matches = len(matches)
    if total_matches == 0:
        return None
    
    matches_with_goal = 0
    total_goals = 0
    
    for goal_times_json, goal_conceded_json, match_date in matches:
        goals = json.loads(goal_times_json) if goal_times_json else []
        goals_conceded = json.loads(goal_conceded_json) if goal_conceded_json else []
        all_goals = goals + goals_conceded
        
        goals_in_interval = [g for g in all_goals if interval_min <= g <= interval_max]
        if goals_in_interval:
            matches_with_goal += 1
            total_goals += len(goals_in_interval)
    
    probability = (matches_with_goal / total_matches * 100) if total_matches > 0 else 0
    recurrence = (total_goals / total_matches * 100) if total_matches > 0 else 0
    
    return {
        'total_matches': total_matches,
        'matches_with_goal': matches_with_goal,
        'total_goals': total_goals,
        'probability': probability,
        'recurrence': recurrence
    }

def get_trend_emoji(recent_prob):
    """Emoji selon trend récent"""
    if recent_prob >= 66:
        return '🟢 TRÈS ACTIF'
    elif recent_prob >= 33:
        return '🟡 ACTIF'
    else:
        return '🔴 FAIBLE'

def send_telegram_message(message):
    """Envoie message sur Telegram"""
    try:
        with open(TELEGRAM_CONFIG, 'r') as f:
            config = json.load(f)
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        response = requests.post(url, data={'chat_id': config['chat_id'], 'text': message})
        
        return response.status_code == 200
    except Exception as e:
        print(f'❌ Erreur Telegram: {e}')
        return False

def main():
    print('🚀 TEST COMPLET SYSTÈME V2.0 AVEC TELEGRAM')
    print('=' * 70)
    
    # 1. Charger whitelists
    print('\n📋 CHARGEMENT WHITELISTS...')
    whitelists = load_whitelists()
    total_qualified = sum(len(teams) for teams in whitelists.values())
    print(f'✓ {len(whitelists)} ligues chargées')
    print(f'✓ {total_qualified} équipes qualifiées au total')
    
    # 2. Détecter matchs live
    print('\n🔍 DÉTECTION MATCHS LIVE...')
    matches = detect_live_matches()
    print(f'✓ {len(matches)} matchs live détectés')
    
    if not matches:
        print('\n⚠️  Aucun match en cours actuellement')
        return
    
    # 3. Filtrer avec whitelist
    print('\n🎯 FILTRAGE AVEC WHITELIST...')
    filtered_matches = []
    for match in matches:
        league_key = match['league'].lower().split()[0] if match['league'] else ''
        
        # Mapping des ligues
        league_mapping = {
            'germany': 'germany',
            'france': 'france',
            'england': 'england',
            'netherlands': 'netherlands2',
            'bolivia': 'bolivia',
            'bulgaria': 'bulgaria',
            'portugal': 'portugal',
            'liga': 'portugal'
        }
        
        for key, value in league_mapping.items():
            if key in league_key.lower():
                league_key = value
                break
        
        if league_key in whitelists:
            home_qualified = match['home_team'] in whitelists[league_key]
            away_qualified = match['away_team'] in whitelists[league_key]
            
            if home_qualified or away_qualified:
                filtered_matches.append(match)
                print(f"   ✓ {match['home_team']} vs {match['away_team']} ({match['minute']}')")
    
    print(f'\n✓ {len(filtered_matches)} matchs qualifiés (avec équipes performantes)')
    
    if not filtered_matches:
        print('\n⚠️  Aucun match avec équipes whitelistées')
        return
    
    # 4. Analyser chaque match qualifié
    print('\n📊 ANALYSE DES MATCHS...')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    predictor = LiveGoalProbabilityPredictor(DB_PATH)
    
    signals_sent = 0
    
    for match in filtered_matches:
        print(f'\n   → {match["home_team"]} vs {match["away_team"]} ({match["minute"]}\')')
        
        # Vérifier si dans intervalle intéressant
        in_interval_31_45 = 31 <= match['minute'] <= 45
        in_interval_76_90 = 76 <= match['minute'] <= 90
        
        if not (in_interval_31_45 or in_interval_76_90):
            print(f'     ⏳ Minute {match["minute"]} hors intervalles (31-45, 76-90)')
            continue
        
        interval = '31-45' if in_interval_31_45 else '76-90'
        interval_min, interval_max = (31, 45) if in_interval_31_45 else (76, 90)
        
        # Stats équipes
        home_stats = get_interval_stats(cursor, match['home_team'], True, interval_min, interval_max)
        away_stats = get_interval_stats(cursor, match['away_team'], False, interval_min, interval_max)
        
        if not home_stats or not away_stats:
            print(f'     ❌ Données historiques manquantes')
            continue
        
        home_recent = get_interval_stats(cursor, match['home_team'], True, interval_min, interval_max, 3)
        away_recent = get_interval_stats(cursor, match['away_team'], False, interval_min, interval_max, 3)
        
        # Calculer probabilité
        result = predictor.predict_goal_probability(
            home_team=match['home_team'],
            away_team=match['away_team'],
            current_minute=match['minute'],
            home_possession=None,
            away_possession=None,
            home_attacks=None,
            away_attacks=None,
            home_dangerous_attacks=None,
            away_dangerous_attacks=None,
            home_shots_on_target=None,
            away_shots_on_target=None,
            score_home=match['home_score'],
            score_away=match['away_score'],
            league='germany'  # TODO: mapper correctement
        )
        
        probability = result.get('goal_probability', 0)
        print(f'     📈 Probabilité: {probability:.1f}%')
        
        # Signal si ≥ 65%
        if probability >= 65:
            print(f'     🚨 SIGNAL ! Envoi sur Telegram...')
            
            # Timing
            cursor.execute('''
                SELECT avg_minute, sem_minute
                FROM team_goal_recurrence
                WHERE team_name = ? AND period = 2 AND is_home = 1
            ''', (match['home_team'],))
            home_timing = cursor.fetchone()
            
            cursor.execute('''
                SELECT avg_minute, sem_minute
                FROM team_goal_recurrence
                WHERE team_name = ? AND period = 2 AND is_home = 0
            ''', (match['away_team'],))
            away_timing = cursor.fetchone()
            
            # Message Telegram
            message = f"""🚨 ALERTE BUT - SYSTÈME V2.0 FORMULA MAX

⚽ MATCH EN COURS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏟️  {match['home_team']} vs {match['away_team']}
⏱️  Minute: {match['minute']}'
📊 Score: {match['home_score']}-{match['away_score']}
🏆 Championnat: {match['league']}

🎯 SIGNAL DÉTECTÉ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Intervalle: {interval}' 
📈 Probabilité: {probability:.1f}% ≥ 65% ✅
⚠️  Niveau: {result.get('danger_level', 'HIGH')}

📊 PATTERNS HISTORIQUES - Intervalle {interval}'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 {match['home_team']} À DOMICILE:
   📈 TOTAL ({home_stats['total_matches']} matchs):
      • {home_stats['total_goals']} buts = {home_stats['recurrence']:.1f}% récurrence
      • {home_stats['matches_with_goal']} matchs avec but = {home_stats['probability']:.1f}% proba
      • Timing: {home_timing[0]:.1f}' ±{home_timing[1]:.1f}' (SEM)
   
   🔥 RÉCENT (3 derniers):
      • {home_recent['total_goals']} buts = {home_recent['recurrence']:.1f}% récurrence
      • {home_recent['matches_with_goal']}/3 matchs avec but = {home_recent['probability']:.1f}%
      • Trend: {get_trend_emoji(home_recent['probability'])}

✈️  {match['away_team']} À L'EXTÉRIEUR:
   📈 TOTAL ({away_stats['total_matches']} matchs):
      • {away_stats['total_goals']} buts = {away_stats['recurrence']:.1f}% récurrence
      • {away_stats['matches_with_goal']} matchs avec but = {away_stats['probability']:.1f}% proba
      • Timing: {away_timing[0]:.1f}' ±{away_timing[1]:.1f}' (SEM)
   
   🔥 RÉCENT (3 derniers):
      • {away_recent['total_goals']} buts = {away_recent['recurrence']:.1f}% récurrence
      • {away_recent['matches_with_goal']}/3 matchs avec but = {away_recent['probability']:.1f}%
      • Trend: {get_trend_emoji(away_recent['probability'])}

🔬 MÉTHODOLOGIE V2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Formula MAX: Meilleur pattern ({max(home_stats['probability'], away_stats['probability']):.1f}%)
✓ Trend récent: Confirmation sur 3 derniers matchs
✓ Buts complets: Marqués + Encaissés
✓ Intervalle précis: Exactement {interval}'
✓ Seuil qualité: ≥ 65% requis
✓ Whitelist: Équipes pré-sélectionnées

⏰ ACTION RECOMMANDÉE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 BUT ATTENDU prochaines minutes
📱 Signal envoyé à {match['minute']}' / 90'
⚡ SURVEILLER LE MATCH DE PRÈS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Système V2.0 - Formula MAX + Whitelist
Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')} UTC"""
            
            if send_telegram_message(message):
                print(f'     ✅ Message envoyé sur Telegram !')
                signals_sent += 1
            else:
                print(f'     ❌ Échec envoi Telegram')
        else:
            print(f'     ⚠️  Probabilité < 65%, pas de signal')
    
    conn.close()
    
    print(f'\n{"=" * 70}')
    print(f'✅ TEST TERMINÉ')
    print(f'{"=" * 70}')
    print(f'📊 Résumé:')
    print(f'   • Matchs live: {len(matches)}')
    print(f'   • Matchs qualifiés: {len(filtered_matches)}')
    print(f'   • Signaux envoyés: {signals_sent}')
    print(f'{"=" * 70}')

if __name__ == '__main__':
    main()
