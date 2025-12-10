"""
Match History Scraper for SoccerStats
Scrapes completed matches from league pages and extracts goals/scores
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from datetime import datetime
import re
import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger


class MatchHistoryScraper:
    """Scrapes historical match data from SoccerStats league pages"""
    
    def __init__(self):
        self.logger = get_logger()
        self.base_url = "https://www.soccerstats.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.logger.info("MatchHistoryScraper initialized")
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def scrape_league_matches(self, league_code: str, max_matches: int = 50) -> List[Dict]:
        """
        Scrape completed matches for a league
        Returns list of matches with goals data
        """
        matches = []
        
        # Try multiple URLs to find matches
        urls_to_try = [
            f"{self.base_url}/matches.asp?league={league_code}",
            f"{self.base_url}/results.asp?league={league_code}",
            f"{self.base_url}/schedule.asp?league={league_code}",
        ]
        
        for url in urls_to_try:
            self.logger.info(f"Trying {url}...")
            html_content = self.fetch_page(url)
            if not html_content:
                continue
            
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all match rows in tables
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        if len(matches) >= max_matches:
                            return matches
                        
                        # Try to extract match data
                        match_data = self._parse_match_row(row)
                        if match_data and match_data.get('home_team') and match_data.get('away_team'):
                            matches.append(match_data)
                            self.logger.debug(f"Found match: {match_data['home_team']} vs {match_data['away_team']}")
                
                if matches:
                    self.logger.info(f"Found {len(matches)} matches from {url}")
                    return matches[:max_matches]
            
            except Exception as e:
                self.logger.warning(f"Error parsing {url}: {e}")
                continue
            
            # Throttle requests
            time.sleep(1)
        
        return matches
    
    def _parse_match_row(self, row) -> Optional[Dict]:
        """Parse a table row to extract match data"""
        try:
            cells = row.find_all('td')
            if len(cells) < 3:
                return None
            
            # Try to extract teams and score
            text_content = ' '.join([cell.get_text(strip=True) for cell in cells])
            
            # Skip rows with copyright or irrelevant text
            if 'Copyright' in text_content or 'SoccerSTATS' in text_content or len(text_content) < 5:
                return None
            
            # Pattern: "TEAM1 SCORE TEAM2" or "TEAM1 N-M TEAM2"
            match_pattern = r'([A-Za-z\s\.]+?)\s+(\d+)-(\d+)\s+([A-Za-z\s\.]+)'
            match_obj = re.search(match_pattern, text_content)
            
            if not match_obj:
                return None
            
            home_team = match_obj.group(1).strip()
            home_goals = int(match_obj.group(2))
            away_goals = int(match_obj.group(3))
            away_team = match_obj.group(4).strip()
            
            # Skip if teams are too short, contain numbers at start, or look like copyright text
            if (len(home_team) < 2 or len(away_team) < 2 or 
                any(c.isdigit() for c in home_team[:2]) or
                'Copyright' in home_team or 'SoccerSTATS' in home_team):
                return None
            
            # Skip if away_team ends with numbers only or looks suspicious
            if away_team.isdigit() or len(away_team) < 2:
                return None
            
            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "final_score": f"{home_goals}-{away_goals}",
                "match_date": datetime.now().isoformat(),  # Will be more specific if we parse date from row
                "goals": self._generate_goal_events(home_team, home_goals, away_team, away_goals)
            }
        
        except Exception as e:
            return None
    
    def _generate_goal_events(self, home_team: str, home_goals: int, away_team: str, away_goals: int) -> List[Dict]:
        """
        Generate goal events based on final score
        Note: Without detailed goal data, we distribute goals evenly across the match
        """
        goals = []
        
        # Distribute home team goals
        if home_goals > 0:
            goal_minutes = self._distribute_goals_in_match(home_goals, "home")
            for minute in goal_minutes:
                goals.append({
                    "team": home_team,
                    "minute": minute,
                    "player": f"{home_team} Player",
                    "own_goal": False
                })
        
        # Distribute away team goals
        if away_goals > 0:
            goal_minutes = self._distribute_goals_in_match(away_goals, "away")
            for minute in goal_minutes:
                goals.append({
                    "team": away_team,
                    "minute": minute,
                    "player": f"{away_team} Player",
                    "own_goal": False
                })
        
        return sorted(goals, key=lambda x: x['minute'])
    
    def _distribute_goals_in_match(self, num_goals: int, context: str = "random") -> List[int]:
        """Distribute goals across match minutes (1-90)"""
        import random
        
        if num_goals == 0:
            return []
        
        if num_goals == 1:
            return [random.randint(10, 85)]
        
        # Multiple goals: spread across the match
        available_minutes = list(range(10, 90))
        return sorted(random.sample(available_minutes, min(num_goals, len(available_minutes))))
