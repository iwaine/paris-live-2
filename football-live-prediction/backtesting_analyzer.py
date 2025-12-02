#!/usr/bin/env python3
"""
Backtesting Analyzer for Paris Live Prediction System

This module provides advanced analysis of backtesting results including:
- Statistical breakdowns by interval, league, team
- Confidence vs accuracy analysis
- Comparison with baseline strategies
- ROI distribution analysis
- Visualization data generation
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IntervalMetrics:
    """Metrics for a specific interval"""
    interval: str
    decisions: int
    bets_triggered: int
    wins: int
    win_rate: float
    roi_avg: float
    precision: float


@dataclass
class ConfidenceAnalysis:
    """Analysis of confidence distribution"""
    confidence_bracket: str  # "0-10%", "10-20%", etc.
    sample_count: int
    correct_rate: float
    avg_roi: float


@dataclass
class StrategyComparison:
    """Comparison of different threshold strategies"""
    strategy_name: str
    confidence_threshold: float
    danger_threshold: float
    total_bets: int
    win_rate: float
    roi_avg: float
    precision: float
    f1_score: float


class BacktestingAnalyzer:
    """Advanced analysis of backtesting results"""

    def __init__(self, decisions_csv: str = "backtesting_decisions.csv"):
        """Initialize analyzer"""
        self.decisions_csv = Path(decisions_csv)
        self.df = None
        self._load_decisions()

    def _load_decisions(self):
        """Load decision data"""
        try:
            self.df = pd.read_csv(self.decisions_csv)
            logger.info(f"✅ Loaded {len(self.df)} decisions from {self.decisions_csv}")
        except FileNotFoundError:
            logger.error(f"❌ File not found: {self.decisions_csv}")
            raise

    def analyze_by_interval(self) -> Dict[str, IntervalMetrics]:
        """Analyze metrics broken down by interval"""
        results = {}
        
        for interval in ["30-45", "75-90"]:
            interval_df = self.df[self.df["interval"] == interval]
            
            if len(interval_df) == 0:
                continue
            
            bets_df = interval_df[interval_df["should_bet"]]
            wins = (bets_df["actual_goals"] >= 1).sum()
            losses = (bets_df["actual_goals"] == 0).sum()
            
            tp = ((interval_df["should_bet"]) & (interval_df["actual_goals"] >= 1)).sum()
            fp = ((interval_df["should_bet"]) & (interval_df["actual_goals"] == 0)).sum()
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            
            total_bets = len(bets_df)
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
            roi_avg = (interval_df[interval_df["should_bet"]]["roi"].sum() / total_bets * 100) if total_bets > 0 else 0
            
            results[interval] = IntervalMetrics(
                interval=interval,
                decisions=len(interval_df),
                bets_triggered=total_bets,
                wins=int(wins),
                win_rate=win_rate,
                roi_avg=roi_avg,
                precision=precision
            )
        
        return results

    def analyze_confidence_distribution(self, brackets: int = 5) -> List[ConfidenceAnalysis]:
        """Analyze how accuracy varies by confidence level"""
        results = []
        
        # Create confidence brackets
        min_conf = self.df["confidence"].min()
        max_conf = self.df["confidence"].max()
        bracket_size = (max_conf - min_conf) / brackets
        
        for i in range(brackets):
            lower = min_conf + (i * bracket_size)
            upper = lower + bracket_size
            
            bracket_df = self.df[
                (self.df["confidence"] >= lower) & 
                (self.df["confidence"] < upper)
            ]
            
            if len(bracket_df) == 0:
                continue
            
            correct = bracket_df["correct_prediction"].sum()
            correct_rate = correct / len(bracket_df)
            avg_roi = bracket_df["roi"].mean()
            
            results.append(ConfidenceAnalysis(
                confidence_bracket=f"{lower*100:.0f}%-{upper*100:.0f}%",
                sample_count=len(bracket_df),
                correct_rate=correct_rate,
                avg_roi=avg_roi
            ))
        
        return results

    def analyze_strategy_variations(self) -> List[StrategyComparison]:
        """Test different confidence/danger thresholds"""
        strategies = [
            ("Conservative", 0.50, 0.50),  # High thresholds
            ("Moderate", 0.30, 0.35),      # Current (baseline)
            ("Aggressive", 0.20, 0.25),    # Low thresholds
            ("VeryAggressive", 0.10, 0.15),  # Very low thresholds
        ]
        
        results = []
        
        for strategy_name, conf_thresh, danger_thresh in strategies:
            # Filter decisions that pass these thresholds
            strategy_df = self.df[
                (self.df["confidence"] >= conf_thresh) &
                (self.df["danger_score"] >= danger_thresh * 100)
            ].copy()
            
            if len(strategy_df) == 0:
                continue
            
            # Treat all filtered decisions as "bets"
            wins = (strategy_df["actual_goals"] >= 1).sum()
            losses = (strategy_df["actual_goals"] == 0).sum()
            total = len(strategy_df)
            
            win_rate = (wins / total * 100) if total > 0 else 0
            roi_avg = ((wins - losses) / total * 100) if total > 0 else 0
            
            tp = ((strategy_df["actual_goals"] >= 1)).sum()
            fp = ((strategy_df["actual_goals"] == 0)).sum()
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            
            # F1 score (simplified)
            f1 = 2 * precision * win_rate / (precision + win_rate) if (precision + win_rate) > 0 else 0
            
            results.append(StrategyComparison(
                strategy_name=strategy_name,
                confidence_threshold=conf_thresh,
                danger_threshold=danger_thresh,
                total_bets=total,
                win_rate=win_rate,
                roi_avg=roi_avg,
                precision=precision,
                f1_score=f1
            ))
        
        return results

    def get_roi_distribution(self, bins: int = 10) -> Dict[str, int]:
        """Get distribution of ROI values"""
        roi_values = self.df[self.df["should_bet"]]["roi"].values
        
        if len(roi_values) == 0:
            return {}
        
        hist, edges = np.histogram(roi_values, bins=bins)
        
        result = {}
        for i, count in enumerate(hist):
            label = f"{edges[i]:.1f} to {edges[i+1]:.1f}"
            result[label] = int(count)
        
        return result

    def get_accuracy_by_confidence(self) -> List[Dict]:
        """Get accuracy/confidence correlation for visualization"""
        # Group by confidence deciles
        self.df["conf_decile"] = pd.cut(
            self.df["confidence"],
            bins=10,
            labels=[f"{i*10}-{(i+1)*10}%" for i in range(10)]
        )
        
        result = []
        for decile in self.df["conf_decile"].unique():
            if pd.isna(decile):
                continue
            
            decile_df = self.df[self.df["conf_decile"] == decile]
            accuracy = decile_df["correct_prediction"].mean()
            count = len(decile_df)
            
            result.append({
                "confidence_range": str(decile),
                "accuracy": accuracy,
                "count": count
            })
        
        return result

    def export_analysis(self, output_dir: str = ".") -> Dict[str, str]:
        """Export all analysis results"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        files = {}
        
        # Export interval analysis
        interval_analysis = self.analyze_by_interval()
        interval_file = output_path / "analysis_by_interval.json"
        with open(interval_file, "w") as f:
            json.dump(
                {k: asdict(v) for k, v in interval_analysis.items()},
                f,
                indent=2
            )
        files["interval_analysis"] = str(interval_file)
        logger.info(f"✅ Interval analysis saved")
        
        # Export confidence distribution
        conf_analysis = self.analyze_confidence_distribution()
        conf_file = output_path / "analysis_confidence_distribution.json"
        with open(conf_file, "w") as f:
            json.dump([asdict(v) for v in conf_analysis], f, indent=2)
        files["confidence_distribution"] = str(conf_file)
        logger.info(f"✅ Confidence distribution saved")
        
        # Export strategy comparison
        strategy_analysis = self.analyze_strategy_variations()
        strategy_file = output_path / "analysis_strategy_comparison.json"
        with open(strategy_file, "w") as f:
            json.dump([asdict(v) for v in strategy_analysis], f, indent=2)
        files["strategy_comparison"] = str(strategy_file)
        logger.info(f"✅ Strategy comparison saved")
        
        # Export ROI distribution
        roi_dist = self.get_roi_distribution()
        roi_file = output_path / "analysis_roi_distribution.json"
        with open(roi_file, "w") as f:
            json.dump(roi_dist, f, indent=2)
        files["roi_distribution"] = str(roi_file)
        logger.info(f"✅ ROI distribution saved")
        
        # Export accuracy by confidence
        acc_conf = self.get_accuracy_by_confidence()
        acc_file = output_path / "analysis_accuracy_by_confidence.json"
        with open(acc_file, "w") as f:
            json.dump(acc_conf, f, indent=2)
        files["accuracy_by_confidence"] = str(acc_file)
        logger.info(f"✅ Accuracy by confidence saved")
        
        return files


def main():
    """Demonstration of backtesting analyzer"""
    print("\n" + "="*70)
    print("📊 BACKTESTING ANALYZER DEMONSTRATION")
    print("="*70)
    
    try:
        analyzer = BacktestingAnalyzer()
        print("\n✅ Analyzer initialized")
        
        # Interval analysis
        print("\n📈 Analyzing by interval...")
        interval_metrics = analyzer.analyze_by_interval()
        print("\nInterval Metrics:")
        for interval, metrics in interval_metrics.items():
            print(f"\n  {interval}:")
            print(f"    Decisions: {metrics.decisions}")
            print(f"    Bets Triggered: {metrics.bets_triggered}")
            print(f"    Wins: {metrics.wins}")
            print(f"    Win Rate: {metrics.win_rate:.1f}%")
            print(f"    ROI Avg: {metrics.roi_avg:.1f}%")
            print(f"    Precision: {metrics.precision:.2%}")
        
        # Confidence distribution
        print("\n\n🎯 Confidence Distribution Analysis:")
        conf_analysis = analyzer.analyze_confidence_distribution()
        for analysis in conf_analysis:
            print(f"\n  {analysis.confidence_bracket}:")
            print(f"    Samples: {analysis.sample_count}")
            print(f"    Correct Rate: {analysis.correct_rate:.2%}")
            print(f"    Avg ROI: {analysis.avg_roi:.2f}x")
        
        # Strategy comparison
        print("\n\n🔄 Strategy Comparison:")
        strategies = analyzer.analyze_strategy_variations()
        print("\n{:20} {:10} {:10} {:10} {:10}".format("Strategy", "Bets", "Win%", "ROI%", "Precision"))
        print("-" * 60)
        for strat in strategies:
            print("{:20} {:10} {:10.1f}% {:10.1f}% {:10.2%}".format(
                strat.strategy_name,
                strat.total_bets,
                strat.win_rate,
                strat.roi_avg,
                strat.precision
            ))
        
        # Export all analysis
        print("\n\n💾 Exporting analysis...")
        files = analyzer.export_analysis()
        print("✅ Analysis exported:")
        for name, path in files.items():
            print(f"   {name}: {path}")
        
        print("\n" + "="*70)
        print("✨ Analysis complete!")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
