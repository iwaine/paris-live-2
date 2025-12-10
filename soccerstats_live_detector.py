#!/usr/bin/env python3
"""
SoccerStats Live Match Detector
Détecte automatiquement les matches en cours depuis la page principale
Filtre selon les ligues configurées dans config.yaml
"""

import requests
import re
import time
import yaml
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LiveMatch:
    """Match en cours détecté"""
    league: str
    home_team: str
    away_team: str
    match_url: str
    score: Optional[str] = None
    minute: Optional[int] = None


class SoccerStatsLiveDetector:
    """
    Détecte les matches en direct sur SoccerStats.com
    Filtre selon config.yaml
    """
    
    MAIN_URL = "https://www.soccerstats.com/"
    DEFAULT_THROTTLE = 3  # secondes
    
    def __init__(self, config_path: str = "football-live-prediction/config.yaml"):
        """
        Initialise le détecteur
        
        Args:
            config_path: Chemin vers config.yaml
        """
        self.config_path = config_path
        self.followed_leagues = self._load_followed_leagues()
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "paris-live-bot/1.0 (Match Analysis)"
        })
    
    def _load_followed_leagues(self) -> set:
        """Charge les ligues suivies depuis config.yaml"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'leagues' in config:
                        leagues = set()
                        for league_config in config['leagues']:
                            if isinstance(league_config, dict):
                                league_name = league_config.get('name', '').lower()
                                if league_name:
                                    leagues.add(league_name)
                        print(f"✅ {len(leagues)} ligues suivies chargées depuis config.yaml")
                        return leagues
        except Exception as e:
            print(f"⚠️ Erreur lecture config.yaml: {e}")
        
        # Fallback: ligues par défaut
        default_leagues = {
            'bulgaria', 'france', 'spain', 'italy', 'england', 'germany',
            'portugal', 'netherlands', 'belgium', 'turkey', 'greece'
        }
        print(f"⚠️ Utilisation ligues par défaut: {len(default_leagues)}")
        return default_leagues
    
    def _respect_throttle(self):
        """Attend si nécessaire pour respecter le throttling"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.DEFAULT_THROTTLE:
            time.sleep(self.DEFAULT_THROTTLE - elapsed)
        self.last_request_time = time.time()
    
    def fetch_main_page(self) -> Optional[BeautifulSoup]:
        """
        Télécharge la page principale de SoccerStats
        
        Returns:
            BeautifulSoup object ou None si erreur
        """
        try:
            self._respect_throttle()
            response = self.session.get(self.MAIN_URL, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"❌ Erreur téléchargement page principale: {e}")
            return None
    
    def extract_live_matches(self, soup: BeautifulSoup) -> List[LiveMatch]:
        """
        Extrait tous les matches en direct depuis la page principale
        
        Args:
            soup: BeautifulSoup de la page principale
        
        Returns:
            Liste de LiveMatch objects
        """
        live_matches = []
        
        # Chercher section "In-Play" ou "Live Matches"
        # Structure typique: <h2>In-Play</h2> suivi de liens vers matches
        
        # MÉTHODE 1: Chercher liens pmatch.asp (matches en direct)
        for link in soup.find_all('a', href=re.compile(r'pmatch\.asp\?')):
            try:
                match_url = link['href']
                if not match_url.startswith('http'):
                    match_url = f"https://www.soccerstats.com/{match_url}"
                
                # Extraire league depuis l'URL
                league_match = re.search(r'league=([^&]+)', match_url)
                if not league_match:
                    continue
                
                league = league_match.group(1).lower()
                
                # Filtrer selon config.yaml
                if league not in self.followed_leagues:
                    continue
                
                # Extraire équipes du texte du lien
                link_text = link.get_text(strip=True)
                
                # Format typique: "TEAM A - TEAM B" ou "TEAM A v TEAM B"
                teams_match = re.search(r'(.+?)\s*[-v]\s*(.+)', link_text)
                if teams_match:
                    home_team = teams_match.group(1).strip()
                    away_team = teams_match.group(2).strip()
                    
                    # Extraire score si présent (ex: "1:0")
                    score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', link_text)
                    score = score_match.group(0) if score_match else None
                    
                    live_match = LiveMatch(
                        league=league,
                        home_team=home_team,
                        away_team=away_team,
                        match_url=match_url,
                        score=score
                    )
                    
                    live_matches.append(live_match)
            
            except Exception as e:
                continue
        
        # MÉTHODE 2: Chercher tables avec classe spécifique ou structure "In-Play"
        # (à ajuster selon structure réelle HTML de SoccerStats)
        for table in soup.find_all('table'):
            # Vérifier si table contient "In-Play" ou "Live"
            table_text = table.get_text().lower()
            if 'in-play' not in table_text and 'live' not in table_text:
                continue
            
            # Parser les lignes de la table
            for row in table.find_all('tr'):
                links = row.find_all('a', href=re.compile(r'pmatch\.asp\?'))
                for link in links:
                    try:
                        match_url = link['href']
                        if not match_url.startswith('http'):
                            match_url = f"https://www.soccerstats.com/{match_url}"
                        
                        # Éviter doublons
                        if any(m.match_url == match_url for m in live_matches):
                            continue
                        
                        # Extraire league
                        league_match = re.search(r'league=([^&]+)', match_url)
                        if not league_match:
                            continue
                        
                        league = league_match.group(1).lower()
                        
                        if league not in self.followed_leagues:
                            continue
                        
                        # Extraire équipes
                        link_text = link.get_text(strip=True)
                        teams_match = re.search(r'(.+?)\s*[-v]\s*(.+)', link_text)
                        
                        if teams_match:
                            home_team = teams_match.group(1).strip()
                            away_team = teams_match.group(2).strip()
                            
                            score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', link_text)
                            score = score_match.group(0) if score_match else None
                            
                            live_match = LiveMatch(
                                league=league,
                                home_team=home_team,
                                away_team=away_team,
                                match_url=match_url,
                                score=score
                            )
                            
                            live_matches.append(live_match)
                    
                    except Exception:
                        continue
        
        return live_matches
    
    def detect_live_matches(self) -> List[LiveMatch]:
        """
        Détecte tous les matches en direct filtrés selon config.yaml
        
        Returns:
            Liste de LiveMatch objects
        """
        print(f"\n🔍 Détection matches live sur {self.MAIN_URL}...")
        print(f"📋 Ligues suivies: {len(self.followed_leagues)}")
        
        soup = self.fetch_main_page()
        if not soup:
            return []
        
        live_matches = self.extract_live_matches(soup)
        
        # Dédupliquer par URL
        unique_matches = []
        seen_urls = set()
        for match in live_matches:
            if match.match_url not in seen_urls:
                unique_matches.append(match)
                seen_urls.add(match.match_url)
        
        print(f"\n✅ {len(unique_matches)} match(es) en direct détecté(s)")
        
        return unique_matches
    
    def get_live_matches_summary(self) -> List[Dict]:
        """
        Retourne résumé des matches live en format dict
        
        Returns:
            Liste de dicts avec clés: league, home_team, away_team, match_url
        """
        matches = self.detect_live_matches()
        return [
            {
                'league': m.league,
                'home_team': m.home_team,
                'away_team': m.away_team,
                'match_url': m.match_url,
                'score': m.score
            }
            for m in matches
        ]


def detect_live_matches(config_path: str = "football-live-prediction/config.yaml") -> List[Dict]:
    """
    Fonction utilitaire pour détecter matches live
    
    Args:
        config_path: Chemin vers config.yaml
    
    Returns:
        Liste de dicts avec matches live
    
    Exemple:
        >>> matches = detect_live_matches()
        >>> for m in matches:
        ...     print(f"{m['league']}: {m['home_team']} vs {m['away_team']}")
    """
    detector = SoccerStatsLiveDetector(config_path)
    return detector.get_live_matches_summary()


if __name__ == '__main__':
    # Test détection
    print("="*80)
    print("🎯 DÉTECTEUR DE MATCHES LIVE - SOCCERSTATS.COM")
    print("="*80)
    
    detector = SoccerStatsLiveDetector()
    matches = detector.detect_live_matches()
    
    if matches:
        print(f"\n📊 MATCHES EN DIRECT DÉTECTÉS:\n")
        for i, match in enumerate(matches, 1):
            print(f"{i}. [{match.league.upper()}] {match.home_team} vs {match.away_team}")
            if match.score:
                print(f"   Score: {match.score}")
            print(f"   URL: {match.match_url}")
            print()
    else:
        print("\n⚠️ Aucun match en direct détecté")
        print("   Causes possibles:")
        print("   • Pas de matches en cours actuellement")
        print("   • Aucun match dans les ligues suivies (config.yaml)")
        print("   • Structure HTML de SoccerStats.com modifiée")
    
    print("="*80)
