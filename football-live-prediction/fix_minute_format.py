"""Correction pour supporter le format '18 min.' en plus de '18''"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# Trouver et remplacer la méthode _extract_status
old_status = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        # Chercher <td colspan="2"> avec <font color=#87CEFA>
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag and 'color:#87CEFA' in str(font_tag.get('style', '')):
                status_text = font_tag.get_text(strip=True)
                
                if status_text == 'FT':
                    return "FT"
                elif status_text == 'HT':
                    return "HT"
                elif re.match(r'^\\d+\\'$', status_text):
                    return "Live"
        
        # Fallback: chercher "In-play match stats"
        if soup.find(string=re.compile('In-play match stats', re.IGNORECASE)):
            return "Live"
        
        return "Unknown"'''

new_status = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        # Chercher <td colspan="2"> avec <font color=#87CEFA>
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag and 'color:#87CEFA' in str(font_tag.get('style', '')):
                status_text = font_tag.get_text(strip=True)
                
                if status_text == 'FT':
                    return "FT"
                elif status_text == 'HT':
                    return "HT"
                elif re.match(r'^\\d+\\'$', status_text):  # Format: 35'
                    return "Live"
                elif re.match(r'^\\d+\\s*min\\.?$', status_text, re.IGNORECASE):  # Format: 18 min.
                    return "Live"
        
        # Fallback: chercher "In-play match stats"
        if soup.find(string=re.compile('In-play match stats', re.IGNORECASE)):
            return "Live"
        
        return "Unknown"'''

content = content.replace(old_status, new_status)

# Trouver et remplacer la méthode _extract_minute
old_minute = '''    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle du match"""
        # Chercher <td colspan="2"> avec <font color=#87CEFA>
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag and 'color:#87CEFA' in str(font_tag.get('style', '')):
                status_text = font_tag.get_text(strip=True)
                
                # Format: 35'
                match = re.match(r'^(\\d+)\\'$', status_text)
                if match:
                    return int(match.group(1))
        
        return None'''

new_minute = '''    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle du match"""
        # Chercher <td colspan="2"> avec <font color=#87CEFA>
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag and 'color:#87CEFA' in str(font_tag.get('style', '')):
                status_text = font_tag.get_text(strip=True)
                
                # Format: 35' OU 18 min.
                match = re.match(r'^(\\d+)\\'$', status_text)
                if match:
                    return int(match.group(1))
                
                match2 = re.match(r'^(\\d+)\\s*min\\.?$', status_text, re.IGNORECASE)
                if match2:
                    return int(match2.group(1))
        
        return None'''

content = content.replace(old_minute, new_minute)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.write(content)

print("✅ Format minute corrigé")
print("   → Support de '35'' (apostrophe)")
print("   → Support de '18 min.' (texte)")
