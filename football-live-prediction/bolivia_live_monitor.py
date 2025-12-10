#!/usr/bin/env python3
"""
Moniteur live pour championnat bolivien (Division Profesional).
Détecte automatiquement les matches en cours et génère des prédictions.
COPIE EXACTE de la structure bulgare avec adaptations Bolivie.
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soccerstats_live_selector import get_live_matches
from soccerstats_live_scraper import SoccerStatsLiveScraper
from live_predictor_v2 import LivePredictorV2, LiveMatchContext

# Importer le notifier Telegram
try:
    sys.path.insert(0, '/workspaces/paris-live')
    from telegram_notifier import TelegramNotifier
    from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALERTS_ENABLED, ALERT_THRESHOLD_COMBINED, ALERT_THRESHOLD_SINGLE
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BoliviaLiveMonitor:
    """Moniteur live pour matches boliviens."""
    
    # Équipes boliviennes connues (Division Profesional)
    BOLIVIAN_TEAMS = {
        "Always Ready", "Blooming", "Bolivar", "G.V. San Jose",
        "Ind. Petrolero", "Nacional Potosi", "Oriente Petrolero",
        "Real Tomayapo", "Real Santa Cruz", "Royal Pari",
        "San Antonio", "The Strongest", "U. de Vinto",
        "Union Tarija", "Wilstermann", "Aurora"
    }
    
    # Intervalle de scan (secondes)
    SCAN_INTERVAL = 30
    
    # Intervalles critiques
    CRITICAL_INTERVALS = [(31, 45), (75, 90)]
    
    def __init__(self, db_path='data/predictions.db'):
        self.scraper = SoccerStatsLiveScraper(throttle_seconds=5)
        self.predictor = LivePredictorV2(db_path=db_path)
        self.monitored_matches = {}  # match_url -> last_alert_minute
        
        # Initialiser Telegram si disponible
        if TELEGRAM_AVAILABLE and ALERTS_ENABLED:
            self.telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            logger.info("✅ Alertes Telegram activées")
        else:
            self.telegram = None
            logger.info("ℹ️ Alertes Telegram désactivées")
    
    def is_bolivian_match(self, home_team: str, away_team: str) -> bool:
        """Vérifier si c'est un match bolivien."""
        # Normaliser noms (enlever espaces multiples, majuscules)
        home_norm = ' '.join(home_team.split()).strip()
        away_norm = ' '.join(away_team.split()).strip()
        
        # Vérification exacte ou par substring
        for team in self.BOLIVIAN_TEAMS:
            if team.lower() in home_norm.lower() or team.lower() in away_norm.lower():
                return True
        return False
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normaliser nom équipe pour correspondre à la DB."""
        team_norm = ' '.join(team_name.split()).strip()
        
        # Mapping manuel connu (soccerstats vs DB)
        mappings = {
            "the strongest": "The Strongest",
            "bolivar": "Bolivar",
            "always ready": "Always Ready",
            "blooming": "Blooming",
            "san jose": "G.V. San Jose",
            "gv san jose": "G.V. San Jose",
            "g.v. san jose": "G.V. San Jose",
            "ind petrolero": "Ind. Petrolero",
            "ind. petrolero": "Ind. Petrolero",
            "nacional potosi": "Nacional Potosi",
            "oriente petrolero": "Oriente Petrolero",
            "real tomayapo": "Real Tomayapo",
            "real santa cruz": "Real Santa Cruz",
            "royal pari": "Royal Pari",
            "san antonio": "San Antonio",
            "u de vinto": "U. de Vinto",
            "u. de vinto": "U. de Vinto",
            "union tarija": "Union Tarija",
            "wilstermann": "Wilstermann",
            "aurora": "Aurora"
        }
        
        # Recherche dans mapping
        norm_lower = team_norm.lower()
        if norm_lower in mappings:
            return mappings[norm_lower]
        
        # Correspondances exactes avec équipes connues
        for db_team in self.BOLIVIAN_TEAMS:
            if db_team.lower() == norm_lower:
                return db_team
            # Correspondance partielle
            if db_team.lower() in norm_lower or norm_lower in db_team.lower():
                if len(db_team) >= len(team_norm):
                    return db_team
        
        # Si aucune correspondance, retourner tel quel
        return team_norm
    
    def _should_send_telegram(self, analysis: Dict) -> bool:
        """Vérifier si on doit envoyer une alerte Telegram (seuils)."""
        predictions = analysis.get('predictions', {})
        combined = predictions.get('combined_active')
        home = predictions.get('home_active')
        away = predictions.get('away_active')
        
        if not combined:
            return False
        
        # Seuil global : combiné ≥ 85%
        if combined['probability'] >= ALERT_THRESHOLD_COMBINED:
            return True
        
        # Seuil individuel : au moins une équipe ≥ 75%
        if home and home['probability'] >= ALERT_THRESHOLD_SINGLE:
            return True
        if away and away['probability'] >= ALERT_THRESHOLD_SINGLE:
            return True
        
        return False
    
    def _send_telegram_alert(self, analysis: Dict):
        """Envoyer alerte Telegram formatée."""
        if not self.telegram:
            return
        
        try:
            context = analysis['context']
            predictions = analysis['predictions']
            combined = predictions['combined_active']
            home = predictions.get('home_active')
            away = predictions.get('away_active')
            
            # Message formaté
            message = f"🚨 <b>ALERTE BOLIVIE - Intervalle Critique Actif</b>\n\n"
            message += f"⚽ <b>{context['home_team']} vs {context['away_team']}</b>\n"
            message += f"🕐 Minute {context['current_minute']}' - Score {context['home_score']}-{context['away_score']}\n"
            message += f"📊 Intervalle: <b>{combined['interval_name']}</b>\n\n"
            
            message += f"🎯 <b>Probabilité Combinée: {combined['probability']*100:.1f}%</b>\n"
            if combined['probability'] >= 0.90:
                message += "🟢 SIGNAL TRÈS FORT\n\n"
            elif combined['probability'] >= 0.75:
                message += "🟡 SIGNAL FORT\n\n"
            else:
                message += "⚪ SIGNAL MODÉRÉ\n\n"
            
            if home:
                message += f"🏠 {context['home_team']}: {home['probability']*100:.1f}%"
                if home.get('avg_minute'):
                    message += f" (moy {home['avg_minute']:.0f}')"
                message += "\n"
            
            if away:
                message += f"✈️ {context['away_team']}: {away['probability']*100:.1f}%"
                if away.get('avg_minute'):
                    message += f" (moy {away['avg_minute']:.0f}')"
                message += "\n"
            
            self.telegram.send_message(message)
            logger.info("📤 Alerte Telegram envoyée")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi Telegram: {e}")
    
    def analyze_match(self, match_url: str, league_name: str = "bolivia") -> Optional[Dict]:
        """Analyser un match et générer prédictions."""
        try:
            # 1. Scraper stats live
            logger.info(f"\n{'='*80}")
            logger.info(f"🔍 Analyse match: {match_url}")
            
            match_data = self.scraper.scrape_match(match_url)
            
            if not match_data:
                logger.warning("❌ Impossible de scraper le match")
                return None
            
            home_team = match_data['home_team']
            away_team = match_data['away_team']
            
            # 2. Vérifier si match bolivien
            if not self.is_bolivian_match(home_team, away_team):
                logger.info(f"ℹ️ Match non-bolivien ignoré: {home_team} vs {away_team}")
                return None
            
            # 3. Normaliser noms équipes
            home_team_db = self.normalize_team_name(home_team)
            away_team_db = self.normalize_team_name(away_team)
            
            logger.info(f"⚽ {home_team_db} vs {away_team_db}")
            logger.info(f"🕐 Minute {match_data['minute']}' - Score {match_data['home_score']}-{match_data['away_score']}")
            
            # 4. Créer contexte de prédiction
            context = LiveMatchContext(
                home_team=home_team_db,
                away_team=away_team_db,
                current_minute=match_data['minute'],
                home_score=match_data['home_score'],
                away_score=match_data['away_score'],
                country="Bolivia",
                league=league_name,
                possession_home=match_data.get('possession_home'),
                possession_away=match_data.get('possession_away'),
                corners_home=match_data.get('corners_home'),
                corners_away=match_data.get('corners_away'),
                shots_home=match_data.get('shots_home'),
                shots_away=match_data.get('shots_away'),
                shots_on_target_home=match_data.get('shots_on_target_home'),
                shots_on_target_away=match_data.get('shots_on_target_away'),
                attacks_home=match_data.get('attacks_home'),
                attacks_away=match_data.get('attacks_away'),
                dangerous_attacks_home=match_data.get('dangerous_attacks_home'),
                dangerous_attacks_away=match_data.get('dangerous_attacks_away')
            )
            
            # 5. Détecter si intervalle critique actif
            is_critical = False
            for start, end in self.CRITICAL_INTERVALS:
                if start <= match_data['minute'] <= end:
                    is_critical = True
                    logger.info(f"🚨 INTERVALLE CRITIQUE {start}-{end} ACTIF!")
                    break
            
            # 6. Générer prédictions
            predictions = self.predictor.predict(context)
            
            # 7. Afficher résultats
            self._display_predictions(predictions, context, is_critical)
            
            # 8. Préparer analyse complète
            analysis = {
                'context': {
                    'home_team': home_team_db,
                    'away_team': away_team_db,
                    'current_minute': match_data['minute'],
                    'home_score': match_data['home_score'],
                    'away_score': match_data['away_score']
                },
                'predictions': {
                    'combined_active': next((p for p in predictions if p.is_active), None),
                    'home_active': None,
                    'away_active': None
                },
                'is_critical': is_critical,
                'match_url': match_url
            }
            
            # Extraire prédictions home/away actives
            # (Note: predictor retourne liste de PredictionResult, pas détails home/away séparés)
            # On utilise la prédiction combinée comme proxy
            
            # 9. Alertes Telegram si intervalle critique actif
            if is_critical and self.telegram and ALERTS_ENABLED:
                if self._should_send_telegram(analysis):
                    # Éviter spam : 1 alerte par minute
                    last_alert = self.monitored_matches.get(match_url, 0)
                    if match_data['minute'] - last_alert >= 1:
                        self._send_telegram_alert(analysis)
                        self.monitored_matches[match_url] = match_data['minute']
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse match: {e}", exc_info=True)
            return None
    
    def _display_predictions(self, predictions: List, context: LiveMatchContext, is_critical: bool):
        """Afficher prédictions formatées."""
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 PRÉDICTIONS - {context.home_team} vs {context.away_team}")
        logger.info(f"{'='*80}")
        
        for pred in predictions:
            status = "🚨 ACTIF" if pred.is_active else "⏳ Prochain"
            logger.info(f"\n{status} - Intervalle {pred.interval_name}")
            logger.info(f"  🎯 Probabilité: {pred.probability*100:.1f}%")
            logger.info(f"  📈 Confiance: {pred.confidence_level}")
            logger.info(f"  📊 Pattern: {pred.freq_any_goal*100:.1f}% ({pred.matches_with_goal}/{pred.total_matches} matches)")
            
            if pred.avg_minute:
                logger.info(f"  ⏰ Timing: {pred.avg_minute:.1f}' (±{pred.std_minute:.1f})")
            
            if pred.recurrence_last_5 is not None:
                logger.info(f"  🔄 Récurrence 5 derniers: {pred.recurrence_last_5*100:.0f}%")
        
        logger.info(f"\n{'='*80}")
    
    def scan_once(self):
        """Scanner une fois tous les matches live."""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 SCAN BOLIVIE - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'='*80}")
        
        # Récupérer matches live depuis soccerstats
        live_matches = get_live_matches()
        
        if not live_matches:
            logger.info("ℹ️ Aucun match live détecté")
            return
        
        logger.info(f"✅ {len(live_matches)} match(es) live détecté(s)")
        
        # Filtrer matches boliviens et analyser
        analyzed = 0
        for match in live_matches:
            # Vérifier si bolivien (par ligue ou équipes)
            if 'bolivia' in match.get('league', '').lower():
                self.analyze_match(match['url'], league_name='bolivia')
                analyzed += 1
                time.sleep(2)  # Pause entre matches
        
        if analyzed == 0:
            logger.info("ℹ️ Aucun match bolivien en cours")
    
    def run_continuous(self, interval_seconds: int = None):
        """Exécuter monitoring en continu."""
        if interval_seconds is None:
            interval_seconds = self.SCAN_INTERVAL
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 MONITORING BOLIVIE - MODE CONTINU")
        logger.info(f"{'='*80}")
        logger.info(f"⏱️ Intervalle de scan: {interval_seconds}s")
        logger.info(f"🔴 Intervalles critiques: {self.CRITICAL_INTERVALS}")
        if self.telegram:
            logger.info(f"📱 Alertes Telegram: ACTIVÉES")
        logger.info(f"{'='*80}\n")
        
        try:
            while True:
                self.scan_once()
                logger.info(f"\n⏸️ Pause {interval_seconds}s jusqu'au prochain scan...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n\n⏹️ Monitoring arrêté par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur monitoring: {e}", exc_info=True)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Moniteur live Bolivie')
    parser.add_argument('--once', action='store_true', help='Scan unique au lieu de continu')
    parser.add_argument('--interval', type=int, default=30, help='Intervalle de scan (secondes)')
    parser.add_argument('--db', default='data/predictions.db', help='Chemin vers la DB')
    
    args = parser.parse_args()
    
    monitor = BoliviaLiveMonitor(db_path=args.db)
    
    if args.once:
        monitor.scan_once()
    else:
        monitor.run_continuous(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
