#!/usr/bin/env python3
"""
Build enhanced recurrence statistics with:
1. Global team stats (all matches, home/away separated)
2. Recent form (last 4 matches)
3. Critical interval patterns (existing)
"""

import sqlite3
import logging
from collections import defaultdict
import numpy as np
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedRecurrenceBuilder:
    """Build complete recurrence stats: global + recent + intervals."""
    
    INTERVAL_1 = (31, 50, "31-45")
    INTERVAL_2 = (76, 100, "76-90")
    RECENT_MATCHES_COUNT = 4
    
    def __init__(self, db_path='data/predictions.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def _parse_goal_times(self, goal_times_str):
        """Parse goal times from string."""
        if not goal_times_str:
            return []
        try:
            return [int(x.strip()) for x in goal_times_str.split(',') if x.strip()]
        except (ValueError, AttributeError):
            return []
    
    def _in_interval(self, minute, interval):
        """Check if minute is in interval."""
        return interval[0] <= minute <= interval[1]
    
    def _create_tables(self):
        """Create all recurrence tables."""
        
        # Table 1: Global team stats (all matches)
        self.cursor.execute('DROP TABLE IF EXISTS team_global_stats')
        self.cursor.execute('''
            CREATE TABLE team_global_stats (
                id INTEGER PRIMARY KEY,
                team_name TEXT NOT NULL,
                is_home INTEGER NOT NULL,
                
                total_matches INTEGER,
                matches_with_goals INTEGER,
                total_goals INTEGER,
                avg_goals_per_match REAL,
                goals_frequency REAL,
                
                matches_with_conceded INTEGER,
                total_conceded INTEGER,
                avg_conceded_per_match REAL,
                conceded_frequency REAL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_name, is_home)
            )
        ''')
        
        # Table 2: Recent form (last N matches)
        self.cursor.execute('DROP TABLE IF EXISTS team_recent_form')
        self.cursor.execute('''
            CREATE TABLE team_recent_form (
                id INTEGER PRIMARY KEY,
                team_name TEXT NOT NULL,
                is_home INTEGER NOT NULL,
                interval_name TEXT NOT NULL,
                
                recent_matches INTEGER,
                recent_goals INTEGER,
                recent_frequency REAL,
                recent_avg_minute REAL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_name, is_home, interval_name)
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ Created team_global_stats and team_recent_form tables")
    
    def _build_global_stats(self):
        """Build global stats for each team (all matches, not interval-specific)."""
        
        logger.info("\n📊 Building GLOBAL team statistics...")
        
        # Get all matches grouped by team + is_home
        self.cursor.execute('''
            SELECT 
                team,
                is_home,
                COUNT(*) as total_matches,
                SUM(CASE WHEN goals_for > 0 THEN 1 ELSE 0 END) as matches_with_goals,
                SUM(goals_for) as total_goals,
                SUM(CASE WHEN goals_against > 0 THEN 1 ELSE 0 END) as matches_with_conceded,
                SUM(goals_against) as total_conceded
            FROM soccerstats_scraped_matches
            GROUP BY team, is_home
        ''')
        
        rows = self.cursor.fetchall()
        inserted = 0
        
        for team, is_home, total, matches_goals, total_goals, matches_conceded, total_conceded in rows:
            avg_goals = total_goals / total if total > 0 else 0
            freq_goals = matches_goals / total if total > 0 else 0
            avg_conceded = total_conceded / total if total > 0 else 0
            freq_conceded = matches_conceded / total if total > 0 else 0
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO team_global_stats
                (team_name, is_home, total_matches, matches_with_goals, total_goals,
                 avg_goals_per_match, goals_frequency, matches_with_conceded,
                 total_conceded, avg_conceded_per_match, conceded_frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (team, is_home, total, matches_goals, total_goals, avg_goals,
                  freq_goals, matches_conceded, total_conceded, avg_conceded, freq_conceded))
            
            inserted += 1
        
        self.conn.commit()
        logger.info(f"✅ Inserted {inserted} global team statistics")
    
    def _build_recent_form(self):
        """Build recent form stats (last N matches) for critical intervals."""
        
        logger.info(f"\n📊 Building RECENT FORM (last {self.RECENT_MATCHES_COUNT} matches)...")
        
        # Get all teams
        self.cursor.execute('''
            SELECT DISTINCT team, is_home
            FROM soccerstats_scraped_matches
            ORDER BY team, is_home
        ''')
        
        teams = self.cursor.fetchall()
        inserted = 0
        
        for team, is_home in teams:
            # Get last N matches for this team+context
            self.cursor.execute(f'''
                SELECT id, goal_times
                FROM soccerstats_scraped_matches
                WHERE team = ? AND is_home = ?
                ORDER BY id DESC
                LIMIT {self.RECENT_MATCHES_COUNT}
            ''', (team, is_home))
            
            recent_matches = self.cursor.fetchall()
            
            if len(recent_matches) < 3:
                continue  # Not enough recent data
            
            # Analyze for each interval
            for interval, interval_name in [(self.INTERVAL_1, "31-45"), (self.INTERVAL_2, "76-90")]:
                goals_in_interval = []
                
                for match_id, goal_times_str in recent_matches:
                    goals = self._parse_goal_times(goal_times_str)
                    interval_goals = [g for g in goals if self._in_interval(g, interval)]
                    goals_in_interval.extend(interval_goals)
                
                recent_goal_count = len(goals_in_interval)
                recent_freq = recent_goal_count / len(recent_matches)
                recent_avg = float(np.mean(goals_in_interval)) if goals_in_interval else None
                
                self.cursor.execute('''
                    INSERT OR REPLACE INTO team_recent_form
                    (team_name, is_home, interval_name, recent_matches,
                     recent_goals, recent_frequency, recent_avg_minute)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (team, is_home, interval_name, len(recent_matches),
                      recent_goal_count, recent_freq, recent_avg))
                
                inserted += 1
        
        self.conn.commit()
        logger.info(f"✅ Inserted {inserted} recent form records")
    
    def _print_summary(self):
        """Print summary of enhanced statistics."""
        
        logger.info("\n" + "="*80)
        logger.info("📊 GLOBAL TEAM STATISTICS - TOP SCORERS")
        logger.info("="*80)
        
        self.cursor.execute('''
            SELECT 
                team_name,
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as loc,
                total_matches,
                matches_with_goals,
                ROUND(goals_frequency, 3) as freq,
                ROUND(avg_goals_per_match, 2) as avg_goals
            FROM team_global_stats
            ORDER BY total_goals DESC
            LIMIT 15
        ''')
        
        rows = self.cursor.fetchall()
        logger.info(f"\n{'Team':<18} {'Loc':<6} {'Matches':<8} {'w/Goals':<8} {'Freq':<8} {'Avg/Match':<10}")
        logger.info("-" * 80)
        
        for row in rows:
            logger.info(f"{row[0]:<18} {row[1]:<6} {row[2]:<8} {row[3]:<8} {row[4]:<8} {row[5]:<10}")
        
        logger.info("\n" + "="*80)
        logger.info("📊 RECENT FORM - TOP PERFORMERS (Last 4 matches)")
        logger.info("="*80)
        
        self.cursor.execute('''
            SELECT 
                team_name,
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as loc,
                interval_name,
                recent_matches,
                recent_goals,
                ROUND(recent_frequency, 3) as freq
            FROM team_recent_form
            WHERE recent_goals > 0
            ORDER BY recent_frequency DESC, recent_goals DESC
            LIMIT 15
        ''')
        
        rows = self.cursor.fetchall()
        logger.info(f"\n{'Team':<18} {'Loc':<6} {'Interval':<10} {'Matches':<8} {'Goals':<7} {'Freq':<8}")
        logger.info("-" * 80)
        
        for row in rows:
            logger.info(f"{row[0]:<18} {row[1]:<6} {row[2]:<10} {row[3]:<8} {row[4]:<7} {row[5]:<8}")
        
        # Example: Angers
        logger.info("\n" + "="*80)
        logger.info("🔍 EXAMPLE: ANGERS COMPLETE PROFILE")
        logger.info("="*80)
        
        # Global stats
        self.cursor.execute('''
            SELECT 
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as loc,
                total_matches,
                ROUND(goals_frequency, 3) as freq,
                ROUND(avg_goals_per_match, 2) as avg
            FROM team_global_stats
            WHERE team_name = 'Angers'
            ORDER BY is_home DESC
        ''')
        
        logger.info("\nGLOBAL STATS:")
        for loc, matches, freq, avg in self.cursor.fetchall():
            logger.info(f"  {loc}: {matches} matches, freq={freq:.3f}, avg={avg:.2f} goals/match")
        
        # Recent form
        self.cursor.execute('''
            SELECT 
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as loc,
                interval_name,
                recent_goals,
                ROUND(recent_frequency, 3) as freq
            FROM team_recent_form
            WHERE team_name = 'Angers'
            ORDER BY is_home DESC, interval_name
        ''')
        
        logger.info("\nRECENT FORM (last 4 matches):")
        for loc, interval, goals, freq in self.cursor.fetchall():
            logger.info(f"  {loc} {interval}: {goals} goals, freq={freq:.3f}")
    
    def build_all(self):
        """Build complete enhanced recurrence statistics."""
        
        logger.info("\n" + "="*80)
        logger.info("🔄 BUILDING ENHANCED RECURRENCE STATISTICS")
        logger.info("="*80)
        logger.info("Components:")
        logger.info("  1. Global team stats (all matches)")
        logger.info("  2. Recent form (last 4 matches)")
        logger.info("  3. Critical intervals (existing table)")
        
        self._create_tables()
        self._build_global_stats()
        self._build_recent_form()
        self._print_summary()


def main():
    """Main entry point."""
    builder = EnhancedRecurrenceBuilder()
    
    try:
        builder.build_all()
        logger.info("\n" + "="*80)
        logger.info("✅ Enhanced recurrence statistics successfully built!")
        logger.info("Tables:")
        logger.info("  - team_global_stats (overall performance)")
        logger.info("  - team_recent_form (last 4 matches)")
        logger.info("  - team_critical_intervals (existing)")
        logger.info("="*80)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        builder.close()


if __name__ == "__main__":
    main()
