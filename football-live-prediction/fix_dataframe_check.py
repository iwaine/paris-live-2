"""Correction du test DataFrame ambiguë dans setup_profiles_for_league"""

with open('setup_profiles.py', 'r') as f:
    lines = f.readlines()

# Chercher et corriger la ligne problématique
fixed = False
for i, line in enumerate(lines):
    # Chercher les patterns problématiques
    if 'if timing_data is None:' in line:
        # Déjà corrigé
        continue
    elif 'if not timing_data:' in line and 'setup_profiles_for_league' in ''.join(lines[max(0,i-20):i]):
        # Corriger le test ambiguë
        indent = len(line) - len(line.lstrip())
        lines[i] = ' ' * indent + 'if timing_data is None:\n'
        print(f"✅ Ligne {i+1} corrigée:")
        print(f"   AVANT: {line.strip()}")
        print(f"   APRÈS: if timing_data is None:")
        fixed = True
    elif 'if timing_data:' in line and 'setup_profiles_for_league' in ''.join(lines[max(0,i-20):i]):
        # Inverser la logique
        indent = len(line) - len(line.lstrip())
        lines[i] = ' ' * indent + 'if timing_data is not None:\n'
        print(f"✅ Ligne {i+1} corrigée:")
        print(f"   AVANT: {line.strip()}")
        print(f"   APRÈS: if timing_data is not None:")
        fixed = True

if not fixed:
    print("⚠️  Pattern non trouvé, affichage de la section...")
    # Afficher la fonction pour diagnostic manuel
    in_function = False
    for i, line in enumerate(lines):
        if 'def setup_profiles_for_league' in line:
            in_function = True
        if in_function:
            print(f"{i+1:4d}: {line.rstrip()}")
            if line.strip().startswith('return profiles') and in_function:
                break
else:
    with open('setup_profiles.py', 'w') as f:
        f.writelines(lines)
    print("\n✅ Fichier corrigé et sauvegardé")
