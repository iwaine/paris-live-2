import re

with open('scrapers/soccerstats_live.py', 'r') as f:
    lines = f.readlines()

# Trouver la ligne de la méthode _extract_status
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'def _extract_status' in line:
        start_line = i
    if start_line is not None and i > start_line and line.strip().startswith('def '):
        end_line = i
        break

if start_line is None:
    print("❌ Méthode _extract_status non trouvée")
else:
    if end_line is None:
        end_line = len(lines)
    
    print(f"✅ Méthode trouvée lignes {start_line+1} à {end_line}")
    
    # Nouvelle méthode
    new_method = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        # 1. Chercher "In-play match stats" = match LIVE
        in_play = soup.find(string=re.compile('In-play match stats', re.IGNORECASE))
        if in_play:
            logger.info("Match LIVE détecté (In-play stats)")
            return "Live"
        
        # 2. Présence de stats = match en cours
        stat_tables = soup.find_all('table', {'bgcolor': '#cccccc', 'width': '99%'})
        if len(stat_tables) >= 3:
            logger.info("Match LIVE détecté (stats actives)")
            return "Live"
        
        # 3. Fallback
        all_text = soup.get_text()
        
        if re.search(r'\\bFT\\b.*\\d+\\s*-\\s*\\d+|Full\\s*Time', all_text, re.IGNORECASE):
            return "FT"
        elif re.search(r'\\bHT\\b.*\\d+\\s*-\\s*\\d+|Half\\s*Time', all_text, re.IGNORECASE):
            return "HT"
        else:
            return "Live"
    
'''
    
    # Remplacer
    new_lines = lines[:start_line] + [new_method] + lines[end_line:]
    
    with open('scrapers/soccerstats_live.py', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Méthode remplacée avec succès")
    print("\n🧪 Relance le test:")
    print("   python scrapers/soccerstats_live.py")
