#!/usr/bin/env python3
"""
Script rapide pour scraper les données historiques de Bulgarie depuis latest.asp
"""

import sys
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "football-live-prediction"))

from utils.database_manager import DatabaseManager

def scrape_bulgaria_matches(max_matches=100):
    """Scrape Bulgaria matches depuis latest.asp"""
    print("\n🔄 Fetching Bulgaria matches from latest.asp...")
    
    url = "https://www.soccerstats.com/latest.asp?league=bulgaria"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    matches = []
    
    # Chercher tous les tables avec matches
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            if len(matches) >= max_matches:
                break
                
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            
            # Chercher le pattern: Team1 X:Y Team2
            text = row.get_text(strip=True)
            
            # Pattern pour score type "3:1" ou "0:0"
            score_match = re.search(r'(\d+):(\d+)', text)
            if not score_match:
                continue
            
            home_goals = int(score_match.group(1))
            away_goals = int(score_match.group(2))
            
            # Extraire les noms d'équipes
            # Chercher le texte avant et après le score
            parts = text.split(score_match.group(0))
            if len(parts) != 2:
                continue
            
            # Nettoyer les noms d'équipes
            home_team = parts[0].strip()
            away_team = parts[1].strip()
            
            # Filtrer les lignes qui ne sont pas des matches
            if not home_team or not away_team:
                continue
            if len(home_team) < 3 or len(away_team) < 3:
                continue
            if any(x in text.lower() for x in ['total', 'average', 'league', 'table']):
                continue
            
            # Chercher une date si possible
            match_date = datetime.now().strftime('%Y-%m-%d')
            
            match_data = {
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'away_goals': away_goals,
                'final_score': f"{home_goals}:{away_goals}",
                'match_date': match_date,
                'league': 'bulgaria'
            }
            
            # Éviter les doublons
            if match_data not in matches:
                matches.append(match_data)
                print(f"   ✓ {home_team} {home_goals}:{away_goals} {away_team}")
    
    return matches

def main():
    print("\n" + "=" * 80)
    print("🇧🇬 SCRAPING BULGARIA - Parva Liga (Method 2)")
    print("=" * 80)

    # Initialiser DB
    db = DatabaseManager(db_path="football-live-prediction/data/predictions.db")

    max_matches = 100

    try:
        matches = scrape_bulgaria_matches(max_matches=max_matches)

        if not matches:
            print(f"\n   ❌ Aucun match scrappé pour Bulgaria")
            return

        print(f"\n   ✅ {len(matches)} matches scrappés")

        # Insérer dans la base
        total_inserted = 0
        total_goals = 0
        teams = set()

        for i, match in enumerate(matches, 1):
            try:
                # Insérer le match
                match_id = db.insert_match(match)
                
                if match_id:
                    total_inserted += 1
                    total_goals += match.get("home_goals", 0) + match.get("away_goals", 0)
                    teams.add(match.get("home_team"))
                    teams.add(match.get("away_team"))

            except Exception as e:
                print(f"   ⚠️ Erreur insertion: {e}")
                continue

        print(f"\n   📊 RÉSULTAT:")
        print(f"      Matches insérés: {total_inserted}")
        print(f"      Buts totaux: {total_goals}")
        print(f"      Équipes uniques: {len(teams)}")
        if teams:
            print(f"      Équipes: {', '.join(sorted(teams)[:10])}")

        print("\n✅ SCRAPING TERMINÉ!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
