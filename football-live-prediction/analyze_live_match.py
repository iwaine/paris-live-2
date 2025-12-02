"""Analyse d'un match en cours sur SoccerStats"""
import requests
from bs4 import BeautifulSoup
import json

url = "https://www.soccerstats.com/pmatch.asp?league=georgia2&stats=264-8-1-2025"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("="*70)
    print("🏆 ANALYSE DU MATCH LIVE")
    print("="*70)
    
    # 1. EXTRAIRE LES ÉQUIPES
    print("\n📋 ÉQUIPES:")
    # Chercher les noms d'équipes dans le titre ou h1/h2
    title = soup.find('title')
    if title:
        print(f"  Titre: {title.get_text(strip=True)}")
    
    h1 = soup.find('h1')
    if h1:
        print(f"  H1: {h1.get_text(strip=True)}")
    
    # 2. EXTRAIRE LE SCORE ACTUEL
    print("\n⚽ SCORE:")
    # Chercher les scores (patterns possibles)
    score_patterns = [
        soup.find('span', class_='score'),
        soup.find('div', class_='score'),
        soup.find_all('td', class_='score')
    ]
    
    for pattern in score_patterns:
        if pattern:
            print(f"  Score trouvé: {pattern}")
    
    # Recherche générique de scores (format X-X)
    import re
    all_text = soup.get_text()
    scores = re.findall(r'\b(\d+)\s*[-:]\s*(\d+)\b', all_text)
    if scores:
        print(f"  Scores détectés: {scores[:5]}")
    
    # 3. EXTRAIRE LA MINUTE ACTUELLE
    print("\n⏱️ MINUTE:")
    # Chercher "min", "'", ou patterns de temps
    time_patterns = [
        re.findall(r"(\d+)'", all_text),
        re.findall(r"(\d+)\s*min", all_text, re.IGNORECASE),
        re.findall(r"HT|FT|\d+:\d+", all_text)
    ]
    
    for pattern in time_patterns:
        if pattern:
            print(f"  Temps trouvé: {pattern[:5]}")
    
    # 4. EXTRAIRE LES STATS LIVE
    print("\n📊 STATISTIQUES LIVE:")
    
    # Chercher des tables avec stats
    tables = soup.find_all('table')
    print(f"  Nombre de tableaux: {len(tables)}")
    
    for i, table in enumerate(tables[:5]):
        print(f"\n  📋 TABLEAU {i+1}:")
        rows = table.find_all('tr')[:3]
        for row in rows:
            cols = row.find_all(['td', 'th'])
            if cols and len(cols) > 1:
                text = " | ".join([col.get_text(strip=True) for col in cols[:5]])
                if text.strip():
                    print(f"    {text[:80]}")
    
    # 5. CHERCHER DES STATS SPÉCIFIQUES
    print("\n🎯 RECHERCHE STATS CLÉS:")
    keywords = ['shots', 'tirs', 'possession', 'corners', 'fouls', 'yellow', 'red']
    
    for keyword in keywords:
        found = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
        if found:
            print(f"  • '{keyword}': {len(found)} occurrences")
            # Afficher contexte
            for item in found[:2]:
                parent = item.parent
                if parent:
                    print(f"      → {parent.get_text(strip=True)[:60]}")
    
    # 6. STRUCTURE HTML GLOBALE
    print("\n🔍 STRUCTURE HTML:")
    main_divs = soup.find_all('div', class_=True)[:10]
    print(f"  Classes div principales:")
    for div in main_divs:
        classes = ' '.join(div.get('class', []))
        if classes:
            print(f"    • {classes}")
    
    # 7. SAUVEGARDER POUR INSPECTION
    print("\n💾 SAUVEGARDE:")
    with open('live_match_sample.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("  ✅ Fichier sauvegardé: live_match_sample.html")
    
    # 8. EXTRAIRE LA STRUCTURE JSON (si disponible)
    print("\n🔍 RECHERCHE DONNÉES JSON:")
    scripts = soup.find_all('script')
    for i, script in enumerate(scripts):
        script_text = script.get_text()
        if 'json' in script_text.lower() or '{' in script_text:
            print(f"  Script {i+1}: {len(script_text)} caractères")
            if len(script_text) < 500:
                print(f"    Contenu: {script_text[:200]}")
    
    print("\n" + "="*70)
    print("✅ ANALYSE TERMINÉE")
    print("="*70)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
