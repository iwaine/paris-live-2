#!/usr/bin/env python3
"""
Scraper automatique SoccerStats
Détecte tous les matchs live sur la page principale et extrait les stats live pour chaque match
"""
import requests
import re
import time
from bs4 import BeautifulSoup
from scrape_live_soccerstats import scrape_live_match, LiveMatchData

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
MAIN_URL = "https://www.soccerstats.com/"


def detect_live_matches():
    """Détecte tous les liens de matchs live sur la page principale"""
    response = requests.get(MAIN_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    all_match_links = soup.find_all('a', href=re.compile(r'pmatch\\.asp'))
    live_matches = []
    for link in all_match_links:
        href = link.get('href', '')
        parent = link.find_parent('tr')
        parent_text = parent.get_text(strip=True) if parent else ""
        # Cherche une minute ou indicateur live dans le <tr>
        if re.search(r"(\\d+)'", parent_text) or 'In-play' in parent_text or 'Live' in parent_text:
            live_matches.append({
                'url': f"https://www.soccerstats.com/{href}",
                'parent_text': parent_text
            })
    return live_matches


def main():
    print("\n============================")
    print("🔍 SCRAPING AUTOMATIQUE SOCCERSTATS")
    print("============================\n")
    live_matches = detect_live_matches()
    print(f"✅ {len(live_matches)} match(s) live détecté(s)\n")
    for i, match in enumerate(live_matches, 1):
        print(f"\n--- MATCH LIVE #{i} ---")
        print(f"URL: {match['url']}")
        print(f"Résumé: {match['parent_text']}")
        print("Extraction des stats...")
        data = scrape_live_match(match['url'])
        if data:
            print(f"✅ Stats extraites:")
            for key, value in data.to_dict().items():
                print(f"   {key:25} = {value}")
        else:
            print("❌ Échec extraction stats")
        time.sleep(2)  # Respect robots.txt

if __name__ == "__main__":
    main()
