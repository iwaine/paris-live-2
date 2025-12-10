#!/usr/bin/env python3
"""
Load existing historical data from paris_live.db to predictions.db
This ensures we use REAL data, not demo data
"""

import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from utils.database_manager import DatabaseManager


def load_historical_data():
    """
    Load historical match data from paris_live.db to predictions.db
    """
    
    # Connect to source database (existing historical data)
    source_db_path = Path("./paris_live.db")
    if not source_db_path.exists():
        print(f"❌ Source database not found: {source_db_path}")
        return False
    
    source_conn = sqlite3.connect(str(source_db_path))
    source_conn.row_factory = sqlite3.Row
    source_cursor = source_conn.cursor()
    
    # Connect to target database (predictions)
    db = DatabaseManager(db_path="data/predictions.db")
    
    print("\n" + "=" * 80)
    print("LOADING HISTORICAL DATA FROM paris_live.db")
    print("=" * 80)
    
    # Get all historical matches
    source_cursor.execute("SELECT * FROM historical_matches LIMIT 1")
    columns = [description[0] for description in source_cursor.description]
    print(f"✅ Available columns: {', '.join(columns)}")
    
    # Count total records
    source_cursor.execute("SELECT COUNT(*) as total FROM historical_matches")
    total_records = source_cursor.fetchone()['total']
    print(f"✅ Found {total_records} historical matches to load")
    
    # Load matches
    source_cursor.execute("SELECT * FROM historical_matches")
    rows = source_cursor.fetchall()
    
    loaded = 0
    failed = 0
    
    for row in rows:
        try:
            # Extract match data
            match_data = {
                "home_team": row.get('home_team') or row.get('home') or 'Unknown',
                "away_team": row.get('away_team') or row.get('away') or 'Unknown',
                "league": row.get('league', 'unknown'),
                "match_date": row.get('match_date', row.get('date')),
                "final_score": f"{row.get('home_goals', 0)}-{row.get('away_goals', 0)}",
                "home_goals": row.get('home_goals', 0),
                "away_goals": row.get('away_goals', 0),
            }
            
            # Insert into predictions database
            match_id = db.insert_match(match_data)
            if match_id:
                loaded += 1
        
        except Exception as e:
            failed += 1
            continue
    
    source_conn.close()
    
    print("\n" + "=" * 80)
    print(f"✅ Successfully loaded: {loaded} matches")
    print(f"⚠️ Failed: {failed} matches")
    print(f"📊 Total in database: {loaded}")
    print("=" * 80)
    
    # Verify data loaded
    db_cursor = db.connection.cursor()
    db_cursor.execute("SELECT COUNT(*) as total FROM matches")
    final_count = db_cursor.fetchone()[0]
    print(f"\n✅ Final verification: {final_count} matches in predictions database")
    
    return loaded > 0


if __name__ == "__main__":
    try:
        success = load_historical_data()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(2)
