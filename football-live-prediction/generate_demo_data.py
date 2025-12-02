#!/usr/bin/env python3
"""
Generate demo historical data for Phase 1 testing.

Since SoccerStats scraping URLs are complex, this generates realistic
training data to validate the entire Phase 1 pipeline:
- Feature extraction
- ML model training
- Danger score calculation
- Historical label generation

Output: historical_matches.csv with 500 demo matches (1000 labels)
"""

import csv
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

# Demo match data
DEMO_MATCHES = [
    ("Paris", "Lyon", "France", "Ligue 1"),
    ("Real Madrid", "Barcelona", "Spain", "La Liga"),
    ("Manchester United", "Liverpool", "England", "Premier League"),
    ("Bayern Munich", "Borussia Dortmund", "Germany", "Bundesliga"),
    ("Juventus", "AC Milan", "Italy", "Serie A"),
    ("PSG", "Marseille", "France", "Ligue 1"),
    ("Arsenal", "Chelsea", "England", "Premier League"),
    ("RB Leipzig", "Stuttgart", "Germany", "Bundesliga"),
    ("Inter Milan", "Roma", "Italy", "Serie A"),
    ("Atletico Madrid", "Sevilla", "Spain", "La Liga"),
]

# Generate event data
def generate_events(home_goals: int, away_goals: int) -> List[dict]:
    """Generate realistic goal events for a match."""
    events = []
    
    # Home team goals
    for _ in range(home_goals):
        minute = random.randint(5, 85)
        events.append({
            "minute": minute,
            "event_type": "goal",
            "team": "home",
            "player": f"Player_{random.randint(1, 100)}"
        })
    
    # Away team goals
    for _ in range(away_goals):
        minute = random.randint(5, 85)
        events.append({
            "minute": minute,
            "event_type": "goal",
            "team": "away",
            "player": f"Player_{random.randint(1, 100)}"
        })
    
    return events


def generate_label_for_interval(events: List[dict], interval_start: int, interval_end: int) -> Tuple[int, List[int]]:
    """
    Generate label for an interval.
    Returns: (label, goal_minutes)
    
    label = 1 if at least one goal in [interval_start, interval_end]
    label = 0 otherwise
    """
    goal_minutes = [
        e["minute"] for e in events
        if e["event_type"] == "goal" and interval_start <= e["minute"] <= interval_end
    ]
    
    label = 1 if len(goal_minutes) > 0 else 0
    return label, goal_minutes


def generate_demo_data(num_matches: int = 500) -> None:
    """Generate demo historical data and save to CSV + SQLite."""
    
    print(f"🔄 Generating {num_matches} demo matches...")
    
    matches = []
    labels_data = []
    
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_matches):
        # Randomly select teams
        home_team, away_team, league, league_name = random.choice(DEMO_MATCHES)
        
        # Generate realistic score distribution
        # Most matches 0-3 goals per team (follows real football distribution)
        home_goals = random.choices(
            [0, 1, 2, 3, 4],
            weights=[30, 35, 20, 10, 5],
            k=1
        )[0]
        away_goals = random.choices(
            [0, 1, 2, 3, 4],
            weights=[30, 35, 20, 10, 5],
            k=1
        )[0]
        
        match_id = f"DEMO_{i:05d}"
        match_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Generate events
        events = generate_events(home_goals, away_goals)
        events_json = json.dumps(events)
        
        matches.append({
            "match_id": match_id,
            "match_date": match_date,
            "league": league_name,
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "events_json": events_json,
        })
        
        # Generate labels for both intervals
        for interval_start, interval_end in [(30, 45), (75, 90)]:
            label, goal_minutes = generate_label_for_interval(events, interval_start, interval_end)
            goals_count = len(goal_minutes)
            goal_minutes_str = ",".join(map(str, goal_minutes))
            
            labels_data.append({
                "match_id": match_id,
                "interval_start": interval_start,
                "interval_end": interval_end,
                "label": label,
                "goals_count": goals_count,
                "goal_minutes": goal_minutes_str,
            })
    
    # Save to CSV
    csv_path = Path("historical_matches.csv")
    print(f"💾 Saving {len(matches)} matches to {csv_path}...")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["match_id", "match_date", "league", "home_team", "away_team", "home_goals", "away_goals", "interval_start", "interval_end", "label", "goals_count", "goal_minutes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write matches with labels
        for match in matches:
            for label_data in labels_data:
                if label_data["match_id"] == match["match_id"]:
                    writer.writerow({
                        "match_id": match["match_id"],
                        "match_date": match["match_date"],
                        "league": match["league"],
                        "home_team": match["home_team"],
                        "away_team": match["away_team"],
                        "home_goals": match["home_goals"],
                        "away_goals": match["away_goals"],
                        "interval_start": label_data["interval_start"],
                        "interval_end": label_data["interval_end"],
                        "label": label_data["label"],
                        "goals_count": label_data["goals_count"],
                        "goal_minutes": label_data["goal_minutes"],
                    })
    
    # Save to SQLite
    db_path = Path("paris_live.db")
    print(f"💾 Saving data to {db_path}...")
    
    conn = sqlite3.connect(str(db_path))
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
    
    # Insert matches
    for match in matches:
        cursor.execute('''
            INSERT OR REPLACE INTO historical_matches
            (match_id, match_date, league, home_team, away_team, home_goals, away_goals, events_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match["match_id"],
            match["match_date"],
            match["league"],
            match["home_team"],
            match["away_team"],
            match["home_goals"],
            match["away_goals"],
            match["events_json"],
        ))
    
    # Insert labels
    for label_data in labels_data:
        cursor.execute('''
            INSERT INTO historical_labels
            (match_id, interval_start, interval_end, label, goals_count, goal_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            label_data["match_id"],
            label_data["interval_start"],
            label_data["interval_end"],
            label_data["label"],
            label_data["goals_count"],
            label_data["goal_minutes"],
        ))
    
    conn.commit()
    conn.close()
    
    # Print summary
    total_labels = len(labels_data)
    goals_count = sum(1 for l in labels_data if l["label"] == 1)
    no_goals_count = total_labels - goals_count
    
    print("\n" + "=" * 70)
    print("✅ DEMO DATA GENERATION COMPLETE")
    print("=" * 70)
    print(f"Total matches: {len(matches)}")
    print(f"Total labels: {total_labels}")
    print(f"  - Goals in interval: {goals_count} ({goals_count/total_labels*100:.1f}%)")
    print(f"  - No goals: {no_goals_count} ({no_goals_count/total_labels*100:.1f}%)")
    print(f"\nOutput files:")
    print(f"  - CSV: {csv_path.absolute()}")
    print(f"  - SQLite: {db_path.absolute()}")
    print("=" * 70)
    print("\n✅ Ready for Phase 1 ML training pipeline!")
    print("   Next: python ml_model_training.py")
    print("=" * 70)


if __name__ == "__main__":
    generate_demo_data(num_matches=500)
