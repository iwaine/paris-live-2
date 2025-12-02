"""Correction précise de setup_profiles_for_league"""

with open('setup_profiles.py', 'r') as f:
    content = f.read()

# Remplacer l'ancien appel par le nouveau
old_line = "        timing_df = scraper.scrape_timing_stats(league_code)"
new_line = "        timing_data = scraper.scrape_timing_stats_all_venues(league_code)"

if old_line in content:
    content = content.replace(old_line, new_line)
    print("✅ Ligne corrigée:")
    print(f"   AVANT: {old_line.strip()}")
    print(f"   APRÈS: {new_line.strip()}")
else:
    print("❌ Ligne non trouvée, recherche alternative...")
    print("Recherche: 'scrape_timing_stats(league_code)'")

# Correction supplémentaire: timing_df → timing_data
old_check = "        if timing_df is None or timing_df.empty:"
new_check = "        if timing_data is None:"

if old_check in content:
    content = content.replace(old_check, new_check)
    print("✅ Vérification corrigée")

# Correction: Extraire les équipes depuis timing_data (dict) au lieu de DataFrame
old_extract = """        # Extraire les noms d'équipes (première colonne)
        team_col = timing_df.columns[0]
        teams = timing_df[team_col].unique()"""

new_extract = """        # Extraire les noms d'équipes depuis Overall
        if 'overall' not in timing_data or not timing_data['overall']:
            logger.warning(f"No overall data for {league_name}")
            return profiles
        teams = list(timing_data['overall'].keys())"""

if old_extract in content:
    content = content.replace(old_extract, new_extract)
    print("✅ Extraction équipes corrigée (DataFrame → Dict)")
else:
    print("⚠️  Extraction non trouvée (peut-être déjà corrigée)")

with open('setup_profiles.py', 'w') as f:
    f.write(content)

print("\n✅ Fichier setup_profiles.py corrigé")
print("   scrape_timing_stats() → scrape_timing_stats_all_venues()")
print("   timing_df → timing_data (dict avec overall/home/away)")
