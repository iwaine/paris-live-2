#!/usr/bin/env python3
"""
Build critical interval recurrence statistics.
Focus on end-of-half periods where goals are most likely:
- Interval 1: 31-45' + added time (up to 45+5)
- Interval 2: 76-90' + added time (up to 90+10)

For each team + home/away context:
- Goals scored in interval
- Goals conceded in interval
- Frequency (goals per match)
- Average minute of goals
"""

import sqlite3
import logging
from collections import defaultdict
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CriticalIntervalRecurrence:
    """Build recurrence stats for critical end-of-half intervals."""
    
    INTERVAL_1 = (31, 45)  # 31-45' (bornes incluses)
    INTERVAL_2 = (75, 90)  # 75-90' (bornes incluses)
    
    def __init__(self, db_path='data/predictions.db', country=None, league=None):
        self.db_path = db_path
        self.country = country
        self.league = league
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def _parse_goal_times(self, goal_times_str):
        """Parse goal times from string format 'min1,min2,min3' or JSON '[min1,min2,min3]'
        
        IMPORTANT: Filtre les zéros (padding) pour obtenir seulement les buts réels.
        Exemple: '[12, 0, 0, 0, 0, 0, 0, 0, 0, 0]' → [12] (1 seul but)
        """
        if not goal_times_str:
            return []
        try:
            # Supporter format JSON "[13,24,50]"
            if goal_times_str.startswith('['):
                import json
                times = json.loads(goal_times_str)
                # Filtrer les zéros (padding)
                return [t for t in times if t > 0]
            # Supporter format CSV "13,24,50"
            return [int(x.strip()) for x in goal_times_str.split(',') if x.strip() and int(x.strip()) > 0]
        except (ValueError, AttributeError, json.JSONDecodeError):
            return []
    
    def _in_interval(self, minute, interval):
        """Check if minute is in interval (min, max)"""
        return interval[0] <= minute <= interval[1]
    
    def _calculate_goal_averages(self, team_name, is_home):
        """Calculate average goals per match (full + halves) for a team.
        
        Returns:
            tuple: (avg_full_match, avg_first_half, avg_second_half)
        """
        query = '''
            SELECT goals_for, goals_against
            FROM soccerstats_scraped_matches
            WHERE team = ? AND is_home = ?
        '''
        
        self.cursor.execute(query, (team_name, is_home))
        matches = self.cursor.fetchall()
        
        if not matches:
            return 0.0, 0.0, 0.0
        
        total_goals_full = []
        
        for goals_for, goals_against in matches:
            # Total match (marqués + encaissés)
            total_goals_full.append((goals_for or 0) + (goals_against or 0))
        
        # Pour calculer moyennes par mi-temps, on doit utiliser goal_times
        query2 = '''
            SELECT goal_times, goal_times_conceded
            FROM soccerstats_scraped_matches
            WHERE team = ? AND is_home = ?
        '''
        
        self.cursor.execute(query2, (team_name, is_home))
        matches_times = self.cursor.fetchall()
        
        total_goals_first_half = []
        total_goals_second_half = []
        
        for goal_times_str, goal_times_conceded_str in matches_times:
            scored = self._parse_goal_times(goal_times_str)
            conceded = self._parse_goal_times(goal_times_conceded_str)
            
            # 1ère mi-temps (0-45)
            scored_first = [g for g in scored if 0 <= g <= 45]
            conceded_first = [g for g in conceded if 0 <= g <= 45]
            total_goals_first_half.append(len(scored_first) + len(conceded_first))
            
            # 2nde mi-temps (46-90)
            scored_second = [g for g in scored if 46 <= g <= 90]
            conceded_second = [g for g in conceded if 46 <= g <= 90]
            total_goals_second_half.append(len(scored_second) + len(conceded_second))
        
        # Calculer moyennes
        avg_full = sum(total_goals_full) / len(total_goals_full) if total_goals_full else 0.0
        avg_first = sum(total_goals_first_half) / len(total_goals_first_half) if total_goals_first_half else 0.0
        avg_second = sum(total_goals_second_half) / len(total_goals_second_half) if total_goals_second_half else 0.0
        
        return avg_full, avg_first, avg_second
    
    def _create_table(self):
        """Create team_critical_intervals table (if not exists)."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_critical_intervals (
                id INTEGER PRIMARY KEY,
                country TEXT NOT NULL,
                league TEXT NOT NULL,
                team_name TEXT NOT NULL,
                is_home INTEGER NOT NULL,
                interval_name TEXT NOT NULL,
                
                -- Buts marqués
                goals_scored INTEGER,
                matches_with_goals_scored INTEGER,
                freq_goals_scored REAL,
                avg_minute_scored REAL,
                std_minute_scored REAL,
                
                -- Buts encaissés
                goals_conceded INTEGER,
                matches_with_goals_conceded INTEGER,
                freq_goals_conceded REAL,
                avg_minute_conceded REAL,
                std_minute_conceded REAL,
                
                -- ANY GOAL (marqué OU encaissé)
                any_goal_total INTEGER,
                matches_with_any_goal INTEGER,
                freq_any_goal REAL,
                
                -- Récurrence et confiance
                recurrence_last_5 REAL,
                confidence_level TEXT,
                
                -- Moyennes de buts (saturation)
                avg_goals_full_match REAL,      -- Moyenne buts total (marqués + encaissés)
                avg_goals_first_half REAL,       -- Moyenne buts 1ère mi-temps (0-45)
                avg_goals_second_half REAL,      -- Moyenne buts 2nde mi-temps (46-90)
                
                -- Contexte
                total_matches INTEGER,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(country, league, team_name, is_home, interval_name)
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ team_critical_intervals table ready")
    
    def _extract_goals_by_interval(self):
        """Extract goals scored and conceded for each team in critical intervals."""
        
        # Structure: {(team, is_home, interval_name): {scored: [minutes], conceded: [minutes], matches: set()}}
        # Utiliser match_id pour déduplication automatique (au lieu de id)
        team_data = defaultdict(lambda: {
            'scored_minutes': [],
            'conceded_minutes': [],
            'any_goal_minutes': [],  # Marqués OU encaissés
            'matches_scored': set(),
            'matches_conceded': set(),
            'matches_any_goal': set(),  # Match avec AU MOINS 1 but (marqué ou encaissé)
            'total_matches': set(),
            'matches_chronological': []  # Liste de (date, has_any_goal) pour calcul récurrence récente
        })
        
        # Récupérer tous les matchs (filtrer par country/league si spécifié)
        query = '''
            SELECT 
                id,
                country,
                league,
                team,
                opponent,
                is_home,
                goal_times,
                goal_times_conceded,
                goals_for,
                goals_against,
                match_id,
                date
            FROM soccerstats_scraped_matches
        '''
        params = []
        if self.country and self.league:
            query += ' WHERE country = ? AND league = ?'
            params = [self.country, self.league]
        
        query += ' ORDER BY date DESC'  # Trier par date pour récurrence récente
        
        self.cursor.execute(query, params)
        
        matches = self.cursor.fetchall()
        filter_str = f" ({self.country} / {self.league})" if self.country and self.league else ""
        logger.info(f"Processing {len(matches)} matches{filter_str}...")
        
        for match_id, country, league, team, opponent, is_home, goal_times_str, goal_times_conceded_str, goals_for, goals_against, match_unique_id, date in matches:
            # Buts marqués par l'équipe
            goals_scored = self._parse_goal_times(goal_times_str)
            
            # Buts encaissés (directement depuis goal_times_conceded)
            goals_conceded = self._parse_goal_times(goal_times_conceded_str)
            
            # Traiter les 2 intervalles
            for interval, interval_name in [(self.INTERVAL_1, '31-45+'), (self.INTERVAL_2, '75-90+')]:
                key = (country, league, team, is_home, interval_name)
                
                # Ajouter ce match au total (utiliser match_unique_id pour déduplication)
                team_data[key]['total_matches'].add(match_unique_id)
                
                # Buts marqués dans l'intervalle
                scored_in_interval = [m for m in goals_scored if self._in_interval(m, interval)]
                if scored_in_interval:
                    team_data[key]['scored_minutes'].extend(scored_in_interval)
                    team_data[key]['matches_scored'].add(match_unique_id)
                
                # Buts encaissés dans l'intervalle
                conceded_in_interval = [m for m in goals_conceded if self._in_interval(m, interval)]
                if conceded_in_interval:
                    team_data[key]['conceded_minutes'].extend(conceded_in_interval)
                    team_data[key]['matches_conceded'].add(match_unique_id)
                
                # ANY GOAL (marqué OU encaissé) dans l'intervalle
                any_goal_in_interval = scored_in_interval + conceded_in_interval
                has_any_goal = len(any_goal_in_interval) > 0
                
                if any_goal_in_interval:
                    team_data[key]['any_goal_minutes'].extend(any_goal_in_interval)
                    team_data[key]['matches_any_goal'].add(match_unique_id)
                
                # Enregistrer chronologiquement (date, has_goal) pour calcul récurrence récente
                team_data[key]['matches_chronological'].append((date, has_any_goal))
        
        return team_data
    
    def _calc_stats(self, minutes):
        """Calculate mean and std for list of minutes."""
        if not minutes:
            return None, None
        arr = np.array(minutes)
        return float(np.mean(arr)), float(np.std(arr))
    
    def _calculate_confidence(self, freq_any_goal, total_matches, recurrence_last_5):
        """
        Calcule le niveau de confiance basé sur :
        - Fréquence globale (freq_any_goal)
        - Nombre de matches (fiabilité statistique)
        - Récurrence sur les 5 derniers matches
        
        Niveaux :
        - EXCELLENT : freq ≥ 0.65 ET total ≥ 8 ET récurrence_5 ≥ 0.6
        - TRES_BON : freq ≥ 0.55 ET total ≥ 6 ET récurrence_5 ≥ 0.4
        - BON : freq ≥ 0.45 ET total ≥ 5
        - MOYEN : freq ≥ 0.35
        - FAIBLE : freq < 0.35
        """
        if total_matches < 3:
            return "INSUFFICIENT_DATA"
        
        # Pas de données récentes = on baisse le niveau
        if recurrence_last_5 is None:
            if freq_any_goal >= 0.60 and total_matches >= 8:
                return "BON"
            elif freq_any_goal >= 0.50:
                return "MOYEN"
            else:
                return "FAIBLE"
        
        # Avec récurrence récente
        if freq_any_goal >= 0.65 and total_matches >= 8 and recurrence_last_5 >= 0.6:
            return "EXCELLENT"
        elif freq_any_goal >= 0.55 and total_matches >= 6 and recurrence_last_5 >= 0.4:
            return "TRES_BON"
        elif freq_any_goal >= 0.45 and total_matches >= 5:
            return "BON"
        elif freq_any_goal >= 0.35:
            return "MOYEN"
        else:
            return "FAIBLE"
    
    def build_stats(self):
        """Build complete critical interval statistics."""
        logger.info("\n" + "="*80)
        logger.info("🔄 BUILDING CRITICAL INTERVAL RECURRENCE")
        logger.info("="*80)
        logger.info("Intervals: 31-45min, 75-90min (bornes incluses)")
        logger.info("Metrics: Goals scored/conceded, frequencies, avg minutes")
        
        self._create_table()
        
        team_data = self._extract_goals_by_interval()
        
        logger.info(f"Found {len(team_data)} team-context-interval combinations")
        
        # Insert statistics
        inserted = 0
        for (country, league, team, is_home, interval_name), data in team_data.items():
            # Buts marqués
            goals_scored = len(data['scored_minutes'])
            matches_scored = len(data['matches_scored'])
            avg_scored, std_scored = self._calc_stats(data['scored_minutes'])
            
            # Buts encaissés
            goals_conceded = len(data['conceded_minutes'])
            matches_conceded = len(data['matches_conceded'])
            avg_conceded, std_conceded = self._calc_stats(data['conceded_minutes'])
            
            # ANY GOAL (marqué OU encaissé)
            any_goal_total = len(data['any_goal_minutes'])
            matches_any_goal = len(data['matches_any_goal'])
            
            # Total matchs
            total_matches = len(data['total_matches'])
            
            # Fréquences
            freq_scored = goals_scored / total_matches if total_matches > 0 else 0
            freq_conceded = goals_conceded / total_matches if total_matches > 0 else 0
            freq_any_goal = matches_any_goal / total_matches if total_matches > 0 else 0
            
            # RÉCURRENCE SUR LES 5 DERNIERS MATCHES
            last_5_matches = data['matches_chronological'][:5]  # Déjà triés par date DESC
            if len(last_5_matches) >= 5:
                goals_in_last_5 = sum(1 for _, has_goal in last_5_matches if has_goal)
                recurrence_last_5 = goals_in_last_5 / 5.0
            else:
                recurrence_last_5 = None  # Pas assez de données
            
            # NIVEAU DE CONFIANCE
            confidence = self._calculate_confidence(freq_any_goal, total_matches, recurrence_last_5)
            
            # MOYENNES DE BUTS (pour saturation)
            avg_full, avg_first, avg_second = self._calculate_goal_averages(team, is_home)
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO team_critical_intervals
                (country, league, team_name, is_home, interval_name,
                 goals_scored, matches_with_goals_scored, freq_goals_scored, 
                 avg_minute_scored, std_minute_scored,
                 goals_conceded, matches_with_goals_conceded, freq_goals_conceded,
                 avg_minute_conceded, std_minute_conceded,
                 any_goal_total, matches_with_any_goal, freq_any_goal,
                 recurrence_last_5, confidence_level,
                 avg_goals_full_match, avg_goals_first_half, avg_goals_second_half,
                 total_matches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                country, league, team, is_home, interval_name,
                goals_scored, matches_scored, freq_scored, avg_scored, std_scored,
                goals_conceded, matches_conceded, freq_conceded, avg_conceded, std_conceded,
                any_goal_total, matches_any_goal, freq_any_goal,
                recurrence_last_5, confidence,
                avg_full, avg_first, avg_second,
                total_matches
            ))
            
            inserted += 1
        
        self.conn.commit()
        logger.info(f"✅ Inserted {inserted} recurrence records")
        
        # Warn about low-quality recurrence (few matches with goals)
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM team_critical_intervals 
            WHERE matches_with_goals_scored < 3 AND goals_scored > 0
        ''')
        low_quality = self.cursor.fetchone()[0]
        
        if low_quality > 0:
            logger.warning(f"⚠️  {low_quality} records have <3 matches with goals (weak recurrence pattern)")
        
        self._print_summary()
    
    def _print_summary(self):
        """Print summary statistics."""
        logger.info("\n" + "="*80)
        logger.info("📊 RECURRENCE QUALITY CHECK")
        logger.info("="*80)
        
        # Valid recurrence (≥3 matches with goals)
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM team_critical_intervals 
            WHERE matches_with_goals_scored >= 3
        ''')
        valid_recurrence = self.cursor.fetchone()[0]
        
        # Weak recurrence (<3 matches with goals)
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM team_critical_intervals 
            WHERE matches_with_goals_scored > 0 AND matches_with_goals_scored < 3
        ''')
        weak_recurrence = self.cursor.fetchone()[0]
        
        logger.info(f"✅ Valid recurrence patterns: {valid_recurrence} (≥3 matches with goals)")
        logger.info(f"⚠️  Weak patterns: {weak_recurrence} (<3 matches with goals)")
        
        logger.info("\n" + "="*80)
        logger.info("📊 TOP TEAMS - GOALS SCORED IN CRITICAL INTERVALS (VALID RECURRENCE)")
        logger.info("="*80)
        
        self.cursor.execute('''
            SELECT 
                team_name,
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as loc,
                interval_name,
                goals_scored,
                matches_with_goals_scored,
                ROUND(freq_goals_scored, 2) as freq,
                ROUND(avg_minute_scored, 1) as avg_min,
                ROUND(std_minute_scored, 1) as std_min,
                total_matches
            FROM team_critical_intervals
            WHERE goals_scored > 0 AND matches_with_goals_scored >= 3
            ORDER BY goals_scored DESC
            LIMIT 15
        ''')
        
        rows = self.cursor.fetchall()
        logger.info("\n{:<18} {:<6} {:<10} {:<7} {:<9} {:<7} {:<10} {:<10} {:<8}".format(
            "Team", "Loc", "Interval", "Goals", "Matches+", "Freq", "Avg Min", "Std", "Total"
        ))
        logger.info("-" * 90)
        
        for row in rows:
            logger.info("{:<18} {:<6} {:<10} {:<7} {:<9} {:<7} {:<10} {:<10} {:<8}".format(
                row[0][:17], row[1], row[2], row[3], row[4], row[5], row[6] or 0, row[7] or 0, row[8]
            ))
        
        logger.info("\n" + "="*80)
        logger.info("📊 TOP TEAMS - GOALS CONCEDED IN CRITICAL INTERVALS")
        logger.info("="*80)
        
        self.cursor.execute('''
            SELECT 
                team_name,
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as loc,
                interval_name,
                goals_conceded,
                ROUND(freq_goals_conceded, 2) as freq,
                ROUND(avg_minute_conceded, 1) as avg_min,
                ROUND(std_minute_conceded, 1) as std_min,
                total_matches
            FROM team_critical_intervals
            WHERE goals_conceded > 0
            ORDER BY goals_conceded DESC
            LIMIT 15
        ''')
        
        rows = self.cursor.fetchall()
        logger.info("\n{:<18} {:<6} {:<10} {:<7} {:<7} {:<10} {:<10} {:<8}".format(
            "Team", "Loc", "Interval", "Goals", "Freq", "Avg Min", "Std", "Matches"
        ))
        logger.info("-" * 80)
        
        for row in rows:
            logger.info("{:<18} {:<6} {:<10} {:<7} {:<7} {:<10} {:<10} {:<8}".format(
                row[0][:17], row[1], row[2], row[3], row[4], row[5] or 0, row[6] or 0, row[7]
            ))
        
        # Exemples d'équipes
        logger.info("\n" + "="*80)
        logger.info("🔍 SAMPLE: ANGERS")
        logger.info("="*80)
        
        self.cursor.execute('''
            SELECT 
                CASE WHEN is_home=1 THEN 'HOME' ELSE 'AWAY' END as loc,
                interval_name,
                goals_scored,
                ROUND(freq_goals_scored, 3) as freq_sc,
                ROUND(avg_minute_scored, 1) as avg_sc,
                goals_conceded,
                ROUND(freq_goals_conceded, 3) as freq_co,
                ROUND(avg_minute_conceded, 1) as avg_co,
                total_matches
            FROM team_critical_intervals
            WHERE team_name = 'Angers'
            ORDER BY is_home DESC, interval_name
        ''')
        
        rows = self.cursor.fetchall()
        for row in rows:
            loc, interval, sc, freq_sc, avg_sc, co, freq_co, avg_co, matches = row
            logger.info(f"\n{loc} - {interval}' ({matches} matches):")
            logger.info(f"  Scored:   {sc} goals (freq={freq_sc:.3f}, avg={avg_sc:.1f} min)")
            logger.info(f"  Conceded: {co} goals (freq={freq_co:.3f}, avg={avg_co:.1f} min)")

def main():
    """Main entry point."""
    builder = CriticalIntervalRecurrence()
    
    try:
        builder.build_stats()
        logger.info("\n" + "="*80)
        logger.info("✅ Critical interval recurrence successfully built!")
        logger.info("Table: team_critical_intervals")
        logger.info("="*80)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        builder.close()

if __name__ == "__main__":
    main()
