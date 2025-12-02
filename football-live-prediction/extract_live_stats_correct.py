"""Extraction correcte des stats live avec la vraie structure HTML"""
from bs4 import BeautifulSoup
import re

with open('live_match_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("="*70)
print("📊 EXTRACTION STATS LIVE - VERSION CORRIGÉE")
print("="*70)

# Chercher tous les tableaux avec bgcolor="#cccccc"
stat_tables = soup.find_all('table', {'bgcolor': '#cccccc', 'width': '99%'})

print(f"\n✅ Tableaux de stats trouvés: {len(stat_tables)}")

stats_data = {}

for table in stat_tables:
    # Trouver le H3 avec le nom de la stat
    h3 = table.find('h3')
    if not h3:
        continue
    
    stat_name = h3.get_text(strip=True)
    
    # Trouver la ligne avec les valeurs (height="24")
    value_row = table.find('tr', {'height': '24'})
    if not value_row:
        continue
    
    # Extraire les 2 cellules avec les valeurs (width="80")
    value_cells = value_row.find_all('td', {'width': '80'})
    
    if len(value_cells) >= 2:
        home_val = value_cells[0].get_text(strip=True)
        away_val = value_cells[1].get_text(strip=True)
        
        stats_data[stat_name] = {
            'home': home_val,
            'away': away_val
        }
        
        print(f"  ✅ {stat_name:25s}: {home_val:6s} (H) vs {away_val:6s} (A)")

print("\n" + "="*70)
print("📋 RÉSUMÉ JSON:")
print("="*70)

import json
print(json.dumps(stats_data, indent=2, ensure_ascii=False))

print("\n" + "="*70)
print("🎯 VÉRIFICATION STATS CRITIQUES:")
print("="*70)

critical_stats = [
    'Possession',
    'Total shots',
    'Shots on target',
    'Corners',
    'Attacks',
    'Dangerous attacks'
]

all_found = True
for stat in critical_stats:
    if stat in stats_data:
        print(f"  ✅ {stat}")
    else:
        print(f"  ❌ {stat} - MANQUANT")
        all_found = False

if all_found:
    print("\n🎉 TOUTES LES STATS CRITIQUES EXTRAITES !")
else:
    print("\n⚠️  Certaines stats manquent")

print("\n" + "="*70)
