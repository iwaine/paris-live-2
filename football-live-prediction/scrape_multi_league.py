#!/usr/bin/env python3
"""
Multi-League SoccerStats Scraper
Supports all major leagues: Ligue 1, Premier League, La Liga, Serie A, Bundesliga

Usage:
  python3 scrape_multi_league.py france           # Scrape Ligue 1
  python3 scrape_multi_league.py england          # Scrape Premier League
  python3 scrape_multi_league.py spain            # Scrape La Liga
  python3 scrape_multi_league.py italy            # Scrape Serie A
  python3 scrape_multi_league.py germany          # Scrape Bundesliga
  python3 scrape_multi_league.py all              # Scrape toutes les ligues
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiLeagueScraper:
    """Scrape historical team data from SoccerStats for multiple leagues"""
    
    BASE_URL = "https://www.soccerstats.com"
    
    # League configurations: league_id -> (league_name, season, team_ids)
    LEAGUE_CONFIGS = {
        "france": {
            "name": "Ligue 1",
            "league_id": "france",
            "season": "2024",
            "teams": {
                "Angers": "u502-angers",
                "Auxerre": "u7648-auxerre",
                "Brest": "u510-brest",
                "Le Havre": "u7655-le-havre",
                "Lens": "u512-lens",
                "Lille": "u503-lille",
                "Lorient": "u507-lorient",
                "Lyon": "u513-lyon",
                "Marseille": "u517-marseille",
                "Metz": "u515-metz",
                "Monaco": "u505-monaco",
                "Nantes": "u500-nantes",
                "Nice": "u511-nice",
                "PSG": "u518-paris-sg",
                "Paris FC": "u7654-paris-fc",
                "Rennes": "u504-rennes",
                "Strasbourg": "u508-strasbourg",
                "Toulouse": "u7659-toulouse",
            }
        },
        "england": {
            "name": "Premier League",
            "league_id": "england",
            "season": "2024",
            "teams": {}  # À remplir via scraping automatique
        },
        "spain": {
            "name": "La Liga",
            "league_id": "spain",
            "season": "2024",
            "teams": {}  # À remplir via scraping automatique
        },
        "italy": {
            "name": "Serie A",
            "league_id": "italy",
            "season": "2024",
            "teams": {}  # À remplir via scraping automatique
        },
        "germany": {
            "name": "Bundesliga",
            "league_id": "germany",
            "season": "2024",
            "teams": {}  # À remplir via scraping automatique
        },
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch page avec retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def extract_team_ids_from_standings(self, league_id: str) -> Dict[str, str]:
        """
        Extract team IDs automatically from league standings page
        
        Returns: Dict[team_name -> team_id]
        """
        standings_url = f"{self.BASE_URL}/standings.asp?league={league_id}"
        logger.info(f"Fetching standings: {standings_url}")
        
        html = self.fetch_page(standings_url)
        if not html:
            logger.error(f"Failed to fetch standings for {league_id}")
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        teams = {}
        
        # Try to find team links in standings table
        # Format: <a href="/teamstats.asp?league=france&stats=u512-lens">Lens</a>
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if f'league={league_id}' in href and 'stats=u' in href:
                # Extract team name and ID
                team_name = link.text.strip()
                # Extract stats parameter: "u512-lens"
                start = href.find('stats=') + 6
                end = href.find('&', start) if '&' in href[start:] else len(href)
                team_id = href[start:end]
                
                if team_name and team_id:
                    teams[team_name] = team_id
                    logger.debug(f"Found: {team_name} -> {team_id}")
        
        return teams
    
    def parse_match_details(self, match_text: str, team_name: str) -> Optional[Dict]:
        """
        Parse match details from match text
        
        Expected format: "DATE | OPPONENT | SCORE | extra info"
        """
        import re
        
        try:
            # Split match components
            parts = [p.strip() for p in match_text.split('|')]
            if len(parts) < 3:
                return None
            
            date_str = parts[0]
            opponent_full = parts[1]
            score_str = parts[2]
            
            # Parse opponent and home/away
            is_home = opponent_full.startswith('vs')  # or use position logic
            opponent = opponent_full.replace('vs ', '').strip()
            
            # Parse score: "1-2" or "1 - 2"
            score_match = re.search(r'(\d+)\s*-\s*(\d+)', score_str)
            if not score_match:
                return None
            
            goals_for = int(score_match.group(1))
            goals_against = int(score_match.group(2))
            
            # Determine result
            if goals_for > goals_against:
                result = 'W'
            elif goals_for < goals_against:
                result = 'L'
            else:
                result = 'D'
            
            # Extract goal times: (45), (67), etc.
            goal_times = re.findall(r'\((\d+)\)', score_str)
            
            return {
                "opponent": opponent,
                "is_home": is_home,
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
    
    def extract_team_matches(
        self,
        league_id: str,
        team_name: str,
        team_id: str,
        max_matches: int = 100
    ) -> List[Dict]:
        """
        Scrape all matches for a specific team
        
        Returns: List of match dicts with full metadata
        """
        url = f"{self.BASE_URL}/teamstats.asp?league={league_id}&stats={team_id}"
        logger.info(f"Scraping {team_name}: {url}")
        
        html = self.fetch_page(url)
        if not html:
            logger.error(f"Failed to scrape {team_name}")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        # Find table with match history (look for date pattern in cells)
        import re
        
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows:
                continue
            
            # Check if this table contains matches (has date pattern)
            table_text = table.get_text()
            if not re.search(r'\d{1,2}\s+\w{3}', table_text):
                continue
            
            # Parse matches from this table
            for row in rows[1:]:  # Skip header
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if len(cells) < 3:
                    continue
                
                # Try to parse this row as a match
                # Expected format: DATE | TEAMS | SCORE
                match_text = ' | '.join(cells[:3])
                match_data = self.parse_match_details(match_text, team_name)
                
                if match_data:
                    matches.append(match_data)
                    if len(matches) >= max_matches:
                        break
            
            if matches:
                break  # Found the right table
        
        logger.info(f"  → {len(matches)} matches extracted for {team_name}")
        return matches
    
    def scrape_league(self, league_id: str, auto_detect_teams: bool = False) -> Dict:
        """
        Scrape all teams in a league
        
        Returns: Dict with league metadata and all team data
        """
        if league_id not in self.LEAGUE_CONFIGS:
            logger.error(f"League {league_id} not configured")
            return {}
        
        league_config = self.LEAGUE_CONFIGS[league_id]
        league_name = league_config['name']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🏟️  SCRAPING {league_name}")
        logger.info(f"{'='*80}")
        
        # Get team IDs
        teams_dict = league_config.get('teams', {})
        
        if not teams_dict and auto_detect_teams:
            logger.info(f"Auto-detecting team IDs for {league_name}...")
            teams_dict = self.extract_team_ids_from_standings(league_id)
        
        if not teams_dict:
            logger.error(f"No teams found for {league_id}")
            return {}
        
        logger.info(f"Found {len(teams_dict)} teams to scrape")
        
        # Scrape each team
        all_data = {
            "league": league_name,
            "league_id": league_id,
            "season": league_config['season'],
            "teams": {}
        }
        
        for idx, (team_name, team_id) in enumerate(teams_dict.items(), 1):
            logger.info(f"\n[{idx}/{len(teams_dict)}] Scraping {team_name}...")
            
            matches = self.extract_team_matches(league_id, team_name, team_id)
            
            all_data['teams'][team_name] = {
                "team_id": team_id,
                "matches_count": len(matches),
                "matches": matches
            }
            
            time.sleep(1)  # Politeness delay
        
        return all_data
    
    def scrape_all_leagues(self) -> Dict:
        """Scrape all configured leagues"""
        all_leagues_data = {}
        
        for league_id in self.LEAGUE_CONFIGS.keys():
            data = self.scrape_league(league_id, auto_detect_teams=True)
            if data:
                all_leagues_data[league_id] = data
        
        return all_leagues_data
    
    def save_to_json(self, data: Dict, output_path: str = "data/soccerstats_multi_league.json"):
        """Save scraped data to JSON"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Data saved to {output_path}")
    
    def print_stats(self, data: Dict):
        """Print statistics about scraped data"""
        print(f"\n{'='*80}")
        print(f"📊 SCRAPING STATISTICS")
        print(f"{'='*80}\n")
        
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


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-League SoccerStats Scraper")
    parser.add_argument(
        'league',
        nargs='?',
        default='france',
        choices=['france', 'england', 'spain', 'italy', 'germany', 'all'],
        help='League to scrape'
    )
    parser.add_argument(
        '--output',
        default='data/soccerstats_multi_league.json',
        help='Output JSON file path'
    )
    
    args = parser.parse_args()
    
    scraper = MultiLeagueScraper()
    
    if args.league == 'all':
        data = scraper.scrape_all_leagues()
    else:
        data = {args.league: scraper.scrape_league(args.league, auto_detect_teams=True)}
    
    if data:
        scraper.save_to_json(data, args.output)
        scraper.print_stats(data)
    else:
        logger.error("No data scraped")
        sys.exit(1)


if __name__ == "__main__":
    main()
