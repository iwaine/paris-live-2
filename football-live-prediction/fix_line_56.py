"""Correction de la ligne 56 - Test DataFrame ambiguë"""

with open('setup_profiles.py', 'r') as f:
    content = f.read()

# Ligne problématique
old_line = "        if 'overall' not in timing_data or not timing_data['overall']:"

# Correction : Vérifier si le dict est vide au lieu de "not dict"
new_line = "        if 'overall' not in timing_data or len(timing_data['overall']) == 0:"

if old_line in content:
    content = content.replace(old_line, new_line)
    
    with open('setup_profiles.py', 'w') as f:
        f.write(content)
    
    print("✅ LIGNE 56 CORRIGÉE")
    print(f"   AVANT: {old_line.strip()}")
    print(f"   APRÈS: {new_line.strip()}")
    print("\n💡 Explication:")
    print("   'not timing_data['overall']' → Erreur avec DataFrame")
    print("   'len(timing_data['overall']) == 0' → OK !")
else:
    print("❌ Ligne non trouvée exactement, affichage...")
    # Trouver et afficher la ligne
    for i, line in enumerate(content.split('\n'), 1):
        if 'overall' in line and 'not timing_data' in line:
            print(f"Ligne {i}: {line}")
