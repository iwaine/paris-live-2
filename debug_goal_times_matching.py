#!/usr/bin/env python3
"""
Debug script pour vérifier pourquoi les goal_times ne matchent pas
"""

import sqlite3
import requests
import re
from bs4 import BeautifulSoup

def scrape_one_team_debug(team_slug, team_name):
    """Scrape une équipe et compare avec la DB"""
    url = f"https://www.soccerstats.com/teamstats.asp?league=bulgaria&stats={team_slug}"
    
    print(f"\n{'='*80}")
    print(f"🔍 DEBUG: {team_name}")
    print(f"{'='*80}")
    print(f"URL: {url}\n")
    
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Trouver la table
    main_table = soup.find('table', attrs={'cellspacing': '0', 'cellpadding': '0', 'bgcolor': '#cccccc'})
    
    if not main_table:
        print("❌ Table non trouvée")
        return
    
    # Extraire les matches
    scraped_matches = []
    for tr in main_table.find_all('tr', attrs={'height': '36'}):
        try:
            cells = tr.find_all('td')
            if len(cells) < 4:
                continue
            
            # Date (colonne 0)
            date_cell = cells[0]
            date = date_cell.get_text(strip=True)
            
            # HOME (colonne 1)
            home_cell = cells[1]
            home_team = home_cell.get_text(strip=True)
            
            # Score (colonne 2)
            score_cell = cells[2]
            score = score_cell.get_text(strip=True)
            
            # AWAY (colonne 3)
            away_cell = cells[3]
            away_team = away_cell.get_text(strip=True)
            
            # Déterminer is_home
            is_home = bool(home_cell.find('b'))
            
            scraped_matches.append({
                'date': date,
                'home': home_team,
                'away': away_team,
                'score': score,
                'is_home': is_home,
                'team': home_team if is_home else away_team,
                'opponent': away_team if is_home else home_team
            })
        except:
            continue
    
    print(f"📊 Matches scrapés depuis teamstats.asp: {len(scraped_matches)}\n")
    
    # Comparer avec la DB
    conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT date, team, opponent, is_home, goal_times 
        FROM soccerstats_scraped_matches 
        WHERE league='bulgaria' AND team=?
        ORDER BY date DESC
    ''', (team_name,))
    
    db_matches = cursor.fetchall()
    
    print(f"📊 Matches dans la DB pour '{team_name}': {len(db_matches)}\n")
    
    # Afficher les 5 premiers de chaque source
    print(f"{'SCRAPÉ':<50} | {'DB':<50}")
    print(f"{'-'*50} | {'-'*50}")
    
    for i in range(min(10, max(len(scraped_matches), len(db_matches)))):
        scraped_line = ""
        db_line = ""
        
        if i < len(scraped_matches):
            s = scraped_matches[i]
            loc = "HOME" if s['is_home'] else "AWAY"
            scraped_line = f"{s['date']:10} {s['team']:20} vs {s['opponent']:15} ({loc})"
        
        if i < len(db_matches):
            date, team, opp, is_home, gt = db_matches[i]
            loc = "HOME" if is_home else "AWAY"
            has_gt = "✅" if gt else "❌"
            db_line = f"{date:10} {team:20} vs {opp:15} ({loc}) {has_gt}"
        
        print(f"{scraped_line:<50} | {db_line:<50}")
    
    # Chercher le match du 5 Oct dans les deux sources
    print(f"\n{'='*80}")
    print(f"🔍 RECHERCHE: Match du 5 Oct (Botev Plovdiv)")
    print(f"{'='*80}\n")
    
    for s in scraped_matches:
        if '5 Oct' in s['date'] or 'Oct 5' in s['date']:
            print(f"SCRAPÉ: {s}")
    
    cursor.execute('''
        SELECT date, team, opponent, is_home, score, goal_times 
        FROM soccerstats_scraped_matches 
        WHERE league='bulgaria' AND team=? AND (date LIKE '%5 Oct%' OR date LIKE '%Oct 5%')
    ''', (team_name,))
    
    oct5_matches = cursor.fetchall()
    for m in oct5_matches:
        print(f"DB: date={m[0]}, team={m[1]}, opp={m[2]}, is_home={m[3]}, score={m[4]}, goal_times={m[5]}")
    
    conn.close()

if __name__ == '__main__':
    scrape_one_team_debug('u1752-botev-vratsa', 'Botev Vratsa')
