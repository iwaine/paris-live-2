"""Correction de la vérification du style"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# Remplacer la vérification du style
old_check = "if font_tag and 'color:#87CEFA' in str(font_tag.get('style', '')):"
new_check = "if font_tag and '#87CEFA' in str(font_tag.get('style', '')).upper():"

content = content.replace(old_check, new_check)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.write(content)

print("✅ Vérification du style corrigée")
print("   → Utilise .upper() pour comparaison insensible à la casse")
