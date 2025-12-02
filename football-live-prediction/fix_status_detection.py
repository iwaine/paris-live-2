"""Amélioration de la détection du statut du match"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# Remplacer la méthode _extract_status
old_method = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        all_text = soup.get_text()
        
        if re.search(r'\bFT\b|Full\s*Time|Terminé', all_text, re.IGNORECASE):
            return "FT"
        elif re.search(r'\bHT\b|Half\s*Time|Mi-temps', all_text, re.IGNORECASE):
            return "HT"
        elif re.search(r'\bLive\b|En\s*cours', all_text, re.IGNORECASE):
            return "Live"
        else:
            return "Unknown"'''

new_method = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        # 1. Chercher "In-play match stats" = match LIVE
        in_play = soup.find(string=re.compile('In-play match stats', re.IGNORECASE))
        if in_play:
            return "Live"
        
        # 2. Présence de stats = match en cours
        stat_tables = soup.find_all('table', {'bgcolor': '#cccccc', 'width': '99%'})
        if len(stat_tables) >= 3:
            return "Live"
        
        # 3. Fallback
        all_text = soup.get_text()
        
        if re.search(r'\bFT\b.*\d+\s*-\s*\d+|Full\s*Time', all_text, re.IGNORECASE):
            return "FT"
        elif re.search(r'\bHT\b.*\d+\s*-\s*\d+|Half\s*Time', all_text, re.IGNORECASE):
            return "HT"
        else:
            return "Live"'''

if old_method in content:
    content = content.replace(old_method, new_method)
    with open('scrapers/soccerstats_live.py', 'w') as f:
        f.write(content)
    print("✅ Statut corrigé")
else:
    print("❌ Non trouvé")
