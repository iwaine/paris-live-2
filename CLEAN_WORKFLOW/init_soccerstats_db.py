import sqlite3

DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

schema = '''
DROP TABLE IF EXISTS soccerstats_scraped_matches;
CREATE TABLE IF NOT EXISTS soccerstats_scraped_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT,
    league_code TEXT,
    league TEXT,
    league_display_name TEXT,
    team TEXT,
    opponent TEXT,
    date TEXT,
    is_home BOOLEAN,
    score TEXT,
    goals_for INTEGER,
    goals_against INTEGER,
    goal_times TEXT,
    goal_times_conceded TEXT,
    match_id TEXT,
    ht_score TEXT,
    url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()
    conn.close()
    print("Table soccerstats_scraped_matches créée (ou déjà existante) dans predictions.db")

if __name__ == "__main__":
    main()
