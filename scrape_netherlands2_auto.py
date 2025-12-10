#!/usr/bin/env python3
"""
Scraper automatique pour Eerste Divisie néerlandaise (Netherlands 2)
MÊME MÉTHODOLOGIE QUE BULGARIE :
1. Extraire les codes équipes depuis formtable.asp
2. Scraper chaque équipe avec teamstats.asp + tooltip4 parsing
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import time
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

class Netherlands2AutoScraper:
    BASE_URL = "https://www.soccerstats.com"
    DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_team_codes(self, league_code: str = "netherlands2") -> List[Tuple[str, str]]:
        """
        ÉTAPE 1 : Extraire tous les codes équipes depuis formtable.asp
        
        Args:
            league_code: Code du championnat (netherlands2)
        
        Returns:
            Liste de tuples (code_equipe, nom_equipe)
            Exemple: [('u1234-fc-den-bosch', 'FC Den Bosch'), ...]
        """
        url = f"{self.BASE_URL}/formtable.asp?league={league_code}"
        
        print("\n" + "="*80)
        print(f"🇳🇱 ÉTAPE 1 : Extraction des codes équipes depuis {url}")
        print("="*80)
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver tous les liens vers teamstats
            links = soup.find_all('a', href=re.compile(r'teamstats\.asp\?league=' + league_code + r'&stats=u\d+-'))
            
            teams = []
            for link in links:
                href = link.get('href')
                match = re.search(r'stats=(u\d+-[^&]+)', href)
                if match:
                    team_code = match.group(1)
                    team_name = link.get_text(strip=True)
                    teams.append((team_code, team_name))
            
            # Dédupliquer (certains liens peuvent apparaître plusieurs fois)
            teams = sorted(set(teams), key=lambda x: x[1])
            
            print(f"\n✅ {len(teams)} équipes trouvées :")
            for code, name in teams:
                print(f"   • {code:30s} → {name}")
            
            return teams
            
        except Exception as e:
            print(f"❌ Erreur extraction codes : {e}")
            return []
    
    def _extract_goals_from_tooltip(self, tooltip_html: str, team_is_home: bool) -> Tuple[List[int], List[int]]:
        """
        Extraire les buts marqués et encaissés depuis le tooltip HTML
        COPIE EXACTE DE LA BULGARIE
        
        Args:
            tooltip_html: HTML du tooltip avec détails des buts
            team_is_home: True si l'équipe joue à domicile
        
        Returns:
            (goals_scored, goals_conceded) : Listes des minutes de buts
        """
        goals_scored = []
        goals_conceded = []
        
        if not tooltip_html or 'span' not in tooltip_html.lower():
            return goals_scored, goals_conceded
        
        soup = BeautifulSoup(tooltip_html, 'html.parser')
        
        # Trouver tous les scores progressifs <b>X-Y</b>
        score_tags = soup.find_all('b')
        
        prev_home = 0
        prev_away = 0
        
        for score_tag in score_tags:
            score_text = score_tag.get_text().strip()
            match = re.match(r'(\d+)-(\d+)', score_text)
            
            if not match:
                continue
            
            home_score = int(match.group(1))
            away_score = int(match.group(2))
            
            # Trouver la minute du but dans le parent
            parent = score_tag.parent
            if parent:
                parent_text = parent.get_text()
                minute_match = re.search(r'\((\d+)\)', parent_text)
                if minute_match:
                    minute = int(minute_match.group(1))
                    
                    # Déterminer qui a marqué
                    if home_score > prev_home:
                        # But équipe domicile
                        if team_is_home:
                            goals_scored.append(minute)
                        else:
                            goals_conceded.append(minute)
                    
                    elif away_score > prev_away:
                        # But équipe extérieur
                        if not team_is_home:
                            goals_scored.append(minute)
                        else:
                            goals_conceded.append(minute)
                    
                    prev_home = home_score
                    prev_away = away_score
        
        return goals_scored, goals_conceded
    
    
    def scrape_team(self, league_code: str, team_code: str, team_name: str, 
                    country: str = "Netherlands", league_display: str = "Eerste Divisie") -> Optional[List[dict]]:
        """
        ÉTAPE 2 : Scraper tous les matches d'une équipe
        EXACTEMENT COMME BULGARIE : teamstats.asp + tooltip4
        
        Args:
            league_code: Code championnat (netherlands2)
            team_code: Code équipe (u7093-fc-den-bosch)
            team_name: Nom équipe (FC Den Bosch)
            country: Pays
            league_display: Nom affiché du championnat
        
        Returns:
            Liste de dictionnaires avec données des matches
        """
        url = f"{self.BASE_URL}/teamstats.asp?league={league_code}&stats={team_code}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            time.sleep(2)  # Respecter le serveur
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver le tableau des matches (MÊME STRUCTURE QUE BULGARIE)
            table = soup.find('table', {'bgcolor': '#cccccc', 'width': '100%'})
            
            if not table:
                print(f"    ❌ Tableau non trouvé pour {team_name}")
                return None
            
            matches_data = []
            
            # Parser chaque ligne (skip header)
            all_rows = table.find_all('tr')
            rows = all_rows[1:] if len(all_rows) > 1 else all_rows
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 9:
                        continue
                    
                    # Date
                    date = cells[0].get_text(strip=True)
                    
                    # Équipes
                    home_cell = cells[1]
                    away_cell = cells[3]
                    home_team = home_cell.get_text(strip=True)
                    away_team = away_cell.get_text(strip=True)
                    
                    # Déterminer si HOME ou AWAY (équipe en gras = celle qui joue)
                    team_is_home = bool(home_cell.find('b'))
                    
                    # Score
                    score_cell = cells[2]
                    score_link = score_cell.find('a', class_='tooltip4')
                    
                    if not score_link:
                        continue
                    
                    font = score_link.find('font')
                    if not font:
                        continue
                    
                    score_text = font.get_text(strip=True)
                    score = score_text.replace(' ', '')
                    
                    # Tooltip avec détails des buts
                    tooltip_span = score_link.find('span')
                    tooltip_html = str(tooltip_span) if tooltip_span else ""
                    
                    # Extraire buts marqués et encaissés
                    goals_scored, goals_conceded = self._extract_goals_from_tooltip(
                        tooltip_html, team_is_home
                    )
                    
                    # Déterminer opponent
                    opponent = away_team if team_is_home else home_team
                    
                    # Score mi-temps
                    ht_score = cells[7].get_text(strip=True)
                    
                    matches_data.append({
                        'country': country,
                        'league': league_display,
                        'league_code': league_code,
                        'team': team_name,
                        'opponent': opponent,
                        'date': date,
                        'is_home': team_is_home,
                        'score': score,
                        'ht_score': ht_score,
                        'goals_scored': goals_scored,
                        'goals_conceded': goals_conceded
                    })
                    
                except Exception as e:
                    continue
            
            print(f"    ✅ {team_name}: {len(matches_data)} matches")
            return matches_data
            
        except Exception as e:
            print(f"    ❌ {team_name}: Erreur - {e}")
            return None
    
    def save_to_db(self, matches_data: List[dict]):
        """
        Sauvegarder les matches dans la DB avec gestion des doublons
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        inserted = 0
        duplicates = 0
        
        for match in matches_data:
            try:
                # Générer match_id
                team_slug = match['team'].lower().replace(' ', '-').replace('.', '')
                date_slug = match['date'].replace('/', '-')
                match_id = f"{match['league_code']}_{team_slug}_{date_slug}"
                
                # Vérifier si le match existe déjà
                cursor.execute('''
                    SELECT COUNT(*) FROM soccerstats_scraped_matches 
                    WHERE team = ? AND opponent = ? AND date = ? AND is_home = ?
                ''', (match['team'], match['opponent'], match['date'], 1 if match['is_home'] else 0))
                
                if cursor.fetchone()[0] > 0:
                    # Match déjà existant - le mettre à jour
                    duplicates += 1
                    
                    # Convertir goal_times en JSON
                    goal_times_json = json.dumps(match['goals_scored'])
                    goal_times_conceded_json = json.dumps(match['goals_conceded'])
                    
                    cursor.execute('''
                        UPDATE soccerstats_scraped_matches 
                        SET score = ?, goals_for = ?, goals_against = ?, 
                            goal_times = ?, goal_times_conceded = ?, scraped_at = CURRENT_TIMESTAMP
                        WHERE team = ? AND opponent = ? AND date = ? AND is_home = ?
                    ''', (
                        match['score'],
                        len(match['goals_scored']),
                        len(match['goals_conceded']),
                        goal_times_json,
                        goal_times_conceded_json,
                        match['team'],
                        match['opponent'],
                        match['date'],
                        1 if match['is_home'] else 0
                    ))
                else:
                    # Nouveau match - l'insérer
                    # Convertir goal_times en JSON
                    goal_times_json = json.dumps(match['goals_scored'])
                    goal_times_conceded_json = json.dumps(match['goals_conceded'])
                    
                    cursor.execute('''
                        INSERT INTO soccerstats_scraped_matches 
                        (country, league, team, opponent, date, is_home, 
                         score, goals_for, goals_against, goal_times, goal_times_conceded, match_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match['country'],
                        match['league_code'],
                        match['team'],
                        match['opponent'],
                        match['date'],
                        1 if match['is_home'] else 0,
                        match['score'],
                        len(match['goals_scored']),
                        len(match['goals_conceded']),
                        goal_times_json,
                        goal_times_conceded_json,
                        match_id
                    ))
                    inserted += 1
                
            except Exception as e:
                print(f"Erreur insertion : {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n💾 Sauvegarde : {inserted} nouveaux, {duplicates} mis à jour")
        return inserted
    
    def run(self, max_workers: int = 3):
        """
        Exécuter le scraping complet
        EXACTEMENT COMME BULGARIE
        """
        print("\n" + "="*80)
        print("🇳🇱 SCRAPER AUTOMATIQUE - EERSTE DIVISIE PAYS-BAS")
        print("="*80)
        
        # ÉTAPE 1 : Extraire les codes équipes
        teams = self.extract_team_codes("netherlands2")
        
        if not teams:
            print("\n❌ Aucune équipe trouvée. Abandon.")
            return
        
        # ÉTAPE 2 : Scraper chaque équipe
        print("\n" + "="*80)
        print(f"📊 ÉTAPE 2 : Scraping {len(teams)} équipes")
        print("="*80)
        
        all_matches = []
        
        for team_code, team_name in teams:
            matches = self.scrape_team("netherlands2", team_code, team_name)
            if matches:
                all_matches.extend(matches)
            time.sleep(1)  # Rate limiting
        
        # ÉTAPE 3 : Nettoyer la base avant sauvegarde
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM soccerstats_scraped_matches WHERE league = 'netherlands2'")
        conn.commit()
        conn.close()
        print("🧹 Anciennes données Netherlands2 supprimées de la base.")
        print("\n" + "="*80)
        print("💾 ÉTAPE 3 : Sauvegarde en base de données")
        print("="*80)
        inserted = self.save_to_db(all_matches)
        
        print("\n" + "="*80)
        print("✅ SCRAPING TERMINÉ")
        print("="*80)
        print(f"\n📊 RÉSUMÉ :")
        print(f"   • Équipes scrapées : {len(teams)}")
        print(f"   • Matches collectés : {len(all_matches)}")
        print(f"   • Matches insérés en DB : {inserted}")
        print(f"   • Base de données : {self.DB_PATH}")
        print("\n🎯 Prochaine étape :")
        print("   cd football-live-prediction")
        print("   python3 build_critical_interval_recurrence.py --country Netherlands --league netherlands2")


if __name__ == "__main__":
    scraper = Netherlands2AutoScraper()
    scraper.run(max_workers=3)
