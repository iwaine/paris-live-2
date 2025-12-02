"""Correction des derniers problèmes"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# 1. Corriger l'affichage de la minute dans le log
content = content.replace(
    "logger.success(f\"Live data scraped: {match_data.get('score', 'N/A')} @ {match_data.get('current_minute', 'N/A')}'\")",
    "minute_display = f\"{match_data.get('current_minute')}'\" if match_data.get('current_minute') else 'N/A'\n            logger.success(f\"Live data scraped: {match_data.get('score', 'N/A')} @ {minute_display}\")"
)

# 2. Remettre l'ancienne extraction des stats (qui marchait)
old_stats_extract = '''        # Trouver tous les tableaux de stats (bgcolor="#cccccc", width="99%")
        stat_tables = soup.find_all('table', {'bgcolor': '#cccccc', 'width': '99%'})
        
        for table in stat_tables:
            # Trouver le nom de la stat (H3)
            h3 = table.find('h3')
            if not h3:
                continue
            
            stat_name = h3.get_text(strip=True)
            
            # Trouver la ligne avec les valeurs (height="24")
            value_row = table.find('tr', {'height': '24'})
            if not value_row:
                continue
            
            # Extraire les cellules avec width="80"
            value_cells = value_row.find_all('td', {'width': '80'})
            
            if len(value_cells) >= 2:
                home_val = value_cells[0].get_text(strip=True)
                away_val = value_cells[1].get_text(strip=True)
                
                stats_data[stat_name] = {
                    'home': home_val,
                    'away': away_val
                }'''

# Vérifier si cette partie existe encore
if old_stats_extract not in content:
    print("⚠️  Méthode d'extraction des stats modifiée, restauration...")
    
    # Trouver la méthode _extract_live_stats et la remplacer complètement
    import re
    
    # Nouvelle méthode complète
    new_stats_method = '''    def _extract_live_stats(self, soup: BeautifulSoup) -> Dict:
        """
        Extrait les statistiques live du match
        
        Returns:
            Dict avec toutes les stats (Possession, Corners, Shots, etc.)
        """
        stats_data = {}
        
        # Trouver tous les tableaux de stats (bgcolor="#cccccc", width="99%")
        stat_tables = soup.find_all('table', {'bgcolor': '#cccccc', 'width': '99%'})
        
        for table in stat_tables:
            # Trouver le nom de la stat (H3)
            h3 = table.find('h3')
            if not h3:
                continue
            
            stat_name = h3.get_text(strip=True)
            
            # Trouver la ligne avec les valeurs (height="24")
            value_row = table.find('tr', {'height': '24'})
            if not value_row:
                continue
            
            # Extraire les cellules avec width="80"
            value_cells = value_row.find_all('td', {'width': '80'})
            
            if len(value_cells) >= 2:
                home_val = value_cells[0].get_text(strip=True)
                away_val = value_cells[1].get_text(strip=True)
                
                stats_data[stat_name] = {
                    'home': home_val,
                    'away': away_val
                }
        
        logger.info(f"Stats extracted: {len(stats_data)} categories")
        
        return stats_data
'''
    
    # Trouver et remplacer
    pattern = r'    def _extract_live_stats\(self, soup: BeautifulSoup\) -> Dict:.*?(?=\n    def |\nclass |\nif __name__|$)'
    content = re.sub(pattern, new_stats_method, content, flags=re.DOTALL)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.write(content)

print("✅ Corrections finales appliquées")
print("   1. Affichage minute corrigé (None' → N/A)")
print("   2. Extraction stats restaurée")
