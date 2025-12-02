"""Correction export Excel + ID onglets Espagne"""
from pathlib import Path

# 1. Corriger l'export Excel
setup_path = Path('setup_profiles.py')

with open(setup_path, 'r') as f:
    content = f.read()

# Remplacer la fonction export
old_export = '''            "Play Style": profile["play_style"]["summary"],'''
new_export = '''            "Play Style": profile.get("overall", {}).get("play_style", {}).get("summary", "N/A"),'''

content = content.replace(old_export, new_export)

# Corriger aussi danger_zones si nécessaire
old_danger = '''            "Danger Zones": len(profile["danger_zones"])'''
new_danger = '''            "Danger Zones": len(profile.get("overall", {}).get("danger_zones", []))'''

content = content.replace(old_danger, new_danger)

with open(setup_path, 'w') as f:
    f.write(content)

print("✅ Export Excel corrigé\n")

# 2. Corriger le mapping des préfixes de ligues
scraper_path = Path('scrapers/soccerstats_historical.py')

with open(scraper_path, 'r') as f:
    scraper_content = f.read()

old_mapping = '''            league_prefix_map = {
                'england': 'eng',
                'spain': 'esp',
                'france': 'fra',
                'italy': 'ita',
                'germany': 'ger'
            }'''

new_mapping = '''            league_prefix_map = {
                'england': 'eng',
                'spain': 'spain',
                'france': 'fra',
                'italy': 'ita',
                'germany': 'ger'
            }'''

scraper_content = scraper_content.replace(old_mapping, new_mapping)

with open(scraper_path, 'w') as f:
    f.write(scraper_content)

print("✅ Préfixe Espagne corrigé: esp → spain\n")
