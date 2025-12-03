#!/usr/bin/env python3
"""
SoccerStats Live Scraper
Extrait les données en direct d'un match SoccerStats
Compatible avec live_prediction_pipeline.py
"""

import requests
import re
import time
from bs4 import BeautifulSoup
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LiveMatchData:
    """Données extraites d'un match en direct"""
    home_team: str
    away_team: str
    score_home: int
    score_away: int
    minute: Optional[int]
    possession_home: Optional[float]
    possession_away: Optional[float]
    corners_home: Optional[int]
    corners_away: Optional[int]
    shots_home: Optional[int]
    shots_away: Optional[int]
    shots_on_target_home: Optional[int]
    shots_on_target_away: Optional[int]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convertir en dictionnaire pour feature_extractor"""
        return {
            'home_team': self.home_team,
            'away_team': self.away_team,
            'score_home': self.score_home,
            'score_away': self.score_away,
            'minute': self.minute or 0,
            'possession_home': self.possession_home,
            'possession_away': self.possession_away,
            'corners_home': self.corners_home or 0,
            'corners_away': self.corners_away or 0,
            'shots_home': self.shots_home or 0,
            'shots_away': self.shots_away or 0,
            'shots_on_target_home': self.shots_on_target_home or 0,
            'shots_on_target_away': self.shots_on_target_away or 0,
        }


class SoccerStatsLiveScraper:
    """
    Scraper pour SoccerStats.com
    Respecte robots.txt - minimum 3 secondes entre requêtes
    """
    
    DEFAULT_TIMEOUT = 15
    DEFAULT_THROTTLE = 3  # secondes
    
    def __init__(self, throttle_seconds: int = DEFAULT_THROTTLE):
        """
        Initialise le scraper
        
        Args:
            throttle_seconds: Délai minimum entre requêtes (respect robots.txt)
        """
        self.throttle_seconds = throttle_seconds
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "paris-live-bot/1.0 (Match Analysis)"
        })
    
    def _respect_throttle(self):
        """Attend si nécessaire pour respecter le throttling"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.throttle_seconds:
            time.sleep(self.throttle_seconds - elapsed)
        self.last_request_time = time.time()
    
    def fetch_match_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Télécharge la page du match
        
        Args:
            url: URL SoccerStats du match
        
        Returns:
            BeautifulSoup object ou None si erreur
        """
        try:
            self._respect_throttle()
            response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"❌ Erreur téléchargement {url}: {e}")
            return None
    
    def extract_teams(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """Extrait les noms d'équipes"""
        try:
            fonts_blue = soup.find_all('font', 
                                      style=lambda s: s and 'color:blue' in s and '18px' in s)
            if len(fonts_blue) >= 2:
                home = fonts_blue[0].get_text(strip=True)
                away = fonts_blue[1].get_text(strip=True)
                if home and away and home != away:
                    return home, away
        except Exception as e:
            print(f"⚠️ Erreur extraction équipes: {e}")
        return None, None
    
    def extract_score(self, soup: BeautifulSoup) -> Tuple[Optional[int], Optional[int]]:
        """Extrait le score (ex: 0:1 → 0, 1)"""
        try:
            # Méthode 1: Chercher font avec style #87CEFA (couleur du score)
            score_font = soup.find('font', 
                                  style=lambda s: s and '#87CEFA' in s and '26px' in s)
            if score_font:
                score_text = score_font.get_text(strip=True)
                # Format: "0:1" ou "0 - 1"
                match = re.search(r'(\d+)\s*[-:]\s*(\d+)', score_text)
                if match:
                    return int(match.group(1)), int(match.group(2))
        except Exception as e:
            print(f"⚠️ Erreur extraction score: {e}")
        
        # Fallback: Regex simple
        try:
            m = re.search(r'(\d+)\s*[-:]\s*(\d+)', soup.get_text())
            if m:
                return int(m.group(1)), int(m.group(2))
        except:
            pass
        
        return None, None
    
    def extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute du match (cherche le temps actuel, pas les stats)"""
        try:
            # 1) Préférence: trouver le bloc du score (font color #87CEFA) puis chercher la minute
            score_font = soup.find('font', style=lambda s: s and '#87CEFA' in s and ('36px' in s or '26px' in s or '22px' in s))
            if score_font:
                # remonter jusqu'à un ancêtre table raisonnable
                anc = score_font
                for _ in range(5):
                    if anc is None:
                        break
                    if anc.name == 'table':
                        break
                    anc = anc.parent
                if anc is not None:
                    # chercher dans cet ancêtre des fonts proches contenant 'min' ou "'"
                    for font in anc.find_all('font'):
                        txt = font.get_text(strip=True)
                        m = re.search(r"(\d{1,3})\s*(?:'|’|min\.? )", txt)
                        if m:
                            val = int(m.group(1))
                            if 0 <= val <= 130:
                                return val

            # 2) Ensuite: chercher les <font #87CEFA 13px> comme avant
            for font in soup.find_all('font', style=lambda s: s and '#87CEFA' in s and '13px' in s):
                txt = font.get_text(strip=True)
                m = re.search(r"(\d{1,3})\s*(?:'|’|min\.? )?", txt)
                if m:
                    val = int(m.group(1))
                    if 0 <= val <= 130:
                        return val
            
            # 3) Fallback global: première occurrence raisonnable de "XX min" dans la page
            html_text = soup.get_text()
            m = re.search(r'\b(\d{1,3})\s*min\.?', html_text, re.I)
            if m:
                val = int(m.group(1))
                if 0 <= val <= 130:
                    return val
        except Exception as e:
            pass
        
        return None
    
    def extract_stat(self, soup: BeautifulSoup, stat_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrait une statistique (Possession, Corners, Shots, etc.)
        
        Args:
            soup: BeautifulSoup object
            stat_name: Nom de la stat
        
        Returns:
            (home_value, away_value)
        """
        try:
            stat_key = stat_name.lower().rstrip('s')

            # 1) Parcourir les <h3> qui mentionnent la stat et chercher les tables suivantes
            for h3 in soup.find_all('h3'):
                txt = h3.get_text(strip=True).lower()
                if stat_key in txt or stat_key in txt.replace(' ', ''):
                    # Chercher les tables qui suivent ce <h3>
                    for table in h3.find_all_next('table', limit=8):
                        # Parcourir les lignes et chercher une ligne contenant >=2 <b> numériques
                        for tr in table.find_all('tr'):
                            b_tags = tr.find_all('b')
                            nums = []
                            for b in b_tags:
                                t = b.get_text(strip=True)
                                if re.match(r'^\d{1,3}$', t):
                                    nums.append(t)
                            if len(nums) >= 2:
                                return nums[0], nums[1]

            # 2) Fallback: chercher toute table contenant le mot clé (singulier) dans son texte
            for table in soup.find_all('table'):
                if stat_key in table.get_text().lower():
                    for tr in table.find_all('tr'):
                        b_tags = tr.find_all('b')
                        nums = [b.get_text(strip=True) for b in b_tags if re.match(r'^\d{1,3}$', b.get_text(strip=True))]
                        if len(nums) >= 2:
                            return nums[0], nums[1]

        except Exception as e:
            print(f"⚠️ Erreur extraction {stat_name}: {e}")

        return None, None
    
    def parse_stat_value(self, value: Optional[str]) -> Optional[float]:
        """Parse une valeur statistique (ex: '48%' → 48.0, '3' → 3.0)"""
        if not value:
            return None
        try:
            # Enlever les caractères non-numériques
            clean = re.sub(r'[^\d.]', '', value)
            if clean:
                return float(clean)
        except:
            pass
        return None
    
    def scrape_match(self, url: str) -> Optional[LiveMatchData]:
        """
        Scrape un match complet
        
        Args:
            url: URL SoccerStats du match
        
        Returns:
            LiveMatchData object ou None si erreur
        """
        soup = self.fetch_match_page(url)
        if not soup:
            return None
        
        # Extraire tous les éléments
        home_team, away_team = self.extract_teams(soup)
        score_home, score_away = self.extract_score(soup)
        minute = self.extract_minute(soup)
        
        poss_home_str, poss_away_str = self.extract_stat(soup, 'Possession')
        possession_home = self.parse_stat_value(poss_home_str)
        possession_away = self.parse_stat_value(poss_away_str)
        
        corners_home_str, corners_away_str = self.extract_stat(soup, 'Corners')
        corners_home = int(self.parse_stat_value(corners_home_str)) if corners_home_str else None
        corners_away = int(self.parse_stat_value(corners_away_str)) if corners_away_str else None
        
        shots_home_str, shots_away_str = self.extract_stat(soup, 'Total shots')
        shots_home = int(self.parse_stat_value(shots_home_str)) if shots_home_str else None
        shots_away = int(self.parse_stat_value(shots_away_str)) if shots_away_str else None
        
        sot_home_str, sot_away_str = self.extract_stat(soup, 'Shots on target')
        shots_on_target_home = int(self.parse_stat_value(sot_home_str)) if sot_home_str else None
        shots_on_target_away = int(self.parse_stat_value(sot_away_str)) if sot_away_str else None
        
        # Vérifications minimales
        if not home_team or not away_team or score_home is None or score_away is None:
            print(f"❌ Données incomplètes pour {url}")
            return None
        
        return LiveMatchData(
            home_team=home_team,
            away_team=away_team,
            score_home=score_home,
            score_away=score_away,
            minute=minute,
            possession_home=possession_home,
            possession_away=possession_away,
            corners_home=corners_home,
            corners_away=corners_away,
            shots_home=shots_home,
            shots_away=shots_away,
            shots_on_target_home=shots_on_target_home,
            shots_on_target_away=shots_on_target_away,
            timestamp=datetime.now()
        )
    
    def scrape_matches_batch(self, urls: list) -> list:
        """
        Scrape plusieurs matches
        
        Args:
            urls: Liste d'URLs
        
        Returns:
            Liste de LiveMatchData objects
        """
        results = []
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Scraping {url}...")
            data = self.scrape_match(url)
            if data:
                results.append(data)
                print(f"✓ {data.home_team} {data.score_home}:{data.score_away} {data.away_team}")
            else:
                print(f"✗ Échoué")
        
        return results


def scrape_live_match(url: str) -> Optional[LiveMatchData]:
    """
    Fonction simple pour scraper un match
    
    Args:
        url: URL du match SoccerStats
    
    Returns:
        LiveMatchData ou None
    
    Exemple:
        >>> data = scrape_live_match("https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026")
        >>> print(data.home_team, data.score_home)
        RUDAR PRIJEDOR 0
    """
    scraper = SoccerStatsLiveScraper()
    return scraper.scrape_match(url)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # Test une URL spécifique
        url = sys.argv[1]
        print(f"\n🔍 Scraping: {url}\n")
        data = scrape_live_match(url)
        
        if data:
            print(f"✅ Match extrait avec succès!\n")
            print(f"📊 Données:")
            for key, value in data.to_dict().items():
                print(f"   {key:20} = {value}")
        else:
            print(f"❌ Échec du scraping")
    else:
        # Test par défaut
        urls = [
            'https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026',
        ]
        
        scraper = SoccerStatsLiveScraper()
        results = scraper.scrape_matches_batch(urls)
        
        print(f"\n\n{'='*80}")
        print(f"RÉSUMÉ: {len(results)} match(es) scraped avec succès")
        print(f"{'='*80}")
