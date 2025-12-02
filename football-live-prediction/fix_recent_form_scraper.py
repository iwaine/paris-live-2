"""Correction du scraper pour utiliser formtable.asp"""

with open('scrapers/soccerstats_historical.py', 'r') as f:
    content = f.read()

# Trouver et remplacer la méthode scrape_recent_form
old_method_start = "    def scrape_recent_form(self, team_name: str, league_code: str, venue: str = 'home', last_n: int = 5) -> Dict:"
old_method_end = "            return None\n"

# Nouvelle méthode optimisée
new_method = '''    def scrape_recent_form(self, team_name: str, league_code: str, venue: str = 'home', last_n: int = 5) -> Dict:
        """
        Scrape la forme récente depuis formtable.asp
        
        Args:
            team_name: Nom de l'équipe
            league_code: Code de la ligue
            venue: 'home' ou 'away'
            last_n: Nombre de matchs (4 ou 8)
        """
        logger.info(f"Scraping recent form: {team_name} ({venue}, last {last_n})")
        
        # URL de la page forme
        url = f"https://www.soccerstats.com/formtable.asp?league={league_code}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher la section appropriée
            if venue == 'home':
                section_title = f"Form: Last {last_n} matches (AT HOME)"
            else:
                section_title = f"Form: Last {last_n} matches (AWAY)"
            
            # Trouver le h2 avec ce titre
            h2_section = soup.find('h2', string=re.compile(section_title, re.IGNORECASE))
            
            if not h2_section:
                logger.warning(f"Section '{section_title}' not found")
                return None
            
            # Trouver le tableau juste après
            table = h2_section.find_next('table', {'id': 'btable'})
            
            if not table:
                logger.warning(f"Table not found after section '{section_title}'")
                return None
            
            # Chercher la ligne de l'équipe
            rows = table.find_all('tr', {'class': 'odd'})
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) < 8:
                    continue
                
                # La 2ème colonne contient le nom de l'équipe
                team_cell = cells[1]
                team_link = team_cell.find('a')
                
                if team_link:
                    team_text = team_link.get_text(strip=True)
                else:
                    team_text = team_cell.get_text(strip=True)
                
                # Vérifier si c'est notre équipe
                if team_text == team_name:
                    # Extraire les données
                    gp = int(cells[2].get_text(strip=True))  # Games Played
                    gf = int(cells[6].get_text(strip=True))  # Goals For
                    ga = int(cells[7].get_text(strip=True))  # Goals Against
                    
                    avg_scored = round(gf / gp, 2) if gp > 0 else 0
                    avg_conceded = round(ga / gp, 2) if gp > 0 else 0
                    
                    stats = {
                        'matches_analyzed': gp,
                        'total_scored': gf,
                        'total_conceded': ga,
                        'avg_scored': avg_scored,
                        'avg_conceded': avg_conceded
                    }
                    
                    logger.success(f"Recent form: {gp} matches, avg {avg_scored} scored")
                    return stats
            
            logger.warning(f"Team '{team_name}' not found in {venue} form table")
            return None
            
        except Exception as e:
            logger.error(f"Error scraping recent form for {team_name}: {e}")
            return None
'''

# Trouver où commence l'ancienne méthode
start_idx = content.find(old_method_start)

if start_idx == -1:
    print("❌ Méthode scrape_recent_form non trouvée")
    exit(1)

# Trouver où elle se termine (prochaine méthode def ou fin de classe)
end_search = content[start_idx + len(old_method_start):]
next_method = end_search.find("\n    def ")

if next_method == -1:
    # Pas de méthode suivante, chercher fin de classe
    next_method = end_search.find("\n\nclass ")
    if next_method == -1:
        next_method = len(end_search)

end_idx = start_idx + len(old_method_start) + next_method

# Remplacer
content = content[:start_idx] + new_method + content[end_idx:]

with open('scrapers/soccerstats_historical.py', 'w') as f:
    f.write(content)

print("✅ Scraper corrigé pour formtable.asp")
