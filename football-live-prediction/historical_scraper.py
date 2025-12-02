"""
Historical Data Scraper for SoccerStats.com

Purpose: Scrape 1000-2000 historical matches with event data (goals @ minute)
         to create training labels for ML model.

Strategy:
  1. Iterate over configured leagues (config.yaml)
  2. For each league: fetch 50-100 recent matches
  3. For each match:
     - Parse home/away teams, final score, events list
     - Extract goals (minute + team)
     - Generate labels for intervals [30,45] and [75,90]
     - Store in CSV + SQLite database
  4. Output: 1000+ training examples with labels

Output format (CSV):
  match_id, match_date, league, home_team, away_team, home_goals, away_goals,
  interval_start, interval_end, label (0/1), goals_count, goal_minutes

Label logic:
  For each interval [start, end]:
    - label=1 if at least 1 goal scored in that interval
    - label=0 if no goal scored in that interval
    - goals_count = number of goals in interval
    - goal_minutes = comma-separated list of minutes when goals occurred
"""

import asyncio
import csv
import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlencode

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MatchEvent:
    """Single match event (goal, card, etc.)"""
    minute: int
    event_type: str  # 'goal', 'red_card', 'yellow_card', 'penalty', 'injury'
    team: str  # 'home' or 'away'
    player: Optional[str] = None
    description: Optional[str] = None


@dataclass
class HistoricalMatch:
    """Historical match record with events."""
    match_id: str
    match_date: str
    league: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    events: List[MatchEvent]
    
    @property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals


class SoccerStatsHistoricalScraper:
    """Scraper for SoccerStats.com historical data."""
    
    BASE_URL = "https://www.soccerstats.com"
    
    # League mapping: internal_name → SoccerStats league ID
    # URLs discovered from homepage navigation
    LEAGUE_URLS = {
        'france': '/latest.asp?league=france',
        'england': '/latest.asp?league=england',
        'germany': '/latest.asp?league=germany',
        'spain': '/latest.asp?league=spain',
        'italy': '/latest.asp?league=italy',
    }
    
    def __init__(self, output_csv: str = 'historical_matches.csv', db_path: str = 'paris_live.db'):
        self.output_csv = output_csv
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.matches_scraped = []
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_matches (
                match_id TEXT PRIMARY KEY,
                match_date TEXT,
                league TEXT,
                home_team TEXT,
                away_team TEXT,
                home_goals INTEGER,
                away_goals INTEGER,
                events_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT,
                interval_start INTEGER,
                interval_end INTEGER,
                label INTEGER,
                goals_count INTEGER,
                goal_minutes TEXT,
                FOREIGN KEY(match_id) REFERENCES historical_matches(match_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    def fetch_league_page(self, league_name: str, page: int = 1) -> Optional[str]:
        """Fetch league matches page."""
        if league_name not in self.LEAGUE_URLS:
            logger.warning(f"League {league_name} not configured")
            return None
        
        url = urljoin(self.BASE_URL, self.LEAGUE_URLS[league_name])
        
        try:
            logger.info(f"📥 Fetching {league_name} (page {page})...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"❌ Failed to fetch {league_name}: {e}")
            return None
    
    def parse_matches_from_page(self, html: str, league: str) -> List[Tuple[str, str, str, str]]:
        """
        Parse match links from league page.
        Returns: List of (match_id, match_date, home_team, away_team)
        """
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        # Find match rows (structure depends on SoccerStats layout)
        # Typical: <tr class="tr-match"> or similar
        match_rows = soup.find_all('tr', class_=re.compile('tr-match|match-row|match'))
        
        if not match_rows:
            # Fallback: look for links with match patterns
            links = soup.find_all('a', href=re.compile(r'match\.asp\?id=\d+'))
            for link in links[:50]:  # Limit to 50 per page
                try:
                    match_id = re.search(r'id=(\d+)', link.get('href', '')).group(1)
                    match_text = link.get_text(strip=True)
                    # Try to extract teams (format often "Team1 vs Team2")
                    teams = match_text.split('vs')
                    if len(teams) == 2:
                        home_team = teams[0].strip()
                        away_team = teams[1].strip()
                        matches.append((
                            match_id,
                            datetime.now().strftime('%Y-%m-%d'),  # Fallback date
                            home_team,
                            away_team
                        ))
                except:
                    continue
        else:
            # Parse structured rows
            for row in match_rows[:50]:  # Limit 50 per page
                try:
                    # Extract match link
                    match_link = row.find('a', href=re.compile(r'match\.asp\?id='))
                    if not match_link:
                        continue
                    
                    match_id = re.search(r'id=(\d+)', match_link.get('href', '')).group(1)
                    
                    # Extract date
                    date_cell = row.find('td', class_=re.compile('date'))
                    match_date = date_cell.get_text(strip=True) if date_cell else datetime.now().strftime('%Y-%m-%d')
                    
                    # Extract teams
                    team_cells = row.find_all('td', class_=re.compile('team'))
                    if len(team_cells) >= 2:
                        home_team = team_cells[0].get_text(strip=True)
                        away_team = team_cells[1].get_text(strip=True)
                    else:
                        # Fallback: parse from match link text
                        match_text = match_link.get_text(strip=True)
                        teams = match_text.split('vs')
                        if len(teams) != 2:
                            continue
                        home_team = teams[0].strip()
                        away_team = teams[1].strip()
                    
                    matches.append((match_id, match_date, home_team, away_team))
                except Exception as e:
                    logger.debug(f"Failed to parse row: {e}")
                    continue
        
        logger.info(f"✅ Found {len(matches)} matches in {league}")
        return matches
    
    def fetch_match_details(self, match_id: str) -> Optional[HistoricalMatch]:
        """Fetch and parse single match details (score, events)."""
        url = f"{self.BASE_URL}/match.asp?id={match_id}"
        
        try:
            logger.debug(f"📥 Fetching match {match_id}...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract score (format usually "1 - 0" or similar)
            score_text = soup.find('span', class_=re.compile('score|final-score'))
            if not score_text:
                logger.warning(f"No score found for match {match_id}")
                return None
            
            score_match = re.search(r'(\d+)\s*-\s*(\d+)', score_text.get_text())
            if not score_match:
                logger.warning(f"Could not parse score for match {match_id}")
                return None
            
            home_goals = int(score_match.group(1))
            away_goals = int(score_match.group(2))
            
            # Extract events (goals, cards, etc.)
            events = self._parse_events(soup)
            
            # Build match object (need to extract teams, date, league from page)
            # For now, return partial (caller should add metadata)
            match = HistoricalMatch(
                match_id=match_id,
                match_date=datetime.now().strftime('%Y-%m-%d'),  # Placeholder
                league='unknown',
                home_team='Unknown Home',
                away_team='Unknown Away',
                home_goals=home_goals,
                away_goals=away_goals,
                events=events,
            )
            
            return match
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch match {match_id}: {e}")
            return None
    
    def _parse_events(self, soup: BeautifulSoup) -> List[MatchEvent]:
        """Extract events (goals, cards, etc.) from match page."""
        events = []
        
        # Find events list/timeline
        events_container = soup.find('div', class_=re.compile('events|timeline|match-events'))
        if not events_container:
            logger.debug("No events container found")
            return events
        
        event_items = events_container.find_all(['li', 'div'], class_=re.compile('event|item'))
        
        for item in event_items:
            try:
                text = item.get_text(strip=True)
                
                # Extract minute (format: "45+2" or "45'")
                minute_match = re.search(r"(\d+)(?:\+\d+)?'?", text)
                if not minute_match:
                    continue
                minute = int(minute_match.group(1))
                
                # Detect event type
                if re.search(r'goal|⚽|score', text, re.IGNORECASE):
                    event_type = 'goal'
                elif re.search(r'red card|🔴', text, re.IGNORECASE):
                    event_type = 'red_card'
                elif re.search(r'yellow card|🟡', text, re.IGNORECASE):
                    event_type = 'yellow_card'
                elif re.search(r'penalty', text, re.IGNORECASE):
                    event_type = 'penalty'
                elif re.search(r'injury|hurt', text, re.IGNORECASE):
                    event_type = 'injury'
                else:
                    continue
                
                # Detect team (home or away)
                # Often indicated by team color or position
                team = 'home' if 'home' in text.lower() or 'h' in text else 'away'
                
                events.append(MatchEvent(
                    minute=minute,
                    event_type=event_type,
                    team=team,
                    description=text[:100]
                ))
            
            except Exception as e:
                logger.debug(f"Failed to parse event: {e}")
                continue
        
        return events
    
    def generate_labels(self, match: HistoricalMatch) -> List[Tuple[int, int, int, int, str]]:
        """
        Generate labels for match intervals.
        Returns: List of (interval_start, interval_end, label, goals_count, goal_minutes)
        """
        # Extract goal minutes
        goal_events = [e for e in match.events if e.event_type == 'goal']
        goal_minutes = sorted([e.minute for e in goal_events])
        
        labels = []
        
        # 1st half: interval [30, 45]
        goals_in_interval = [m for m in goal_minutes if 30 <= m <= 45]
        label_1h = 1 if goals_in_interval else 0
        goals_count_1h = len(goals_in_interval)
        goal_minutes_1h = ','.join(map(str, goals_in_interval)) if goals_in_interval else ''
        labels.append((30, 45, label_1h, goals_count_1h, goal_minutes_1h))
        
        # 2nd half: interval [75, 90]
        goals_in_interval = [m for m in goal_minutes if 75 <= m <= 90]
        label_2h = 1 if goals_in_interval else 0
        goals_count_2h = len(goals_in_interval)
        goal_minutes_2h = ','.join(map(str, goals_in_interval)) if goals_in_interval else ''
        labels.append((75, 90, label_2h, goals_count_2h, goal_minutes_2h))
        
        return labels
    
    def save_to_csv(self, matches: List[HistoricalMatch]):
        """Save matches + labels to CSV."""
        with open(self.output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'match_id', 'match_date', 'league', 'home_team', 'away_team',
                'home_goals', 'away_goals', 'interval_start', 'interval_end',
                'label', 'goals_count', 'goal_minutes'
            ])
            
            for match in matches:
                labels = self.generate_labels(match)
                for start, end, label, goals_count, goal_minutes in labels:
                    writer.writerow([
                        match.match_id,
                        match.match_date,
                        match.league,
                        match.home_team,
                        match.away_team,
                        match.home_goals,
                        match.away_goals,
                        start,
                        end,
                        label,
                        goals_count,
                        goal_minutes,
                    ])
        
        logger.info(f"✅ Saved {len(matches)} matches to {self.output_csv}")
    
    def save_to_database(self, matches: List[HistoricalMatch]):
        """Save matches + labels to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for match in matches:
            # Insert match
            events_json = json.dumps([
                {
                    'minute': e.minute,
                    'event_type': e.event_type,
                    'team': e.team,
                    'player': e.player,
                    'description': e.description,
                }
                for e in match.events
            ])
            
            cursor.execute('''
                INSERT OR IGNORE INTO historical_matches
                (match_id, match_date, league, home_team, away_team, home_goals, away_goals, events_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match.match_id,
                match.match_date,
                match.league,
                match.home_team,
                match.away_team,
                match.home_goals,
                match.away_goals,
                events_json,
            ))
            
            # Insert labels
            labels = self.generate_labels(match)
            for start, end, label, goals_count, goal_minutes in labels:
                cursor.execute('''
                    INSERT INTO historical_labels
                    (match_id, interval_start, interval_end, label, goals_count, goal_minutes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    match.match_id,
                    start,
                    end,
                    label,
                    goals_count,
                    goal_minutes,
                ))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Saved {len(matches)} matches to database")
    
    def scrape_all_leagues(self, limit_per_league: int = 50) -> List[HistoricalMatch]:
        """Scrape all configured leagues."""
        all_matches = []
        
        for league_name in self.LEAGUE_URLS.keys():
            logger.info(f"\n{'=' * 60}")
            logger.info(f"🏆 SCRAPING LEAGUE: {league_name.upper()}")
            logger.info(f"{'=' * 60}")
            
            # Fetch league page
            html = self.fetch_league_page(league_name)
            if not html:
                continue
            
            # Parse match links
            match_links = self.parse_matches_from_page(html, league_name)
            
            # Limit matches per league
            match_links = match_links[:limit_per_league]
            
            logger.info(f"📋 Processing {len(match_links)} matches from {league_name}...")
            
            for idx, (match_id, match_date, home_team, away_team) in enumerate(match_links, 1):
                logger.info(f"  [{idx}/{len(match_links)}] {home_team} vs {away_team}...")
                
                # Fetch match details
                match = self.fetch_match_details(match_id)
                if not match:
                    continue
                
                # Update metadata
                match.league = league_name
                match.home_team = home_team
                match.away_team = away_team
                match.match_date = match_date
                
                all_matches.append(match)
                
                # Rate limiting
                time.sleep(1)
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"✅ TOTAL MATCHES SCRAPED: {len(all_matches)}")
        logger.info(f"{'=' * 60}\n")
        
        return all_matches


def main():
    """Main entry point."""
    logger.info("🚀 Starting Historical Data Scraper for SoccerStats.com")
    logger.info("=" * 60)
    
    scraper = SoccerStatsHistoricalScraper(
        output_csv='historical_matches.csv',
        db_path='paris_live.db'
    )
    
    # Scrape all leagues (limit 50 matches per league for Phase 1)
    matches = scraper.scrape_all_leagues(limit_per_league=50)
    
    # Save to both CSV and database
    scraper.save_to_csv(matches)
    scraper.save_to_database(matches)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total matches scraped: {len(matches)}")
    logger.info(f"CSV output: historical_matches.csv")
    logger.info(f"Database output: paris_live.db")
    
    # Count labels
    label_1 = sum(1 for m in matches for _ in m.events if any(e.event_type == 'goal' and 30 <= e.minute <= 45 for e in m.events))
    total_labels = len(matches) * 2 if len(matches) > 0 else 1  # 2 labels per match (1st half + 2nd half)
    label_0 = total_labels - label_1
    logger.info(f"Total labels: {total_labels}")
    logger.info(f"  - Label 1 (goal in interval): {label_1}")
    logger.info(f"  - Label 0 (no goal): {label_0}")
    if total_labels > 0:
        logger.info(f"Class balance: {label_1 / total_labels * 100:.1f}% goal interval")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
