#!/usr/bin/env python3
"""
Scrape historical match data from SoccerStats for French League
Extracts: team names, matches with goals by minute, home/away context
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import time
from urllib.parse import urljoin
import argparse
import os

BASE_URL = "https://www.soccerstats.com"
parser = argparse.ArgumentParser()
parser.add_argument('--league', default='france', help='Code de la ligue SoccerStats (ex: france, germany, spain, italy)')
args = parser.parse_args()
league_code = args.league
LEAGUE_PAGE = f"{BASE_URL}/latest.asp?league={league_code}"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "data/predictions.db")

def get_team_links(league_page_url):
    """Extract team names and their stats page links from league standings"""
    print(f"📥 Fetching league page: {league_page_url}")
    
    try:
        response = requests.get(league_page_url, timeout=10, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching league page: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    teams = []
    
    # Extract all teamstats links from page
    team_links = soup.find_all('a', href=lambda x: x and 'teamstats.asp' in (x or ''))
    
    seen = set()
    for link in team_links:
        team_name = link.get_text(strip=True)
        href = link.get('href')
        
        # Skip if has "stats" suffix in name
        if not team_name or 'stats' in team_name.lower() or href is None:
            continue
        
        # Avoid duplicates and keep only first occurrence
        if team_name not in seen:
            team_url = urljoin(BASE_URL, href)
            teams.append({
                'name': team_name,
                'url': team_url
            })
            seen.add(team_name)
            print(f"  ✓ {team_name}")
            
            # Only keep first 18 (Ligue 1 has exactly 18 teams)
            if len(teams) >= 18:
                break
    
    print(f"\n✅ Found {len(teams)} teams\n")
    return teams


def extract_goals_from_tooltip(tooltip_text):
    """
    Parse tooltip text to extract goal minutes and scorers
    Format: "0-1 Player Name (minute)" or "0-1 Player Name (45) pen."
    
    Returns: dict with 'goals' list containing [minute, team, player]
    """
    goals = []
    lines = tooltip_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or '---' in line:
            continue
        
        # Match pattern: "X-Y PlayerName (minute)" or "X-Y PlayerName (minute) pen."
        match = re.match(r'^(\d+)-(\d+)\s+(.+?)\s+\((\d+)\)', line)
        if match:
            score_left, score_right, player, minute = match.groups()
            score_left, score_right, minute = int(score_left), int(score_right), int(minute)
            
            # Determine which team scored (left or right of dash)
            # This is the score AFTER the goal, so:
            # - If score_left increased from previous, it's a HOME goal
            # - If score_right increased from previous, it's an AWAY goal
            # We need to track progression
            goals.append({
                'minute': minute,
                'score_left': score_left,
                'score_right': score_right,
                'player': player
            })
    
    return goals


def parse_match_row(row, team_name):
    """
    Parse a single match row from team's history
    Returns: match dict or None
    
    Logic: If OUR team is in bold in opponent_td, WE ARE HOME
           If opponent is in bold, OPPONENT is home (we're away)
           If no bold, check position relative to score
    """
    tds = row.find_all('td')
    if len(tds) < 4:
        return None
    
    try:
        # Date
        date_text = tds[0].get_text(strip=True)
        
        # Opponent cell
        opponent_td = tds[1]
        opponent = opponent_td.get_text(strip=True).strip()
        
        # Check bold - if opponent_td contains <b>, opponent is bold = they're home
        # If it doesn't contain <b>, we (team_name) are home
        has_bold = opponent_td.find('b') is not None
        
        if has_bold:
            # Opponent is bold = opponent is home team, we are away
            is_home = False
        else:
            # We're home (no bold means our team is on left side)
            is_home = True
        
        # Score tooltip
        score_td = tds[2]
        score_link = score_td.find('a', {'class': 'tooltip4'})
        
        if not score_link:
            return None
        
        score_text = score_link.get_text(strip=True)
        
        # Extract score: "0 - 1" format
        score_match = re.search(r'(\d+)\s*-\s*(\d+)', score_text)
        if not score_match:
            return None
        
        left_score, right_score = int(score_match.group(1)), int(score_match.group(2))
        
        # Get tooltip content
        span = score_link.find('span')
        tooltip_text = span.get_text(strip=True) if span else ""
        
        # Parse goals from tooltip
        goals_data = extract_goals_from_tooltip(tooltip_text)
        
        # Reconstruct goal events
        events = []
        prev_left, prev_right = 0, 0
        
        for goal in goals_data:
            # Determine scorer team
            if goal['score_left'] > prev_left:
                scorer_team = 'home'
            else:
                scorer_team = 'away'
            
            events.append({
                'minute': goal['minute'],
                'event_type': 'goal',
                'team': scorer_team,
                'player': goal['player']
            })
            
            prev_left = goal['score_left']
            prev_right = goal['score_right']
        
        return {
            'date': date_text,
            'home_team': team_name if is_home else opponent,
            'away_team': opponent if is_home else team_name,
            'home_goals': left_score if is_home else right_score,
            'away_goals': right_score if is_home else left_score,
            'events': events,
            'league': league_code
        }
    
    except Exception as e:
        print(f"  ⚠️ Error parsing row: {e}")
        return None


def scrape_team_history(team_name, team_url):
    """
    Scrape all historical matches for a team
    Returns: list of match dicts
    """
    print(f"📥 Scraping {team_name}...")
    
    try:
        response = requests.get(team_url, timeout=10, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ❌ Error: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find results table
    table = soup.find('table', {'cellspacing': '0', 'cellpadding': '0', 'bgcolor': '#cccccc'})
    if not table:
        print(f"  ⚠️ No results table found")
        return []
    
    # Skip first header row
    rows = table.find_all('tr')[1:]
    
    matches = []
    for row in rows:
        # Skip footer/spacer rows
        if row.get('style') and 'background-color:#fafafa' in row.get('style', ''):
            continue
        if row.get('style') and 'background-color:#e0e0e0' in row.get('style', ''):
            continue
        
        match = parse_match_row(row, team_name)
        if match:
            matches.append(match)
    
    print(f"  ✓ Found {len(matches)} matches")
    return matches


def save_to_db(all_matches):
    """Save matches to SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop and recreate table
    cursor.execute("DROP TABLE IF EXISTS soccerstats_matches")
    cursor.execute("""
        CREATE TABLE soccerstats_matches (
            id INTEGER PRIMARY KEY,
            date TEXT,
            home_team TEXT,
            away_team TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            events_json TEXT,
            league TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    inserted = 0
    for match in all_matches:
        events_json = json.dumps(match['events'])
        cursor.execute("""
            INSERT INTO soccerstats_matches 
            (date, home_team, away_team, home_goals, away_goals, events_json, league)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            match['date'],
            match['home_team'],
            match['away_team'],
            match['home_goals'],
            match['away_goals'],
            events_json,
            match.get('league', league_code)
        ))
        inserted += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Saved {inserted} matches to database")


def main():
    print("\n" + "="*80)
    print(f"SOCCERSTATS HISTORICAL DATA SCRAPER - {league_code.upper()}")
    print("="*80)
    
    # Get team list
    teams = get_team_links(LEAGUE_PAGE)
    
    if not teams:
        print("❌ No teams found")
        return
    
    all_matches = []
    
    # Scrape each team
    for idx, team in enumerate(teams, 1):
        print(f"\n[{idx}/{len(teams)}]", end=" ")
        matches = scrape_team_history(team['name'], team['url'])
        all_matches.extend(matches)
        time.sleep(1)  # Rate limiting
    
    print(f"\n\n📊 SUMMARY:")
    print(f"  Total matches scraped: {len(all_matches)}")
    
    if all_matches:
        # Save to database
        save_to_db(all_matches)
        
        # Show sample
        print(f"\n📋 SAMPLE MATCHES:")
        for match in all_matches[:3]:
            print(f"  {match['date']} | {match['home_team']} {match['home_goals']}-{match['away_goals']} {match['away_team']}")
            if match['events']:
                for event in match['events']:
                    print(f"    └─ Min {event['minute']}: {event['team'].upper()} ({event['player']})")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
