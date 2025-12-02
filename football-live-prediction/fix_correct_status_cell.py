"""Correction pour trouver le BON td avec le statut"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# Remplacer la méthode _extract_status
old_method = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        # Chercher le <td colspan="2"> avec le statut
        status_cell = soup.find('td', {'colspan': '2', 'align': 'center'})
        
        if status_cell:
            font_tag = status_cell.find('font')
            if font_tag:
                status_text = font_tag.get_text(strip=True)
                
                if status_text == 'FT':
                    logger.info("Statut: FT (Full Time)")
                    return "FT"
                elif status_text == 'HT':
                    logger.info("Statut: HT (Half Time)")
                    return "HT"
                elif re.match(r'^\\d+\\'$', status_text):  # Format: 35'
                    logger.info(f"Statut: Live (minute {status_text})")
                    return "Live"
        
        # Fallback si structure non trouvée
        logger.warning("Statut non détecté, fallback à Unknown")
        return "Unknown"'''

new_method = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut du match (Live, HT, FT)"""
        # Chercher TOUS les <td colspan="2" align="center">
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font', {'style': re.compile('color:#87CEFA', re.IGNORECASE)})
            if font_tag:
                status_text = font_tag.get_text(strip=True)
                
                if status_text == 'FT':
                    logger.info("Statut: FT (Full Time)")
                    return "FT"
                elif status_text == 'HT':
                    logger.info("Statut: HT (Half Time)")
                    return "HT"
                elif re.match(r'^\\d+\\'$', status_text):  # Format: 35'
                    logger.info(f"Statut: Live @ {status_text}")
                    return "Live"
        
        # Fallback
        logger.warning("Statut non détecté")
        return "Unknown"'''

content = content.replace(old_method, new_method)

# Remplacer aussi _extract_minute
old_minute_method = '''    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle du match"""
        # Chercher dans le <td colspan="2"> avec la minute
        status_cell = soup.find('td', {'colspan': '2', 'align': 'center'})
        
        if status_cell:
            font_tag = status_cell.find('font')
            if font_tag:
                status_text = font_tag.get_text(strip=True)
                
                # Format: 35'
                match = re.match(r'^(\\d+)\\'$', status_text)
                if match:
                    minute = int(match.group(1))
                    logger.info(f"Minute extraite: {minute}'")
                    return minute
        
        # Fallback: chercher n'importe où
        all_text = soup.get_text()
        matches = re.findall(r'(\\d+)\\'', all_text)
        if matches:
            minutes = [int(m) for m in matches if int(m) <= 120]
            if minutes:
                return min(minutes)
        
        return None'''

new_minute_method = '''    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle du match"""
        # Chercher TOUS les <td colspan="2" align="center"> avec font couleur bleue
        status_cells = soup.find_all('td', {'colspan': '2', 'align': 'center'})
        
        for cell in status_cells:
            font_tag = cell.find('font', {'style': re.compile('color:#87CEFA', re.IGNORECASE)})
            if font_tag:
                status_text = font_tag.get_text(strip=True)
                
                # Format: 35'
                match = re.match(r'^(\\d+)\\'$', status_text)
                if match:
                    minute = int(match.group(1))
                    logger.info(f"Minute extraite: {minute}'")
                    return minute
        
        # Si pas trouvé = match terminé
        return None'''

content = content.replace(old_minute_method, new_minute_method)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.write(content)

print("✅ Correction appliquée")
print("   → Cherche le <font style='color:#87CEFA'>")
print("   → Ignore les minutes dans le tableau des buts")
print("   → Si FT → minute = None")
