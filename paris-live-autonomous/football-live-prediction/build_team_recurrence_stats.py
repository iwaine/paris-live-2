#!/usr/bin/env python3
"""
Build team-specific recurrence statistics.
Calculates when goals are typically scored for each team in each context:
- By team + home/away + period (1st/2nd half)
- Stores: avg_minute, std_minute, goal_count, total_matches
"""

import sqlite3
import logging
from collections import defaultdict
import numpy as np
from pathlib import Path
import json
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeamRecurrenceBuilder:
    """Build per-team recurrence statistics for goal timing."""
    
    def __init__(self, db_path='data/predictions.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def _parse_goal_times(self, goal_times_str):
        """Parse goal times from JSON array or CSV string format"""
        if not goal_times_str:
            return []
        try:
            # Try JSON format first (e.g., "[6, 41, 55, 75, 90, 0, 0, 0, 0, 0]")
            goals = json.loads(goal_times_str)
            return [int(m) for m in goals if m > 0]
        except (json.JSONDecodeError, TypeError):
            # Fallback to CSV format
            try:
                return [int(x.strip()) for x in goal_times_str.split(',') if x.strip()]
            except (ValueError, AttributeError):
                return []
    
    def _classify_period(self, minute):
        """Classify minute into period: 1 for 1st half (0-45), 2 for 2nd half (45-90+)"""
        return 1 if minute <= 45 else 2
    
    def _create_table(self):
        """Create team_goal_recurrence table."""
        self.cursor.execute('''
            DROP TABLE IF EXISTS team_goal_recurrence
        ''')
        
        self.cursor.execute('''
            CREATE TABLE team_goal_recurrence (
                id INTEGER PRIMARY KEY,
                team_name TEXT NOT NULL,
                is_home INTEGER NOT NULL,
                period INTEGER NOT NULL,
                avg_minute REAL,
                std_minute REAL,
                sem_minute REAL,
                iqr_q1 REAL,
                iqr_q3 REAL,
                goal_count INTEGER,
                total_matches INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_name, is_home, period)
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ Created team_goal_recurrence table")
    
    def _extract_team_goals(self):
        """Extract all goals (scored + conceded) by team, home/away, and period."""
        # Dictionary: (team, is_home, period) -> [list of minutes]
        team_goals = defaultdict(list)
        team_matches = defaultdict(set)
        
        # Query all SoccerStats matches - include goal_times_conceded
        self.cursor.execute('''
            SELECT team, is_home, goal_times, goal_times_conceded, id
            FROM soccerstats_scraped_matches
        ''')
        
        rows = self.cursor.fetchall()
        logger.info(f"Processing {len(rows)} matches (buts marqués + encaissés)...")
        
        for team, is_home, goal_times_str, goal_times_conc_str, match_id in rows:
            # Parse buts marqués
            goals_scored = self._parse_goal_times(goal_times_str)
            # Parse buts encaissés
            goals_conceded = self._parse_goal_times(goal_times_conc_str)
            
            # Combiner les deux pour avoir TOUS les buts du match
            all_goals = goals_scored + goals_conceded
            
            for minute in all_goals:
                period = self._classify_period(minute)
                key = (team, is_home, period)
                team_goals[key].append(minute)
                team_matches[key].add(match_id)
        
        return team_goals, team_matches
    
    def _calculate_stats(self, minutes_list):
        """Calculate mean, std dev, SEM, and IQR of goal minutes."""
        if not minutes_list:
            return None, None, None, None, None
        
        arr = np.array(minutes_list)
        n = len(arr)
        
        avg = float(np.mean(arr))
        std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
        sem = float(std / np.sqrt(n)) if n > 1 else 0.0
        
        # Calculate IQR (Q1 and Q3)
        if n >= 4:
            q1, q3 = np.percentile(arr, [25, 75])
        else:
            q1 = float(np.min(arr))
            q3 = float(np.max(arr))
        
        return avg, std, sem, float(q1), float(q3)
    
    def build_stats_tables(self):
        """Build complete team recurrence statistics."""
        logger.info("\n" + "="*80)
        logger.info("🔄 BUILDING TEAM-SPECIFIC RECURRENCE STATISTICS")
        logger.info("="*80)
        
        # Create table
        self._create_table()
        
        # Extract goals
        team_goals, team_matches = self._extract_team_goals()
        
        logger.info(f"Found {len(team_goals)} team-context-period combinations")
        
        # Insert statistics
        inserted = 0
        for (team, is_home, period), minutes in team_goals.items():
            avg_min, std_min, sem_min, q1, q3 = self._calculate_stats(minutes)
            goal_count = len(minutes)
            total_matches = len(team_matches[(team, is_home, period)])
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO team_goal_recurrence
                (team_name, is_home, period, avg_minute, std_minute, sem_minute, 
                 iqr_q1, iqr_q3, goal_count, total_matches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (team, is_home, period, avg_min, std_min, sem_min, q1, q3, goal_count, total_matches))
            
            inserted += 1
        
        self.conn.commit()
        logger.info(f"✅ Inserted {inserted} recurrence records")
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print summary statistics."""
        logger.info("\n" + "="*80)
        logger.info("📊 SUMMARY - TOP TEAMS BY GOAL COUNT")
        logger.info("="*80)
        
        self.cursor.execute('''
            SELECT 
                team_name,
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as location,
                CASE WHEN period=1 THEN '1st half' ELSE '2nd half' END as period,
                avg_minute,
                std_minute,
                goal_count,
                total_matches
            FROM team_goal_recurrence
            ORDER BY goal_count DESC
            LIMIT 20
        ''')
        
        rows = self.cursor.fetchall()
        
        logger.info("\n{:<15} {:<6} {:<10} {:<12} {:<12} {:<12} {:<6} {:<8}".format(
            "Team", "Loc", "Period", "Avg Min", "SEM", "IQR", "Goals", "Matches"
        ))
        logger.info("-" * 90)
        
        for team, loc, period, avg_min, std_min, goal_count, total_matches in rows:
            # Recalculer SEM pour l'affichage
            sem = (std_min / np.sqrt(goal_count)) if goal_count > 1 else 0
            logger.info("{:<15} {:<6} {:<10} {:<12.1f} {:<12.1f} {:<12} {:<6} {:<8}".format(
                team, loc, period, avg_min or 0, sem, "[voir DB]", goal_count, total_matches
            ))
        
        # Stats by location and period
        logger.info("\n" + "="*80)
        logger.info("📈 STATISTICS BY CONTEXT")
        logger.info("="*80)
        
        contexts = [
            (1, 1, "HOME - 1st Half"),
            (1, 2, "HOME - 2nd Half"),
            (0, 1, "AWAY - 1st Half"),
            (0, 2, "AWAY - 2nd Half"),
        ]
        
        for is_home, period, label in contexts:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as teams,
                    AVG(goal_count) as avg_goals_per_team,
                    SUM(goal_count) as total_goals,
                    AVG(avg_minute) as avg_minute_overall
                FROM team_goal_recurrence
                WHERE is_home = ? AND period = ?
            ''', (is_home, period))
            
            teams, avg_goals, total_goals, avg_minute = self.cursor.fetchone()
            
            logger.info(f"\n{label}:")
            logger.info(f"  • Teams with goals: {teams}")
            logger.info(f"  • Avg goals per team: {avg_goals:.1f}")
            logger.info(f"  • Total goals: {int(total_goals or 0)}")
            logger.info(f"  • Avg goal minute: {avg_minute:.1f}" if avg_minute else "  • No goal data")
        
        # Sample queries
        logger.info("\n" + "="*80)
        logger.info("🔍 SAMPLE QUERIES FOR LIVE PREDICTIONS")
        logger.info("="*80)
        
        sample_teams = ['Arsenal', 'Paris Saint-Germain', 'Bayern Munich', 'Napoli', 'Real Madrid']
        
        for team in sample_teams:
            self.cursor.execute('''
                SELECT 
                    team_name,
                    is_home,
                    period,
                    avg_minute,
                    std_minute,
                    sem_minute,
                    iqr_q1,
                    iqr_q3,
                    goal_count,
                    total_matches
                FROM team_goal_recurrence
                WHERE team_name = ?
                ORDER BY is_home DESC, period
            ''', (team,))
            
            rows = self.cursor.fetchall()
            if rows:
                logger.info(f"\n{team}:")
                for row in rows:
                    t_name, is_home, period, avg_min, std_min, sem_min, q1, q3, goals, matches = row
                    loc = "HOME" if is_home else "AWAY"
                    half = "1st" if period == 1 else "2nd"
                    logger.info(f"  • {loc} {half}: avg={avg_min:.1f}±{sem_min:.1f}' (SEM) [IQR: {q1:.0f}'-{q3:.0f}'] ({goals} buts sur {matches} matchs)")
    
    def export_team_recurrence_csv(self, output_path='data/recurrence_stats_export.csv'):
        """Export all team recurrence stats to CSV for live selector."""
        self.cursor.execute('''
            SELECT team_name, is_home, period, avg_minute, std_minute, sem_minute, iqr_q1, iqr_q3, goal_count, total_matches
            FROM team_goal_recurrence
        ''')
        rows = self.cursor.fetchall()
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Team','Context','Period','Avg_Minute','Std_Minute','SEM','IQR_Q1','IQR_Q3','Goal_Count','Total_Matches'])
            for row in rows:
                team, is_home, period, avg_min, std_min, sem_min, q1, q3, goals, matches = row
                context = 'HOME' if is_home else 'AWAY'
                writer.writerow([team, context, period, avg_min, std_min, sem_min, q1, q3, goals, matches])
        logger.info(f"✅ Exported team recurrence stats to {output_path}")

def main():
    """Main entry point."""
    builder = TeamRecurrenceBuilder()
    try:
        builder.build_stats_tables()
        builder.export_team_recurrence_csv()
        logger.info("\n✅ Team recurrence statistics successfully built!")
        logger.info("Table: team_goal_recurrence")
        logger.info("Use for live predictions: SELECT * FROM team_goal_recurrence WHERE team_name='...'" )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        builder.close()

if __name__ == "__main__":
    main()
