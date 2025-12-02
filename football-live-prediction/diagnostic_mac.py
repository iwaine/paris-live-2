#!/usr/bin/env python3
"""
DIAGNOSTIC SETUP_PROFILES - À EXÉCUTER SUR VOTRE MAC
====================================================
Ce script vérifie si votre environnement est correct.
"""

import sys
from pathlib import Path

print("\n" + "="*70)
print(" "*15 + "🔍 DIAGNOSTIC SETUP_PROFILES")
print("="*70 + "\n")

# Test 1: Python version
print("✓ Test 1: Version Python")
print(f"   Python {sys.version}")
if sys.version_info < (3, 8):
    print("   ❌ Python 3.8+ requis!")
else:
    print("   ✅ OK\n")

# Test 2: Fichier config
print("✓ Test 2: Fichier config.yaml")
config_file = Path("config/config.yaml")
if config_file.exists():
    print(f"   ✅ Trouvé: {config_file}")
    # Lire et vérifier test_teams
    with open(config_file, 'r') as f:
        content = f.read()
        if 'test_teams:' in content:
            print("   ✅ Section test_teams trouvée")
            if 'league_code:' in content:
                print("   ✅ Champ league_code présent\n")
            else:
                print("   ❌ Champ league_code manquant!\n")
        else:
            print("   ❌ Section test_teams manquante!\n")
else:
    print(f"   ❌ Fichier non trouvé: {config_file}\n")

# Test 3: Fichier scraper
print("✓ Test 3: Scraper soccerstats_historical.py")
scraper_file = Path("scrapers/soccerstats_historical.py")
if scraper_file.exists():
    print(f"   ✅ Trouvé: {scraper_file}")
    # Vérifier scrape_team_stats
    with open(scraper_file, 'r') as f:
        content = f.read()
        if 'def scrape_team_stats' in content:
            print("   ✅ Méthode scrape_team_stats() présente\n")
        else:
            print("   ❌ Méthode scrape_team_stats() MANQUANTE!")
            print("   → Remplacez avec soccerstats_historical_VERIFIED.py\n")
else:
    print(f"   ❌ Fichier non trouvé: {scraper_file}\n")

# Test 4: Fichier setup_profiles.py
print("✓ Test 4: setup_profiles.py")
setup_file = Path("setup_profiles.py")
if setup_file.exists():
    print(f"   ✅ Trouvé: {setup_file}")
    # Vérifier les corrections
    with open(setup_file, 'r') as f:
        lines = f.readlines()
        
        # Ligne 183
        found_183 = False
        for i, line in enumerate(lines[180:186], 181):
            if "team['league_code']" in line:
                print(f"   ✅ Ligne {i}: Utilise league_code (CORRECT)")
                found_183 = True
                break
            elif "team['league']" in line and "league_code" not in line:
                print(f"   ❌ Ligne {i}: Utilise 'league' (INCORRECT!)")
                print("   → Remplacez avec setup_profiles_CORRECTED.py")
                break
        
        if not found_183:
            # Ligne 193
            for i, line in enumerate(lines[190:196], 191):
                if "team['league_code']" in line:
                    print(f"   ✅ Ligne {i}: Utilise league_code (CORRECT)")
                    break
                elif "team['league']" in line and "league_code" not in line:
                    print(f"   ❌ Ligne {i}: Utilise 'league' (INCORRECT!)")
                    print("   → Remplacez avec setup_profiles_CORRECTED.py")
                    break
        print()
else:
    print(f"   ❌ Fichier non trouvé: {setup_file}\n")

# Test 5: Cache Python
print("✓ Test 5: Cache Python")
pycache_dirs = list(Path(".").rglob("__pycache__"))
pyc_files = list(Path(".").rglob("*.pyc"))

if pycache_dirs or pyc_files:
    print(f"   ⚠️  Trouvé {len(pycache_dirs)} dossiers __pycache__")
    print(f"   ⚠️  Trouvé {len(pyc_files)} fichiers .pyc")
    print("   → Exécutez: find . -name '*.pyc' -delete")
    print("   → Exécutez: find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null\n")
else:
    print("   ✅ Pas de cache Python\n")

# Test 6: Modules requis
print("✓ Test 6: Modules Python requis")
required_modules = ['requests', 'beautifulsoup4', 'pandas', 'pyyaml', 'tenacity', 'loguru']
missing_modules = []

for module in required_modules:
    try:
        if module == 'beautifulsoup4':
            __import__('bs4')
            print(f"   ✅ {module}")
        elif module == 'pyyaml':
            __import__('yaml')
            print(f"   ✅ {module}")
        else:
            __import__(module)
            print(f"   ✅ {module}")
    except ImportError:
        print(f"   ❌ {module} MANQUANT")
        missing_modules.append(module)

if missing_modules:
    print(f"\n   → Installez: pip install {' '.join(missing_modules)}")
print()

# Résumé
print("="*70)
print(" "*25 + "📊 RÉSUMÉ")
print("="*70)

all_ok = (
    sys.version_info >= (3, 8) and
    config_file.exists() and
    scraper_file.exists() and
    setup_file.exists() and
    not missing_modules
)

if all_ok:
    print("\n✅ ENVIRONNEMENT CORRECT - setup_profiles.py devrait fonctionner!\n")
    print("Exécutez: python setup_profiles.py")
else:
    print("\n⚠️  CORRECTIONS NÉCESSAIRES - Voir les erreurs ci-dessus\n")
    print("Consultez: SETUP_PROFILES_CORRECTION_RESUME.md")

print("="*70 + "\n")
