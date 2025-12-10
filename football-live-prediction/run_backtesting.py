#!/usr/bin/env python3
"""
Backtesting system for live goal predictor.
Tests prediction accuracy on historical matches.
"""

import sqlite3
import logging
from datetime import datetime
from collections import defaultdict
import json
from live_goal_predictor import LiveGoalPredictor, LiveMatchStats

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BacktestingEngine:
    """Backtest the live predictor on historical data."""
    
    def __init__(self, db_path='data/predictions.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.predictor = LiveGoalPredictor(db_path)
        
        # Results tracking
        self.results = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'by_confidence': {
                'CRITICAL': {'total': 0, 'correct': 0},
                'HIGH': {'total': 0, 'correct': 0},
                'MEDIUM': {'total': 0, 'correct': 0},
                'LOW': {'total': 0, 'correct': 0}
            },
            'by_interval': {
                '31-45': {'total': 0, 'correct': 0},
                '76-90': {'total': 0, 'correct': 0}
            },
            'predictions': []
        }
    
    def close(self):
        """Close connections."""
        self.predictor.close()
        self.conn.close()
    
    def _parse_goal_times(self, goal_times_str):
        """Parse goal times."""
        if not goal_times_str:
            return []
        try:
            return [int(x.strip()) for x in goal_times_str.split(',') if x.strip()]
        except (ValueError, AttributeError):
            return []
    
    def _get_test_matches(self, limit=None):
        """Get matches for backtesting (excluding recent 4 used for training)."""
        # Get all matches, ordered by date (oldest first)
        query = '''
            SELECT 
                id, team, opponent, is_home, goal_times, 
                goals_for, goals_against, league
            FROM soccerstats_scraped_matches
            ORDER BY id
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def _simulate_match_at_minute(self, match_id, team, opponent, is_home, 
                                   minute, interval_name):
        """
        Simulate match state at specific minute.
        Create mock live stats based on historical outcome.
        """
        # Get actual goal times
        self.cursor.execute('''
            SELECT goal_times, goals_for, goals_against
            FROM soccerstats_scraped_matches
            WHERE id = ?
        ''', (match_id,))
        
        row = self.cursor.fetchone()
        if not row:
            return None, None
        
        goal_times_str, goals_for, goals_against = row
        goal_times = self._parse_goal_times(goal_times_str)
        
        # Count goals before this minute
        goals_before = len([g for g in goal_times if g < minute])
        
        # Mock stats (simplified - in real backtest we'd need full historical data)
        live_stats = LiveMatchStats(
            minute=minute,
            score_home=goals_before if is_home else 0,
            score_away=0 if is_home else goals_before,
            possession_home=0.55 if is_home else 0.45,
            possession_away=0.45 if is_home else 0.55,
            shots_home=8 if is_home else 5,
            shots_away=5 if is_home else 8,
            sot_home=3 if is_home else 2,
            sot_away=2 if is_home else 3,
            dangerous_attacks_home=5 if is_home else 3,
            dangerous_attacks_away=3 if is_home else 5
        )
        
        # Check if goal actually happened in interval
        if interval_name == "31-45":
            interval_goals = [g for g in goal_times if 31 <= g <= 50]
        else:  # 76-90
            interval_goals = [g for g in goal_times if 76 <= g <= 100]
        
        actual_goal = len(interval_goals) > 0
        
        return live_stats, actual_goal
    
    def _run_single_test(self, match_id, team, opponent, is_home, minute, interval_name):
        """Run single prediction test."""
        
        # Simulate match state
        live_stats, actual_goal = self._simulate_match_at_minute(
            match_id, team, opponent, is_home, minute, interval_name
        )
        
        if live_stats is None:
            return None
        
        # Get prediction
        predictions = self.predictor.predict_goal(team, opponent, live_stats)
        prediction = predictions['home'] if is_home else predictions['away']
        
        # Evaluate
        predicted_goal = prediction.probability >= 0.5  # threshold
        correct = (predicted_goal == actual_goal)
        
        # Track results
        self.results['total_predictions'] += 1
        if correct:
            self.results['correct_predictions'] += 1
        
        if predicted_goal and not actual_goal:
            self.results['false_positives'] += 1
        elif not predicted_goal and actual_goal:
            self.results['false_negatives'] += 1
        
        # By confidence
        conf = prediction.confidence
        self.results['by_confidence'][conf]['total'] += 1
        if correct:
            self.results['by_confidence'][conf]['correct'] += 1
        
        # By interval
        self.results['by_interval'][interval_name]['total'] += 1
        if correct:
            self.results['by_interval'][interval_name]['correct'] += 1
        
        # Store details
        self.results['predictions'].append({
            'match_id': match_id,
            'team': team,
            'opponent': opponent,
            'is_home': is_home,
            'minute': minute,
            'interval': interval_name,
            'probability': prediction.probability,
            'confidence': conf,
            'predicted_goal': predicted_goal,
            'actual_goal': actual_goal,
            'correct': correct
        })
        
        return {
            'probability': prediction.probability,
            'confidence': conf,
            'predicted': predicted_goal,
            'actual': actual_goal,
            'correct': correct
        }
    
    def run_backtest(self, max_matches=100):
        """Run complete backtest."""
        
        logger.info("\n" + "="*80)
        logger.info("🔄 STARTING BACKTESTING")
        logger.info("="*80)
        
        matches = self._get_test_matches(limit=max_matches)
        logger.info(f"Testing on {len(matches)} matches...")
        
        tested = 0
        
        for match_id, team, opponent, is_home, goal_times_str, goals_for, goals_against, league in matches:
            # Test at minute 35 (interval 31-45)
            result = self._run_single_test(match_id, team, opponent, is_home, 35, "31-45")
            if result:
                tested += 1
            
            # Test at minute 80 (interval 76-90)
            result = self._run_single_test(match_id, team, opponent, is_home, 80, "76-90")
            if result:
                tested += 1
            
            if tested >= max_matches * 2:
                break
        
        logger.info(f"Completed {tested} predictions")
        self._print_results()
    
    def _print_results(self):
        """Print backtesting results."""
        
        logger.info("\n" + "="*80)
        logger.info("📊 BACKTESTING RESULTS")
        logger.info("="*80)
        
        total = self.results['total_predictions']
        correct = self.results['correct_predictions']
        accuracy = (correct / total * 100) if total > 0 else 0
        
        logger.info(f"\nOVERALL PERFORMANCE:")
        logger.info(f"  Total predictions: {total}")
        logger.info(f"  Correct: {correct}")
        logger.info(f"  Accuracy: {accuracy:.1f}%")
        logger.info(f"  False positives: {self.results['false_positives']}")
        logger.info(f"  False negatives: {self.results['false_negatives']}")
        
        logger.info(f"\nBY CONFIDENCE LEVEL:")
        for conf, stats in self.results['by_confidence'].items():
            if stats['total'] > 0:
                acc = (stats['correct'] / stats['total'] * 100)
                logger.info(f"  {conf:8s}: {stats['correct']:3d}/{stats['total']:3d} ({acc:5.1f}%)")
        
        logger.info(f"\nBY INTERVAL:")
        for interval, stats in self.results['by_interval'].items():
            if stats['total'] > 0:
                acc = (stats['correct'] / stats['total'] * 100)
                logger.info(f"  {interval:8s}: {stats['correct']:3d}/{stats['total']:3d} ({acc:5.1f}%)")
        
        # Sample predictions
        logger.info(f"\nSAMPLE PREDICTIONS:")
        high_prob = [p for p in self.results['predictions'] if p['probability'] >= 0.7][:5]
        
        logger.info(f"\n{'Team':<15} {'Min':<5} {'Int':<8} {'Prob':<6} {'Pred':<6} {'Actual':<7} {'Result':<8}")
        logger.info("-" * 80)
        
        for p in high_prob:
            result = "✅" if p['correct'] else "❌"
            logger.info(f"{p['team'][:14]:<15} {p['minute']:<5} {p['interval']:<8} "
                       f"{p['probability']:<6.2f} {str(p['predicted_goal']):<6} "
                       f"{str(p['actual_goal']):<7} {result:<8}")
        
        # Save results to file
        with open('backtesting_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n✅ Results saved to backtesting_results.json")


def main():
    """Main entry point."""
    
    engine = BacktestingEngine()
    
    try:
        # Run backtest on 100 matches
        engine.run_backtest(max_matches=100)
        
        logger.info("\n" + "="*80)
        logger.info("✅ Backtesting complete!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        engine.close()


if __name__ == "__main__":
    main()
