#!/usr/bin/env python3
"""
Live Prediction Pipeline avec SoccerStats Scraper
Combine: Scraper → Feature Extraction → ML Predictions → Telegram Alerts
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Ajouter le dossier football-live-prediction au PATH
football_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'football-live-prediction')
sys.path.insert(0, football_dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from soccerstats_live_scraper import SoccerStatsLiveScraper, LiveMatchData
from feature_extractor import FeatureVector
from live_prediction_pipeline import BettingDecision, LivePredictionPipeline


def create_feature_vector(
    minute: int,
    score_home: int,
    score_away: int,
    possession_home: float,
    possession_away: float,
    corners_home: int,
    corners_away: int,
    shots_home: int,
    shots_away: int,
    shots_on_target_home: int,
    shots_on_target_away: int
) -> FeatureVector:
    """Crée un FeatureVector pour le modèle ML"""
    
    # Normaliser possession en 0-1
    poss_h = possession_home / 100.0 if possession_home > 1 else possession_home
    poss_a = possession_away / 100.0 if possession_away > 1 else possession_away
    
    # Calculer les ratios
    shot_sot_ratio_home = min(1.0, shots_on_target_home / shots_home if shots_home > 0 else 0)
    shot_sot_ratio_away = min(1.0, shots_on_target_away / shots_away if shots_away > 0 else 0)
    
    # Bucket minute
    if minute < 15:
        minute_bucket = "0-15"
    elif minute < 30:
        minute_bucket = "15-30"
    elif minute < 45:
        minute_bucket = "30-45"
    elif minute < 60:
        minute_bucket = "45-60"
    elif minute < 75:
        minute_bucket = "60-75"
    else:
        minute_bucket = "75-90"
    
    return FeatureVector(
        minute=minute,
        minute_bucket=minute_bucket,
        score_home=score_home,
        score_away=score_away,
        goal_diff=score_home - score_away,
        possession_home=poss_h,
        possession_away=poss_a,
        shots_home=shots_home,
        shots_away=shots_away,
        sot_home=shots_on_target_home,
        sot_away=shots_on_target_away,
        shot_sot_ratio_home=shot_sot_ratio_home,
        shot_sot_ratio_away=shot_sot_ratio_away,
        shots_delta_5m_home=0,  # Pas d'historique
        shots_delta_5m_away=0,
        sot_delta_5m_home=0,
        sot_delta_5m_away=0,
        corners_home=corners_home,
        corners_away=corners_away,
        corners_delta_5m_home=0,
        corners_delta_5m_away=0,
        red_cards_home=0,
        red_cards_away=0,
        yellow_cards_home=0,
        yellow_cards_away=0,
        team_elo_home=1500.0,  # ELO par défaut
        team_elo_away=1500.0,
        elo_diff=0.0,
        home_advantage=1.0,
        recent_goal_count_5m=0,
        saturation_score=(score_home + score_away) * 10 + (shots_on_target_home + shots_on_target_away) / 2
    )


class LiveMatchPipeline:
    """
    Pipeline complet: Scraping → Features → Prédictions → Décisions
    """
    
    def __init__(self, model_path: str = "lightgbm_model.pkl", config_path: str = "config.yaml"):
        """
        Initialise le pipeline
        
        Args:
            model_path: Chemin du modèle LightGBM
            config_path: Chemin de la config YAML
        """
        self.scraper = SoccerStatsLiveScraper(throttle_seconds=3)
        self.predictor = LivePredictionPipeline()
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Charge la configuration YAML"""
        if self.config_path.exists():
            import yaml
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        return {
            'strategy': 'conservative',
            'danger_threshold': 60,
            'min_possession_diff': 5,
            'min_shots_diff': 2
        }
    
    def process_match(self, url: str) -> Optional[Dict]:
        """
        Traite un match de bout en bout
        
        Args:
            url: URL du match SoccerStats
        
        Returns:
            Dict avec tous les résultats ou None
        """
        
        print(f"\n{'='*80}")
        print(f"🔄 TRAITEMENT MATCH: {url}")
        print(f"{'='*80}\n")
        
        # ÉTAPE 1: SCRAPER
        print("📥 [1/4] Scraping du match...")
        live_data = self.scraper.scrape_match(url)
        
        if not live_data:
            print("❌ Erreur: Impossible de scraper le match")
            return None
        
        print(f"✓ {live_data.home_team} {live_data.score_home}:{live_data.score_away} {live_data.away_team}")
        print(f"  Minute: {live_data.minute}, Possession: {live_data.possession_home}% vs {live_data.possession_away}%\n")
        
        # ÉTAPE 2: FEATURE EXTRACTION
        print("🧠 [2/4] Extraction des features...")
        try:
            features = create_feature_vector(
                minute=live_data.minute or 0,
                score_home=live_data.score_home,
                score_away=live_data.score_away,
                possession_home=live_data.possession_home or 50,
                possession_away=live_data.possession_away or 50,
                corners_home=live_data.corners_home or 0,
                corners_away=live_data.corners_away or 0,
                shots_home=live_data.shots_home or 0,
                shots_away=live_data.shots_away or 0,
                shots_on_target_home=live_data.shots_on_target_home or 0,
                shots_on_target_away=live_data.shots_on_target_away or 0
            )
            print(f"✓ {len(features.to_dict())} features générées\n")
        except Exception as e:
            print(f"❌ Erreur extraction features: {e}\n")
            return None
        
        # ÉTAPE 3: PRÉDICTION
        print("🤖 [3/4] Prédiction ML...")
        try:
            prediction_result = self.predictor.calculate_danger_score(features.to_dict())
            danger_score = prediction_result.get('danger_score', 0)
            confidence = prediction_result.get('confidence', 0)
            print(f"✓ Danger Score: {danger_score:.1f}%")
            print(f"  Confiance: {confidence:.1f}%\n")
        except Exception as e:
            print(f"❌ Erreur prédiction: {e}\n")
            return None
        
        # ÉTAPE 4: DÉCISION
        print("⚡ [4/4] Décision finale...")
        
        action = "BUY" if danger_score >= self.config['danger_threshold'] else "SKIP"
        reasoning = self._generate_reasoning(danger_score, confidence, live_data)
        
        print(f"✓ Décision: {action}")
        print(f"  Raison: {reasoning[:60]}...\n")
        
        result = {
            'url': url,
            'live_data': live_data.to_dict(),
            'features': features.to_dict(),
            'prediction': {
                'danger_score': danger_score,
                'confidence': confidence
            },
            'decision': {
                'action': action,
                'reasoning': reasoning,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return result
    
    def _generate_reasoning(self, danger_score: float, confidence: float, live_data: LiveMatchData) -> str:
        """Génère une explication pour la décision"""
        factors = []
        
        if live_data.minute and live_data.minute < 15:
            factors.append("match jeune")
        
        if live_data.shots_away and live_data.shots_away > 8:
            factors.append("beaucoup de tirs adverses")
        
        if live_data.possession_home and live_data.possession_home < 40:
            factors.append("possession faible")
        
        if confidence > 80:
            factors.append("haute confiance du modèle")
        
        return f"Danger={danger_score:.0f}%, " + ", ".join(factors) if factors else "Critères standards"
    
    def process_matches_batch(self, urls: List[str], output_file: Optional[str] = None):
        """
        Traite plusieurs matches
        
        Args:
            urls: Liste d'URLs
            output_file: Fichier de sortie JSON (optionnel)
        """
        print(f"\n{'#'*80}")
        print(f"# PIPELINE LIVE MATCHES")
        print(f"# {len(urls)} matches à traiter")
        print(f"{'#'*80}")
        
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Traitement match {i}...\n")
            result = self.process_match(url)
            
            if result:
                results.append(result)
                
                # Afficher un résumé
                print(f"{'─'*80}")
                print(f"📊 RÉSUMÉ MATCH {i}")
                print(f"{'─'*80}")
                print(f"Match: {result['live_data']['home_team']} vs {result['live_data']['away_team']}")
                print(f"Score: {result['live_data']['score_home']}:{result['live_data']['score_away']}")
                print(f"Danger Score: {result['prediction']['danger_score']:.1f}%")
                print(f"Décision: {result['decision']['action']}")
                print(f"Raison: {result['decision']['reasoning']}\n")
            
            if i < len(urls):
                print(f"⏳ Attente 5s avant prochain match...\n")
                time.sleep(5)
        
        # Sauvegarder les résultats
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n✓ Résultats sauvegardés dans {output_file}\n")
        
        # Résumé final
        print(f"\n{'#'*80}")
        print(f"# RÉSUMÉ FINAL")
        print(f"{'#'*80}")
        print(f"Matches traités: {len(results)}/{len(urls)}")
        
        buy_count = sum(1 for r in results if r['decision']['action'] == 'BUY')
        skip_count = sum(1 for r in results if r['decision']['action'] == 'SKIP')
        
        print(f"Décisions BUY: {buy_count}")
        print(f"Décisions SKIP: {skip_count}")
        print(f"Taux de BUY: {buy_count/len(results)*100:.1f}%\n" if results else "Aucun match\n")
        
        return results


if __name__ == '__main__':
    # URLs de test
    test_urls = [
        'https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026',
    ]
    
    # Créer et exécuter le pipeline
    pipeline = LiveMatchPipeline()
    
    if len(sys.argv) > 1:
        # URL spécifique en paramètre
        result = pipeline.process_match(sys.argv[1])
        if result:
            print("\n✅ Traitement réussi!")
    else:
        # Traiter URLs de test
        results = pipeline.process_matches_batch(
            test_urls,
            output_file="/tmp/pipeline_results.json"
        )
