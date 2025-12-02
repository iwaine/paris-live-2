#!/usr/bin/env python3
"""
Phase 3: Signal TTL & Freshness Decay Manager

Manages signal staleness and confidence decay over time.

Key Features:
  - Freshness decay: confidence * e^(-elapsed_time / TTL)
  - TTL = 300 seconds (5 minutes) - configurable
  - Stale signal filtering: signals older than TTL are dropped
  - Signal history tracking with timestamps
  - Confidence thresholds for betting

Architecture:
  Signal Flow → TTL Manager → Decay Applied → Confidence Threshold → Output Decision

Formulas:
  - Freshness decay: P(t) = P(0) * e^(-t / TTL)
  - Where: t = elapsed time (seconds), TTL = 300s
  - Example: at t=150s (halfway through TTL), confidence = 0.606 * original

Output:
  - danger_score_fresh: Decayed danger score (0-100)
  - confidence_fresh: Decayed confidence (0-1)
  - freshness_factor: e^(-t/TTL) (0-1 scale)
  - is_stale: Boolean (True if t > TTL)
  - signal_age_seconds: Time elapsed since signal generation
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DangerSignal:
    """A danger signal with timestamp and metadata."""
    signal_id: str
    timestamp: float  # Unix timestamp (seconds)
    danger_score: float  # 0-100
    confidence: float  # 0-1
    interval: Tuple[int, int]  # (30, 45) or (75, 90)
    market_suspended: bool
    ttl_seconds: int
    match_id: str
    minute: int
    home_team: str
    away_team: str
    score: str  # "1-0"
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)


class SignalTTLManager:
    """
    Manages signal TTL and freshness decay.
    
    TTL = 300 seconds (5 minutes)
    At t=0: confidence = 100%
    At t=150s: confidence = 60.6%
    At t=300s: confidence = 36.8%
    At t>300s: signal is STALE (filtered out)
    """
    
    DEFAULT_TTL = 300  # 5 minutes
    DECAY_BASE = np.e  # Natural exponential
    
    def __init__(self, ttl_seconds: int = DEFAULT_TTL, confidence_threshold: float = 0.3):
        """
        Initialize TTL manager.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default 300s = 5 min)
            confidence_threshold: Minimum confidence to emit signal (0-1, default 0.3 = 30%)
        """
        self.ttl_seconds = ttl_seconds
        self.confidence_threshold = confidence_threshold
        self.signal_history: List[DangerSignal] = []
        self.logger = logger
    
    def calculate_freshness_factor(self, signal_age_seconds: float) -> float:
        """
        Calculate freshness decay factor: e^(-t / TTL).
        
        At t=0: factor = 1.0 (100% confidence)
        At t=TTL: factor ≈ 0.368 (36.8% confidence)
        At t=2*TTL: factor ≈ 0.135 (13.5% confidence)
        """
        if signal_age_seconds < 0:
            return 1.0
        
        exponent = -signal_age_seconds / self.ttl_seconds
        freshness = np.exp(exponent)
        
        return float(freshness)
    
    def apply_freshness_decay(self, signal: DangerSignal,
                             current_time: Optional[float] = None) -> Dict:
        """
        Apply freshness decay to a signal.
        
        Returns: {
            'signal_id': str,
            'danger_score_fresh': float (0-100),
            'confidence_fresh': float (0-1),
            'freshness_factor': float (0-1),
            'signal_age_seconds': float,
            'is_stale': bool,
            'is_filtered': bool,
            'reason': str (optional, if filtered)
        }
        """
        if current_time is None:
            current_time = datetime.now().timestamp()
        
        # Calculate signal age
        signal_age = current_time - signal.timestamp
        
        # Check if stale (older than TTL)
        is_stale = signal_age > self.ttl_seconds
        
        # Calculate freshness factor
        freshness = self.calculate_freshness_factor(signal_age)
        
        # Apply decay to confidence
        confidence_fresh = signal.confidence * freshness
        
        # Apply decay to danger score (via confidence)
        danger_score_fresh = signal.danger_score * freshness
        
        # Check confidence threshold
        is_filtered = False
        filter_reason = None
        
        if is_stale:
            is_filtered = True
            filter_reason = f"Signal older than TTL ({signal_age:.1f}s > {self.ttl_seconds}s)"
        elif confidence_fresh < self.confidence_threshold:
            is_filtered = True
            filter_reason = f"Confidence below threshold ({confidence_fresh:.2f} < {self.confidence_threshold:.2f})"
        
        result = {
            'signal_id': signal.signal_id,
            'danger_score_fresh': float(danger_score_fresh),
            'confidence_fresh': float(confidence_fresh),
            'freshness_factor': float(freshness),
            'signal_age_seconds': float(signal_age),
            'is_stale': is_stale,
            'is_filtered': is_filtered,
        }
        
        if filter_reason:
            result['filter_reason'] = filter_reason
        
        return result
    
    def process_signal(self, signal: DangerSignal,
                      current_time: Optional[float] = None,
                      emit_if_filtered: bool = False) -> Optional[Dict]:
        """
        Process a danger signal with TTL and freshness decay.
        
        Returns processed signal dict, or None if filtered (and emit_if_filtered=False).
        """
        if current_time is None:
            current_time = datetime.now().timestamp()
        
        # Apply freshness decay
        decayed = self.apply_freshness_decay(signal, current_time)
        
        # Check if should be filtered
        if decayed['is_filtered']:
            if emit_if_filtered:
                logger.warning(f"⚠️ Signal filtered: {decayed['filter_reason']}")
                return decayed
            else:
                logger.warning(f"🚫 Signal dropped: {decayed['filter_reason']}")
                return None
        
        # Add to history
        self.signal_history.append(signal)
        
        # Log processed signal
        logger.info(f"✅ Signal processed: danger_score_fresh={decayed['danger_score_fresh']:.1f}%, "
                   f"confidence={decayed['confidence_fresh']:.2f}, "
                   f"freshness={decayed['freshness_factor']:.2f}, "
                   f"age={decayed['signal_age_seconds']:.1f}s")
        
        return decayed
    
    def process_signal_stream(self, signals: List[DangerSignal],
                             current_time: Optional[float] = None) -> List[Dict]:
        """
        Process a stream of danger signals, applying freshness decay.
        
        Returns: List of processed signals (filtered signals excluded)
        """
        if current_time is None:
            current_time = datetime.now().timestamp()
        
        processed = []
        filtered_count = 0
        
        for signal in signals:
            result = self.process_signal(signal, current_time, emit_if_filtered=False)
            if result is not None:
                processed.append(result)
            else:
                filtered_count += 1
        
        logger.info(f"Signal stream: {len(signals)} input → {len(processed)} output, "
                   f"{filtered_count} filtered")
        
        return processed
    
    def get_signal_statistics(self) -> Dict:
        """Get statistics about signal processing."""
        if not self.signal_history:
            return {
                'total_signals': 0,
                'avg_age': 0.0,
                'avg_confidence': 0.0,
                'avg_danger_score': 0.0,
            }
        
        current_time = datetime.now().timestamp()
        ages = [current_time - s.timestamp for s in self.signal_history]
        
        return {
            'total_signals': len(self.signal_history),
            'avg_age': float(np.mean(ages)),
            'avg_confidence': float(np.mean([s.confidence for s in self.signal_history])),
            'avg_danger_score': float(np.mean([s.danger_score for s in self.signal_history])),
            'oldest_signal_age': float(max(ages)) if ages else 0.0,
            'newest_signal_age': float(min(ages)) if ages else 0.0,
        }
    
    def get_confidence_evolution(self, signal_age_points: Optional[List[int]] = None) -> Dict:
        """
        Get confidence evolution over time for visualization.
        
        Args:
            signal_age_points: Time points in seconds (default: 0, 50, 100, ..., 300+)
        
        Returns: {
            'age_seconds': [0, 50, 100, ...],
            'confidence_factor': [1.0, 0.849, 0.721, ...],
            'confidence_percentage': [100, 84.9, 72.1, ...],
        }
        """
        if signal_age_points is None:
            signal_age_points = list(range(0, self.ttl_seconds + 60, 50))
        
        factors = [self.calculate_freshness_factor(t) for t in signal_age_points]
        percentages = [f * 100 for f in factors]
        
        return {
            'age_seconds': signal_age_points,
            'confidence_factor': [float(f) for f in factors],
            'confidence_percentage': [float(p) for p in percentages],
            'ttl_seconds': self.ttl_seconds,
        }


class DynamicTTLManager:
    """
    Advanced TTL manager with dynamic TTL adjustment based on events.
    
    Features:
    - Penalty event: extend TTL by 45s (market suspension)
    - Goal scored: reset TTL (fresh signal)
    - No events: normal decay
    """
    
    def __init__(self, base_ttl: int = 300):
        self.base_ttl = base_ttl
        self.current_ttl = base_ttl
        self.event_history = []
    
    def adjust_ttl_for_event(self, event_type: str, event_time: float) -> int:
        """
        Adjust TTL based on event type.
        
        Returns: Current effective TTL in seconds
        """
        if event_type == 'penalty':
            self.current_ttl = self.base_ttl + 45  # Extend for penalty
            logger.info(f"🚨 Penalty detected - TTL extended to {self.current_ttl}s")
        
        elif event_type == 'goal':
            self.current_ttl = self.base_ttl  # Reset to base
            logger.info(f"⚽ Goal scored - TTL reset to {self.current_ttl}s")
        
        elif event_type == 'card':
            self.current_ttl = self.base_ttl + 15  # Minor extension
            logger.info(f"🟨 Card issued - TTL extended to {self.current_ttl}s")
        
        self.event_history.append({
            'timestamp': event_time,
            'event_type': event_type,
            'resulting_ttl': self.current_ttl,
        })
        
        return self.current_ttl


def demo_ttl_manager():
    """Demo: TTL manager with signal processing."""
    
    print("\n" + "=" * 70)
    print("🧪 SIGNAL TTL & FRESHNESS DECAY DEMO")
    print("=" * 70 + "\n")
    
    manager = SignalTTLManager(ttl_seconds=300, confidence_threshold=0.3)
    
    # Demo 1: Confidence evolution
    print("📈 CONFIDENCE EVOLUTION OVER TIME")
    print("-" * 70)
    evolution = manager.get_confidence_evolution()
    print(f"TTL: {evolution['ttl_seconds']}s\n")
    print(f"{'Time (s)':<12} {'Freshness':<12} {'Confidence %':<15}")
    print("-" * 70)
    for age, factor, pct in zip(
        evolution['age_seconds'],
        evolution['confidence_factor'],
        evolution['confidence_percentage']
    ):
        print(f"{age:<12} {factor:<12.4f} {pct:<15.1f}%")
    
    # Demo 2: Process signals with varying ages
    print("\n" + "=" * 70)
    print("⏱️ SIGNAL PROCESSING WITH VARYING AGES")
    print("=" * 70 + "\n")
    
    base_time = datetime.now().timestamp()
    
    # Create signals at different ages
    signals = [
        DangerSignal(
            signal_id=f"SIG_{i:03d}",
            timestamp=base_time - age,  # Signal created 'age' seconds ago
            danger_score=60.0,
            confidence=0.75,
            interval=(30, 45),
            market_suspended=False,
            ttl_seconds=0,
            match_id="MATCH_001",
            minute=38,
            home_team="Test Home",
            away_team="Test Away",
            score="1-0",
        )
        for i, age in enumerate([0, 60, 150, 300, 350])
    ]
    
    print("Processing signal stream:")
    print(f"{'Signal ID':<12} {'Age (s)':<10} {'Original':<12} {'After Decay':<12} {'Status':<15}")
    print("-" * 70)
    
    processed = manager.process_signal_stream(signals, current_time=base_time)
    
    for signal, processed_result in zip(signals, [manager.apply_freshness_decay(s, base_time) for s in signals]):
        age = base_time - signal.timestamp
        status = "✅ ACTIVE" if not processed_result['is_filtered'] else "🚫 FILTERED"
        print(
            f"{signal.signal_id:<12} {age:<10.0f} {signal.danger_score:<12.1f}% "
            f"{processed_result['danger_score_fresh']:<12.1f}% {status:<15}"
        )
    
    # Demo 3: Dynamic TTL adjustment
    print("\n" + "=" * 70)
    print("⚡ DYNAMIC TTL ADJUSTMENT")
    print("=" * 70 + "\n")
    
    dyn_manager = DynamicTTLManager(base_ttl=300)
    
    events = [
        ('normal', base_time),
        ('penalty', base_time + 5),
        ('goal', base_time + 10),
        ('card', base_time + 15),
    ]
    
    print(f"{'Event':<12} {'Time':<10} {'Resulting TTL':<15}")
    print("-" * 70)
    for event_type, event_time in events:
        ttl = dyn_manager.adjust_ttl_for_event(event_type, event_time)
        print(f"{event_type:<12} {event_time-base_time:<10.0f}s {ttl:<15}s")
    
    # Demo 4: Statistics
    print("\n" + "=" * 70)
    print("📊 SIGNAL STATISTICS")
    print("=" * 70 + "\n")
    
    stats = manager.get_signal_statistics()
    print(f"Total signals processed: {stats['total_signals']}")
    print(f"Average age: {stats['avg_age']:.1f}s")
    print(f"Average confidence: {stats['avg_confidence']:.2f}")
    print(f"Average danger score: {stats['avg_danger_score']:.1f}%")
    print(f"Oldest signal: {stats['oldest_signal_age']:.1f}s")
    print(f"Newest signal: {stats['newest_signal_age']:.1f}s")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_ttl_manager()
