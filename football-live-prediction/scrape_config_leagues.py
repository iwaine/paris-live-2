#!/usr/bin/env python3
"""
Multi-League SoccerStats Scraper - Configuration-driven

Lire config.yaml et scraper TOUTES les ligues configurées
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
import yaml
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigDrivenScraper:
    """Scrape all leagues from config.yaml"""
    
    BASE_URL = "https://www.soccerstats.com"
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def load_config(self) -> bool:
        """Load config.yaml"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"✅ Loaded config: {len(self.config.get('leagues', []))} leagues")
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def extract_league_id_from_url(self, url: str) -> str:
        """Extract league_id from URL like https://www.soccerstats.com/latest.asp?league=france"""
        match = re.search(r'league=([^&]+)', url)
        if match:
            return match.group(1)
        return None
    
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
                    time.sleep(2 ** attempt)
        return None
    
    def extract_team_ids_from_standings(self, league_id: str) -> Dict[str, str]:
        """Extract team IDs from standings page"""
        standings_url = f"{self.BASE_URL}/standings.asp?league={league_id}"
        logger.debug(f"Fetching standings: {standings_url}")
        
        html = self.fetch_page(standings_url)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        teams = {}
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if f'league={league_id}' in href and 'stats=u' in href:
                team_name = link.text.strip()
                start = href.find('stats=') + 6
                end = href.find('&', start) if '&' in href[start:] else len(href)
                team_id = href[start:end]
                
                if team_name and team_id:
                    teams[team_name] = team_id
                    logger.debug(f"Found: {team_name} -> {team_id}")
        
        return teams
    
    def parse_match_details(self, match_text: str) -> Optional[Dict]:
        """Parse match details from HTML"""
        try:
            parts = [p.strip() for p in match_text.split('|')]
            if len(parts) < 3:
                return None
            
            date_str = parts[0]
            opponent_str = parts[1]
            score_str = parts[2]
            
            # Parse opponent and home/away
            is_home = opponent_str.startswith('vs')
            opponent = opponent_str.replace('vs ', '').strip()
            
            # Parse score
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
            
            # Extract goal times
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
        """Scrape all matches for a specific team"""
        url = f"{self.BASE_URL}/teamstats.asp?league={league_id}&stats={team_id}"
        
        html = self.fetch_page(url)
        if not html:
            logger.warning(f"Failed to scrape {team_name}")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows:
                continue
            
            table_text = table.get_text()
            if not re.search(r'\d{1,2}\s+\w{3}', table_text):
                continue
            
            for row in rows[1:]:
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if len(cells) < 3:
                    continue
                
                match_text = ' | '.join(cells[:3])
                match_data = self.parse_match_details(match_text)
                
                if match_data:
                    matches.append(match_data)
                    if len(matches) >= max_matches:
                        return matches[:max_matches]
        
        return matches[:max_matches]
    
    def scrape_league(self, league_name: str, league_id: str) -> Dict:
        """Scrape all teams in a league"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🏟️  SCRAPING: {league_name}")
        logger.info(f"{'='*80}")
        
        # Extract team IDs
        teams_dict = self.extract_team_ids_from_standings(league_id)
        
        if not teams_dict:
            logger.warning(f"No teams found for {league_name} ({league_id})")
            return {}
        
        logger.info(f"Found {len(teams_dict)} teams to scrape")
        
        all_data = {
            "league": league_name,
            "league_id": league_id,
            "teams": {}
        }
        
        for idx, (team_name, team_id) in enumerate(teams_dict.items(), 1):
            logger.info(f"  [{idx}/{len(teams_dict)}] {team_name}...", end="")
            
            matches = self.extract_team_matches(league_id, team_name, team_id)
            
            if matches:
                logger.info(f" ✅ {len(matches)} matches")
            else:
                logger.info(f" ⚠️  no matches")
            
            all_data['teams'][team_name] = {
                "team_id": team_id,
                "matches_count": len(matches),
                "matches": matches
            }
            
            time.sleep(0.5)  # Politeness delay
        
        return all_data
    
    def scrape_all_leagues(self) -> Dict:
        """Scrape all leagues from config"""
        if not self.config:
            logger.error("Config not loaded")
            return {}
        
        all_data = {}
        leagues = self.config.get('leagues', [])
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🌍 SCRAPING ALL {len(leagues)} LEAGUES FROM CONFIG.YAML")
        logger.info(f"{'='*80}\n")
        
        for idx, league_info in enumerate(leagues, 1):
            league_name = league_info.get('name', 'Unknown')
            url = league_info.get('url', '')
            
            league_id = self.extract_league_id_from_url(url)
            if not league_id:
                logger.warning(f"Could not extract league_id from {url}")
                continue
            
            logger.info(f"\n[{idx}/{len(leagues)}] {league_name} ({league_id})")
            
            data = self.scrape_league(league_name, league_id)
            if data:
                all_data[league_id] = data
            
            time.sleep(1)  # Rate limiting between leagues
        
        return all_data
    
    def save_to_json(self, data: Dict, output_path: str = "data/soccerstats_all_leagues.json"):
        """Save scraped data to JSON"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Data saved to {output_path}")
    
    def print_summary(self, data: Dict):
        """Print summary statistics"""
        print(f"\n{'='*80}")
        print(f"📊 SCRAPING SUMMARY")
        print(f"{'='*80}\n")
        
        total_leagues = len(data)
        total_teams = 0
        total_matches = 0
        
        for league_id, league_data in sorted(data.items()):
            league_name = league_data.get('league', league_id)
            teams = league_data.get('teams', {})
            
            leagues_teams_count = len(teams)
            leagues_matches = sum(t['matches_count'] for t in teams.values())
            
            total_teams += leagues_teams_count
            total_matches += leagues_matches
            
            print(f"📍 {league_name}")
            print(f"   Teams: {leagues_teams_count}")
            print(f"   Matches: {leagues_matches}")
            print()
        
        print(f"{'='*80}")
        print(f"📈 TOTALS")
        print(f"   Leagues: {total_leagues}")
        print(f"   Teams: {total_teams}")
        print(f"   Matches: {total_matches}")
        print(f"{'='*80}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Config-driven Multi-League Scraper")
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config.yaml'
    )
    parser.add_argument(
        '--output',
        default='data/soccerstats_all_leagues.json',
        help='Output JSON file path'
    )
    
    args = parser.parse_args()
    
    scraper = ConfigDrivenScraper(args.config)
    
    if not scraper.load_config():
        return False
    
    data = scraper.scrape_all_leagues()
    
    if data:
        scraper.save_to_json(data, args.output)
        scraper.print_summary(data)
        return True
    else:
        logger.error("No data scraped")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
