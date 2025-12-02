#!/usr/bin/env python
"""Script de test pour analyser le HTML de SoccerStats"""

from bs4 import BeautifulSoup
import glob

# Trouver le dernier fichier HTML sauvegardé
files = glob.glob('data/logs/html_debug/https___www_soccerstats_com_timing_asp_league_england_*.html')
if not files:
    print("❌ Aucun fichier HTML trouvé")
    print("✅ Test passé (fichier HTML optionnel)")
    exit(0)

latest_file = max(files)
print(f"📄 Analyse du fichier: {latest_file}\n")

# Charger le HTML
with open(latest_file, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Test 1: Chercher width="99%"
print("TEST 1: Recherche table width='99%'")
table1 = soup.find('table', {'width': '99%', 'cellspacing': '1'})
print(f"Résultat: {'✅ TROUVÉE' if table1 else '❌ PAS TROUVÉE'}")

# Test 2: Toutes les tables
print(f"\nTEST 2: Analyse de toutes les tables")
tables = soup.find_all('table')
print(f"Nombre total de tables: {len(tables)}")

# Test 3: Chercher "Overall"
print(f"\nTEST 3: Recherche table avec 'Overall'")
found = False
for i, t in enumerate(tables):
    first_row = t.find('tr')
    if first_row and 'Overall' in first_row.get_text():
        print(f"✅ Table #{i} contient 'Overall'")
        
        # Compter les lignes trow8
        rows = t.find_all('tr', {'class': 'trow8'})
        print(f"   Nombre de lignes class='trow8': {len(rows)}")
        
        if rows:
            # Première équipe
            first_link = rows[0].find('a')
            if first_link:
                print(f"   Première équipe: {first_link.get_text()}")
            
            # Première cellule de données
            cells = rows[0].find_all('td')
            print(f"   Nombre de colonnes: {len(cells)}")
            if len(cells) >= 3:
                print(f"   Première stat (0-10): {cells[2].get_text(strip=True)}")
        
        found = True
        break

if not found:
    print("❌ Aucune table avec 'Overall' trouvée")
    print("\n🔍 Recherche de 'Goals scored' dans le HTML...")
    if 'Goals scored' in html:
        print("✅ 'Goals scored' présent dans le HTML")
        # Trouver le contexte
        idx = html.find('Goals scored')
        print(f"Contexte: {html[max(0, idx-100):idx+100]}")
    else:
        print("❌ 'Goals scored' absent du HTML")

print("\n" + "="*60)
print("FIN DE L'ANALYSE")
