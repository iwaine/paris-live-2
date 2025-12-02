"""Correction finale de l'extraction minute + statut"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# 1. CORRIGER _extract_status
old_status = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
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
            return "Live"'''

new_status = '''    def _extract_status(self, soup: BeautifulSoup) -> str:
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
                elif re.match(r'^\\d+\'$', status_text):  # Format: 35'
                    logger.info(f"Statut: Live (minute {status_text})")
                    return "Live"
        
        # Fallback si structure non trouvée
        logger.warning("Statut non détecté, fallback à Unknown")
        return "Unknown"'''

content = content.replace(old_status, new_status)

# 2. CORRIGER _extract_minute
old_minute = '''    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle du match"""
        all_text = soup.get_text()
        
        # Pattern 1: 45' ou 45 min
        patterns = [
            r"(\\d+)'",
            r"(\\d+)\\s*min",
            r"Minute\\s*:\\s*(\\d+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                # Prendre le plus petit nombre (éviter les grandes valeurs aberrantes)
                minutes = [int(m) for m in matches if int(m) <= 120]  # Max 120 min
                if minutes:
                    return min(minutes)
        
        return None'''

new_minute = '''    def _extract_minute(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait la minute actuelle du match"""
        # Chercher dans le <td colspan="2"> avec la minute
        status_cell = soup.find('td', {'colspan': '2', 'align': 'center'})
        
        if status_cell:
            font_tag = status_cell.find('font')
            if font_tag:
                status_text = font_tag.get_text(strip=True)
                
                # Format: 35'
                match = re.match(r'^(\\d+)\'$', status_text)
                if match:
                    minute = int(match.group(1))
                    logger.info(f"Minute extraite: {minute}'")
                    return minute
        
        # Fallback: chercher n'importe où
        all_text = soup.get_text()
        matches = re.findall(r'(\\d+)\'', all_text)
        if matches:
            minutes = [int(m) for m in matches if int(m) <= 120]
            if minutes:
                return min(minutes)
        
        return None'''

content = content.replace(old_minute, new_minute)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.write(content)

print("✅ Extraction minute + statut corrigée")
print("   → Cherche dans <td colspan='2'><font>...</font></td>")
print("   → FT = match terminé")
print("   → HT = mi-temps")
print("   → 35' = minute actuelle (Live)")
print("\n🧪 Teste maintenant avec un VRAI match live!")
