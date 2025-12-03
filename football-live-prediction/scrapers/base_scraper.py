"""
Base Scraper - Classe de base pour tous les scrapers
Inclut: gestion d'erreurs, retry, rate limiting, logging
"""
import time
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config
from utils.logger import get_logger


class BaseScraper(ABC):
    """Classe de base abstraite pour tous les scrapers"""
    
    def __init__(self):
        """Initialise le scraper avec configuration et logger"""
        self.config = get_config()
        self.logger = get_logger()
        
        # Configuration scraping
        self.timeout = self.config.get("soccerstats.scraping.timeout", 30)
        self.retry_attempts = self.config.get("soccerstats.scraping.retry_attempts", 3)
        self.rate_limit_delay = self.config.get("soccerstats.scraping.rate_limit_delay", 1.5)
        
        # Headers - Simule un vrai navigateur
        self.headers = {
            'User-Agent': self.config.get("soccerstats.scraping.user_agent"),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            # ❌ RETIRER Accept-Encoding pour éviter compression gzip
            # 'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Session pour réutiliser connexions
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Désactiver les proxies (éviter les erreurs 403)
        self.session.trust_env = False

        # Compteur de requêtes (pour rate limiting)
        self.request_count = 0
        self.last_request_time = 0
        
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    def _rate_limit(self):
        """Applique le rate limiting entre les requêtes"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError)),
        reraise=True
    )
    def fetch_page(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """
        Récupère une page avec retry automatique
        
        Args:
            url: URL à récupérer
            params: Paramètres GET optionnels
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: Si la requête échoue après tous les retries
        """
        self._rate_limit()
        
        self.logger.debug(f"Fetching: {url}")
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            self.logger.debug(f"Success: {url} (Status: {response.status_code})")
            
            # Sauvegarder HTML si debug mode
            if self.config.get("development.save_html_responses", False):
                self._save_debug_html(url, response.text)
            
            return response
            
        except requests.HTTPError as e:
            self.logger.error(f"HTTP Error {e.response.status_code}: {url}")
            raise
        except requests.Timeout:
            self.logger.error(f"Timeout error: {url}")
            raise
        except requests.RequestException as e:
            self.logger.error(f"Request error: {url} - {e}")
            raise
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML avec BeautifulSoup
        
        Args:
            html_content: Contenu HTML brut
            
        Returns:
            BeautifulSoup object
        """
        # ✅ UTILISER LXML (comme dans les anciens scripts qui fonctionnent)
        return BeautifulSoup(html_content, 'lxml')
    
    def _save_debug_html(self, url: str, html_content: str):
        """
        Sauvegarde le HTML pour debug
        
        Args:
            url: URL source
            html_content: Contenu HTML
        """
        try:
            # Créer nom de fichier safe
            safe_filename = "".join(c if c.isalnum() else "_" for c in url)
            timestamp = int(time.time())
            filename = f"{safe_filename}_{timestamp}.html"
            
            debug_dir = self.config.get_data_directory("logs") / "html_debug"
            debug_dir.mkdir(exist_ok=True)
            
            filepath = debug_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.debug(f"HTML saved: {filepath}")
        except Exception as e:
            self.logger.warning(f"Failed to save debug HTML: {e}")
    
    def validate_response(self, response: requests.Response) -> bool:
        """
        Valide que la réponse est correcte
        
        Args:
            response: Response object à valider
            
        Returns:
            True si valide, False sinon
        """
        # Vérifier status code
        if response.status_code != 200:
            self.logger.warning(f"Invalid status code: {response.status_code}")
            return False
        
        # Vérifier que le contenu n'est pas vide
        if not response.text or len(response.text) < 100:
            self.logger.warning("Response content too short or empty")
            return False
        
        # Vérifier qu'on n'a pas une vraie page d'erreur (404, 500, etc.)
        # CORRECTION: Ne chercher que dans le titre et les h1
        soup = self.parse_html(response.text)
        title = soup.find('title')
        h1 = soup.find('h1')
        
        if title and any(word in title.get_text().lower() for word in ['404', 'not found', 'error 500', 'access denied']):
            self.logger.warning("Error page detected in title")
            return False
        
        if h1 and any(word in h1.get_text().lower() for word in ['404', 'not found', 'error', 'access denied']):
            self.logger.warning("Error page detected in h1")
            return False
        
        return True
    
    def extract_table(self, soup: BeautifulSoup, table_selector: str) -> Optional[BeautifulSoup]:
        """
        Extrait une table HTML
        
        Args:
            soup: BeautifulSoup object
            table_selector: Sélecteur CSS pour la table
            
        Returns:
            Table element ou None
        """
        table = soup.select_one(table_selector)
        
        if not table:
            self.logger.warning(f"Table not found: {table_selector}")
            return None
        
        return table
    
    def cleanup(self):
        """Nettoie les ressources"""
        if hasattr(self, 'session'):
            self.session.close()
            self.logger.debug("Session closed")
    
    def __del__(self):
        """Destructeur - nettoie les ressources"""
        self.cleanup()
    
    @abstractmethod
    def scrape(self, *args, **kwargs):
        """
        Méthode abstraite à implémenter par les classes filles
        
        Chaque scraper doit implémenter sa propre logique de scraping
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(requests={self.request_count})"


# Exemple d'utilisation
if __name__ == "__main__":
    # Test de la classe de base avec une classe concrète simple
    class TestScraper(BaseScraper):
        """Scraper de test"""
        
        def scrape(self, url: str):
            """Implémentation simple pour test"""
            response = self.fetch_page(url)
            if self.validate_response(response):
                soup = self.parse_html(response.text)
                title = soup.find('title')
                return title.text if title else "No title"
            return None
    
    # Test
    scraper = TestScraper()
    
    try:
        result = scraper.scrape("https://www.soccerstats.com")
        print(f"\n✅ Test réussi!")
        print(f"Titre de la page: {result}")
        print(f"Nombre de requêtes: {scraper.request_count}")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        scraper.cleanup()
