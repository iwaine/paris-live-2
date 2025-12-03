"""
Live Match Scraper pour SoccerStats.com
Extrait les données en temps réel d'un match
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, Optional
from datetime import datetime
from loguru import logger


class SoccerStatsLiveScraper:
    """Scraper pour matchs en direct sur SoccerStats.com"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        logger.info("SoccerStatsLiveScraper initialized")
    
    def scrape_live_match(self, match_url: str) -> Optional[Dict]:
        """Scrape les données live d'un match"""
        try:
            response = requests.get(match_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            match_data = {}
            
            # 1. ÉQUIPES (Nouvelle méthode basée sur balises précises)
            # Balise: <font style="color:blue;18px;bold">
            teams_fonts = []

            # Méthode 1: Chercher les fonts bleus avec taille 18px ou 28px (équipes)
            all_fonts = soup.find_all('font')
            for font in all_fonts:
                style = font.get('style', '')
                # Chercher fonts avec "blue" ou couleur bleue et taille >= 18px
                if ('blue' in style.lower() or '#' in style) and any(size in style for size in ['18px', '28px', '26px']):
                    text = font.get_text(strip=True)
                    if text and len(text) > 2 and not any(c.isdigit() for c in text):  # Pas de chiffres
                        teams_fonts.append(text)

            # Méthode 2: Fallback sur <h1> si pas trouvé
            if len(teams_fonts) >= 2:
                match_data['home_team'] = teams_fonts[0]
                match_data['away_team'] = teams_fonts[1]
                logger.info(f"Match: {match_data['home_team']} vs {match_data['away_team']}")
            else:
                h1 = soup.find('h1')
                if h1:
                    match_title = h1.get_text(strip=True)
                    teams = match_title.split(' vs ')
                    if len(teams) == 2:
                        match_data['home_team'] = teams[0].strip()
                        match_data['away_team'] = teams[1].strip()
                        logger.info(f"Match: {match_data['home_team']} vs {match_data['away_team']}")
            
            # 2. STATUT
            match_data['status'] = self._extract_status(soup)
            
            # 3. MINUTE
            match_data['current_minute'] = self._extract_minute(soup)
            
            # 4. SCORE
            match_data['score'] = self._extract_score(soup)
            
            # 5. STATS
            match_data['stats'] = self._extract_live_stats(soup)
            
            # 6. TIMESTAMP
            match_data['scraped_at'] = datetime.now().isoformat()
            
            minute_display = f"{match_data.get('current_minute')}" if match_data.get('current_minute') else 'N/A'
            logger.success(f"Live data scraped: {match_data.get('score', 'N/A')} @ {minute_display}'")
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error scraping live match: {e}")
            return None
    
    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match"""
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag:
                style_attr = font_tag.get('style', '')
                if '#87CEFA' in style_attr.upper():
                    status_text = font_tag.get_text(strip=True)
                    
                    if status_text == 'FT':
                        logger.info("Statut: FT")
                        return "FT"
                    elif status_text == 'HT':
                        logger.info("Statut: HT")
                        return "HT"
                    elif re.match(r'^\d+\'$', status_text):
                        logger.info(f"Statut: Live ({status_text})")
                        return "Live"
                    elif re.match(r'^\d+\s*min\.?$', status_text, re.IGNORECASE):
                        logger.info(f"Statut: Live ({status_text})")
                        return "Live"
        
        logger.warning("Statut: Unknown")
        return "Unknown"
    
    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle"""
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag:
                style_attr = font_tag.get('style', '')
                if '#87CEFA' in style_attr.upper():
                    status_text = font_tag.get_text(strip=True)
                    
                    # Format: 35'
                    match = re.match(r'^(\d+)\'$', status_text)
                    if match:
                        minute = int(match.group(1))
                        logger.info(f"Minute: {minute}'")
                        return minute
                    
                    # Format: 25 min.
                    match2 = re.match(r'^(\d+)\s*min\.?$', status_text, re.IGNORECASE)
                    if match2:
                        minute = int(match2.group(1))
                        logger.info(f"Minute: {minute}'")
                        return minute
        
        return None
    
    def _extract_score(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extrait le score
        Balise: <font style="color:#87CEFA;26px;bold"> ou <font style="color:#87CEFA;36px;bold">
        """
        # Méthode 1: Chercher font avec #87CEFA et taille 26px ou 36px (score)
        all_fonts = soup.find_all('font')
        for font in all_fonts:
            style = font.get('style', '')
            # Chercher #87CEFA avec taille 26px ou 36px
            if '#87CEFA' in style.upper() and any(size in style for size in ['26px', '36px']):
                text = font.get_text(strip=True)
                # Pattern score: "X - X" ou "X-X"
                match = re.match(r'^(\d+)\s*[-:]\s*(\d+)$', text)
                if match:
                    score = f"{match.group(1)}-{match.group(2)}"
                    logger.info(f"Score: {score}")
                    return score

        # Méthode 2: Fallback - recherche globale
        all_text = soup.get_text()
        scores = re.findall(r'\b(\d+)\s*[-:]\s*(\d+)\b', all_text)
        if scores:
            score = f"{scores[0][0]}-{scores[0][1]}"
            logger.info(f"Score (fallback): {score}")
            return score

        return None
    
    def _extract_live_stats(self, soup: BeautifulSoup) -> Dict:
        """Extrait les statistiques live"""
        stats_data = {}
        
        stat_tables = soup.find_all('table', {'bgcolor': '#cccccc', 'width': '99%'})
        
        for table in stat_tables:
            h3 = table.find('h3')
            if not h3:
                continue
            
            stat_name = h3.get_text(strip=True)
            value_row = table.find('tr', {'height': '24'})
            if not value_row:
                continue
            
            value_cells = value_row.find_all('td', {'width': '80'})
            
            if len(value_cells) >= 2:
                home_val = value_cells[0].get_text(strip=True)
                away_val = value_cells[1].get_text(strip=True)
                
                stats_data[stat_name] = {
                    'home': home_val,
                    'away': away_val
                }
        
        logger.info(f"Stats extracted: {len(stats_data)} categories")
        return stats_data
    
    def monitor_match(self, match_url: str, interval: int = 45, callback=None):
        """Surveille un match en continu"""
        logger.info(f"🔴 Surveillance démarrée (intervalle: {interval}s)")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"[Iteration {iteration}] Scraping...")
                
                match_data = self.scrape_live_match(match_url)
                
                if match_data:
                    if callback:
                        callback(match_data)
                    
                    if match_data.get('status') == 'FT':
                        logger.success("Match terminé (FT)")
                        break
                
                logger.info(f"Attente de {interval} secondes...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.warning("Surveillance interrompue")
        except Exception as e:
            logger.error(f"Erreur: {e}")


def test_live_scraper():
    """Test du scraper"""
    print("="*70)
    print("🧪 TEST DU LIVE SCRAPER")
    print("="*70)
    
    test_url = "https://www.soccerstats.com/pmatch.asp?league=georgia2&stats=264-8-1-2025"
    
    scraper = SoccerStatsLiveScraper()
    
    print("\n📊 Test 1: Scraping unique")
    print("-"*70)
    
    match_data = scraper.scrape_live_match(test_url)
    
    if match_data:
        print(f"\n✅ DONNÉES EXTRAITES:")
        print(f"  🏠 Domicile: {match_data.get('home_team', 'N/A')}")
        print(f"  ✈️  Extérieur: {match_data.get('away_team', 'N/A')}")
        print(f"  ⚽ Score: {match_data.get('score', 'N/A')}")
        print(f"  ⏱️  Minute: {match_data.get('current_minute', 'N/A')}")
        print(f"  📡 Statut: {match_data.get('status', 'N/A')}")
        
        stats = match_data.get('stats', {})
        if stats:
            print(f"\n📊 STATISTIQUES LIVE ({len(stats)} catégories):")
            for stat_name, values in stats.items():
                print(f"  {stat_name:25s}: {values['home']:6s} vs {values['away']:6s}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_live_scraper()
