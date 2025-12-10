#!/usr/bin/env python3
"""
Scrape Top 4 Leagues: Premier League, La Liga, Serie A, Bundesliga
Extract team IDs from latest.asp pages and scrape matches
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
import re
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Top4LeaguesScraper:
    """Scrape from latest.asp pages"""
    
    BASE_URL = "https://www.soccerstats.com"
    
    TOP_4_LEAGUES = {
        "england": {
            "name": "Premier League",
            "latest_url": "https://www.soccerstats.com/latest.asp?league=england"
        },
        "spain": {
            "name": "LaLiga",
            "latest_url": "https://www.soccerstats.com/latest.asp?league=spain"
        },
        "italy": {
            "name": "Serie A",
            "latest_url": "https://www.soccerstats.com/latest.asp?league=italy"
        },
        "germany": {
            "name": "Bundesliga",
            "latest_url": "https://www.soccerstats.com/latest.asp?league=germany"
        },
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url, max_retries=3):
        """Fetch page with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def extract_team_ids_from_latest(self, league_id, latest_url):
        """Extract team IDs from latest.asp page"""
        logger.info(f"Fetching latest matches page: {latest_url}")
        
        html = self.fetch_page(latest_url)
        if not html:
            logger.error(f"Failed to fetch {latest_url}")
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        teams = {}
        
        # Extract team links from match tables
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Look for teamstats.asp links
            if f'league={league_id}' in href and 'stats=u' in href:
                team_name = link.text.strip()
                # Extract team_id
                start = href.find('stats=') + 6
                end = href.find('&', start) if '&' in href[start:] else len(href)
                team_id = href[start:end]
                
                if team_name and team_id and len(team_id) > 2:
                    teams[team_name] = team_id
                    logger.debug(f"  Found: {team_name} -> {team_id}")
        
        # Remove duplicates and keep first occurrence
        seen = set()
        unique_teams = {}
        for name, tid in teams.items():
            if name not in seen:
                unique_teams[name] = tid
                seen.add(name)
        
        logger.info(f"✅ {len(unique_teams)} unique teams found for {league_id}")
        return unique_teams
    
    def parse_match(self, match_text):
        """Parse match details"""
        try:
            parts = [p.strip() for p in match_text.split('|')]
            if len(parts) < 3:
                return None
            
            date_str = parts[0]
            opponent = parts[1].replace('vs ', '').strip()
            score_str = parts[2]
            
            score_match = re.search(r'(\d+)\s*-\s*(\d+)', score_str)
            if not score_match:
                return None
            
            goals_for = int(score_match.group(1))
            goals_against = int(score_match.group(2))
            
            if goals_for > goals_against:
                result = 'W'
            elif goals_for < goals_against:
                result = 'L'
            else:
                result = 'D'
            
            goal_times = re.findall(r'\((\d+)\)', score_str)
            
            return {
                "opponent": opponent,
                "is_home": 1,
                "score": f"{goals_for}-{goals_against}",
                "goals_for": goals_for,
                "goals_against": goals_against,
                "goal_times": goal_times,
                "result": result,
                "date": date_str,
            }
        except Exception as e:
            logger.debug(f"Error parsing match: {e}")
            return None
    
    def extract_team_matches(self, league_id, team_name, team_id, max_matches=50):
        """Scrape matches for a team"""
        url = f"{self.BASE_URL}/teamstats.asp?league={league_id}&stats={team_id}"
        logger.info(f"  Scraping {team_name}...")
        
        html = self.fetch_page(url)
        if not html:
            logger.warning(f"    Failed to scrape {team_name}")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        # Find table with matches (look for date pattern)
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows:
                continue
            
            table_text = table.get_text()
            if not re.search(r'\d{1,2}\s+\w{3}', table_text):
                continue
            
            # Parse matches
            for row in rows[1:]:
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if len(cells) < 3:
                    continue
                
                match_text = ' | '.join(cells[:3])
                match_data = self.parse_match(match_text)
                
                if match_data:
                    matches.append(match_data)
                    if len(matches) >= max_matches:
                        break
            
            if matches:
                break
        
        if matches:
            logger.info(f"    ✅ {len(matches)} matches")
        else:
            logger.warning(f"    ⚠️  No matches found")
        
        return matches
    
    def scrape_league(self, league_id):
        """Scrape all teams in a league"""
        league_config = self.TOP_4_LEAGUES[league_id]
        league_name = league_config['name']
        latest_url = league_config['latest_url']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🏟️  {league_name.upper()}")
        logger.info(f"{'='*60}")
        
        # Get team IDs from latest page
        teams_dict = self.extract_team_ids_from_latest(league_id, latest_url)
        
        if not teams_dict:
            logger.error(f"No teams found for {league_id}")
            return None
        
        # Scrape each team
        all_data = {
            "league": league_name,
            "league_id": league_id,
            "teams": {}
        }
        
        for idx, (team_name, team_id) in enumerate(teams_dict.items(), 1):
            logger.info(f"[{idx}/{len(teams_dict)}] {team_name}")
            
            matches = self.extract_team_matches(league_id, team_name, team_id)
            
            all_data['teams'][team_name] = {
                "team_id": team_id,
                "matches_count": len(matches),
                "matches": matches
            }
            
            time.sleep(0.3)  # Politeness delay
        
        return all_data
    
    def scrape_all_top_4(self):
        """Scrape all 4 top leagues"""
        all_leagues = {}
        
        for league_id in ["england", "spain", "italy", "germany"]:
            try:
                data = self.scrape_league(league_id)
                if data:
                    all_leagues[league_id] = data
                time.sleep(2)  # Between leagues
            except Exception as e:
                logger.error(f"Error scraping {league_id}: {e}")
        
        return all_leagues
    
    def save_to_json(self, data, output_path="data/soccerstats_top4_leagues.json"):
        """Save scraped data"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Data saved to {output_path}")
    
    def print_stats(self, data):
        """Print statistics"""
        print(f"\n{'='*80}")
        print(f"📊 TOP 4 LEAGUES SCRAPING COMPLETE")
        print(f"{'='*80}\n")
        
        total_all = 0
        for league_id, league_data in data.items():
            league_name = league_data.get('league', league_id)
            teams = league_data.get('teams', {})
            
            total_matches = sum(t['matches_count'] for t in teams.values())
            avg_matches = total_matches / len(teams) if teams else 0
            
            print(f"🏟️  {league_name}")
            print(f"   Teams: {len(teams)}")
            print(f"   Total matches: {total_matches}")
            print(f"   Avg per team: {avg_matches:.1f}")
            print()
            
            total_all += total_matches
        
        print(f"{'='*80}")
        print(f"🎯 TOTAL: {total_all} matches from top 4 leagues")
        print(f"{'='*80}\n")


def main():
    logger.info("\n🚀 SCRAPING TOP 4 LEAGUES (Fixed)\n")
    
    scraper = Top4LeaguesScraper()
    data = scraper.scrape_all_top_4()
    
    if data:
        scraper.save_to_json(data)
        scraper.print_stats(data)
        logger.info("✅ Scraping complete!")
        return True
    else:
        logger.error("❌ No data scraped")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
