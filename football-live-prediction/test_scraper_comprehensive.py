#!/usr/bin/env python
"""
Comprehensive test suite for historical_scraper.py

Validates:
1. Scraper initialization
2. Event parsing logic
3. Label generation logic
4. CSV/Database output format
"""

import csv
import sqlite3
import tempfile
from pathlib import Path

from historical_scraper import (
    HistoricalMatch,
    MatchEvent,
    SoccerStatsHistoricalScraper,
)


def test_match_event_creation():
    """Test MatchEvent dataclass."""
    print("🧪 Test 1: MatchEvent creation... ", end="")
    
    event = MatchEvent(
        minute=42,
        event_type='goal',
        team='home',
        player='Mbappé',
        description='Header from corner'
    )
    
    assert event.minute == 42
    assert event.event_type == 'goal'
    assert event.team == 'home'
    print("✅ PASS")


def test_historical_match_creation():
    """Test HistoricalMatch dataclass."""
    print("🧪 Test 2: HistoricalMatch creation... ", end="")
    
    events = [
        MatchEvent(38, 'goal', 'home', 'Mbappé'),
        MatchEvent(45, 'goal', 'away', 'Salah'),
        MatchEvent(82, 'goal', 'home', 'Neymar'),
    ]
    
    match = HistoricalMatch(
        match_id='123456',
        match_date='2024-11-15',
        league='france',
        home_team='Paris SG',
        away_team='Lyon',
        home_goals=2,
        away_goals=1,
        events=events,
    )
    
    assert match.total_goals == 3
    assert len(match.events) == 3
    print("✅ PASS")


def test_label_generation_30_45():
    """Test label generation for [30, 45] interval."""
    print("🧪 Test 3: Label generation [30,45]... ", end="")
    
    events = [
        MatchEvent(38, 'goal', 'home', 'Mbappé'),
        MatchEvent(82, 'goal', 'away', 'Salah'),
    ]
    
    match = HistoricalMatch(
        match_id='123456',
        match_date='2024-11-15',
        league='france',
        home_team='Paris SG',
        away_team='Lyon',
        home_goals=2,
        away_goals=1,
        events=events,
    )
    
    scraper = SoccerStatsHistoricalScraper()
    labels = scraper.generate_labels(match)
    
    # Should have 2 labels: [30,45] and [75,90]
    assert len(labels) == 2
    
    # [30,45]: label should be 1 (goal at 38)
    start_30, end_45, label_30_45, goals_30_45, mins_30_45 = labels[0]
    assert start_30 == 30 and end_45 == 45
    assert label_30_45 == 1, f"Expected label 1, got {label_30_45}"
    assert goals_30_45 == 1
    assert mins_30_45 == '38'
    
    # [75,90]: label should be 1 (goal at 82)
    start_75, end_90, label_75_90, goals_75_90, mins_75_90 = labels[1]
    assert start_75 == 75 and end_90 == 90
    assert label_75_90 == 1, f"Expected label 1, got {label_75_90}"
    assert goals_75_90 == 1
    assert mins_75_90 == '82'
    
    print("✅ PASS")


def test_label_generation_no_goals():
    """Test label generation with no goals in intervals."""
    print("🧪 Test 4: Label generation (no goals)... ", end="")
    
    events = [
        MatchEvent(15, 'goal', 'home', 'Mbappé'),  # Before [30,45]
        MatchEvent(60, 'goal', 'away', 'Salah'),  # Between intervals
    ]
    
    match = HistoricalMatch(
        match_id='654321',
        match_date='2024-11-15',
        league='england',
        home_team='Manchester',
        away_team='Liverpool',
        home_goals=2,
        away_goals=1,
        events=events,
    )
    
    scraper = SoccerStatsHistoricalScraper()
    labels = scraper.generate_labels(match)
    
    # [30,45]: label should be 0 (no goal in interval)
    start_30, end_45, label_30_45, goals_30_45, mins_30_45 = labels[0]
    assert label_30_45 == 0
    assert goals_30_45 == 0
    assert mins_30_45 == ''
    
    # [75,90]: label should be 0 (no goal in interval)
    start_75, end_90, label_75_90, goals_75_90, mins_75_90 = labels[1]
    assert label_75_90 == 0
    assert goals_75_90 == 0
    assert mins_75_90 == ''
    
    print("✅ PASS")


def test_label_generation_multiple_goals():
    """Test label generation with multiple goals in interval."""
    print("🧪 Test 5: Label generation (multiple goals)... ", end="")
    
    events = [
        MatchEvent(32, 'goal', 'home', 'Player A'),
        MatchEvent(40, 'goal', 'home', 'Player B'),
        MatchEvent(42, 'goal', 'away', 'Player C'),
        MatchEvent(80, 'goal', 'home', 'Player D'),
        MatchEvent(85, 'goal', 'away', 'Player E'),
    ]
    
    match = HistoricalMatch(
        match_id='999999',
        match_date='2024-11-15',
        league='germany',
        home_team='Bayern',
        away_team='Dortmund',
        home_goals=3,
        away_goals=2,
        events=events,
    )
    
    scraper = SoccerStatsHistoricalScraper()
    labels = scraper.generate_labels(match)
    
    # [30,45]: 3 goals (32, 40, 42)
    _, _, label_30_45, goals_30_45, mins_30_45 = labels[0]
    assert label_30_45 == 1
    assert goals_30_45 == 3
    assert mins_30_45 == '32,40,42'
    
    # [75,90]: 2 goals (80, 85)
    _, _, label_75_90, goals_75_90, mins_75_90 = labels[1]
    assert label_75_90 == 1
    assert goals_75_90 == 2
    assert mins_75_90 == '80,85'
    
    print("✅ PASS")


def test_csv_output_format():
    """Test CSV output generation."""
    print("🧪 Test 6: CSV output format... ", end="")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / 'test_matches.csv'
        
        events = [
            MatchEvent(38, 'goal', 'home', 'Mbappé'),
            MatchEvent(82, 'goal', 'away', 'Salah'),
        ]
        
        match = HistoricalMatch(
            match_id='123456',
            match_date='2024-11-15',
            league='france',
            home_team='Paris SG',
            away_team='Lyon',
            home_goals=2,
            away_goals=1,
            events=events,
        )
        
        scraper = SoccerStatsHistoricalScraper(
            output_csv=str(csv_path),
            db_path=str(Path(tmpdir) / 'test.db')
        )
        
        scraper.save_to_csv([match])
        
        # Verify file exists and has correct format
        assert csv_path.exists()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
            
            # First row: [30,45] interval with goal
            row1 = rows[0]
            assert row1['match_id'] == '123456'
            assert row1['league'] == 'france'
            assert row1['home_team'] == 'Paris SG'
            assert row1['interval_start'] == '30'
            assert row1['interval_end'] == '45'
            assert row1['label'] == '1'
            assert row1['goals_count'] == '1'
            assert row1['goal_minutes'] == '38'
            
            # Second row: [75,90] interval with goal
            row2 = rows[1]
            assert row2['interval_start'] == '75'
            assert row2['interval_end'] == '90'
            assert row2['label'] == '1'
            assert row2['goal_minutes'] == '82'
    
    print("✅ PASS")


def test_database_output_format():
    """Test SQLite database output."""
    print("🧪 Test 7: Database output format... ", end="")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'test.db'
        
        events = [
            MatchEvent(38, 'goal', 'home', 'Mbappé'),
            MatchEvent(82, 'goal', 'away', 'Salah'),
        ]
        
        match = HistoricalMatch(
            match_id='123456',
            match_date='2024-11-15',
            league='france',
            home_team='Paris SG',
            away_team='Lyon',
            home_goals=2,
            away_goals=1,
            events=events,
        )
        
        scraper = SoccerStatsHistoricalScraper(
            output_csv=str(Path(tmpdir) / 'test.csv'),
            db_path=str(db_path)
        )
        
        scraper.save_to_database([match])
        
        # Verify database schema and content
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check historical_matches table
        cursor.execute("SELECT COUNT(*) FROM historical_matches WHERE match_id = '123456'")
        match_count = cursor.fetchone()[0]
        assert match_count == 1
        
        # Check historical_labels table
        cursor.execute("SELECT COUNT(*) FROM historical_labels WHERE match_id = '123456'")
        label_count = cursor.fetchone()[0]
        assert label_count == 2
        
        # Verify label values
        cursor.execute("""
            SELECT interval_start, interval_end, label, goals_count
            FROM historical_labels
            WHERE match_id = '123456'
            ORDER BY interval_start
        """)
        rows = cursor.fetchall()
        
        assert rows[0] == (30, 45, 1, 1)
        assert rows[1] == (75, 90, 1, 1)
        
        conn.close()
    
    print("✅ PASS")


def test_database_initialization():
    """Test database initialization creates required tables."""
    print("🧪 Test 8: Database initialization... ", end="")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'test.db'
        
        scraper = SoccerStatsHistoricalScraper(db_path=str(db_path))
        
        # Verify tables exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
        """)
        tables = {row[0] for row in cursor.fetchall()}
        
        assert 'historical_matches' in tables
        assert 'historical_labels' in tables
        
        conn.close()
    
    print("✅ PASS")


def test_class_balance_calculation():
    """Test class balance calculation from multiple matches."""
    print("🧪 Test 9: Class balance calculation... ", end="")
    
    # Create matches with mixed labels
    matches = []
    
    # Match 1: 2 goals (one in each interval)
    matches.append(HistoricalMatch(
        match_id='1',
        match_date='2024-11-15',
        league='france',
        home_team='A',
        away_team='B',
        home_goals=2,
        away_goals=0,
        events=[
            MatchEvent(38, 'goal', 'home', 'X'),
            MatchEvent(82, 'goal', 'home', 'Y'),
        ],
    ))
    
    # Match 2: 0 goals
    matches.append(HistoricalMatch(
        match_id='2',
        match_date='2024-11-15',
        league='france',
        home_team='C',
        away_team='D',
        home_goals=0,
        away_goals=0,
        events=[],
    ))
    
    # Match 3: 1 goal (in 1st interval only)
    matches.append(HistoricalMatch(
        match_id='3',
        match_date='2024-11-15',
        league='france',
        home_team='E',
        away_team='F',
        home_goals=1,
        away_goals=0,
        events=[
            MatchEvent(35, 'goal', 'home', 'Z'),
        ],
    ))
    
    scraper = SoccerStatsHistoricalScraper()
    
    total_labels = 0
    goal_labels = 0
    
    for match in matches:
        labels = scraper.generate_labels(match)
        for _, _, label, _, _ in labels:
            total_labels += 1
            if label == 1:
                goal_labels += 1
    
    # Total: 3 matches × 2 intervals = 6 labels
    # Goals: 1 (38) + 0 + 0 + 0 + 0 + 1 (82) + 1 (35) = 3 goals
    # Actually: [30,45] has 2 goals (38, 35), [75,90] has 1 goal (82)
    # So we expect ~50% balance
    
    assert total_labels == 6
    balance = goal_labels / total_labels
    assert 0.4 < balance < 0.7, f"Class balance {balance} outside expected range"
    
    print("✅ PASS")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 RUNNING HISTORICAL SCRAPER TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_match_event_creation,
        test_historical_match_creation,
        test_label_generation_30_45,
        test_label_generation_no_goals,
        test_label_generation_multiple_goals,
        test_csv_output_format,
        test_database_output_format,
        test_database_initialization,
        test_class_balance_calculation,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ TESTS PASSED: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ TESTS FAILED: {failed}/{len(tests)}")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
