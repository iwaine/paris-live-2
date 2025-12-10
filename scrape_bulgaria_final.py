#!/usr/bin/env python3
"""
Scraper Bulgarie - Direct team extraction
"""

import sys
import re
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "football-live-prediction"))

from scrape_config_leagues import ConfigDrivenScraper
from utils.database_manager import DatabaseManager

def extract_bulgaria_teams():
    """Extraire les équipes bulgares depuis latest.asp"""
    import requests
    from bs4 import BeautifulSoup
    
    url = "https://www.soccerstats.com/latest.asp?league=bulgaria"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    teams = {}
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if 'stats=u' in href and 'bulgaria' in href:
            team_name = link.get_text(strip=True)
            match = re.search(r'stats=([^&]+)', href)
            if match and team_name and len(team_name) > 2:
                teams[team_name] = match.group(1)
    
    return teams

def main():
    print("\n" + "=" * 80)
    print("🇧🇬 SCRAPING BULGARIA - Direct Team Method")
    print("=" * 80)
    
    # Extraire les équipes
    print("\n🔍 Extraction des équipes bulgares...")
    teams_dict = extract_bulgaria_teams()
    
    if not teams_dict:
        print("❌ Aucune équipe trouvée")
        return
    
    print(f"✅ {len(teams_dict)} équipes trouvées:")
    for team in list(teams_dict.keys())[:10]:
        print(f"   - {team}")
    if len(teams_dict) > 10:
        print(f"   ... et {len(teams_dict) - 10} autres")
    
    # Initialiser scraper et DB
    scraper = ConfigDrivenScraper()
    db = DatabaseManager(db_path="data/predictions.db")
    
    league_id = "bulgaria"
    max_matches_per_team = 50  # Augmenter pour plus de données historiques
    
    all_matches = []  # Liste de tuples (team_name, match_data)
    processed_teams = 0
    
    print(f"\n🔄 Scraping des matches (max {max_matches_per_team} par équipe)...\n")
    
    for idx, (team_name, team_id) in enumerate(teams_dict.items(), 1):
        print(f"  [{idx}/{len(teams_dict)}] {team_name}...", end=" ", flush=True)
        
        try:
            matches = scraper.extract_team_matches(league_id, team_name, team_id, max_matches=max_matches_per_team)
            
            if matches:
                # Ajouter le team_name à chaque match
                for match in matches:
                    all_matches.append((team_name, match))
                print(f"✅ {len(matches)} matches")
                processed_teams += 1
            else:
                print(f"⚠️  0 matches")
            
            time.sleep(0.5)  # Politesse
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    print(f"\n📊 Total matches collectés: {len(all_matches)}")
    
    # Convertir et dédupliquer les matches
    unique_matches = {}
    for team_name, match in all_matches:
        # Le scraper retourne opponent qui contient "Team1 -Team2" ou "Team1- Team2"
        opponent_raw = match.get('opponent', '').strip()
        
        # Parser le opponent pour extraire le vrai nom
        # Format: "Slavia Sofia -Dobrudzha" ou "Dobrudzha- Lok. Plovdiv"
        # On cherche le délimiteur " -" ou "- "
        import re
        parts = re.split(r'\s*-\s*', opponent_raw)
        
        # Identifier quel est l'opponent réel (celui qui n'est pas team_name)
        opponent = None
        for part in parts:
            part_clean = part.strip()
            if part_clean and part_clean != team_name:
                opponent = part_clean
                break
        
        if not opponent:
            # Fallback: prendre opponent_raw
            opponent = opponent_raw.replace(' -', '').replace('- ', '').replace(team_name, '').strip()
        
        # Convertir le format (opponent, is_home) vers (home_team, away_team)
        if match.get('is_home'):
            home = team_name
            away = opponent
            home_goals = match.get('goals_for', 0)
            away_goals = match.get('goals_against', 0)
        else:
            home = opponent
            away = team_name
            home_goals = match.get('goals_against', 0)
            away_goals = match.get('goals_for', 0)
        
        key = (home, away, match.get('score', ''), match.get('date', ''))
        if key not in unique_matches:
            unique_matches[key] = {
                'home_team': home,
                'away_team': away,
                'home_goals': home_goals,
                'away_goals': away_goals,
                'score': match.get('score', '0-0').replace('-', ':'),
                'date': match.get('date', ''),
            }
    
    print(f"   Matches uniques: {len(unique_matches)}")
    
    # Insérer dans la DB
    print(f"\n💾 Insertion dans la base de données...")
    inserted = 0
    teams_set = set()
    
    import sqlite3
    conn = sqlite3.connect("data/predictions.db")
    cursor = conn.cursor()
    
    for match in unique_matches.values():
        try:
            # Format pour soccerstats_scraped_matches: team, opponent, is_home
            # On insère 2 fois: une fois pour home, une fois pour away
            
            # Entrée pour l'équipe domicile
            cursor.execute('''
                INSERT OR IGNORE INTO soccerstats_scraped_matches
                (team, opponent, date, score, goals_for, goals_against, is_home, league)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match['home_team'],
                match['away_team'],
                match['date'],
                match['score'],
                match['home_goals'],
                match['away_goals'],
                1,  # is_home = True
                league_id
            ))
            
            # Entrée pour l'équipe visiteur
            cursor.execute('''
                INSERT OR IGNORE INTO soccerstats_scraped_matches
                (team, opponent, date, score, goals_for, goals_against, is_home, league)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match['away_team'],
                match['home_team'],
                match['date'],
                match['score'],
                match['away_goals'],
                match['home_goals'],
                0,  # is_home = False
                league_id
            ))
            
            inserted += 2
            teams_set.add(match['home_team'])
            teams_set.add(match['away_team'])
        except Exception as e:
            print(f"⚠️ Erreur: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ RÉSULTAT FINAL:")
    print(f"   Matches insérés: {inserted}")
    print(f"   Équipes uniques: {len(teams_set)}")
    print(f"   Équipes: {', '.join(sorted(teams_set)[:10])}")
    
    print("\n✅ SCRAPING TERMINÉ!")
    print("=" * 80)

if __name__ == "__main__":
    main()
