"""Réécriture complète des méthodes _extract_status et _extract_minute"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    lines = f.readlines()

# Trouver les lignes des méthodes
status_start = None
status_end = None
minute_start = None
minute_end = None

for i, line in enumerate(lines):
    if 'def _extract_status(self' in line:
        status_start = i
    elif status_start and 'def _extract_minute(self' in line:
        status_end = i
        minute_start = i
    elif minute_start and line.strip().startswith('def ') and '_extract_minute' not in line:
        minute_end = i
        break

if not minute_end:
    minute_end = len(lines)

print(f"✅ Méthodes trouvées:")
print(f"   _extract_status: lignes {status_start+1}-{status_end}")
print(f"   _extract_minute: lignes {minute_start+1}-{minute_end}")

# Nouvelles méthodes
new_extract_status = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag:
                style_attr = font_tag.get('style', '')
                if '#87CEFA' in style_attr.upper():
                    status_text = font_tag.get_text(strip=True)
                    
                    if status_text == 'FT':
                        return "FT"
                    elif status_text == 'HT':
                        return "HT"
                    elif re.match(r'^\\d+\\'$', status_text):
                        return "Live"
                    elif re.match(r'^\\d+\\s*min\\.?$', status_text, re.IGNORECASE):
                        return "Live"
        
        return "Unknown"

'''

new_extract_minute = '''    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle du match"""
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font')
            if font_tag:
                style_attr = font_tag.get('style', '')
                if '#87CEFA' in style_attr.upper():
                    status_text = font_tag.get_text(strip=True)
                    
                    # Format: 35'
                    match = re.match(r'^(\\d+)\\'$', status_text)
                    if match:
                        return int(match.group(1))
                    
                    # Format: 25 min.
                    match2 = re.match(r'^(\\d+)\\s*min\\.?$', status_text, re.IGNORECASE)
                    if match2:
                        return int(match2.group(1))
        
        return None

'''

# Remplacer
new_lines = (
    lines[:status_start] +
    [new_extract_status] +
    [new_extract_minute] +
    lines[minute_end:]
)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Méthodes réécrites avec la logique testée")
