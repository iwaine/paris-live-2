#!/usr/bin/env python3
"""
Debug: Analyser les stats disponibles sur une page pmatch.asp
"""

import sys
import requests
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print("Usage: python3 debug_stats.py <URL>")
    sys.exit(1)

url = sys.argv[1]

session = requests.Session()
session.trust_env = False
headers = {'User-Agent': 'Mozilla/5.0'}

response = session.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'lxml')

print("\n" + "="*80)
print(f"🔍 ANALYSE DES STATS: {url}")
print("="*80 + "\n")

# Chercher tous les <h3>
h3_elements = soup.find_all('h3')

print(f"📊 Trouvé {len(h3_elements)} éléments <h3>\n")

for i, h3 in enumerate(h3_elements, 1):
    stat_name = h3.get_text(strip=True)

    print(f"{i:2d}. <h3> '{stat_name}'")

    # Remonter à la table parente
    table = h3.find_parent('table')

    if table:
        # Chercher les <td width="80">
        td_cells = table.find_all('td', {'width': '80'})

        print(f"    Table parente trouvée: {len(td_cells)} <td width='80'>")

        if len(td_cells) >= 2:
            # Chercher <b> dans chaque td
            home_b = td_cells[0].find('b')
            away_b = td_cells[1].find('b')

            home_val = home_b.get_text(strip=True) if home_b else td_cells[0].get_text(strip=True)
            away_val = away_b.get_text(strip=True) if away_b else td_cells[1].get_text(strip=True)

            print(f"    Valeurs: Home='{home_val}' | Away='{away_val}'")
        else:
            print(f"    ⚠️  Pas assez de <td width='80'>")
    else:
        print(f"    ❌ Pas de table parente")

    print()

print("="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80 + "\n")
