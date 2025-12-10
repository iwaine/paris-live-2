#!/usr/bin/env python3
"""
Moniteur live pour championnat néerlandais (Eerste Divisie).
Détecte automatiquement les matches en cours et génère des prédictions.
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
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class NetherlandsLiveMonitor:
    """Moniteur live pour matches néerlandais (Eerste Divisie)."""
    
    # Équipes néerlandaises connues (Eerste Divisie)
    DUTCH_TEAMS = {
        "ADO Den Haag", "Almere City", "Cambuur", "De Graafschap",
        "FC Den Bosch", "FC Dordrecht", "FC Eindhoven", "FC Emmen",
        "Helmond Sport", "Jong AZ", "Jong Ajax", "Jong PSV",
        "Jong Utrecht", "MVV Maastricht", "RKC Waalwijk", "Roda JC",
        "TOP Oss", "VVV", "Vitesse Arnhem", "Willem II"
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
    
    def is_dutch_match(self, home_team: str, away_team: str) -> bool:
        """Vérifier si c'est un match néerlandais."""
        # Normaliser noms (enlever espaces multiples, majuscules)
        home_norm = ' '.join(home_team.split()).strip()
        away_norm = ' '.join(away_team.split()).strip()
        
        # Vérification exacte ou par substring
        for team in self.DUTCH_TEAMS:
            if team.lower() in home_norm.lower() or team.lower() in away_norm.lower():
                return True
        return False
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normaliser nom équipe pour correspondre à la DB."""
        team_norm = ' '.join(team_name.split()).strip()
        
        # Correspondances exactes
        for db_team in self.DUTCH_TEAMS:
            if db_team.lower() == team_norm.lower():
                return db_team
            # Correspondance partielle (ex: "Vitesse" -> "Vitesse Arnhem")
            if db_team.lower() in team_norm.lower() or team_norm.lower() in db_team.lower():
                # Préférer le nom complet de la DB
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
        
        # Vérifier seuil combiné
        if combined['probability'] >= ALERT_THRESHOLD_COMBINED:
            return True
        
        # Vérifier seuil individuel
        if home and home.probability >= ALERT_THRESHOLD_SINGLE:
            return True
        if away and away.probability >= ALERT_THRESHOLD_SINGLE:
            return True
        
        return False
    
    def is_in_critical_interval(self, minute: int) -> bool:
        """Vérifier si on est dans un intervalle critique."""
        if minute is None:
            return False
        for start, end in self.CRITICAL_INTERVALS:
            if start <= minute <= end:
                return True
        return False
    
    def get_next_critical_minute(self, minute: int) -> Optional[int]:
        """Obtenir la prochaine minute critique."""
        if minute is None:
            return 31
        if minute < 31:
            return 31
        elif minute < 75:
            return 75
        return None
    
    def should_alert(self, match_url: str, minute: int) -> bool:
        """Décider si on doit alerter pour ce match."""
        if not self.is_in_critical_interval(minute):
            return False
        
        # Première fois qu'on voit ce match
        if match_url not in self.monitored_matches:
            self.monitored_matches[match_url] = minute
            return True
        
        # Déjà alerté pour cet intervalle ?
        last_alert = self.monitored_matches[match_url]
        
        # Si on est dans 31-45 et qu'on a alerté avant 31, ne pas re-alerter
        if 31 <= minute <= 45 and last_alert >= 31 and last_alert <= 45:
            return False
        
        # Si on est dans 75-90 et qu'on a alerté avant 75, ne pas re-alerter
        if 75 <= minute <= 90 and last_alert >= 75 and last_alert <= 90:
            return False
        
        # Nouvel intervalle critique
        self.monitored_matches[match_url] = minute
        return True
    
    def analyze_match(self, match_info: Dict) -> Optional[Dict]:
        """Analyser un match et générer prédiction."""
        url = match_info.get('url')
        if not url:
            return None
        
        logger.info(f"🔍 Analyse match: {url}")
        
        # Scraper détails du match
        soup = self.scraper.fetch_match_page(url)
        if not soup:
            logger.warning(f"⚠️ Impossible de récupérer {url}")
            return None
        
        # Extraire données
        match_data = self.scraper.scrape_match(url)
        if not match_data:
            logger.warning(f"⚠️ Impossible de parser {url}")
            return None
        
        home_team = match_data.home_team
        away_team = match_data.away_team
        minute = match_data.minute
        
        # Vérifier si néerlandais
        if not self.is_dutch_match(home_team, away_team):
            logger.info(f"⏭️ Match non néerlandais: {home_team} vs {away_team}")
            return None
        
        logger.info(f"🇳🇱 Match néerlandais détecté: {home_team} vs {away_team} | Minute {minute}")
        
        # Normaliser noms équipes
        home_norm = self.normalize_team_name(home_team)
        away_norm = self.normalize_team_name(away_team)
        
        # Créer contexte
        context = LiveMatchContext(
            home_team=home_norm,
            away_team=away_norm,
            current_minute=minute or 0,
            home_score=match_data.score_home or 0,
            away_score=match_data.score_away or 0,
            country="Netherlands",
            league="netherlands2",
            possession_home=match_data.possession_home,
            possession_away=match_data.possession_away,
            corners_home=match_data.corners_home,
            corners_away=match_data.corners_away,
            shots_home=match_data.shots_home,
            shots_away=match_data.shots_away,
            shots_on_target_home=match_data.shots_on_target_home,
            shots_on_target_away=match_data.shots_on_target_away,
            shots_inside_box_home=match_data.shots_inside_box_home,
            shots_inside_box_away=match_data.shots_inside_box_away,
            shots_outside_box_home=match_data.shots_outside_box_home,
            shots_outside_box_away=match_data.shots_outside_box_away,
            attacks_home=match_data.attacks_home,
            attacks_away=match_data.attacks_away,
            dangerous_attacks_home=match_data.dangerous_attacks_home,
            dangerous_attacks_away=match_data.dangerous_attacks_away
        )
        
        # Générer prédictions
        predictions = self.predictor.predict(context)
        
        return {
            'url': url,
            'context': context,
            'predictions': predictions,
            'match_data': match_data
        }
    
    def format_alert(self, analysis: Dict) -> str:
        """Formater alerte pour affichage."""
        context = analysis['context']
        predictions = analysis['predictions']
        match_data = analysis['match_data']
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"🚨 ALERTE MATCH NÉERLANDAIS - INTERVALLE CRITIQUE")
        lines.append("=" * 80)
        lines.append(f"🏟️  {context.home_team} vs {context.away_team}")
        lines.append(f"⏱️  Minute {context.current_minute} | Score: {context.home_score}-{context.away_score}")
        lines.append("")
        
        # Intervalle actif
        if 'home_active' in predictions:
            home_pred = predictions['home_active']
            away_pred = predictions['away_active']
            combined = predictions['combined_active']
            
            lines.append(f"⚡ INTERVALLE ACTIF: {home_pred.interval_name}")
            lines.append("")
            lines.append(f"  {context.home_team} (HOME):")
            lines.append(f"    📊 Probabilité: {home_pred.probability*100:.1f}%")
            lines.append(f"    🎯 Confiance: {home_pred.confidence_level}")
            lines.append(f"    📈 Historique: {home_pred.matches_with_goal}/{home_pred.total_matches} matches ({home_pred.freq_any_goal*100:.0f}%)")
            if home_pred.recurrence_last_5:
                lines.append(f"    🔄 Récurrence 5 derniers: {home_pred.recurrence_last_5*100:.0f}%")
            lines.append(f"    ⚽ Détails: {home_pred.goals_scored} marqués, {home_pred.goals_conceded} encaissés")
            lines.append("")
            lines.append(f"  {context.away_team} (AWAY):")
            lines.append(f"    📊 Probabilité: {away_pred.probability*100:.1f}%")
            lines.append(f"    🎯 Confiance: {away_pred.confidence_level}")
            lines.append(f"    📈 Historique: {away_pred.matches_with_goal}/{away_pred.total_matches} matches ({away_pred.freq_any_goal*100:.0f}%)")
            if away_pred.recurrence_last_5:
                lines.append(f"    🔄 Récurrence 5 derniers: {away_pred.recurrence_last_5*100:.0f}%")
            lines.append(f"    ⚽ Détails: {away_pred.goals_scored} marqués, {away_pred.goals_conceded} encaissés")
            lines.append("")
            lines.append(f"  🎯 PROBABILITÉ COMBINÉE: {combined['probability']*100:.1f}%")
            lines.append(f"     (Au moins 1 but marqué par l'une des 2 équipes)")
            
            # Recommandation
            if combined['probability'] >= 0.80:
                lines.append("")
                lines.append("  ✅ SIGNAL FORT: Très forte probabilité de but!")
            elif combined['probability'] >= 0.65:
                lines.append("")
                lines.append("  ⚠️ SIGNAL MOYEN: Probabilité significative")
        
        # Prochain intervalle
        if 'home_next' in predictions:
            home_next = predictions['home_next']
            away_next = predictions['away_next']
            combined_next = predictions['combined_next']
            
            lines.append("")
            lines.append(f"📅 PROCHAIN INTERVALLE: {home_next.interval_name}")
            lines.append(f"   {context.home_team}: {home_next.probability*100:.1f}% ({home_next.confidence_level})")
            lines.append(f"   {context.away_team}: {away_next.probability*100:.1f}% ({away_next.confidence_level})")
            lines.append(f"   Combiné: {combined_next['probability']*100:.1f}%")
        
        lines.append("")
        lines.append(f"🔗 URL: {analysis['url']}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def scan_once(self) -> List[Dict]:
        """Scanner une fois tous les matches live."""
        logger.info("🔍 Scan des matches live...")
        
        try:
            live_matches = get_live_matches()
            logger.info(f"📊 {len(live_matches)} matches live détectés")
            
            alerts = []
            
            for match in live_matches:
                try:
                    # Analyser le match
                    analysis = self.analyze_match(match)
                    if not analysis:
                        continue
                    
                    # Vérifier si on doit alerter
                    minute = analysis['context'].current_minute
                    if self.should_alert(match['url'], minute):
                        alert_text = self.format_alert(analysis)
                        print("\n" + alert_text + "\n")
                        
                        # Envoyer alerte Telegram si activé et seuils atteints
                        if self.telegram and self._should_send_telegram(analysis):
                            logger.info("📱 Envoi alerte Telegram...")
                            self.telegram.send_alert(analysis, championship="Pays-Bas")
                        
                        alerts.append(analysis)
                    else:
                        logger.info(f"⏭️ Match déjà alerté: {analysis['context'].home_team} vs {analysis['context'].away_team}")
                
                except Exception as e:
                    logger.error(f"❌ Erreur analyse match {match.get('url')}: {e}")
                    continue
            
            return alerts
        
        except Exception as e:
            logger.error(f"❌ Erreur scan: {e}")
            return []
    
    def monitor_continuous(self, duration_minutes: Optional[int] = None):
        """
        Monitorer en continu.
        
        Args:
            duration_minutes: Durée max (None = infini)
        """
        logger.info("🚀 Démarrage moniteur live Pays-Bas")
        logger.info(f"📡 Scan toutes les {self.SCAN_INTERVAL} secondes")
        
        start_time = time.time()
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"📡 SCAN #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                self.scan_once()
                
                # Vérifier durée
                if duration_minutes:
                    elapsed = (time.time() - start_time) / 60
                    if elapsed >= duration_minutes:
                        logger.info(f"⏰ Durée max atteinte ({duration_minutes} min)")
                        break
                
                # Attendre avant prochain scan
                logger.info(f"⏸️ Attente {self.SCAN_INTERVAL}s avant prochain scan...")
                time.sleep(self.SCAN_INTERVAL)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt demandé par l'utilisateur")
        
        finally:
            self.predictor.close()
            logger.info(f"✅ Moniteur arrêté après {scan_count} scans")


def main():
    """Point d'entrée."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Moniteur live matches néerlandais')
    parser.add_argument('--once', action='store_true', help='Scanner une seule fois')
    parser.add_argument('--duration', type=int, help='Durée max en minutes (continu)')
    parser.add_argument('--db', default='data/predictions.db', help='Chemin DB')
    
    args = parser.parse_args()
    
    monitor = NetherlandsLiveMonitor(db_path=args.db)
    
    if args.once:
        logger.info("🔍 Scan unique")
        monitor.scan_once()
    else:
        monitor.monitor_continuous(duration_minutes=args.duration)


if __name__ == "__main__":
    main()
