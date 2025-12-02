"""Correction de l'extraction des noms d'équipes depuis le DataFrame"""

with open('setup_profiles.py', 'r') as f:
    content = f.read()

# Trouver la ligne qui extrait les équipes
old_line = "        teams = list(timing_data['overall'].keys())"

# Nouvelle extraction correcte depuis le DataFrame
new_line = "        teams = timing_data['overall']['team'].tolist()"

if old_line in content:
    content = content.replace(old_line, new_line)
    
    with open('setup_profiles.py', 'w') as f:
        f.write(content)
    
    print("✅ EXTRACTION D'ÉQUIPES CORRIGÉE")
    print(f"   AVANT: {old_line.strip()}")
    print(f"   APRÈS: {new_line.strip()}")
    print("\n💡 Explication:")
    print("   DataFrame.keys() → Noms de COLONNES (team, gp, goals...)")
    print("   DataFrame['team'] → Noms d'ÉQUIPES (Real Madrid, Barcelona...)")
else:
    print("⚠️  Pattern non trouvé, recherche alternative...")
    
    # Chercher d'autres patterns possibles
    patterns = [
        "teams = list(timing_data['overall']",
        "teams = timing_data['overall'].keys()",
        "for team in timing_data['overall']"
    ]
    
    found = False
    for pattern in patterns:
        if pattern in content:
            print(f"✓ Trouvé: {pattern}")
            found = True
            # Afficher le contexte
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if pattern in line:
                    print(f"\nLigne {i+1}:")
                    for j in range(max(0, i-2), min(len(lines), i+5)):
                        print(f"  {j+1}: {lines[j]}")
    
    if not found:
        print("❌ Aucun pattern trouvé, affichage manuel requis")
        print("\n📋 Lignes 55-65 de setup_profiles.py:")
        lines = content.split('\n')
        for i in range(54, min(65, len(lines))):
            print(f"  {i+1}: {lines[i]}")
