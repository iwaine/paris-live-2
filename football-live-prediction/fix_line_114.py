"""Correction ligne 114"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# Corriger la ligne 114
content = content.replace(
    "matches = re.findall(r'(\\d+)'', all_text)",
    "matches = re.findall(r'(\\d+)\\'', all_text)"
)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.write(content)

print("✅ Ligne 114 corrigée")
