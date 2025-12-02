"""Extraction du tableau de statistiques live"""
from bs4 import BeautifulSoup
import re

with open('live_match_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("="*70)
print("📊 EXTRACTION TABLEAU STATISTIQUES LIVE")
print("="*70)

# Chercher "Possession" comme point d'ancrage
possession_elem = soup.find(string=re.compile('Possession', re.IGNORECASE))

if possession_elem:
    print("\n✅ Tableau de stats trouvé!")
    
    # Remonter au tableau parent
    table = possession_elem.find_parent('table')
    
    if table:
        print(f"\n📋 Structure du tableau:")
        print(f"  ID: {table.get('id', 'N/A')}")
        print(f"  Class: {table.get('class', 'N/A')}")
        
        # Extraire toutes les lignes
        rows = table.find_all('tr')
        print(f"\n📊 Nombre de lignes: {len(rows)}")
        
        stats_data = {}
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            
            if len(cells) >= 3:  # Format: [Home Value] [Stat Name] [Away Value]
                home_val = cells[0].get_text(strip=True)
                stat_name = cells[1].get_text(strip=True)
                away_val = cells[2].get_text(strip=True)
                
                # Stocker si c'est une stat importante
                if stat_name and (home_val or away_val):
                    stats_data[stat_name] = {
                        'home': home_val,
                        'away': away_val
                    }
                    print(f"  {stat_name:25s} | {home_val:6s} vs {away_val:6s}")
        
        # Afficher le résumé structuré
        print("\n" + "="*70)
        print("✅ STATS EXTRAITES (format JSON):")
        print("="*70)
        
        import json
        print(json.dumps(stats_data, indent=2, ensure_ascii=False))
        
        # Identifier les stats critiques pour prédictions
        print("\n" + "="*70)
        print("🎯 STATS CRITIQUES POUR PRÉDICTIONS:")
        print("="*70)
        
        critical_stats = [
            'Possession',
            'Total shots',
            'Shots on target', 
            'Corners',
            'Attacks',
            'Dangerous attacks'
        ]
        
        for stat in critical_stats:
            if stat in stats_data:
                home = stats_data[stat]['home']
                away = stats_data[stat]['away']
                print(f"  ✅ {stat:25s}: {home} (H) vs {away} (A)")
            else:
                print(f"  ❌ {stat:25s}: NON TROUVÉ")
        
    else:
        print("❌ Impossible de trouver le tableau parent")
else:
    print("❌ 'Possession' non trouvé, recherche alternative...")
    
    # Chercher tous les tableaux
    tables = soup.find_all('table')
    print(f"\n🔍 Analyse de {len(tables)} tableaux...")
    
    for i, table in enumerate(tables):
        text = table.get_text()
        if 'Possession' in text or 'shots' in text.lower():
            print(f"\n📋 Tableau {i+1} contient des stats!")
            rows = table.find_all('tr')[:10]
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    row_text = " | ".join([c.get_text(strip=True) for c in cells])
                    print(f"  {row_text[:70]}")

print("\n" + "="*70)
