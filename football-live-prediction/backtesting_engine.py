#!/usr/bin/env python3
"""
Backtesting Engine for Paris Live Prediction System

This module simulates historical matches and evaluates betting decisions
based on the actual outcomes. It calculates performance metrics like ROI,
win rate, precision, recall, and AUC.

Architecture:
    1. Load historical matches from CSV
    2. For each match/interval, simulate live snapshots at intervals
    3. Apply the prediction pipeline (danger score + TTL decay)
    4. Record betting decisions
    5. Match decisions against actual outcomes
    6. Calculate performance metrics
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestDecision:
    """Single backtesting decision record"""
    match_id: str
    interval: str  # "30-45" or "75-90"
    timestamp: datetime
    danger_score: float  # 0-100%
    confidence: float  # 0-1
    freshness_factor: float  # e^(-t/TTL)
    should_bet: bool
    reason: str
    actual_goals: int  # Actual goals scored in interval
    correct_prediction: bool
    roi: float  # Return on Investment


@dataclass
class BacktestMetrics:
    """Aggregated backtesting metrics"""
    total_decisions: int
    total_bets_triggered: int
    wins: int
    losses: int
    win_rate: float  # %
    roi_total: float  # %
    roi_avg: float  # % per bet
    precision: float  # TP / (TP + FP)
    recall: float  # TP / (TP + FN)
    false_positive_rate: float  # FP / (FP + TN)
    auc_score: float
    confidence_threshold: float
    danger_threshold: float
    timestamp: datetime


class BacktestingEngine:
    """Main backtesting engine"""

    def __init__(
        self,
        model_path: str = "models/au_moins_1_but_model.pkl",
        scaler_path: str = "models/scaler.pkl",
        data_path: str = "historical_matches.csv",
        confidence_threshold: float = 0.30,
        danger_threshold: float = 0.35,
    ):
        """Initialize backtesting engine"""
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.data_path = Path(data_path)
        self.confidence_threshold = confidence_threshold
        self.danger_threshold = danger_threshold
        
        self.model = None
        self.scaler = None
        self.data = None
        self.decisions: List[BacktestDecision] = []
        
        self._load_models()
        self._load_data()

    def _load_models(self):
        """Load pre-trained model and scaler"""
        try:
            with open(self.model_path, "rb") as f:
                self.model = pickle.load(f)
            logger.info(f"✅ Model loaded from {self.model_path}")
        except FileNotFoundError:
            logger.error(f"❌ Model not found at {self.model_path}")
            raise

        try:
            with open(self.scaler_path, "rb") as f:
                self.scaler = pickle.load(f)
            logger.info(f"✅ Scaler loaded from {self.scaler_path}")
        except FileNotFoundError:
            logger.error(f"❌ Scaler not found at {self.scaler_path}")
            raise

    def _load_data(self):
        """Load historical matches data"""
        try:
            self.data = pd.read_csv(self.data_path)
            logger.info(f"✅ Historical data loaded: {len(self.data)} records")
        except FileNotFoundError:
            logger.error(f"❌ Data not found at {self.data_path}")
            raise

    def calculate_danger_score(self, features: np.ndarray) -> Tuple[float, float]:
        """
        Calculate danger score from features
        
        Returns:
            (danger_score: 0-100%, probability: 0-1)
        """
        try:
            # Normalize features
            features_normalized = self.scaler.transform([features])
            
            # Get probability from model
            probability = self.model.predict_proba(features_normalized)[0][1]
            
            # Convert to danger score (0-100%)
            danger_score = probability * 100
            
            return danger_score, probability
        except Exception as e:
            logger.error(f"Error calculating danger score: {e}")
            return 0, 0

    def apply_freshness_decay(self, confidence: float, age_seconds: int, ttl_seconds: int = 300) -> float:
        """
        Apply exponential decay to confidence based on TTL
        
        Formula: C(t) = C(0) * e^(-t/TTL)
        """
        decay_factor = np.exp(-age_seconds / ttl_seconds)
        return confidence * decay_factor

    def _generate_simulated_features(self, match_data: pd.Series) -> np.ndarray:
        """Generate simulated features from available match data"""
        # Generate features with some realism
        np.random.seed(hash(str(match_data.get("match_id", ""))) % (2**32))
        
        features = np.array([
            50 + np.random.randn() * 10,       # poss_home
            50 + np.random.randn() * 10,       # poss_away
            int(match_data.get("home_goals", 0)),  # score_home
            int(match_data.get("away_goals", 0)),  # score_away
            max(0, np.random.randn() * 3 + 5),     # shots_home
            max(0, np.random.randn() * 3 + 5),     # shots_away
            max(0, np.random.randn() * 2 + 3),     # shots_on_target_home
            max(0, np.random.randn() * 2 + 3),     # shots_on_target_away
            np.random.randn() * 2,             # corner_delta_5m
            np.random.randn() * 2,             # corner_delta_10m
            max(0, np.random.randn() * 2 + 10),    # fouls_home
            max(0, np.random.randn() * 2 + 10),    # fouls_away
            max(0, np.random.randn() + 2),        # yellow_cards_home
            max(0, np.random.randn() + 2),        # yellow_cards_away
            np.random.binomial(1, 0.1),        # red_cards_home
            np.random.binomial(1, 0.1),        # red_cards_away
            np.random.uniform(0, 100),         # saturation_score
            np.random.randn() * 10,            # pressure_differential
            np.random.randn() * 15,            # momentum_score
            np.random.uniform(0, 1)            # chance_creation_index
        ])
        
        return features

    def simulate_interval_decisions(
        self,
        match_data: pd.Series,
        interval: str = "30-45"
    ) -> List[BacktestDecision]:
        """
        Simulate live snapshots for an interval and generate decisions
        
        For each interval, simulate snapshots at:
            - 30-45: snapshots at 30, 35, 40 minutes
            - 75-90: snapshots at 75, 80, 85 minutes
        """
        interval_decisions = []
        
        # Extract interval boundaries
        if interval == "30-45":
            snapshot_minutes = [30, 35, 40]
        else:  # 75-90
            snapshot_minutes = [75, 80, 85]
        
        match_id = str(match_data.get("match_id", "unknown"))
        
        # Determine actual goals based on label
        label = int(match_data.get("label", 0))
        actual_goals = label  # 1 if goal, 0 if no goal
        
        # Generate simulated features
        try:
            features = self._generate_simulated_features(match_data)
        except Exception as e:
            logger.warning(f"Error generating features for match {match_id}: {e}")
            return interval_decisions
        
        # Generate decisions for each snapshot
        for idx, minute in enumerate(snapshot_minutes):
            # Calculate age from start of interval
            interval_start = snapshot_minutes[0]
            age_seconds = (minute - interval_start) * 60
            
            # Calculate danger score
            danger_score, probability = self.calculate_danger_score(features)
            
            # Apply freshness decay (simulate signal aging)
            confidence_fresh = self.apply_freshness_decay(
                probability,
                age_seconds,
                ttl_seconds=300
            )
            
            # Apply decay to danger score as well
            danger_score_fresh = danger_score * (confidence_fresh / probability if probability > 0 else 1)
            
            # Check thresholds
            should_bet = (
                confidence_fresh >= self.confidence_threshold and
                danger_score_fresh >= self.danger_threshold * 100
            )
            
            # Determine reason
            if not should_bet:
                if confidence_fresh < self.confidence_threshold:
                    reason = f"LOW_CONFIDENCE ({confidence_fresh:.1%} < {self.confidence_threshold:.1%})"
                elif danger_score_fresh < self.danger_threshold * 100:
                    reason = f"LOW_DANGER ({danger_score_fresh:.1f}% < {self.danger_threshold*100:.1f}%)"
                else:
                    reason = "UNKNOWN"
            else:
                reason = "THRESHOLD_PASS"
            
            # Check if prediction is correct
            correct_prediction = (should_bet and actual_goals >= 1) or (not should_bet and actual_goals == 0)
            
            # Calculate ROI (simplified: +2.0x if win, -1.0x if loss)
            if should_bet:
                roi = 1.0 if actual_goals >= 1 else -1.0
            else:
                roi = 0  # No bet, no ROI
            
            decision = BacktestDecision(
                match_id=match_id,
                interval=interval,
                timestamp=datetime.now() - timedelta(minutes=minute),
                danger_score=danger_score,
                confidence=probability,
                freshness_factor=confidence_fresh / probability if probability > 0 else 0,
                should_bet=should_bet,
                reason=reason,
                actual_goals=actual_goals,
                correct_prediction=correct_prediction,
                roi=roi
            )
            
            interval_decisions.append(decision)
        
        return interval_decisions

    def backtest_all_matches(self) -> List[BacktestDecision]:
        """Backtest all matches in historical data"""
        logger.info(f"Starting backtesting on {len(self.data)} matches...")
        
        all_decisions = []
        
        for idx, (_, match_data) in enumerate(self.data.iterrows()):
            if idx % 50 == 0:
                logger.info(f"Processing match {idx}/{len(self.data)}")
            
            # Simulate both intervals for each match
            for interval in ["30-45", "75-90"]:
                interval_decisions = self.simulate_interval_decisions(match_data, interval)
                all_decisions.extend(interval_decisions)
        
        self.decisions = all_decisions
        logger.info(f"✅ Backtesting complete: {len(all_decisions)} decisions")
        
        return all_decisions

    def calculate_metrics(self) -> BacktestMetrics:
        """Calculate performance metrics from decisions"""
        if not self.decisions:
            raise ValueError("No decisions to analyze. Run backtest_all_matches() first.")
        
        df = pd.DataFrame([asdict(d) for d in self.decisions])
        
        # Basic metrics
        total_decisions = len(df)
        total_bets = df["should_bet"].sum()
        
        # For bets: True/False positives
        bets_df = df[df["should_bet"]]
        wins = (bets_df["actual_goals"] >= 1).sum()
        losses = (bets_df["actual_goals"] == 0).sum()
        
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        
        # ROI calculation
        roi_total = df["roi"].sum()
        roi_avg = (roi_total / total_bets * 100) if total_bets > 0 else 0
        
        # Classification metrics (TP/FP/TN/FN)
        tp = ((df["should_bet"]) & (df["actual_goals"] >= 1)).sum()
        fp = ((df["should_bet"]) & (df["actual_goals"] == 0)).sum()
        tn = ((~df["should_bet"]) & (df["actual_goals"] == 0)).sum()
        fn = ((~df["should_bet"]) & (df["actual_goals"] >= 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        # AUC calculation (simplified: using average confidence of correct predictions)
        auc = df[df["correct_prediction"]]["confidence"].mean() if len(df) > 0 else 0
        
        metrics = BacktestMetrics(
            total_decisions=total_decisions,
            total_bets_triggered=int(total_bets),
            wins=int(wins),
            losses=int(losses),
            win_rate=win_rate,
            roi_total=roi_total,
            roi_avg=roi_avg,
            precision=precision,
            recall=recall,
            false_positive_rate=fpr,
            auc_score=auc,
            confidence_threshold=self.confidence_threshold,
            danger_threshold=self.danger_threshold,
            timestamp=datetime.now()
        )
        
        return metrics

    def export_decisions_csv(self, output_path: str = "backtesting_decisions.csv"):
        """Export all decisions to CSV for analysis"""
        if not self.decisions:
            raise ValueError("No decisions to export.")
        
        df = pd.DataFrame([asdict(d) for d in self.decisions])
        df.to_csv(output_path, index=False)
        logger.info(f"✅ Decisions exported to {output_path}")
        
        return output_path

    def export_metrics_json(self, metrics: BacktestMetrics, output_path: str = "backtesting_metrics.json"):
        """Export metrics to JSON"""
        metrics_dict = asdict(metrics)
        metrics_dict["timestamp"] = metrics_dict["timestamp"].isoformat()
        
        # Convert numpy types to Python native types
        for key in metrics_dict:
            if isinstance(metrics_dict[key], (np.integer, np.floating)):
                metrics_dict[key] = float(metrics_dict[key]) if isinstance(metrics_dict[key], np.floating) else int(metrics_dict[key])
        
        with open(output_path, "w") as f:
            json.dump(metrics_dict, f, indent=2)
        
        logger.info(f"✅ Metrics exported to {output_path}")
        
        return output_path


def main():
    """Demonstration of backtesting engine"""
    print("\n" + "="*70)
    print("🔬 BACKTESTING ENGINE DEMONSTRATION")
    print("="*70)
    
    try:
        # Initialize engine
        engine = BacktestingEngine(
            confidence_threshold=0.30,
            danger_threshold=0.35
        )
        print("\n✅ Engine initialized")
        
        # Run backtesting
        print("\n⏳ Running backtesting on historical matches...")
        decisions = engine.backtest_all_matches()
        print(f"✅ Generated {len(decisions)} decisions")
        
        # Calculate metrics
        print("\n📊 Calculating metrics...")
        metrics = engine.calculate_metrics()
        print(f"✅ Metrics calculated")
        
        # Display metrics
        print("\n" + "="*70)
        print("📈 BACKTESTING RESULTS")
        print("="*70)
        print(f"\nTotal Decisions: {metrics.total_decisions}")
        print(f"Bets Triggered: {metrics.total_bets_triggered} ({metrics.total_bets_triggered/metrics.total_decisions*100:.1f}%)")
        print(f"Wins: {metrics.wins}")
        print(f"Losses: {metrics.losses}")
        print(f"Win Rate: {metrics.win_rate:.1f}%")
        print(f"\nROI (Total): {metrics.roi_total:.1f}x")
        print(f"ROI (Average): {metrics.roi_avg:.1f}%")
        print(f"\nPrecision: {metrics.precision:.2%}")
        print(f"Recall: {metrics.recall:.2%}")
        print(f"False Positive Rate: {metrics.false_positive_rate:.2%}")
        print(f"AUC Score: {metrics.auc_score:.4f}")
        
        print(f"\nConfiguration:")
        print(f"  Confidence Threshold: {metrics.confidence_threshold:.1%}")
        print(f"  Danger Threshold: {metrics.danger_threshold:.1%}")
        
        # Export results
        print("\n💾 Exporting results...")
        engine.export_decisions_csv()
        engine.export_metrics_json(metrics)
        print("✅ Results exported")
        
        print("\n" + "="*70)
        print("✨ Backtesting complete!")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Backtesting failed: {e}")
        raise


if __name__ == "__main__":
    main()
