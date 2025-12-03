"""
HistoricalDataLoader - Scrape et charge les données de matchs historiques
avec les minutes exactes de chaque but
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.database_manager import DatabaseManager


class HistoricalDataLoader:
    """Charge les données historiques dans la BD"""

    def __init__(self, db_path: str = "data/predictions.db"):
        self.db = DatabaseManager(db_path)
        self.logger = logger
        logger.info("HistoricalDataLoader initialized")

    def load_test_data(self):
        """Charge des données de test réalistes"""

        # Teams
        teams = ["Arsenal", "Chelsea", "Manchester City", "Liverpool", "Manchester United"]

        logger.info(f"Loading test data for {len(teams)} teams...")

        match_count = 0

        # Pour chaque équipe, créer des matchs passés
        for i, home_team in enumerate(teams):
            for away_team in teams:
                if home_team == away_team:
                    continue

                # Créer 5 matchs passés pour chaque paire
                for match_num in range(5):
                    match_date = datetime.now() - timedelta(days=random.randint(50, 200))

                    # Générer des buts réalistes
                    home_goals = random.randint(0, 3)
                    away_goals = random.randint(0, 3)

                    match_data = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': 'england',
                        'match_date': match_date.isoformat(),
                        'final_score': f"{home_goals}-{away_goals}",
                        'home_goals': home_goals,
                        'away_goals': away_goals,
                    }

                    match_id = self.db.insert_match_history(match_data)

                    if match_id:
                        # Générer les buts avec minutes exactes
                        # Plus de buts dans [31-45] et [76-90]
                        for _ in range(home_goals):
                            minute = self._generate_goal_minute()
                            self.db.insert_goal(match_id, {
                                'team': 'home',
                                'minute': minute,
                                'player_name': f"{home_team} Player"
                            })

                        for _ in range(away_goals):
                            minute = self._generate_goal_minute()
                            self.db.insert_goal(match_id, {
                                'team': 'away',
                                'minute': minute,
                                'player_name': f"{away_team} Player"
                            })

                        match_count += 1

                        if match_count % 20 == 0:
                            logger.info(f"Loaded {match_count} matches...")

        logger.success(f"✓ Test data loaded: {match_count} matches with realistic goal distributions")

    def _generate_goal_minute(self) -> int:
        """
        Génère une minute réaliste pour un but
        Plus de probabilité dans [31-45] et [76-90]
        """
        choice = random.random()

        if choice < 0.35:  # 35% dans [31-45]
            return random.randint(31, 45)
        elif choice < 0.70:  # 35% dans [76-90]
            return random.randint(76, 90)
        elif choice < 0.85:  # 15% dans [16-30]
            return random.randint(16, 30)
        else:  # 15% dans [46-75]
            return random.randint(46, 75)

    def load_from_soccerstats(self, league_code: str, max_matches: int = 100):
        """
        Scrape les données depuis SoccerStats.com
        """
        from scrapers.soccerstats_match_history_scraper import SoccerStatsHistoricalScraper

        scraper = SoccerStatsHistoricalScraper()
        return scraper.scrape_league_history(league_code, max_matches)

    def get_teams_in_db(self) -> List[str]:
        """Récupère toutes les équipes de la BD"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute('''
                SELECT DISTINCT home_team FROM match_history
                UNION
                SELECT DISTINCT away_team FROM match_history
                ORDER BY 1
            ''')
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            return []

    def get_match_stats(self) -> Dict:
        """Récupère les stats de la BD"""
        try:
            cursor = self.db.connection.cursor()

            # Total matches
            cursor.execute('SELECT COUNT(*) FROM match_history')
            total_matches = cursor.fetchone()[0]

            # Total goals
            cursor.execute('SELECT COUNT(*) FROM goals')
            total_goals = cursor.fetchone()[0]

            # Teams
            cursor.execute('SELECT COUNT(DISTINCT home_team) FROM match_history')
            total_teams = cursor.fetchone()[0]

            return {
                'total_matches': total_matches,
                'total_goals': total_goals,
                'total_teams': total_teams,
            }
        except Exception as e:
            logger.error(f"Error getting match stats: {e}")
            return {}

    def clear_all(self):
        """Clear all data (DANGER!)"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute('DELETE FROM goals')
            cursor.execute('DELETE FROM match_history')
            cursor.execute('DELETE FROM goal_stats')
            self.db.connection.commit()
            logger.warning("✓ All historical data cleared!")
        except Exception as e:
            logger.error(f"Error clearing data: {e}")


if __name__ == "__main__":
    loader = HistoricalDataLoader()

    print("\n" + "="*70)
    print("📊 HISTORICAL DATA LOADER")
    print("="*70)

    # Check current stats
    stats = loader.get_match_stats()
    print(f"\n📈 Current data in DB:")
    print(f"  Matches: {stats.get('total_matches', 0)}")
    print(f"  Goals: {stats.get('total_goals', 0)}")
    print(f"  Teams: {stats.get('total_teams', 0)}")

    # Load test data if empty
    if stats.get('total_matches', 0) == 0:
        print(f"\n🔄 Loading test data...")
        loader.load_test_data()

        stats = loader.get_match_stats()
        print(f"\n✅ Data loaded:")
        print(f"  Matches: {stats.get('total_matches')}")
        print(f"  Goals: {stats.get('total_goals')}")
        print(f"  Teams: {stats.get('total_teams')}")

        teams = loader.get_teams_in_db()
        print(f"\n📋 Teams: {', '.join(teams[:5])}...")
    else:
        print(f"\n✓ Data already exists")

    print("\n" + "="*70)
