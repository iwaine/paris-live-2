"""
Système de surveillance live des matchs
Scrape régulièrement les matchs et envoie des notifications
"""
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import json
import re
from loguru import logger

# Imports du projet
import sys
sys.path.insert(0, 'scrapers')
sys.path.insert(0, 'predictors')

from soccerstats_live import SoccerStatsLiveScraper
from interval_predictor import IntervalPredictor


class MatchMonitor:
    """Surveille un match live et envoie des notifications"""
    
    def __init__(
        self, 
        match_url: str,
        scraper: Optional[SoccerStatsLiveScraper] = None,
        predictor: Optional[IntervalPredictor] = None,
        interval: int = 30  # Scrape toutes les 30 secondes
    ):
        """
        Initialise le moniteur
        
        Args:
            match_url: URL du match live
            scraper: Scraper live (créé si None)
            predictor: Prédicteur (créé si None)
            interval: Intervalle de scraping en secondes
        """
        self.match_url = match_url
        self.scraper = scraper or SoccerStatsLiveScraper()
        self.predictor = predictor or IntervalPredictor()
        self.interval = interval
        
        # État du match
        self.previous_state = {}
        self.current_state = {}
        self.match_ended = False
        
        # Callbacks
        self.on_new_goal: Optional[Callable] = None
        self.on_danger_alert: Optional[Callable] = None
        self.on_update: Optional[Callable] = None
        self.on_match_start: Optional[Callable] = None
        self.on_match_end: Optional[Callable] = None
        
        logger.info(f"✅ MatchMonitor initialized for: {match_url}")
    
    def set_callbacks(self, **kwargs):
        """
        Enregistre les callbacks
        
        Args:
            on_new_goal: Appelé quand un but est marqué
            on_danger_alert: Appelé quand danger_score > seuil
            on_update: Appelé à chaque mise à jour
            on_match_start: Appelé au début du match
            on_match_end: Appelé à la fin du match
        """
        self.on_new_goal = kwargs.get('on_new_goal')
        self.on_danger_alert = kwargs.get('on_danger_alert')
        self.on_update = kwargs.get('on_update')
        self.on_match_start = kwargs.get('on_match_start')
        self.on_match_end = kwargs.get('on_match_end')
    
    def _detect_new_goal(self, old_score: str, new_score: str) -> Dict:
        """
        Détecte si un but a été marqué
        
        Args:
            old_score: Score précédent (ex: "1-1")
            new_score: Nouveau score (ex: "2-1")
            
        Returns:
            Dict avec info du but ou None
        """
        try:
            old_home, old_away = map(int, old_score.split('-'))
            new_home, new_away = map(int, new_score.split('-'))
            
            if new_home > old_home:
                return {
                    'team': 'home',
                    'scorer': self.current_state.get('home_team', 'N/A'),
                    'goal_time': self.current_state.get('current_minute', 'N/A')
                }
            elif new_away > old_away:
                return {
                    'team': 'away',
                    'scorer': self.current_state.get('away_team', 'N/A'),
                    'goal_time': self.current_state.get('current_minute', 'N/A')
                }
        except:
            pass
        
        return None

    def _normalize_live_stats(self, stats: Dict, match_data: Dict) -> Dict:
        """
        Normalise les statistiques extraites par le scraper vers la structure attendue
        par le prédicteur: {
            'score': '1-0',
            'red_cards': {'home': int, 'away': int},
            'penalties': {'home': int, 'away': int},
            'injuries': {'home': int, 'away': int},
            ... raw ...
        }
        """
        normalized = {}

        # Score
        normalized['score'] = match_data.get('score', '0-0')

        # Defaults
        normalized['red_cards'] = {'home': 0, 'away': 0}
        normalized['penalties'] = {'home': 0, 'away': 0}
        normalized['injuries'] = {'home': 0, 'away': 0}

        if not stats:
            return normalized

        # Heuristiques simples pour trouver les valeurs
        for k, v in stats.items():
            key = k.lower()
            try:
                # v expected {'home': str, 'away': str}
                home_val = v.get('home') if isinstance(v, dict) else None
                away_val = v.get('away') if isinstance(v, dict) else None
            except Exception:
                home_val = None
                away_val = None

            def to_int(x):
                if x is None:
                    return 0
                try:
                    # some values like '1' or '1 (45')'
                    num = int(re.findall(r"\d+", str(x))[0]) if re.findall(r"\d+", str(x)) else 0
                    return num
                except Exception:
                    return 0

            if 'red' in key and 'card' in key:
                normalized['red_cards']['home'] = to_int(home_val)
                normalized['red_cards']['away'] = to_int(away_val)
            elif 'penalt' in key:
                normalized['penalties']['home'] = to_int(home_val)
                normalized['penalties']['away'] = to_int(away_val)
            elif 'injur' in key:
                normalized['injuries']['home'] = to_int(home_val)
                normalized['injuries']['away'] = to_int(away_val)

        # always include raw stats for debugging
        normalized['raw'] = stats
        return normalized
    
    def monitor(self, max_duration: int = 5400):
        """
        Surveille le match en continu
        
        Args:
            max_duration: Durée max de surveillance en secondes (90 min par défaut)
        """
        start_time = time.time()
        logger.info(f"🔴 Starting match monitoring for max {max_duration}s...")
        
        try:
            while not self.match_ended:
                # Vérifier durée max
                if time.time() - start_time > max_duration:
                    logger.info("⏱️  Max duration reached, stopping monitoring")
                    self.match_ended = True
                    if self.on_match_end:
                        self.on_match_end(self.current_state)
                    break
                
                # Scraper les données
                match_data = self.scraper.scrape_live_match(self.match_url)
                
                if not match_data:
                    logger.warning("⚠️  Failed to scrape match data, retrying...")
                    time.sleep(self.interval)
                    continue

                # Normaliser et propager live_stats
                try:
                    stats = match_data.get('stats', {})
                    live_stats = self._normalize_live_stats(stats, match_data)
                    match_data['live_stats'] = live_stats
                except Exception:
                    match_data['live_stats'] = {'score': match_data.get('score', '0-0'),
                                                'red_cards': {'home': 0, 'away': 0},
                                                'penalties': {'home': 0, 'away': 0},
                                                'injuries': {'home': 0, 'away': 0}}

                self.current_state = match_data
                
                # Première donnée
                if not self.previous_state:
                    logger.info(f"🏟️  Match started: {match_data.get('home_team')} vs {match_data.get('away_team')}")
                    if self.on_match_start:
                        self.on_match_start(match_data)
                    self.previous_state = match_data.copy()
                    time.sleep(self.interval)
                    continue
                
                # Vérifier nouveau but
                old_score = self.previous_state.get('score', '0-0')
                new_score = match_data.get('score', '0-0')
                
                if old_score != new_score:
                    goal_info = self._detect_new_goal(old_score, new_score)
                    if goal_info and self.on_new_goal:
                        logger.success(f"⚽ Goal by {goal_info['scorer']} at {goal_info['goal_time']}'")
                        # Passer live_stats avec match_data
                        self.on_new_goal(match_data, goal_info)
                
                # Prédiction et alerte
                status = match_data.get('status', '')
                minute = match_data.get('current_minute')
                
                if status == 'Live' and minute:
                    # Propager les live_stats normalisées (si présentes)
                    prediction = self.predictor.predict_match(
                        home_team=match_data.get('home_team'),
                        away_team=match_data.get('away_team'),
                        current_minute=minute,
                        live_stats=match_data.get('live_stats', match_data.get('stats'))
                    )
                    
                    if prediction.get('success'):
                        danger_score = prediction.get('danger_score', 0)
                        
                        # Alerte si danger élevé
                        if danger_score >= 3.5 and self.on_danger_alert:
                            logger.warning(f"🔴 High danger score: {danger_score:.2f}")
                            self.on_danger_alert(prediction)
                
                # Appel callback de mise à jour
                if self.on_update:
                    self.on_update(match_data)
                
                # Vérifier fin du match
                if status in ['Full Time', 'Finished', 'Ended']:
                    logger.info(f"✅ Match ended: {match_data.get('score')}")
                    self.match_ended = True
                    if self.on_match_end:
                        self.on_match_end(match_data)
                    break
                
                # Mise à jour
                self.previous_state = match_data.copy()
                
                # Pause avant la prochaine vérification
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("⏹️  Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error during monitoring: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.scraper.cleanup()


class MultiMatchMonitor:
    """Surveille plusieurs matchs simultanément"""
    
    def __init__(self):
        """Initialise le moniteur multi-matchs"""
        self.monitors: Dict[str, MatchMonitor] = {}
        self.history = []
    
    def add_match(self, match_url: str, monitor: MatchMonitor):
        """Ajoute un match à surveiller"""
        self.monitors[match_url] = monitor
        logger.info(f"✅ Added match: {match_url}")
    
    def monitor_all(self, parallel: bool = False):
        """
        Surveille tous les matchs
        
        Args:
            parallel: Si True, utilise threading (non implémenté)
        """
        if not parallel:
            # Séquentiel
            for url, monitor in self.monitors.items():
                logger.info(f"🔴 Starting monitor for: {url}")
                monitor.monitor()
        else:
            # TODO: Implémenter avec threading
            logger.warning("Parallel monitoring not yet implemented")


def create_telegram_callbacks(notifier):
    """
    Crée les callbacks Telegram
    
    Args:
        notifier: Instance de TelegramNotifier
        
    Returns:
        Dict avec les callbacks
    """
    def on_new_goal(match_data, goal_info):
        # Passer match_data contenant live_stats pour que le notifier puisse afficher les événements
        notifier.send_goal_notification(match_data, goal_info['scorer'], goal_info['goal_time'])
    
    def on_danger_alert(prediction):
        # Envoyer la prédiction complète afin que TelegramNotifier puisse afficher les événements
        try:
            notifier.send_match_alert(prediction)
        except Exception:
            # Fallback minimal
            data = {
                'home_team': prediction['details'].get('home_team'),
                'away_team': prediction['details'].get('away_team'),
                'current_minute': prediction.get('current_minute'),
                'score': prediction.get('current_score'),
                'danger_score': prediction.get('danger_score'),
                'interpretation': prediction.get('interpretation')
            }
            notifier.send_match_alert(data)
    
    def on_update(match_data):
        logger.info(f"📊 Update: {match_data.get('home_team')} vs {match_data.get('away_team')} ({match_data.get('score')})")
    
    def on_match_start(match_data):
        # Notifier du début
        message = f"""
🏟️  <b>MATCH DÉMARRÉ</b>

<b>{match_data.get('home_team')}</b> vs <b>{match_data.get('away_team')}</b>
<b>Score:</b> {match_data.get('score')}

Surveillance en cours...
        """
        # notifier.send_message(message)  # À décommenter si async
    
    def on_match_end(match_data):
        message = f"""
✅ <b>MATCH TERMINÉ</b>

<b>{match_data.get('home_team')}</b> vs <b>{match_data.get('away_team')}</b>
<b>Score final:</b> {match_data.get('score')}
        """
        # notifier.send_message(message)  # À décommenter si async
    
    return {
        'on_new_goal': on_new_goal,
        'on_danger_alert': on_danger_alert,
        'on_update': on_update,
        'on_match_start': on_match_start,
        'on_match_end': on_match_end
    }


if __name__ == "__main__":
    # Test
    print("✅ Match monitor module loaded")
