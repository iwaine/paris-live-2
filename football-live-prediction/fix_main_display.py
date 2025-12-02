"""Correction affichage dans main_live_predictor.py"""

with open('main_live_predictor.py', 'r') as f:
    content = f.read()

# Remplacer next_interval par current_interval
content = content.replace("'next_interval'", "'current_interval'")
content = content.replace('next_interval', 'current_interval')
content = content.replace('Intervalle suivant', 'Intervalle ACTUEL')

with open('main_live_predictor.py', 'w') as f:
    f.write(content)

print("✅ Affichage corrigé dans main_live_predictor.py")
