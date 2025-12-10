#!/usr/bin/env python3
"""
Scraper automatique pour championnat bolivien (Division Profesional)
Stratégie IDENTIQUE à Bulgaria :
1. Extraire les codes équipes depuis formtable.asp
2. Scraper chaque équipe avec son code via teamstats.asp
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import time
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

class BoliviaAutoScraper:
    BASE_URL = "https://www.soccerstats.com"
    DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_team_codes(self, league_code: str = "bolivia") -> List[Tuple[str, str]]:
        """
        ÉTAPE 1 : Extraire tous les codes équipes depuis formtable.asp
        
        Args:
            league_code: Code du championnat (bolivia)
        
        Returns:
            Liste de tuples (code_equipe, nom_equipe)
            Exemple: [('u1234-the-strongest', 'The Strongest'), ...]
        """
        url = f"{self.BASE_URL}/formtable.asp?league={league_code}"
        
        print("\n" + "="*80)
        print(f"🔍 ÉTAPE 1 : Extraction des codes équipes depuis {url}")
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
        COPIE EXACTE de la méthode bulgare
        
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
            
            # Trouver la minute du but dans le parent (MÉTHODE BULGARE)
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
    
    def scrape_team(self, team_code: str, team_name: str, league_code: str = "bolivia") -> List[dict]:
        """
        ÉTAPE 2 : Scraper tous les matches d'une équipe
        COPIE EXACTE de la méthode bulgare
        
        Args:
            team_code: Code de l'équipe (ex: u1234-the-strongest)
            team_name: Nom de l'équipe
            league_code: Code championnat
        
        Returns:
            Liste de dictionnaires représentant les matches
        """
        url = f"{self.BASE_URL}/teamstats.asp?league={league_code}&stats={team_code}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            time.sleep(1)  # Respecter le serveur
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver le tableau des matches (MÉTHODE BULGARE)
            table = soup.find('table', {'bgcolor': '#cccccc', 'width': '100%'})
            
            if not table:
                print(f"    ❌ {team_name}: Tableau non trouvé")
                return []
            
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
                    
                    # Tooltip avec détails des buts (CLÉ!)
                    tooltip_span = score_link.find('span')
                    tooltip_html = str(tooltip_span) if tooltip_span else ""
                    
                    # Extraire buts marqués et encaissés
                    goals_scored, goals_conceded = self._extract_goals_from_tooltip(
                        tooltip_html, team_is_home
                    )
                    
                    # Déterminer opponent
                    opponent = away_team if team_is_home else home_team
                    
                    matches_data.append({
                        'country': 'Bolivia',
                        'league': league_code,
                        'team': team_name,
                        'opponent': opponent,
                        'date': date,
                        'is_home': team_is_home,
                        'score': score,
                        'goals_scored': goals_scored,
                        'goals_conceded': goals_conceded
                    })
                    
                except Exception as e:
                    continue
            
            print(f"    ✅ {team_name}: {len(matches_data)} matches")
            return matches_data
            
        except Exception as e:
            print(f"    ❌ {team_name}: Erreur - {e}")
            return []
    
    def save_to_db(self, matches_data: List[dict]):
        """
        Sauvegarder les matches en base de données
        COPIE EXACTE de la méthode bulgare
        """
        if not matches_data:
            return
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        inserted = 0
        for match in matches_data:
            try:
                # Générer match_id
                team1, team2 = sorted([match['team'], match['opponent']])
                date_str = match['date']
                match_id = f"{date_str}_{team1}_vs_{team2}"
                
                # Convertir goal_times en JSON (buts marqués ET encaissés)
                # Format bulgare: padding avec des 0 jusqu'à 10 éléments
                goal_times_scored = match['goals_scored'] + [0] * (10 - len(match['goals_scored']))
                goal_times_scored_json = json.dumps(goal_times_scored[:10])
                
                goal_times_conceded = match['goals_conceded'] + [0] * (10 - len(match['goals_conceded']))
                goal_times_conceded_json = json.dumps(goal_times_conceded[:10])
                
                # Calculer goals_for et goals_against
                goals_for = len([g for g in match['goals_scored'] if g > 0])
                goals_against = len([g for g in match['goals_conceded'] if g > 0])
                
                cursor.execute('''
                    INSERT OR REPLACE INTO soccerstats_scraped_matches 
                    (country, league, team, opponent, date, is_home, 
                     score, goals_for, goals_against, goal_times, goal_times_conceded, match_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match['country'],
                    match['league'],
                    match['team'],
                    match['opponent'],
                    date_str,
                    1 if match['is_home'] else 0,
                    match['score'],
                    goals_for,
                    goals_against,
                    goal_times_scored_json,
                    goal_times_conceded_json,
                    match_id
                ))
                
                if cursor.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                print(f"   ❌ Erreur DB: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n💾 Sauvegarde DB: {inserted} matches insérés/mis à jour")
    
    def run(self):
        """Exécuter le scraping complet - MÉTHODE BULGARE"""
        print("\n" + "="*80)
        print("🇧🇴 SCRAPING AUTOMATIQUE - BOLIVIA DIVISION PROFESIONAL")
        print("="*80)
        
        # ÉTAPE 1 : Extraire codes équipes
        teams = self.extract_team_codes("bolivia")
        
        if not teams:
            print("\n❌ Aucune équipe trouvée!")
            return
        
        print("\n" + "="*80)
        print("📥 ÉTAPE 2 : Scraping des matches")
        print("="*80)
        
        # ÉTAPE 2 : Scraper chaque équipe
        all_matches = []
        
        for code, name in teams:
            matches = self.scrape_team(code, name, "bolivia")
            if matches:
                all_matches.extend(matches)
            time.sleep(1)  # Pause entre requêtes
        
        # ÉTAPE 3 : Sauvegarder en DB
        if all_matches:
            self.save_to_db(all_matches)
            print(f"\n✅ TOTAL: {len(all_matches)} matches collectés pour {len(teams)} équipes")
        else:
            print("\n⚠️  Aucun match collecté")
        
        print("\n" + "="*80)
        print("✅ SCRAPING TERMINÉ")
        print("="*80)


def main():
    scraper = BoliviaAutoScraper()
    scraper.run()


if __name__ == "__main__":
    main()
