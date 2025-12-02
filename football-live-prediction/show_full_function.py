with open('setup_profiles.py', 'r') as f:
    lines = f.readlines()

in_function = False
for i, line in enumerate(lines, 1):
    if 'def setup_profiles_for_league' in line:
        in_function = True
    if in_function:
        print(f"{i:4d}: {line.rstrip()}")
        # Arrêter à la fin de la fonction (prochain def ou fin de try/except principal)
        if i > 30 and line.strip() and not line[0].isspace() and 'def ' in line:
            break
        if 'return profiles' in line and in_function:
            print("..." )
            # Afficher encore 5 lignes après return
            for j in range(5):
                if i+j < len(lines):
                    print(f"{i+j+1:4d}: {lines[i+j].rstrip()}")
            break
