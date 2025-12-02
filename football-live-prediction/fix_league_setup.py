"""Correction de setup_profiles_for_league pour utiliser la nouvelle API Home/Away"""

content = open('setup_profiles.py', 'r').read()

# Ancienne fonction qui appelle scrape_timing_stats (n'existe plus)
old_code = """def setup_profiles_for_league(scraper, analyzer, league_name: str, league_code: str):
    \"\"\"Setup profiles for all teams in a league\"\"\"
    try:
        logger.info(f"Setting up profiles for {league_name}")
        
        # Scrape timing stats for the league
        timing_data = scraper.scrape_timing_stats(league_code)"""

# Nouvelle fonction qui utilise la méthode correcte
new_code = """def setup_profiles_for_league(scraper, analyzer, league_name: str, league_code: str):
    \"\"\"Setup profiles for all teams in a league (Home/Away version)\"\"\"
    try:
        logger.info(f"Setting up profiles for {league_name}")
        
        # Scrape timing stats for ALL venues (Overall + Home + Away)
        timing_data = scraper.scrape_timing_stats_all_venues(league_code)"""

if old_code in content:
    content = content.replace(old_code, new_code)
    open('setup_profiles.py', 'w').write(content)
    print("✅ Fonction setup_profiles_for_league corrigée")
    print("   scrape_timing_stats() → scrape_timing_stats_all_venues()")
else:
    print("⚠️  Pattern non trouvé, affichage de la fonction actuelle...")
    # Trouver et afficher la fonction
    start = content.find("def setup_profiles_for_league")
    if start != -1:
        end = content.find("\ndef ", start + 10)
        print(content[start:end])
