#!/usr/bin/env python3
"""
SoccerStats Live Match Selector
Détecte les matchs en direct sur la page d'accueil SoccerStats
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re


def get_live_matches(index_url: str = "https://www.soccerstats.com", timeout: int = 30, debug: bool = False) -> List[Dict]:
    """
    Détecte les matchs en direct sur SoccerStats
    
    Args:
        index_url: URL de la page index
        timeout: Timeout en secondes
        debug: Afficher les détails
    
    Returns:
        Liste de matchs avec {url, minute, snippet}
    """
    
    try:
        response = requests.get(index_url, timeout=timeout)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"Erreur fetch {index_url}: {e}")
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    matches = []
    
    # Stratégie 1: Chercher dans table#btable (priorité)
    btable = soup.find('table', {'id': 'btable'})
    if btable:
        for row in btable.find_all('tr')[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            
            # Chercher lien pmatch
            pmatch_link = row.find('a', href=re.compile(r'pmatch\.asp'))
            if not pmatch_link:
                continue
            
            url = pmatch_link.get('href', '')
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://www.soccerstats.com/' + url
            
            # Extraire minute (font rouge #C70039)
            minute_font = row.find('font', {'color': '#C70039'})
            minute_text = minute_font.get_text(strip=True) if minute_font else "?"
            
            # Parser minute
            minute_match = re.search(r'(\d+)[+\']?', minute_text)
            minute = int(minute_match.group(1)) if minute_match else 0
            
            if 0 <= minute <= 130:  # Validation
                snippet = row.get_text(strip=True)[:60]
                matches.append({
                    "url": url,
                    "minute": minute,
                    "snippet": snippet
                })
    
    # Stratégie 2: Fallback - scanner tous les liens pmatch
    if not matches:
        for link in soup.find_all('a', href=re.compile(r'pmatch\.asp')):
            url = link.get('href', '')
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://www.soccerstats.com/' + url
            
            # Chercher minute dans le contexte proche
            ancestor = link.find_parent(['tr', 'td', 'p', 'li', 'div'])
            if ancestor:
                text = ancestor.get_text()
                minute_match = re.search(r"(\d+)['\+]?", text)
                minute = int(minute_match.group(1)) if minute_match else 0
                
                if 0 <= minute <= 130:
                    matches.append({
                        "url": url,
                        "minute": minute,
                        "snippet": text[:60]
                    })
    
    # Trier par minute (décroissant)
    matches = sorted(matches, key=lambda x: x['minute'], reverse=True)
    
    return matches


if __name__ == "__main__":
    # Liste des ligues à suivre
    LEAGUES_TO_FOLLOW = [
        "germany2", "england", "france", "italy", "spain", "netherlands", "portugal", "belgium"
    ]
    import sys
    matches = get_live_matches(debug=True)
    print(f"\n✅ {len(matches)} matchs détectés")
    count = 0
    for m in matches:
        # Filtrer par ligue suivie (présente dans l'URL)
        if any(ligue in m['url'] for ligue in LEAGUES_TO_FOLLOW):
            print(f"Min {m['minute']} | URL: {m['url']} | {m['snippet']}")
            count += 1
    print(f"\n✅ {count} matchs live dans les ligues suivies.")
