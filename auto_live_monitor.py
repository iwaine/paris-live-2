#!/usr/bin/env python3
"""
🔴 MONITORING AUTOMATIQUE LIVE
Scrape https://www.soccerstats.com/ pour détecter les matchs live
et appliquer automatiquement nos conditions
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
SOCCERSTATS_HOME = "https://www.soccerstats.com/"
TELEGRAM_CONFIG = "telegram_config.json"
DB_PATH = "football-live-prediction/data/predictions.db"

# Mapping des ligues surveillées
LEAGUE_MAPPING = {
    "france": ["ligue 1", "france"],
    "germany": ["bundesliga", "germany", "1. bundesliga"],
    "germany2": ["2. bundesliga", "germany 2"],
    "england": ["premier league", "england", "epl"],
    "netherlands2": ["eerste divisie", "netherlands 2", "holland 2"],
    "bolivia": ["bolivia", "division profesional"],
    "bulgaria": ["bulgaria", "parva liga"],
    "portugal": ["portugal", "liga portugal", "primeira liga"]
}

# Headers pour éviter le blocage
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


class AutoLiveMonitor:
    """Monitoring automatique des matchs live"""
    
    def __init__(self):
        # Charger config Telegram
        with open(TELEGRAM_CONFIG, "r") as f:
            config = json.load(f)
        
        self.bot_token = config['bot_token']
        self.chat_id = config['chat_id']
        
        # Charger whitelists
        self.whitelists = {}
        for league in LEAGUE_MAPPING.keys():
            whitelist_path = f"whitelists/{league}_whitelist.json"
            try:
                with open(whitelist_path, "r", encoding="utf-8") as f:
                    self.whitelists[league] = json.load(f)
            except:
                print(f"⚠️  Whitelist {league} non trouvée")
        
        self.db_path = DB_PATH
        self.processed_matches = set()  # Pour éviter les doublons
        
        print("✅ AutoLiveMonitor initialisé")
        print(f"   - {len(self.whitelists)} whitelists chargées")
    
    
    def scrape_live_matches(self) -> List[Dict]:
        """
        Scrape la page d'accueil de SoccerStats pour détecter les matchs live
        
        Returns:
            Liste de matchs live: [{'league': 'germany', 'home_team': 'Bayern', ...}, ...]
        """
        print(f"\n🔍 Scraping {SOCCERSTATS_HOME} ...")
        
        try:
            response = requests.get(SOCCERSTATS_HOME, headers=HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        live_matches = []
        
        # STRATÉGIE 1: Chercher les liens de matchs live
        # Format typique: /pmatch.asp?league=XXX&stats=...
        match_links = soup.find_all('a', href=re.compile(r'pmatch\.asp\?league='))
        
        print(f"   - {len(match_links)} liens de matchs trouvés")
        
        for link in match_links:
            href = link.get('href', '')
            
            # Extraire le code de la ligue
            league_match = re.search(r'league=([^&]+)', href)
            if not league_match:
                continue
            
            league_code = league_match.group(1).lower()
            
            # Vérifier si c'est une ligue surveillée
            monitored_league = self._match_league_code(league_code)
            if not monitored_league:
                continue
            
            # Extraire les infos du texte du lien
            link_text = link.get_text(strip=True)
            
            # Chercher la minute (ex: "45'", "78 min")
            minute_match = re.search(r'(\d+)[\'\s]*(?:min)?', link_text)
            
            # Chercher le score (ex: "1-0", "2:1")
            score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', link_text)
            
            # Chercher les équipes (souvent séparées par "vs", "-", ou dans des balises adjacentes)
            parent = link.parent
            if parent:
                parent_text = parent.get_text(' ', strip=True)
                
                # Pattern: "Team A vs Team B 1-0 45'"
                teams_match = re.search(r'(.+?)\s+(?:vs|v\.s\.|-)?\s+(.+?)\s+\d+[-:]\d+', parent_text)
                
                if teams_match and minute_match:
                    home_team = teams_match.group(1).strip()
                    away_team = teams_match.group(2).strip()
                    minute = int(minute_match.group(1))
                    
                    if score_match:
                        score_home = int(score_match.group(1))
                        score_away = int(score_match.group(2))
                        
                        match_data = {
                            'league': monitored_league,
                            'home_team': home_team,
                            'away_team': away_team,
                            'minute': minute,
                            'score_home': score_home,
                            'score_away': score_away,
                            'match_url': f"https://www.soccerstats.com{href}" if not href.startswith('http') else href
                        }
                        
                        live_matches.append(match_data)
        
        # STRATÉGIE 2: Chercher dans les tableaux/divs avec "live" ou minute patterns
        live_containers = soup.find_all(text=re.compile(r'\b(live|in-play)\b', re.I))
        
        for container in live_containers:
            parent = container.parent
            if not parent:
                continue
            
            # Chercher dans le parent élargi
            for _ in range(3):  # Remonter jusqu'à 3 niveaux
                if parent.parent:
                    parent = parent.parent
            
            # Chercher tous les liens de matchs dans ce conteneur
            container_links = parent.find_all('a', href=re.compile(r'pmatch\.asp'))
            
            for link in container_links:
                # (Même logique qu'au-dessus)
                pass
        
        print(f"✅ {len(live_matches)} matchs live détectés dans nos ligues")
        
        return live_matches
    
    
    def _match_league_code(self, league_code: str) -> Optional[str]:
        """
        Matche un code de ligue SoccerStats avec nos codes internes
        
        Args:
            league_code: Code brut (ex: "germany", "england_prem")
        
        Returns:
            Notre code interne (ex: "germany") ou None
        """
        league_code_lower = league_code.lower()
        
        for our_code, variants in LEAGUE_MAPPING.items():
            if league_code_lower == our_code:
                return our_code
            
            for variant in variants:
                if variant in league_code_lower or league_code_lower in variant:
                    return our_code
        
        return None
    
    
    def analyze_match(self, match: Dict) -> Optional[Dict]:
        """
        Analyse un match live et détermine s'il faut envoyer une alerte
        
        Args:
            match: {'league': 'germany', 'home_team': 'Bayern', 'minute': 78, ...}
        
        Returns:
            Analyse complète si alerte à envoyer, None sinon
        """
        league = match['league']
        home_team = match['home_team']
        away_team = match['away_team']
        minute = match['minute']
        score_home = match['score_home']
        score_away = match['score_away']
        
        # Identifier match unique
        match_id = f"{league}_{home_team}_{away_team}_{minute}"
        
        if match_id in self.processed_matches:
            return None  # Déjà traité
        
        print(f"\n📊 Analyse: {home_team} vs {away_team} ({minute}', {score_home}-{score_away})")
        
        # Vérifier l'intervalle
        if 31 <= minute <= 45:
            interval = "31-45"
        elif 76 <= minute <= 90:
            interval = "76-90"
        else:
            print(f"   ⚠️  Minute {minute} hors intervalles")
            return None
        
        print(f"   ✅ Intervalle: {interval}")
        
        # Charger la whitelist
        if league not in self.whitelists:
            print(f"   ⚠️  Pas de whitelist pour {league}")
            return None
        
        whitelist = self.whitelists[league]
        qualified_teams = whitelist.get('qualified_teams', [])
        
        # Extraire les stats de la whitelist
        home_stats = None
        away_stats = None
        
        for team in qualified_teams:
            if team['team'] == home_team and team['context'] == 'HOME' and team['period'] == interval:
                home_stats = team
            if team['team'] == away_team and team['context'] == 'AWAY' and team['period'] == interval:
                away_stats = team
        
        # Si une équipe n'est pas dans la whitelist, interroger la DB
        if not home_stats:
            home_stats = self._get_team_stats_from_db(home_team, league, 'HOME', interval)
            if home_stats:
                print(f"   📊 {home_team} (HOME) : Stats extraites de la DB")
        
        if not away_stats:
            away_stats = self._get_team_stats_from_db(away_team, league, 'AWAY', interval)
            if away_stats:
                print(f"   📊 {away_team} (AWAY) : Stats extraites de la DB")
        
        if not home_stats or not away_stats:
            print(f"   ❌ Stats manquantes")
            return None
        
        # Calculer probabilité MAX
        home_prob = home_stats.get('probability', 0)
        away_prob = away_stats.get('probability', 0)
        max_prob = max(home_prob, away_prob)
        
        print(f"   🎯 Probabilités: HOME={home_prob:.1f}% | AWAY={away_prob:.1f}%")
        print(f"   📈 MAX = {max_prob:.1f}%")
        
        # Vérifier le seuil
        if max_prob < 65.0:
            print(f"   ❌ Probabilité insuffisante ({max_prob:.1f}% < 65%)")
            return None
        
        # ✅ SIGNAL VALIDE !
        print(f"   ✅ SIGNAL VALIDE ! ({max_prob:.1f}%)")
        
        # Calculer saturation
        total_goals = score_home + score_away
        saturation_factor = 1.0
        
        if total_goals >= 3:
            saturation_factor = 0.8
        elif total_goals >= 2:
            saturation_factor = 0.9
        
        adjusted_prob = max_prob * saturation_factor
        
        # Marquer comme traité
        self.processed_matches.add(match_id)
        
        return {
            'league': league,
            'home_team': home_team,
            'away_team': away_team,
            'minute': minute,
            'score': f"{score_home}-{score_away}",
            'interval': interval,
            'home_stats': home_stats,
            'away_stats': away_stats,
            'probability': max_prob,
            'saturation_factor': saturation_factor,
            'adjusted_probability': adjusted_prob,
            'match_url': match.get('match_url', '')
        }
    
    
    def _get_team_stats_from_db(self, team_name: str, league: str, context: str, period: str) -> Optional[Dict]:
        """Récupère les stats d'une équipe depuis la DB"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    matches_with_goal,
                    total_matches,
                    total_goals,
                    CAST(matches_with_goal AS REAL) / total_matches * 100 as probability
                FROM team_goal_recurrence
                WHERE team_name = ? 
                  AND league = ?
                  AND context = ?
                  AND period = ?
            """
            
            cursor.execute(query, (team_name, league, context, period))
            row = cursor.fetchone()
            conn.close()
            
            if row and row[1] >= 4:  # Min 4 matchs
                return {
                    'team': team_name,
                    'context': context,
                    'period': period,
                    'matches_with_goal': row[0],
                    'total_matches': row[1],
                    'total_goals': row[2],
                    'probability': row[3]
                }
            
            return None
            
        except Exception as e:
            print(f"   ❌ Erreur DB: {e}")
            return None
    
    
    def send_telegram_alert(self, analysis: Dict):
        """Envoie une alerte Telegram"""
        home_team = analysis['home_team']
        away_team = analysis['away_team']
        minute = analysis['minute']
        score = analysis['score']
        interval = analysis['interval']
        probability = analysis['probability']
        saturation = analysis['saturation_factor']
        adjusted_prob = analysis['adjusted_probability']
        
        home_stats = analysis['home_stats']
        away_stats = analysis['away_stats']
        
        # Récurrence récente (3 derniers matchs)
        home_recent = self._get_recent_recurrence(home_team, analysis['league'], 'HOME')
        away_recent = self._get_recent_recurrence(away_team, analysis['league'], 'AWAY')
        
        message = f"""🚨 ALERTE LIVE - {analysis['league'].upper()}

🏟️ {home_team} vs {away_team}
⏱️ Minute: {minute}' | Score: {score}
📍 Intervalle: {interval}

📊 PROBABILITÉS:
• {home_team} (HOME): {home_stats['probability']:.1f}% ({home_stats['matches_with_goal']}/{home_stats['total_matches']} matchs)
• {away_team} (AWAY): {away_stats['probability']:.1f}% ({away_stats['matches_with_goal']}/{away_stats['total_matches']} matchs)

🎯 MAX = {probability:.1f}%

🔥 RÉCURRENCE RÉCENTE (3 derniers):
• {home_team} (HOME): {home_recent}
• {away_team} (AWAY): {away_recent}

⚖️ Saturation: {saturation:.2f}x (buts actuels: {score})
📈 Probabilité ajustée: {adjusted_prob:.1f}%

🔗 Match: {analysis.get('match_url', 'N/A')}
"""
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            print(f"   ✅ Alerte Telegram envoyée !")
        except Exception as e:
            print(f"   ❌ Erreur Telegram: {e}")
    
    
    def _get_recent_recurrence(self, team_name: str, league: str, context: str) -> str:
        """Calcule la récurrence récente (3 derniers matchs)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer les 3 derniers matchs
            if context == 'HOME':
                condition = "home_team = ?"
            else:
                condition = "away_team = ?"
            
            query = f"""
                SELECT 
                    CASE 
                        WHEN {condition} THEN home_goals 
                        ELSE away_goals 
                    END as goals_scored,
                    CASE 
                        WHEN {condition} THEN away_goals 
                        ELSE home_goals 
                    END as goals_conceded
                FROM soccerstats_scraped_matches
                WHERE league = ? AND {condition}
                ORDER BY match_date DESC
                LIMIT 3
            """
            
            cursor.execute(query, (league, team_name, team_name))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "N/A"
            
            # Compter les matchs avec but (marqué OU encaissé)
            matches_with_goal = sum(1 for row in rows if (row[0] > 0 or row[1] > 0))
            total_goals = sum(row[0] + row[1] for row in rows)
            
            percentage = (matches_with_goal / len(rows)) * 100 if rows else 0
            
            return f"{percentage:.1f}% ({matches_with_goal}/{len(rows)} matchs, {total_goals} buts)"
            
        except Exception as e:
            return f"Erreur: {e}"
    
    
    def run(self, check_interval: int = 60):
        """
        Lance le monitoring en boucle
        
        Args:
            check_interval: Intervalle en secondes entre chaque vérification
        """
        print("="*70)
        print("🔴 MONITORING AUTOMATIQUE LIVE")
        print("="*70)
        print(f"   Intervalle de vérification: {check_interval}s")
        print(f"   Ligues surveillées: {', '.join(LEAGUE_MAPPING.keys())}")
        print(f"   Appuyez sur Ctrl+C pour arrêter")
        print("="*70)
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                print(f"\n[{timestamp}] Itération #{iteration}")
                print("-"*70)
                
                # Scraper les matchs live
                live_matches = self.scrape_live_matches()
                
                if not live_matches:
                    print("   ℹ️  Aucun match live détecté")
                else:
                    # Analyser chaque match
                    for match in live_matches:
                        analysis = self.analyze_match(match)
                        
                        if analysis:
                            # Envoyer alerte Telegram
                            self.send_telegram_alert(analysis)
                
                # Attendre avant la prochaine itération
                print(f"\n⏳ Prochaine vérification dans {check_interval}s...")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n❌ Monitoring arrêté par l'utilisateur")
        except Exception as e:
            print(f"\n\n❌ Erreur fatale: {e}")


if __name__ == "__main__":
    import sys
    
    # Paramètres
    check_interval = 60  # Vérifier toutes les 60 secondes
    
    if len(sys.argv) > 1:
        check_interval = int(sys.argv[1])
    
    # Lancer le monitoring
    monitor = AutoLiveMonitor()
    monitor.run(check_interval=check_interval)
