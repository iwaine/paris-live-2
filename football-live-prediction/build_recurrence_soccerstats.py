#!/usr/bin/env python3
"""
Intégrer les données SoccerStats scraped dans les statistiques de récurrence

Ce script:
1. Charge les matchs SoccerStats importés (soccerstats_scraped_matches)
2. Les convertit en format compatible avec l'analyse de récurrence
3. Les ajoute aux stats de récurrence existantes
4. Recalcule les probabilités par intervalle avec la base augmentée
"""

import sqlite3
import json
from collections import defaultdict
from statistics import mean, stdev
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RecurrenceStatsBuilder:
    """Build recurrence statistics integrating SoccerStats data"""
    
    def __init__(self, db_path: str = "data/predictions.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Time intervals
        self.intervals = {
            "1-15": (1, 15),
            "16-30": (16, 30),
            "31-45": (31, 45),
            "46-60": (46, 60),
            "61-75": (61, 75),
            "76-90": (76, 90),
            "91-120": (91, 120),
        }
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def get_soccerstats_matches(self) -> list:
        """Get all matches from soccerstats_scraped_matches table"""
        
        self.cursor.execute("""
            SELECT league, team, opponent, goals_for, goals_against, is_home, date, goal_times
            FROM soccerstats_scraped_matches
            ORDER BY league, team
        """)
        
        matches = self.cursor.fetchall()
        logger.info(f"Loaded {len(matches)} matches from SoccerStats")
        return matches
    
    def extract_goal_distribution(self, match_data: dict, home_team: str, away_team: str, home_goals: int, away_goals: int):
        """
        Extract goal distribution from match goal_times data
        
        Returns:
            Tuple of (home_goals_by_interval, away_goals_by_interval)
            Each is dict: interval_name -> goal_count
        """
        
        home_goals_by_interval = {interval: 0 for interval in self.intervals}
        away_goals_by_interval = {interval: 0 for interval in self.intervals}
        
        # Parse goal times
        goal_times_str = match_data.get('goal_times', '')
        if not goal_times_str:
            # No detailed data, distribute uniformly
            return self._distribute_goals_uniform(home_goals, away_goals)
        
        goal_times = [int(t.strip()) for t in goal_times_str.split(',') if t.strip()]
        
        # Classify each goal into interval
        for minute in goal_times:
            for interval_name, (start, end) in self.intervals.items():
                if start <= minute <= end:
                    # Alternate between home and away (simplified)
                    # In reality, would need to parse which team scored
                    # For now, assume alternating or equal distribution
                    if home_goals > away_goals:
                        home_goals_by_interval[interval_name] += 1
                        home_goals -= 1
                    else:
                        away_goals_by_interval[interval_name] += 1
                        away_goals -= 1
                    break
        
        return home_goals_by_interval, away_goals_by_interval
    
    def _distribute_goals_uniform(self, home_goals: int, away_goals: int):
        """Distribute goals uniformly across intervals when no timing data"""
        
        home_by_interval = {interval: 0 for interval in self.intervals}
        away_by_interval = {interval: 0 for interval in self.intervals}
        
        # Weight by interval (more goals expected in 76-90)
        weights = {
            "1-15": 0.10,
            "16-30": 0.12,
            "31-45": 0.15,
            "46-60": 0.12,
            "61-75": 0.14,
            "76-90": 0.28,
            "91-120": 0.09,
        }
        
        # Distribute home goals
        for interval, weight in weights.items():
            home_by_interval[interval] = round(home_goals * weight)
        
        # Distribute away goals
        for interval, weight in weights.items():
            away_by_interval[interval] = round(away_goals * weight)
        
        return home_by_interval, away_by_interval
    
    def build_stats_tables(self):
        """Build recurrence statistics tables"""
        
        logger.info("\n" + "="*80)
        logger.info("🔄 BUILDING INTEGRATED RECURRENCE STATISTICS")
        logger.info("="*80)
        
        # Get all matches
        matches = self.get_soccerstats_matches()
        
        if not matches:
            logger.warning("No matches to process")
            return
        
        # Statistics per team, league, and interval
        team_stats = defaultdict(lambda: defaultdict(lambda: {
            "total_matches": 0,
            "home_goals_by_interval": defaultdict(int),
            "away_goals_by_interval": defaultdict(int),
            "goals_conceded_by_interval": defaultdict(int),
        }))
        
        league_stats = defaultdict(lambda: {
            "total_matches": 0,
            "total_goals_by_interval": defaultdict(int),
            "goal_list": []
        })
        
        # Process matches
        for league, team, opponent, goals_for, goals_against, is_home, date, goal_times in matches:
            
            # Get interval distribution
            home_goals_dist, away_goals_dist = self._distribute_goals_uniform(goals_for, goals_against)
            
            # Update team stats
            team_key = f"{league}_{team}"
            league_interval_key = f"{league}_{('home' if is_home else 'away')}"
            
            team_stats[team_key][league_interval_key]["total_matches"] += 1
            
            for interval, count in home_goals_dist.items():
                team_stats[team_key][league_interval_key]["home_goals_by_interval"][interval] += count
            
            for interval, count in away_goals_dist.items():
                team_stats[team_key][league_interval_key]["away_goals_by_interval"][interval] += count
                team_stats[team_key][league_interval_key]["goals_conceded_by_interval"][interval] += count
            
            # Update league stats
            league_stats[league]["total_matches"] += 1
            
            for interval, count in home_goals_dist.items():
                league_stats[league]["total_goals_by_interval"][interval] += count
            
            for interval, count in away_goals_dist.items():
                league_stats[league]["total_goals_by_interval"][interval] += count
            
            league_stats[league]["goal_list"].append(goals_for + goals_against)
        
        # Create recurrence_stats table
        self.cursor.execute("DROP TABLE IF EXISTS recurrence_stats_soccerstats")
        
        self.cursor.execute("""
            CREATE TABLE recurrence_stats_soccerstats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league TEXT NOT NULL,
                team TEXT NOT NULL,
                context TEXT,
                interval TEXT NOT NULL,
                total_matches INTEGER DEFAULT 0,
                total_goals INTEGER DEFAULT 0,
                avg_goals REAL,
                min_goals INTEGER,
                max_goals INTEGER,
                goal_probability REAL,
                std_dev REAL,
                sample_goals TEXT,
                source TEXT DEFAULT 'soccerstats'
            )
        """)
        
        # Insert team statistics
        inserted = 0
        
        for team_key, intervals_data in team_stats.items():
            league, team = team_key.rsplit('_', 1)
            
            for context_key, stats in intervals_data.items():
                _, context = context_key.rsplit('_', 1)
                
                for interval_name in self.intervals.keys():
                    goals = stats["home_goals_by_interval"][interval_name]
                    total_matches = stats["total_matches"]
                    
                    if total_matches > 0:
                        goal_probability = goals / total_matches if total_matches > 0 else 0
                        
                        self.cursor.execute("""
                            INSERT INTO recurrence_stats_soccerstats
                            (league, team, context, interval, total_matches, total_goals, 
                             avg_goals, goal_probability, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'soccerstats')
                        """, (
                            league,
                            team,
                            context,
                            interval_name,
                            total_matches,
                            goals,
                            goals / total_matches if total_matches > 0 else 0,
                            goal_probability
                        ))
                        
                        inserted += 1
        
        self.conn.commit()
        logger.info(f"✅ Inserted {inserted} recurrence records")
        
        # Print summary
        self._print_summary(league_stats)
    
    def _print_summary(self, league_stats):
        """Print summary statistics"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 SUMMARY BY LEAGUE")
        logger.info(f"{'='*80}\n")
        
        for league, stats in sorted(league_stats.items()):
            total = stats["total_matches"]
            goals = stats["goal_list"]
            
            logger.info(f"📍 {league}")
            logger.info(f"   Total matches: {total}")
            logger.info(f"   Avg goals/match: {sum(goals)/len(goals):.2f}" if goals else "   No goals data")
            
            logger.info(f"   Goals by interval:")
            for interval in sorted(self.intervals.keys()):
                count = stats["total_goals_by_interval"][interval]
                pct = (count / sum(stats["total_goals_by_interval"].values()) * 100) if sum(stats["total_goals_by_interval"].values()) > 0 else 0
                logger.info(f"      {interval:8s}: {count:3d} goals ({pct:5.1f}%)")
            
            logger.info("")


def main():
    """Main entry point"""
    
    builder = RecurrenceStatsBuilder()
    
    try:
        builder.build_stats_tables()
        logger.info("\n✅ Recurrence statistics successfully built!")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        builder.close()


if __name__ == "__main__":
    main()
