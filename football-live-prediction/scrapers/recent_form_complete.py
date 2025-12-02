"""
Recent Form Complete Scraper - Avec team_id
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger


class RecentFormCompleteScraper:
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def scrape_team_recent_matches(self, team_name: str, league_code: str,
                                   venue: str = 'home', num_matches: int = 4,
                                   team_id: Optional[str] = None) -> List[Dict]:
        """
        Les N derniers matchs pour un venue donné
        
        Args:
            team_name: Nom de l'équipe
            league_code: Code de la ligue (ex: 'england')
            venue: 'home' ou 'away'
            num_matches: Nombre de matchs
            team_id: ID de l'équipe (ex: 'u321' pour Man City)
        """
        # Si team_id fourni, l'utiliser, sinon générer un slug
        if team_id:
            url = f"https://www.soccerstats.com/teamstats.asp?league={league_code}&stats={team_id}-{team_name.lower().replace(' ', '-')}"
        else:
            team_slug = team_name.lower().replace(' ', '-').replace('.', '')
            url = f"https://www.soccerstats.com/teamstats.asp?league={league_code}&stats=u324-{team_slug}"
        
        logger.info(f"Scraping: {team_name} ({venue}) from {url}")
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            tooltips = soup.find_all('a', class_='tooltip4')
            logger.info(f"Found {len(tooltips)} tooltips")
            
            matches = []
            
            for tooltip in tooltips:
                span = tooltip.find('span')
                if not span:
                    continue
                
                parent_row = tooltip.find_parent('tr')
                if not parent_row:
                    continue
                
                cells = parent_row.find_all('td')
                if len(cells) < 4:
                    continue
                
                date_str = cells[0].get_text(strip=True)
                left_team = cells[1].get_text(strip=True)
                right_team = cells[3].get_text(strip=True)
                
                # Left = HOME, Right = AWAY
                team_lower = team_name.lower()
                
                if team_lower in left_team.lower():
                    we_are_home = True
                    opponent = right_team
                elif team_lower in right_team.lower():
                    we_are_home = False
                    opponent = left_team
                else:
                    continue
                
                if venue == 'home' and not we_are_home:
                    continue
                if venue == 'away' and we_are_home:
                    continue
                
                tooltip_html = str(span)
                match_data = self._parse_match_goals_html(tooltip_html, we_are_home)
                
                if match_data:
                    match_data['date'] = date_str
                    match_data['opponent'] = opponent
                    matches.append(match_data)
                    logger.success(f"{date_str} {'vs' if we_are_home else '@'} {opponent}: {match_data['scored_total']}S {match_data['conceded_total']}C")
            
            matches = self._sort_by_date(matches)
            return matches[:num_matches]
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    def _parse_match_goals_html(self, tooltip_html: str, we_are_home: bool) -> Dict:
        pattern = r'<b>(\d+)-(\d+)</b>.*?\((\d{1,2})\)'
        matches = re.findall(pattern, tooltip_html, re.DOTALL)
        
        if not matches:
            return None
        
        scored_minutes = []
        conceded_minutes = []
        home_score = 0
        away_score = 0
        
        for match in matches:
            new_home = int(match[0])
            new_away = int(match[1])
            minute = int(match[2])
            
            if new_home > home_score:
                if we_are_home:
                    scored_minutes.append(minute)
                else:
                    conceded_minutes.append(minute)
                home_score = new_home
            
            elif new_away > away_score:
                if we_are_home:
                    conceded_minutes.append(minute)
                else:
                    scored_minutes.append(minute)
                away_score = new_away
        
        if not scored_minutes and not conceded_minutes:
            return None
        
        scored_by_interval = self._map_to_intervals(scored_minutes)
        conceded_by_interval = self._map_to_intervals(conceded_minutes)
        
        return {
            'scored_by_interval': scored_by_interval,
            'conceded_by_interval': conceded_by_interval,
            'scored_total': len(scored_minutes),
            'conceded_total': len(conceded_minutes),
            'scored_minutes': scored_minutes,
            'conceded_minutes': conceded_minutes
        }
    
    def _map_to_intervals(self, minutes: List[int]) -> Dict:
        intervals = {
            '0-15': 0, '16-30': 0, '31-45': 0,
            '46-60': 0, '61-75': 0, '76-90': 0
        }
        
        for minute in minutes:
            if 0 <= minute <= 15:
                intervals['0-15'] += 1
            elif 16 <= minute <= 30:
                intervals['16-30'] += 1
            elif 31 <= minute <= 45:
                intervals['31-45'] += 1
            elif 46 <= minute <= 60:
                intervals['46-60'] += 1
            elif 61 <= minute <= 75:
                intervals['61-75'] += 1
            elif 76 <= minute <= 90:
                intervals['76-90'] += 1
        
        return intervals
    
    def _sort_by_date(self, matches: List[Dict]) -> List[Dict]:
        def parse_date(date_str):
            try:
                year = datetime.now().year
                return datetime.strptime(f"{date_str} {year}", "%d %b %Y")
            except:
                return datetime.min
        
        return sorted(matches, key=lambda x: parse_date(x.get('date', '')), reverse=True)


if __name__ == "__main__":
    scraper = RecentFormCompleteScraper()
    
    print("="*80)
    print("TEST AVEC TEAM_ID")
    print("="*80)
    
    # Arsenal HOME (u324)
    arsenal_home = scraper.scrape_team_recent_matches(
        'Arsenal', 'england', 'home', 4, team_id='u324'
    )
    print(f"\n✅ Arsenal HOME: {len(arsenal_home)} matchs\n")
    for m in arsenal_home:
        print(f"  {m['date']} vs {m['opponent']}")
        print(f"    Marqués: {m['scored_minutes']}")
        print(f"    Encaissés: {m['conceded_minutes']}\n")
    
    # Man City AWAY (u321)
    city_away = scraper.scrape_team_recent_matches(
        'Manchester City', 'england', 'away', 4, team_id='u321'
    )
    print(f"\n✅ Man City AWAY: {len(city_away)} matchs\n")
    for m in city_away:
        print(f"  {m['date']} @ {m['opponent']}")
        print(f"    Marqués: {m['scored_minutes']}")
        print(f"    Encaissés: {m['conceded_minutes']}\n")
