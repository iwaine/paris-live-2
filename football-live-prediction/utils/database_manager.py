"""
Base de données SQLite pour stocker les prédictions et matchs
"""
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from loguru import logger


class DatabaseManager:
    """Gestionnaire de la base de données SQLite"""
    
    def __init__(self, db_path: str = "data/predictions.db"):
        """
        Initialise la base de données
        
        Args:
            db_path: Chemin vers le fichier SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        
        self._init_db()
    
    def _init_db(self):
        """Initialise les tables"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            # Créer les tables
            self._create_tables()
            logger.info(f"✅ Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _create_tables(self):
        """Crée les tables si elles n'existent pas"""
        cursor = self.connection.cursor()
        
        # Table MATCHES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                league TEXT,
                match_date DATETIME,
                match_url TEXT,
                final_score TEXT,
                home_goals INTEGER,
                away_goals INTEGER,
                red_cards_home INTEGER DEFAULT 0,
                red_cards_away INTEGER DEFAULT 0,
                penalties_home INTEGER DEFAULT 0,
                penalties_away INTEGER DEFAULT 0,
                injuries_home TEXT,
                injuries_away TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(home_team, away_team, match_date)
            )
        ''')
        
        # Table PREDICTIONS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                minute INTEGER,
                interval TEXT,
                danger_score REAL,
                interpretation TEXT,
                prediction_text TEXT,
                confidence TEXT,
                home_goal_prob REAL,
                away_goal_prob REAL,
                predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                result_correct INTEGER,
                result_notes TEXT,
                FOREIGN KEY(match_id) REFERENCES matches(id)
            )
        ''')
        
        # Table NOTIFICATIONS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                prediction_id INTEGER,
                notification_type TEXT,
                message TEXT,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                FOREIGN KEY(match_id) REFERENCES matches(id),
                FOREIGN KEY(prediction_id) REFERENCES predictions(id)
            )
        ''')
        
        # Table STATS (cache pour les statistiques)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date DATE,
                total_predictions INTEGER,
                correct_predictions INTEGER,
                accuracy REAL,
                roi REAL,
                avg_danger_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stat_date)
            )
        ''')

        # Table MATCH_HISTORY (matchs historiques avec minutes exactes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                league TEXT,
                match_date DATETIME,
                final_score TEXT,
                home_goals INTEGER DEFAULT 0,
                away_goals INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(home_team, away_team, match_date)
            )
        ''')

        # Table GOALS (buts minute par minute)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                team TEXT NOT NULL,
                minute INTEGER NOT NULL,
                player_name TEXT,
                is_own_goal INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES match_history(id)
            )
        ''')

        # Table GOAL_STATS (pré-calculée pour rapidité)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                venue TEXT NOT NULL,
                interval_name TEXT NOT NULL,
                total_matches INTEGER DEFAULT 0,
                goals_scored INTEGER DEFAULT 0,
                goals_conceded INTEGER DEFAULT 0,
                avg_minute REAL,
                std_dev REAL,
                min_minute INTEGER,
                max_minute INTEGER,
                recent_matches INTEGER DEFAULT 0,
                recent_goals INTEGER DEFAULT 0,
                recent_avg_minute REAL,
                recent_std_dev REAL,
                minute_distribution TEXT,
                recent_minute_distribution TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_name, venue, interval_name)
            )
        ''')

        self.connection.commit()
        logger.info("✅ Database tables created")
    
    # ===== MATCHES =====
    
    def insert_match(self, match_data: Dict) -> Optional[int]:
        """
        Insère un match
        
        Args:
            match_data: Dict avec données du match
            
        Returns:
            ID du match inséré
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO matches 
                (home_team, away_team, league, match_date, match_url, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                match_data.get('home_team'),
                match_data.get('away_team'),
                match_data.get('league'),
                match_data.get('match_date'),
                match_data.get('match_url'),
                'live'
            ))
            self.connection.commit()
            logger.success(f"✓ Match inserted: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Match already exists")
            return None
        except Exception as e:
            logger.error(f"Error inserting match: {e}")
            return None
    
    def update_match_score(self, match_id: int, home_goals: int, away_goals: int):
        """Met à jour le score du match"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE matches 
                SET home_goals = ?, away_goals = ?, final_score = ?
                WHERE id = ?
            ''', (home_goals, away_goals, f"{home_goals}-{away_goals}", match_id))
            self.connection.commit()
            logger.success(f"✓ Match score updated: {home_goals}-{away_goals}")
        except Exception as e:
            logger.error(f"Error updating match score: {e}")
    
    def get_match(self, match_id: int) -> Optional[Dict]:
        """Récupère les infos d'un match"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM matches WHERE id = ?', (match_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching match: {e}")
            return None
    
    # ===== PREDICTIONS =====
    
    def insert_prediction(self, prediction_data: Dict) -> Optional[int]:
        """
        Insère une prédiction
        
        Args:
            prediction_data: Dict avec données de prédiction
            
        Returns:
            ID de la prédiction
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO predictions
                (match_id, minute, interval, danger_score, interpretation, 
                 confidence, home_goal_prob, away_goal_prob)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction_data.get('match_id'),
                prediction_data.get('minute'),
                prediction_data.get('interval'),
                prediction_data.get('danger_score'),
                prediction_data.get('interpretation'),
                prediction_data.get('confidence'),
                prediction_data.get('home_goal_prob'),
                prediction_data.get('away_goal_prob')
            ))
            self.connection.commit()
            logger.success(f"✓ Prediction inserted (danger: {prediction_data.get('danger_score')})")
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting prediction: {e}")
            return None
    
    def get_predictions_for_match(self, match_id: int) -> List[Dict]:
        """Récupère toutes les prédictions d'un match"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM predictions 
                WHERE match_id = ? 
                ORDER BY predicted_at DESC
            ''', (match_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching predictions: {e}")
            return []
    
    def mark_prediction_correct(self, prediction_id: int, correct: bool, notes: str = ""):
        """Marque une prédiction comme correcte/incorrecte"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE predictions 
                SET result_correct = ?, result_notes = ?
                WHERE id = ?
            ''', (1 if correct else 0, notes, prediction_id))
            self.connection.commit()
            logger.success(f"✓ Prediction marked as {'correct' if correct else 'incorrect'}")
        except Exception as e:
            logger.error(f"Error marking prediction: {e}")
    
    # ===== NOTIFICATIONS =====
    
    def insert_notification(self, notification_data: Dict) -> Optional[int]:
        """Insère une notification"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO notifications
                (match_id, prediction_id, notification_type, message, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                notification_data.get('match_id'),
                notification_data.get('prediction_id'),
                notification_data.get('type'),
                notification_data.get('message'),
                'sent'
            ))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting notification: {e}")
            return None
    
    # ===== STATISTICS =====
    
    def get_stats(self, days: int = 30) -> Dict:
        """Récupère les stats des derniers N jours"""
        try:
            cursor = self.connection.cursor()
            
            # Stats globales
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT m.id) as total_matches,
                    COUNT(p.id) as total_predictions,
                    SUM(CASE WHEN p.result_correct = 1 THEN 1 ELSE 0 END) as correct_predictions,
                    AVG(p.danger_score) as avg_danger_score
                FROM matches m
                LEFT JOIN predictions p ON m.id = p.match_id
                WHERE date(m.created_at) >= date('now', '-' || ? || ' days')
            ''', (days,))
            
            row = cursor.fetchone()
            
            if row:
                total = row[1] or 0
                correct = row[2] or 0
                accuracy = (correct / total * 100) if total > 0 else 0
                
                return {
                    'total_matches': row[0] or 0,
                    'total_predictions': total,
                    'correct_predictions': correct,
                    'accuracy': round(accuracy, 2),
                    'avg_danger_score': round(row[3] or 0, 2),
                    'period_days': days
                }
            
            return {}
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return {}
    
    def get_accuracy_by_interval(self) -> Dict:
        """Récupère la précision par intervalle"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT 
                    interval,
                    COUNT(*) as total,
                    SUM(CASE WHEN result_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(danger_score) as avg_danger
                FROM predictions
                WHERE result_correct IS NOT NULL
                GROUP BY interval
                ORDER BY interval
            ''')
            
            results = {}
            for row in cursor.fetchall():
                interval, total, correct, avg_danger = row
                accuracy = (correct / total * 100) if total > 0 else 0
                results[interval] = {
                    'total': total,
                    'correct': correct,
                    'accuracy': round(accuracy, 2),
                    'avg_danger': round(avg_danger or 0, 2)
                }
            
            return results
        except Exception as e:
            logger.error(f"Error fetching accuracy by interval: {e}")
            return {}
    
    # ===== MATCH HISTORY & GOALS (RECURRENCE) =====

    def insert_match_history(self, match_data: Dict) -> Optional[int]:
        """Insère un match historique"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO match_history
                (home_team, away_team, league, match_date, final_score, home_goals, away_goals)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data.get('home_team'),
                match_data.get('away_team'),
                match_data.get('league'),
                match_data.get('match_date'),
                match_data.get('final_score'),
                match_data.get('home_goals', 0),
                match_data.get('away_goals', 0)
            ))
            self.connection.commit()
            logger.success(f"✓ Historical match inserted: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.debug(f"Historical match already exists")
            return None
        except Exception as e:
            logger.error(f"Error inserting historical match: {e}")
            return None

    def insert_goal(self, match_id: int, goal_data: Dict) -> Optional[int]:
        """Insère un but avec minute exacte"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO goals
                (match_id, team, minute, player_name, is_own_goal)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                match_id,
                goal_data.get('team'),  # "home" ou "away"
                goal_data.get('minute'),
                goal_data.get('player_name'),
                goal_data.get('is_own_goal', 0)
            ))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting goal: {e}")
            return None

    def get_goals_for_match(self, match_id: int) -> List[Dict]:
        """Récupère tous les buts d'un match"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM goals WHERE match_id = ? ORDER BY minute
            ''', (match_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching goals: {e}")
            return []

    def upsert_goal_stats(self, stats_data: Dict) -> bool:
        """Insère ou met à jour les stats de but pour une équipe/venue/intervalle"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO goal_stats
                (team_name, venue, interval_name, total_matches, goals_scored, goals_conceded,
                 avg_minute, std_dev, min_minute, max_minute, recent_matches, recent_goals,
                 recent_avg_minute, recent_std_dev, minute_distribution, recent_minute_distribution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(team_name, venue, interval_name) DO UPDATE SET
                    total_matches = excluded.total_matches,
                    goals_scored = excluded.goals_scored,
                    goals_conceded = excluded.goals_conceded,
                    avg_minute = excluded.avg_minute,
                    std_dev = excluded.std_dev,
                    min_minute = excluded.min_minute,
                    max_minute = excluded.max_minute,
                    recent_matches = excluded.recent_matches,
                    recent_goals = excluded.recent_goals,
                    recent_avg_minute = excluded.recent_avg_minute,
                    recent_std_dev = excluded.recent_std_dev,
                    minute_distribution = excluded.minute_distribution,
                    recent_minute_distribution = excluded.recent_minute_distribution,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                stats_data.get('team_name'),
                stats_data.get('venue'),  # "home" ou "away"
                stats_data.get('interval_name'),  # "31-45", "75-90"
                stats_data.get('total_matches'),
                stats_data.get('goals_scored'),
                stats_data.get('goals_conceded'),
                stats_data.get('avg_minute'),
                stats_data.get('std_dev'),
                stats_data.get('min_minute'),
                stats_data.get('max_minute'),
                stats_data.get('recent_matches'),
                stats_data.get('recent_goals'),
                stats_data.get('recent_avg_minute'),
                stats_data.get('recent_std_dev'),
                stats_data.get('minute_distribution'),  # JSON string
                stats_data.get('recent_minute_distribution')  # JSON string
            ))
            self.connection.commit()
            logger.success(f"✓ Goal stats upserted: {stats_data.get('team_name')} ({stats_data.get('venue')}) {stats_data.get('interval_name')}")
            return True
        except Exception as e:
            logger.error(f"Error upserting goal stats: {e}")
            return False

    def get_goal_stats(self, team_name: str, venue: str, interval_name: str) -> Optional[Dict]:
        """Récupère les stats de but pour une équipe/venue/intervalle"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM goal_stats
                WHERE team_name = ? AND venue = ? AND interval_name = ?
            ''', (team_name, venue, interval_name))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching goal stats: {e}")
            return None

    def get_match_history(self, home_team: str = None, away_team: str = None, limit: int = 1000) -> List[Dict]:
        """Récupère l'historique des matchs (filtrable par équipe)"""
        try:
            cursor = self.connection.cursor()
            query = "SELECT * FROM match_history WHERE 1=1"
            params = []

            if home_team:
                query += " AND home_team = ?"
                params.append(home_team)
            if away_team:
                query += " AND away_team = ?"
                params.append(away_team)

            query += " ORDER BY match_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching match history: {e}")
            return []

    def close(self):
        """Ferme la connexion"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Database connection closed")


if __name__ == "__main__":
    # Test
    db = DatabaseManager()
    
    # Insérer un match de test
    match_data = {
        'home_team': 'Arsenal',
        'away_team': 'Manchester City',
        'league': 'england',
        'match_url': 'http://example.com'
    }
    
    match_id = db.insert_match(match_data)
    print(f"✅ Match inserted with ID: {match_id}")
    
    # Insérer une prédiction
    prediction_data = {
        'match_id': match_id,
        'minute': 65,
        'interval': '61-75',
        'danger_score': 4.5,
        'interpretation': 'ULTRA-DANGEREUX',
        'confidence': 'HAUTE'
    }
    
    pred_id = db.insert_prediction(prediction_data)
    print(f"✅ Prediction inserted with ID: {pred_id}")
    
    # Récupérer les stats
    stats = db.get_stats(7)
    print(f"📊 Stats: {stats}")
    
    db.close()
