"""
Live Match Detector - Détecte automatiquement les matchs live/HT sur SoccerStats
Cherche les <font style="color:#87CEFA;"> avec "min", "HT", etc.
"""

import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup, Tag
from .base_scraper import BaseScraper


class LiveMatchDetector(BaseScraper):
    """Détecte les matchs live sur une page de ligue SoccerStats"""

    def __init__(self):
        super().__init__()

        # Couleur utilisée pour les statuts live
        self.live_color = "#87CEFA"

        # Patterns pour détecter les statuts live
        self.live_patterns = [
            r'\d+\s*min',      # "51 min", "38min", etc.
            r"\d+\s*'",        # "51'", "38'"
            r'HT',             # Half-time
            r'LIVE',           # Live générique
            r'H-T',            # Half-time variant
        ]

        # Statuts à ignorer (matchs terminés)
        self.ignore_patterns = [
            r'FT',             # Full-time
            r'F-T',            # Full-time variant
            r'Postp',          # Postponed
            r'Canc',           # Cancelled
        ]

    def is_live_status(self, status_text: str) -> bool:
        """
        Vérifie si le texte représente un statut live

        Args:
            status_text: Texte du statut (ex: "51 min", "HT")

        Returns:
            True si c'est un match live
        """
        status_text = status_text.strip()

        # Vérifier les statuts à ignorer
        for pattern in self.ignore_patterns:
            if re.search(pattern, status_text, re.IGNORECASE):
                return False

        # Vérifier les patterns live
        for pattern in self.live_patterns:
            if re.search(pattern, status_text, re.IGNORECASE):
                return True

        return False

    def find_match_link_in_parent(self, element: Tag) -> Optional[str]:
        """
        Remonte dans le DOM pour trouver le lien du match (pmatch.asp)
        Basé sur l'analyse: le lien est dans le <tr> parent qui contient le statut live

        Args:
            element: Element BeautifulSoup à partir duquel chercher

        Returns:
            URL du match ou None
        """
        # D'abord chercher le <tr> parent
        tr_parent = element.find_parent('tr')

        if tr_parent:
            # Chercher le lien dans ce <tr>
            link = tr_parent.find('a', href=lambda x: x and 'pmatch.asp' in x)
            if link:
                href = link.get('href', '')
                if href:
                    # Construire l'URL complète
                    if href.startswith('http'):
                        return href
                    else:
                        return f"https://www.soccerstats.com/{href}"

        # Si pas trouvé dans <tr>, chercher dans les parents plus larges (jusqu'à 15 niveaux)
        current = element
        for _ in range(15):
            if current is None:
                break

            # Chercher un lien <a> dans cet élément ou ses enfants
            link = current.find('a', href=lambda x: x and 'pmatch.asp' in x)
            if link:
                href = link.get('href', '')
                if href:
                    # Construire l'URL complète
                    if href.startswith('http'):
                        return href
                    else:
                        return f"https://www.soccerstats.com/{href}"

            # Remonter au parent
            current = current.parent

        return None

    def find_match_link_in_siblings(self, element: Tag) -> Optional[str]:
        """
        Cherche le lien du match dans les éléments frères (siblings)

        Args:
            element: Element BeautifulSoup

        Returns:
            URL du match ou None
        """
        # Chercher dans les siblings précédents et suivants
        for sibling in list(element.previous_siblings) + list(element.next_siblings):
            if not isinstance(sibling, Tag):
                continue

            # Chercher un lien dans ce sibling
            link = sibling.find('a', href=lambda x: x and 'pmatch.asp' in x)
            if link:
                href = link.get('href', '')
                if href:
                    if href.startswith('http'):
                        return href
                    else:
                        return f"https://www.soccerstats.com/{href}"

        return None

    def extract_team_names(self, element: Tag) -> tuple:
        """
        Extrait les noms des équipes depuis la structure HTML

        Args:
            element: Element contenant le statut live

        Returns:
            (home_team, away_team) ou (None, None)
        """
        # Chercher dans les parents
        current = element
        for _ in range(10):
            if current is None:
                break

            # Chercher les fonts avec les noms d'équipes (couleur #eeeeee, taille 28px)
            team_fonts = current.find_all('font', style=lambda x: x and '#eeeeee' in x and '28px' in x)

            if len(team_fonts) >= 2:
                home_team = team_fonts[0].get_text(strip=True)
                away_team = team_fonts[1].get_text(strip=True)
                return (home_team, away_team)

            current = current.parent

        return (None, None)

    def scrape(self, league_url: str, league_name: str = None) -> List[Dict]:
        """
        Scrape une page de ligue pour détecter les matchs live

        Args:
            league_url: URL de la page latest.asp de la ligue
            league_name: Nom de la ligue (optionnel)

        Returns:
            Liste de dictionnaires avec les infos des matchs live:
            [
                {
                    'url': 'https://www.soccerstats.com/pmatch.asp?...',
                    'league': 'Bulgaria',
                    'status': '51 min',
                    'home_team': 'Septemvri Sofia',
                    'away_team': 'CSKA 1948 Sofia',
                    'score': '0 - 1'
                },
                ...
            ]
        """
        try:
            # Extraire le nom de la ligue depuis l'URL si non fourni
            if not league_name:
                if 'league=' in league_url:
                    league_name = league_url.split('league=')[-1].split('&')[0]
                else:
                    league_name = 'Unknown'

            self.logger.info(f"Scanning for live matches: {league_name}")

            # Récupérer la page
            response = self.fetch_page(league_url)

            if not self.validate_response(response):
                self.logger.warning(f"Invalid response for {league_name}")
                return []

            # Parser le HTML
            soup = self.parse_html(response.text)

            # Chercher tous les <font> avec la couleur live (#87CEFA)
            live_fonts = soup.find_all('font', style=lambda x: x and self.live_color.upper() in x.upper())

            self.logger.debug(f"Found {len(live_fonts)} potential live indicators")

            live_matches = []

            for font in live_fonts:
                status_text = font.get_text(strip=True)

                # Vérifier si c'est un statut live
                if not self.is_live_status(status_text):
                    continue

                self.logger.debug(f"Live status found: {status_text}")

                # Chercher le lien du match
                match_url = self.find_match_link_in_parent(font)

                if not match_url:
                    match_url = self.find_match_link_in_siblings(font)

                if not match_url:
                    self.logger.warning(f"No match link found for status: {status_text}")
                    continue

                # Extraire les noms des équipes
                home_team, away_team = self.extract_team_names(font)

                # Extraire le score (chercher le font avec couleur #87CEFA et taille 36px)
                score = None
                current = font
                for _ in range(10):
                    if current is None:
                        break
                    score_font = current.find('font', style=lambda x: x and '#87CEFA' in x and '36px' in x)
                    if score_font:
                        score = score_font.get_text(strip=True)
                        break
                    current = current.parent

                # Créer l'ID du match
                match_id = None
                if 'stats=' in match_url:
                    stats_part = match_url.split('stats=')[-1].split('&')[0]
                    match_id = f"{league_name}_{stats_part}"

                match_info = {
                    'url': match_url,
                    'league': league_name,
                    'status': status_text,
                    'home_team': home_team,
                    'away_team': away_team,
                    'score': score,
                    'id': match_id or f"{league_name}_{len(live_matches)}"
                }

                # Créer le titre du match
                if home_team and away_team:
                    match_info['title'] = f"{home_team} vs {away_team}"
                elif score:
                    match_info['title'] = f"Match {score}"
                else:
                    match_info['title'] = f"Match live ({status_text})"

                live_matches.append(match_info)

                self.logger.info(f"✅ Live match detected: {match_info['title']} - {status_text}")

            self.logger.info(f"Total live matches found: {len(live_matches)}")

            return live_matches

        except Exception as e:
            self.logger.error(f"Error scanning {league_name}: {e}")
            return []


# Test du scraper
if __name__ == "__main__":
    detector = LiveMatchDetector()

    try:
        # Test avec la Bulgarie
        print("\n" + "="*80)
        print("🔍 TEST: Détection matchs live en Bulgarie")
        print("="*80)

        matches = detector.scrape(
            league_url="https://www.soccerstats.com/latest.asp?league=bulgaria",
            league_name="Bulgaria"
        )

        if matches:
            print(f"\n✅ {len(matches)} match(es) live trouvé(s):\n")
            for i, match in enumerate(matches, 1):
                print(f"{i}. {match['title']}")
                print(f"   Status: {match['status']}")
                print(f"   Score: {match.get('score', 'N/A')}")
                print(f"   URL: {match['url']}")
                print()
        else:
            print("\n❌ Aucun match live trouvé")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        detector.cleanup()
