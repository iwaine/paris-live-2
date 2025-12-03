#!/usr/bin/env python3
"""
ÉTAPE 4: BACKTESTING ENGINE
Valide le système sur tous les matchs passés et calcule l'accuracy
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.append(str(Path(__file__).parent))

from utils.database_manager import DatabaseManager
from predictors.recurrence_predictor import RecurrencePredictor
from loguru import logger


class BacktestingEngine:
    """Backtest le système de prédiction sur matchs passés"""

    def __init__(self):
        self.db = DatabaseManager()
        self.predictor = RecurrencePredictor()
        logger.info("BacktestingEngine initialized")

    def run_backtest(self) -> Dict:
        """Lance le backtesting complet"""

        print("\n" + "="*80)
        print("🧪 BACKTESTING ENGINE - Validating on Historical Data")
        print("="*80)

        # Récupérer tous les matchs
        matches = self._get_all_matches()
        print(f"\n📊 Found {len(matches)} matches to backtest")

        # Tester les prédictions
        results = self._test_predictions(matches)

        # Afficher les résultats
        self._print_results(results)

        return results

    def _get_all_matches(self) -> List[Dict]:
        """Récupère tous les matchs de la BD"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute('''
                SELECT id, home_team, away_team, home_goals, away_goals
                FROM match_history
                ORDER BY id DESC
            ''')
            matches = [dict(row) for row in cursor.fetchall()]
            return matches
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []

    def _test_predictions(self, matches: List[Dict]) -> Dict:
        """Teste les prédictions sur tous les matchs"""

        results = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'predictions_by_danger_level': {},
            'by_minute': {},
            'by_interval': {'31-45': {'total': 0, 'correct': 0}, '76-90': {'total': 0, 'correct': 0}},
        }

        print(f"\nTesting predictions on {len(matches)} matches...")
        print("-"*80)

        for i, match in enumerate(matches):
            if i % 50 == 0 and i > 0:
                print(f"  Processed {i}/{len(matches)} matches...")

            home_team = match['home_team']
            away_team = match['away_team']
            actual_goals = match['home_goals'] + match['away_goals']

            # Test sur minutes clés
            minutes_to_test = [38, 42, 80, 85]  # Exemples de minutes critiques

            for minute in minutes_to_test:
                # Déterminer l'intervalle
                if 31 <= minute <= 45:
                    interval = '31-45'
                elif 76 <= minute <= 90:
                    interval = '76-90'
                else:
                    continue

                try:
                    # Prédire
                    prediction = self.predictor.predict_at_minute(
                        home_team=home_team,
                        away_team=away_team,
                        current_minute=minute,
                        home_possession=0.50  # Neutral
                    )

                    if 'error' in prediction:
                        continue

                    danger = prediction['danger_score_percentage']
                    predicted_goal = danger >= 65  # Seuil: 65%
                    actual_goal = actual_goals >= 1

                    # Track results
                    results['total_predictions'] += 1

                    if predicted_goal == actual_goal:
                        results['correct_predictions'] += 1

                    # By danger level
                    danger_bracket = self._get_danger_bracket(danger)
                    if danger_bracket not in results['predictions_by_danger_level']:
                        results['predictions_by_danger_level'][danger_bracket] = {'total': 0, 'correct': 0}

                    results['predictions_by_danger_level'][danger_bracket]['total'] += 1
                    if predicted_goal == actual_goal:
                        results['predictions_by_danger_level'][danger_bracket]['correct'] += 1

                    # By interval
                    results['by_interval'][interval]['total'] += 1
                    if predicted_goal == actual_goal:
                        results['by_interval'][interval]['correct'] += 1

                    # By minute
                    if minute not in results['by_minute']:
                        results['by_minute'][minute] = {'total': 0, 'correct': 0}

                    results['by_minute'][minute]['total'] += 1
                    if predicted_goal == actual_goal:
                        results['by_minute'][minute]['correct'] += 1

                except Exception as e:
                    logger.debug(f"Error testing {home_team} vs {away_team}: {e}")
                    continue

        return results

    def _get_danger_bracket(self, danger: float) -> str:
        """Classifie le danger score"""
        if danger >= 75:
            return "75-100%"
        elif danger >= 65:
            return "65-75%"
        elif danger >= 50:
            return "50-65%"
        elif danger >= 35:
            return "35-50%"
        else:
            return "<35%"

    def _print_results(self, results: Dict):
        """Affiche les résultats du backtesting"""

        total = results['total_predictions']
        correct = results['correct_predictions']
        accuracy = (correct / total * 100) if total > 0 else 0

        print("\n\n" + "="*80)
        print("📊 BACKTESTING RESULTS")
        print("="*80)

        print(f"\n✅ Overall Performance:")
        print(f"  • Total predictions: {total}")
        print(f"  • Correct: {correct}")
        print(f"  • Accuracy: {accuracy:.1f}%")

        print(f"\n📈 By Danger Level:")
        for bracket in sorted(results['predictions_by_danger_level'].keys()):
            data = results['predictions_by_danger_level'][bracket]
            acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  • {bracket:12s}: {data['correct']:3d}/{data['total']:3d} ({acc:5.1f}%)")

        print(f"\n⏱️  By Interval:")
        for interval in ['31-45', '76-90']:
            data = results['by_interval'][interval]
            acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  • {interval}: {data['correct']:3d}/{data['total']:3d} ({acc:5.1f}%)")

        print(f"\n🎯 By Minute:")
        for minute in sorted(results['by_minute'].keys()):
            data = results['by_minute'][minute]
            acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  • min {minute:2d}: {data['correct']:3d}/{data['total']:3d} ({acc:5.1f}%)")

        # Recommendations
        print(f"\n\n💡 RECOMMENDATIONS:")
        print("-"*80)

        if accuracy >= 60:
            print(f"  ✅ System accuracy is GOOD ({accuracy:.1f}%)")
            print(f"     → Ready for live betting at 65% threshold")
            recommended_threshold = 65
        elif accuracy >= 50:
            print(f"  ⚠️  System accuracy is MODERATE ({accuracy:.1f}%)")
            print(f"     → Consider lowering threshold to 55% for more bets")
            recommended_threshold = 55
        else:
            print(f"  ❌ System accuracy is LOW ({accuracy:.1f}%)")
            print(f"     → Need to improve data or features")
            recommended_threshold = None

        if recommended_threshold:
            print(f"  → Recommended threshold: {recommended_threshold}%")

        print("\n" + "="*80 + "\n")


def main():
    engine = BacktestingEngine()
    results = engine.run_backtest()


if __name__ == "__main__":
    main()
