"""Correction du préfixe Espagne: spain → spa"""
from pathlib import Path

scraper_path = Path('scrapers/soccerstats_historical.py')

with open(scraper_path, 'r') as f:
    content = f.read()

# Remplacer le mapping
old_mapping = """            league_prefix_map = {
                'england': 'eng',
                'spain': 'spain',
                'france': 'fra',
                'italy': 'ita',
                'germany': 'ger'
            }"""

new_mapping = """            league_prefix_map = {
                'england': 'eng',
                'spain': 'spa',
                'france': 'fra',
                'italy': 'ita',
                'germany': 'ger'
            }"""

if old_mapping in content:
    content = content.replace(old_mapping, new_mapping)
    print("✅ Mapping modifié: spain → spa")
else:
    # Essayer une autre variante
    content = content.replace("'spain': 'spain'", "'spain': 'spa'")
    content = content.replace("'spain': 'esp'", "'spain': 'spa'")
    print("✅ Préfixe Espagne corrigé")

with open(scraper_path, 'w') as f:
    f.write(content)

print("✅ Scraper mis à jour avec le bon préfixe espagnol")
