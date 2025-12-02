"""Diagnostic complet: Espagne + analyse config.yaml"""
import requests
from bs4 import BeautifulSoup
import re
import yaml

print("\n" + "="*70)
print("🔍 DIAGNOSTIC COMPLET - ESPAGNE + CONFIG")
print("="*70 + "\n")

# 1. ANALYSER LA PAGE ESPAGNE
print("📊 PARTIE 1: ANALYSE PAGE ESPAGNE")
print("-"*70)

url = "https://www.soccerstats.com/timing.asp?league=spain"

try:
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Chercher tous les input radio avec name contenant GTS10
    all_inputs = soup.find_all('input', {'type': 'radio'})
    
    gts10_inputs = [inp for inp in all_inputs if inp.get('name') and 'GTS10' in inp.get('name')]
    
    if gts10_inputs:
        print(f"\n✅ Trouvé {len(gts10_inputs)} onglets GTS10:\n")
        
        for inp in gts10_inputs:
            input_id = inp.get('id', 'N/A')
            input_name = inp.get('name', 'N/A')
            
            # Trouver le label suivant
            label = inp.find_next_sibling('label')
            label_text = label.get_text(strip=True) if label else 'N/A'
            
            print(f"   ID: {input_id:25s} Name: {input_name:20s} → {label_text}")
    else:
        print("\n❌ Aucun onglet GTS10 trouvé!")
        
        # Chercher tous les inputs radio pour debug
        print("\n📋 Tous les inputs radio trouvés:")
        for inp in all_inputs[:10]:
            print(f"   ID: {inp.get('id', 'N/A'):25s} Name: {inp.get('name', 'N/A')}")
    
except Exception as e:
    print(f"\n❌ Erreur lors de l'analyse: {e}")

# 2. ANALYSER LE CONFIG.YAML
print("\n" + "="*70)
print("📋 PARTIE 2: ANALYSE CONFIG.YAML")
print("-"*70 + "\n")

try:
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    leagues = config.get('leagues', [])
    
    print(f"✅ {len(leagues)} ligues configurées\n")
    
    # Extraire les league codes
    league_codes = {}
    
    for league in leagues:
        name = league.get('name', 'Unknown')
        url = league.get('url', '')
        
        # Extraire le code de la ligue depuis l'URL
        match = re.search(r'league=([^&]+)', url)
        if match:
            code = match.group(1)
            league_codes[code] = name
    
    # Afficher les codes uniques
    unique_codes = sorted(set(league_codes.keys()))
    
    print("📌 Codes de ligues uniques trouvés:")
    print("-"*70)
    
    for code in unique_codes:
        # Trouver toutes les ligues avec ce code
        matching_leagues = [name for c, name in league_codes.items() if c == code]
        print(f"   {code:20s} → {matching_leagues[0]}")
    
    # Focus sur l'Espagne
    spain_leagues = [code for code in unique_codes if 'spain' in code.lower()]
    
    print("\n🇪🇸 Ligues espagnoles:")
    print("-"*70)
    for code in spain_leagues:
        matching = [name for c, name in league_codes.items() if c == code]
        for name in matching:
            print(f"   Code: {code:15s} → {name}")
    
except Exception as e:
    print(f"❌ Erreur lors de l'analyse du config: {e}")

# 3. MAPPING SUGGÉRÉ
print("\n" + "="*70)
print("💡 MAPPING SUGGÉRÉ POUR LE SCRAPER")
print("="*70 + "\n")

suggested_mapping = {
    'england': 'eng',
    'england2': 'eng2',
    'england3': 'eng3',
    'england4': 'eng4',
    'spain': 'spain',
    'spain2': 'spain2',
    'france': 'fra',
    'france2': 'fra2',
    'germany': 'ger',
    'germany2': 'ger2',
    'italy': 'ita',
    'portugal': 'por',
    'portugal2': 'por2'
}

print("league_prefix_map = {")
for code, prefix in suggested_mapping.items():
    print(f"    '{code}': '{prefix}',")
print("}")

print("\n" + "="*70)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*70 + "\n")
