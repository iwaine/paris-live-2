#!/usr/bin/env python3
"""
SoccerStats Live Scraper - Extraction précise des données live
Basé sur les balises HTML documentées dans BALISES_HTML_SCRAPING.md
"""

import requests
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class MatchData:
    """Données structurées d'un match live"""
    # Informations basiques
    home_team: str
    away_team: str
    score_home: int
    score_away: int
    minute: int
    timestamp: str

    # Possession
    possession_home: Optional[float] = None
    possession_away: Optional[float] = None

    # Tirs
    shots_home: Optional[int] = None
    shots_away: Optional[int] = None
    shots_on_target_home: Optional[int] = None
    shots_on_target_away: Optional[int] = None

    # Attaques
    attacks_home: Optional[int] = None
    attacks_away: Optional[int] = None
    dangerous_attacks_home: Optional[int] = None
    dangerous_attacks_away: Optional[int] = None

    # Corners
    corners_home: Optional[int] = None
    corners_away: Optional[int] = None

    def to_dict(self):
        """Convertit en dictionnaire"""
        return asdict(self)


class SoccerStatsLiveScraper:
    """Scraper précis pour données live SoccerStats"""

    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def scrape_match(self, url: str) -> Optional[MatchData]:
        """
        Extrait toutes les données d'un match live

        Args:
            url: URL pmatch.asp du match

        Returns:
            MatchData ou None si erreur
        """
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. ÉQUIPES - <font color="blue"> avec taille 18px/28px
            home_team, away_team = self._extract_teams(soup)
            if not home_team or not away_team:
                print("❌ Impossible d'extraire les équipes")
                return None

            # 2. SCORE - <font style="color:#87CEFA;26px/36px">
            score_home, score_away = self._extract_score(soup)
            if score_home is None or score_away is None:
                print("❌ Impossible d'extraire le score")
                return None

            # 3. MINUTE - <font style="font-size:13px;color:#87CEFA;">
            minute = self._extract_minute(soup)
            if minute is None:
                print("❌ Impossible d'extraire la minute")
                return None

            # 4. STATS - <h3> → table → td[width="80"] → b
            stats = self._extract_stats(soup)

            # Créer l'objet MatchData
            match_data = MatchData(
                home_team=home_team,
                away_team=away_team,
                score_home=score_home,
                score_away=score_away,
                minute=minute,
                timestamp=datetime.now().isoformat(),
                **stats  # Unpack les stats (possession, shots, etc.)
            )

            print(f"✅ Données extraites: {home_team} {score_home}-{score_away} {away_team} ({minute}')")

            return match_data

        except Exception as e:
            print(f"❌ Erreur scraping: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_teams(self, soup: BeautifulSoup) -> tuple:
        """
        ÉQUIPES: <font color="blue"> avec taille 18px/28px

        Returns:
            (home_team, away_team)
        """
        teams = []

        # Chercher tous les <font>
        all_fonts = soup.find_all('font')

        for font in all_fonts:
            # Méthode 1: attribut color="blue"
            color_attr = font.get('color', '')
            style_attr = font.get('style', '')

            # Vérifier si c'est un font d'équipe (bleu avec taille >= 18px)
            is_team_font = (
                'blue' in color_attr.lower() or
                ('blue' in style_attr.lower() and any(size in style_attr for size in ['18px', '28px', '26px']))
            )

            if is_team_font:
                text = font.get_text(strip=True)

                # Filtres pour exclure les non-équipes:
                # 1. Au moins 3 caractères
                if not text or len(text) < 3:
                    continue

                # 2. Exclure les patterns de score (X-X, X:X, X - X)
                if re.match(r'^\d+\s*[-:]\s*\d+$', text):
                    continue

                # 3. Exclure les textes avec trop de chiffres (> 30% du texte)
                digit_count = sum(c.isdigit() for c in text)
                if digit_count / len(text) > 0.3:
                    continue

                teams.append(text)

        # Prendre les 2 premières équipes trouvées
        if len(teams) >= 2:
            return (teams[0], teams[1])

        return (None, None)

    def _extract_score(self, soup: BeautifulSoup) -> tuple:
        """
        SCORE dans <td width="10%">:
        - Bulgaria (terminé): <font style="color:#87CEFA;font-size:36px;">
        - Bosnia (live): <font color="blue">

        Returns:
            (score_home, score_away)
        """
        all_fonts = soup.find_all('font')

        for font in all_fonts:
            # Vérifier que le parent est <td width="10%">
            parent = font.parent
            if not (parent and parent.name == 'td'):
                continue

            width = parent.get('width', '')
            if '10%' not in width:
                continue

            # Le parent est bien <td width="10%">
            text = font.get_text(strip=True)

            # Pattern: "X:X" ou "X - X" ou "X-X"
            match = re.match(r'^(\d+)\s*[-:\s]+\s*(\d+)$', text)
            if not match:
                continue

            # On a trouvé un score dans <td width="10%">!
            # Vérifier que c'est bien le score du match (bleu ou #87CEFA)
            color_attr = font.get('color', '')
            style_attr = font.get('style', '')

            is_score = (
                'blue' in color_attr.lower() or
                '#87CEFA' in style_attr.upper() or
                'blue' in style_attr.lower()
            )

            if is_score:
                home = int(match.group(1))
                away = int(match.group(2))
                return (home, away)

        return (None, None)

    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """
        MINUTE: <font style="font-size:13px;color:#87CEFA;">

        Returns:
            minute (int) ou None
        """
        all_fonts = soup.find_all('font')

        for font in all_fonts:
            style = font.get('style', '')
            color_attr = font.get('color', '')

            # Chercher font bleu avec 13px (minute)
            is_minute_font = (
                ('13px' in style and ('#87CEFA' in style.upper() or 'blue' in style.lower())) or
                ('blue' in color_attr.lower() and '13px' not in style)  # Parfois juste color="blue"
            )

            if is_minute_font:
                text = font.get_text(strip=True)

                # Pattern: "51 min." ou "51'" ou "51 min"
                match = re.match(r'^(\d+)\s*(?:min\.?|\')?$', text, re.IGNORECASE)
                if match:
                    minute = int(match.group(1))
                    # Vérifier que c'est une minute de match (0-120)
                    if 0 <= minute <= 120:
                        return minute

        return None

    def _extract_stats(self, soup: BeautifulSoup) -> dict:
        """
        STATS: <h3>Stat_Name</h3> → parent table → td[width="80"] → b

        Returns:
            dict avec toutes les stats
        """
        stats = {}

        # Mapping des noms de stats vers les clés de sortie
        stat_mapping = {
            'Possession': ('possession_home', 'possession_away'),
            'Total shots': ('shots_home', 'shots_away'),
            'Shots on target': ('shots_on_target_home', 'shots_on_target_away'),
            'Attacks': ('attacks_home', 'attacks_away'),
            'Dangerous attacks': ('dangerous_attacks_home', 'dangerous_attacks_away'),
            'Corners': ('corners_home', 'corners_away'),
        }

        # Chercher tous les <h3>
        h3_elements = soup.find_all('h3')

        for h3 in h3_elements:
            stat_name = h3.get_text(strip=True)

            # Vérifier si c'est une stat qu'on veut
            if stat_name not in stat_mapping:
                continue

            # Remonter à la table parente
            table = h3.find_parent('table')
            if not table:
                continue

            # Chercher les <td width="80">
            td_cells = table.find_all('td', {'width': '80'})

            if len(td_cells) >= 2:
                # Extraire les valeurs (chercher <b> à l'intérieur)
                home_val_el = td_cells[0].find('b')
                away_val_el = td_cells[1].find('b')

                if home_val_el and away_val_el:
                    home_text = home_val_el.get_text(strip=True)
                    away_text = away_val_el.get_text(strip=True)

                    # Convertir en nombre si possible
                    home_key, away_key = stat_mapping[stat_name]

                    # Possession: convertir en float
                    if 'possession' in home_key.lower():
                        try:
                            stats[home_key] = float(home_text.replace('%', ''))
                            stats[away_key] = float(away_text.replace('%', ''))
                        except ValueError:
                            pass
                    # Autres stats: convertir en int
                    else:
                        try:
                            stats[home_key] = int(home_text)
                            stats[away_key] = int(away_text)
                        except ValueError:
                            pass

        return stats


def test_scraper():
    """Test du scraper"""
    print("\n" + "="*70)
    print("🧪 TEST SOCCERSTATS LIVE SCRAPER")
    print("="*70)

    # URL de test
    test_url = "https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026"

    scraper = SoccerStatsLiveScraper()
    match_data = scraper.scrape_match(test_url)

    if match_data:
        print("\n✅ EXTRACTION RÉUSSIE!\n")
        print(f"🏟️  Match: {match_data.home_team} vs {match_data.away_team}")
        print(f"⚽ Score: {match_data.score_home}-{match_data.score_away}")
        print(f"⏱️  Minute: {match_data.minute}'")
        print(f"📊 Possession: {match_data.possession_home}% - {match_data.possession_away}%")
        print(f"🎯 Shots: {match_data.shots_home} - {match_data.shots_away}")
        print(f"🚀 Attacks: {match_data.attacks_home} - {match_data.attacks_away}")
        print(f"🎪 Corners: {match_data.corners_home} - {match_data.corners_away}")
    else:
        print("\n❌ ÉCHEC DE L'EXTRACTION")

    print("\n" + "="*70)


if __name__ == '__main__':
    test_scraper()
