#!/usr/bin/env python3
"""
TEST SCRAPER - SoccerStats Live Match Extraction
Tests tous les sélecteurs HTML sur une URL réelle
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import time

# Couleurs pour affichage terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def test_scraper(url: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Test le scraper sur une URL SoccerStats
    
    Args:
        url: URL du match
        verbose: Afficher les détails
    
    Returns:
        dict avec les données extraites + statut de chaque test
    """
    
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}🧪 TEST SCRAPER - {url}{RESET}")
    print(f"{BOLD}{'='*80}{RESET}\n")
    
    results = {
        'url': url,
        'tests': {}
    }
    
    try:
        # Télécharger la page
        print(f"{BLUE}[1/6]{RESET} Téléchargement de la page...")
        headers = {"User-Agent": "paris-live-bot/1.0"}
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        print(f"{GREEN}✓ Page téléchargée ({len(response.content)} bytes){RESET}\n")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # TEST 1: ÉQUIPES
        print(f"{BLUE}[2/6]{RESET} Extraction des équipes...")
        teams = extract_teams(soup)
        if teams.get('home') and teams.get('away'):
            print(f"{GREEN}✓ Home: {teams['home']}{RESET}")
            print(f"{GREEN}✓ Away: {teams['away']}{RESET}\n")
            results['tests']['teams'] = {'status': 'PASS', **teams}
        else:
            print(f"{RED}✗ Équipes non trouvées{RESET}\n")
            results['tests']['teams'] = {'status': 'FAIL', **teams}
        
        # TEST 2: SCORE
        print(f"{BLUE}[3/6]{RESET} Extraction du score...")
        score = extract_score(soup)
        if score:
            print(f"{GREEN}✓ Score: {score}{RESET}\n")
            results['tests']['score'] = {'status': 'PASS', 'score': score}
        else:
            print(f"{RED}✗ Score non trouvé{RESET}\n")
            results['tests']['score'] = {'status': 'FAIL', 'score': None}
        
        # Instantiate scraper to use the same extractors
        from soccerstats_live_scraper import SoccerStatsLiveScraper
        scraper = SoccerStatsLiveScraper()

        # TEST 3: MINUTE
        print(f"{BLUE}[4/6]{RESET} Extraction de la minute...")
        minute = scraper.extract_minute(soup)
        if minute:
            print(f"{GREEN}✓ Minute: {minute}{RESET}\n")
            results['tests']['minute'] = {'status': 'PASS', 'minute': minute}
        else:
            print(f"{YELLOW}⚠ Minute non trouvée (match peut être terminé){RESET}\n")
            results['tests']['minute'] = {'status': 'WARN', 'minute': None}
        
        # TEST 4: POSSESSION
        print(f"{BLUE}[5/6]{RESET} Extraction de la possession...")
        poss = scraper.extract_stat(soup, 'Possession')
        possession = {'home': poss[0] if poss and poss[0] else None, 'away': poss[1] if poss and poss[1] else None}
        if possession.get('home') and possession.get('away'):
            print(f"{GREEN}✓ Possession Home: {possession['home']}{RESET}")
            print(f"{GREEN}✓ Possession Away: {possession['away']}{RESET}\n")
            results['tests']['possession'] = {'status': 'PASS', **possession}
        else:
            print(f"{RED}✗ Possession non trouvée{RESET}\n")
            results['tests']['possession'] = {'status': 'FAIL', **possession}
        
        # TEST 5: CORNERS
        print(f"{BLUE}[6/6]{RESET} Extraction des corners...")
        cor = scraper.extract_stat(soup, 'Corners')
        corners = {'home': cor[0] if cor and cor[0] else None, 'away': cor[1] if cor and cor[1] else None}
        if corners.get('home') and corners.get('away'):
            print(f"{GREEN}✓ Corners Home: {corners['home']}{RESET}")
            print(f"{GREEN}✓ Corners Away: {corners['away']}{RESET}\n")
            results['tests']['corners'] = {'status': 'PASS', **corners}
        else:
            print(f"{RED}✗ Corners non trouvés{RESET}\n")
            results['tests']['corners'] = {'status': 'FAIL', **corners}
        
        # RÉSUMÉ
        print(f"{BOLD}{'='*80}{RESET}")
        print(f"{BOLD}📊 RÉSUMÉ DES TESTS{RESET}")
        print(f"{BOLD}{'='*80}{RESET}\n")
        
        pass_count = sum(1 for t in results['tests'].values() if t['status'] == 'PASS')
        warn_count = sum(1 for t in results['tests'].values() if t['status'] == 'WARN')
        fail_count = sum(1 for t in results['tests'].values() if t['status'] == 'FAIL')
        
        for test_name, test_result in results['tests'].items():
            status = test_result['status']
            if status == 'PASS':
                symbol = f"{GREEN}✓{RESET}"
            elif status == 'WARN':
                symbol = f"{YELLOW}⚠{RESET}"
            else:
                symbol = f"{RED}✗{RESET}"
            print(f"{symbol} {test_name.upper():15} {status}")
        
        print(f"\n{BOLD}Résultat: {GREEN}{pass_count} OK{RESET} | {YELLOW}{warn_count} WARN{RESET} | {RED}{fail_count} FAIL{RESET}\n")
        
        results['summary'] = {
            'passed': pass_count,
            'warned': warn_count,
            'failed': fail_count,
            'total': len(results['tests'])
        }
        
    except Exception as e:
        print(f"{RED}✗ ERREUR: {e}{RESET}\n")
        results['error'] = str(e)
    
    return results


def extract_teams(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    """Extrait Home Team et Away Team"""
    try:
        # Méthode 1: Chercher les <font> bleus 18px (équipes)
        fonts_blue = soup.find_all('font', 
                                   style=lambda s: s and 'color:blue' in s and '18px' in s)
        
        if len(fonts_blue) >= 2:
            # Les deux premières occurrences sont les équipes
            home = fonts_blue[0].get_text(strip=True)
            away = fonts_blue[1].get_text(strip=True)
            
            # Vérifier que ce ne sont pas des doublons
            if home and away and home != away:
                return {'home': home, 'away': away}
    except Exception as e:
        pass
    
    return {'home': None, 'away': None}


def extract_score(soup: BeautifulSoup) -> Optional[str]:
    """Extrait le score (ex: "2:1")"""
    try:
        # Méthode 1: Chercher font avec style #87CEFA (couleur du score)
        score_font = soup.find('font', 
                              style=lambda s: s and '#87CEFA' in s and '26px' in s)
        if score_font:
            return score_font.get_text(strip=True)
    except:
        pass
    
    # Méthode 2: Regex
    try:
        m = re.search(r'(\d+\s*:\s*\d+)', soup.get_text())
        if m:
            return m.group(1).replace(' ', '')
    except:
        pass
    
    return None


def extract_minute(soup: BeautifulSoup) -> Optional[str]:
    """Extrait la minute du match"""
    try:
        html_text = soup.get_text()
        m = re.search(r'(\d{1,2})\s*min\.?', html_text, re.IGNORECASE)
        if m:
            return m.group(1)
    except:
        pass
    return None


def extract_stat(soup: BeautifulSoup, stat_name: str) -> Dict[str, Optional[str]]:
    """
    Extrait une statistique (Possession, Corners, Shots, etc.)
    
    Args:
        soup: BeautifulSoup object
        stat_name: Nom de la stat (ex: "Possession")
    
    Returns:
        {'home': value, 'away': value}
    """
    try:
        h3 = soup.find('h3', string=re.compile(stat_name, re.IGNORECASE))
        if h3:
            parent_table = h3.find_parent('table')
            if parent_table:
                tds = parent_table.find_all('td', width='80')
                if len(tds) >= 2:
                    home = tds[0].get_text(strip=True)
                    away = tds[1].get_text(strip=True)
                    return {'home': home, 'away': away}
    except Exception as e:
        pass
    
    return {'home': None, 'away': None}


def run_tests():
    """Lance les tests sur plusieurs URLs"""
    
    # URLs de test (différentes ligues)
    test_urls = [
        'https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026',
        'https://www.soccerstats.com/pmatch.asp?league=spain&stats=82-1-13-7644',
        'https://www.soccerstats.com/pmatch.asp?league=england&stats=82-1-1-1001',
    ]
    
    print(f"\n{BOLD}{YELLOW}{'#'*80}{RESET}")
    print(f"{BOLD}{YELLOW}# TEST SCRAPER - SoccerStats Live Match Extraction{RESET}")
    print(f"{BOLD}{YELLOW}{'#'*80}{RESET}\n")
    
    all_results = []
    
    for i, url in enumerate(test_urls, 1):
        result = test_scraper(url, verbose=True)
        all_results.append(result)
        
        if i < len(test_urls):
            print(f"{YELLOW}Attente 3s avant prochain test (respect robots.txt)...{RESET}\n")
            time.sleep(3)
    
    # RAPPORT FINAL
    print(f"\n{BOLD}{YELLOW}{'#'*80}{RESET}")
    print(f"{BOLD}{YELLOW}# RAPPORT FINAL{RESET}")
    print(f"{BOLD}{YELLOW}{'#'*80}{RESET}\n")
    
    for result in all_results:
        if 'error' in result:
            print(f"{RED}✗ {result['url']}: ERREUR - {result['error']}{RESET}")
        else:
            summary = result['summary']
            print(f"{GREEN}✓ {result['url']}{RESET}")
            print(f"   → {summary['passed']}/{summary['total']} tests réussis")
    
    return all_results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # Test une URL spécifique
        url = sys.argv[1]
        result = test_scraper(url)
    else:
        # Tests par défaut
        results = run_tests()
