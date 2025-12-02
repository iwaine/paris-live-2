"""
Recent Form Simple Scraper - Parse HTML avec tri par date
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict
from loguru import logger


class RecentFormSimpleScraper:
    """Scrape les minutes des buts depuis le HTML statique"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def scrape_team_recent_matches(self, team_name: str, league_code: str,
                                   venue: str = 'home', num_matches: int = 4) -> List[Dict]:
        """Scrape les N derniers matchs d'une équipe"""
        team_slug = team_name.lower().replace(' ', '-').replace('.', '')
        url = f"https://www.soccerstats.com/teamstats.asp?league={league_code}&stats=u324-{team_slug}"
        
        logger.info(f"Scraping: {team_name} ({venue})")
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            tooltips = soup.find_all('a', class_='tooltip4')
            logger.info(f"Found {len(tooltips)} matches")
            
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
                
                # Extraire la date
                date_str = cells[0].get_text(strip=True)
                
                right_team = cells[3].get_text(strip=True)
                left_team = cells[1].get_text(strip=True)
                
                # Vérifier home/away
                is_home = team_name in right_team and '<b>' in str(cells[3])
                is_away = team_name in left_team and '<b>' in str(cells[1])
                
                if venue == 'home' and not is_home:
                    continue
                if venue == 'away' and not is_away:
                    continue
                
                tooltip_text = span.get_text()
                match_data = self._parse_goal_minutes(tooltip_text)
                
                if match_data:
                    match_data['date'] = date_str
                    match_data['opponent'] = left_team if is_home else right_team
                    matches.append(match_data)
                    logger.success(f"{date_str}: {match_data['total_goals']} goals")
            
            # Trier par date (plus récent en premier)
            matches = self._sort_by_date(matches)
            
            # Retourner seulement les N plus récents
            return matches[:num_matches]
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    def _sort_by_date(self, matches: List[Dict]) -> List[Dict]:
        """Trie les matchs par date (plus récent en premier)"""
        def parse_date(date_str):
            try:
                year = datetime.now().year
                date_obj = datetime.strptime(f"{date_str} {year}", "%d %b %Y")
                return date_obj
            except:
                return datetime.min
        
        return sorted(matches, key=lambda x: parse_date(x.get('date', '')), reverse=True)
    
    def _parse_goal_minutes(self, tooltip_text: str) -> Dict:
        minute_pattern = re.compile(r'\((\d{1,2})\)')
        minutes = [int(m) for m in minute_pattern.findall(tooltip_text)]
        
        if not minutes:
            return None
        
        goals_by_interval = {
            '0-15': 0, '16-30': 0, '31-45': 0,
            '46-60': 0, '61-75': 0, '76-90': 0
        }
        
        for minute in minutes:
            if 0 <= minute <= 15:
                goals_by_interval['0-15'] += 1
            elif 16 <= minute <= 30:
                goals_by_interval['16-30'] += 1
            elif 31 <= minute <= 45:
                goals_by_interval['31-45'] += 1
            elif 46 <= minute <= 60:
                goals_by_interval['46-60'] += 1
            elif 61 <= minute <= 75:
                goals_by_interval['61-75'] += 1
            elif 76 <= minute <= 90:
                goals_by_interval['76-90'] += 1
        
        return {
            'goals_by_interval': goals_by_interval,
            'total_goals': len(minutes),
            'minutes': minutes
        }


if __name__ == "__main__":
    scraper = RecentFormSimpleScraper()
    
    print("="*80)
    print("TEST SCRAPING FORME PAR INTERVALLE (AVEC TRI)")
    print("="*80)
    
    matches = scraper.scrape_team_recent_matches(
        team_name='Arsenal',
        league_code='england',
        venue='home',
        num_matches=4
    )
    
    print(f"\n✅ {len(matches)} matchs (triés du plus récent):\n")
    
    for i, match in enumerate(matches, 1):
        print(f"Match {i} - {match.get('date', 'N/A')} vs {match.get('opponent', 'N/A')}")
        print(f"  Total: {match['total_goals']} buts - Minutes: {match['minutes']}")
        print(f"  Par intervalle:")
        for interval, goals in match['goals_by_interval'].items():
            if goals > 0:
                print(f"    {interval}: {goals} but(s)")
        print()
