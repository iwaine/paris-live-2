"""Correction de l'erreur de syntaxe"""

with open('scrapers/soccerstats_live.py', 'r') as f:
    content = f.read()

# Corriger les lignes problématiques
content = content.replace(
    "match = re.match(r'^(\\d+)'$', status_text)",
    "match = re.match(r'^(\\d+)\\'$', status_text)"
)

content = content.replace(
    "elif re.match(r'^\\d+\\'$', status_text):",
    "elif re.match(r'^\\d+\\'$', status_text):"
)

with open('scrapers/soccerstats_live.py', 'w') as f:
    f.write(content)

print("✅ Erreur de syntaxe corrigée")
print("   → Échappement des quotes corrigé")
