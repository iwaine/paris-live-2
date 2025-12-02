╔═══════════════════════════════════════════════════════════════╗
║                    SETUP_PROFILES FIX PACKAGE                  ║
║                         Version 1.0                            ║
╚═══════════════════════════════════════════════════════════════╝

📦 CONTENU DU PACKAGE
═══════════════════════════════════════════════════════════════

1. README_SETUP_FIX.txt (ce fichier)
   → Instructions rapides

2. diagnostic_mac.py
   → Script de diagnostic à exécuter EN PREMIER
   → Vérifie que votre environnement est correct

3. setup_profiles_CORRECTED.py
   → Version corrigée de setup_profiles.py
   → Corrige KeyError 'league' → 'league_code'

4. soccerstats_historical_VERIFIED.py
   → Scraper vérifié avec scrape_team_stats()
   → À utiliser si votre scraper est corrompu

5. test_setup_complete.py
   → Script de test pour vérifier que tout fonctionne
   → Teste config, scraper, analyzer

6. INSTRUCTIONS_SETUP_PROFILES.txt
   → Instructions détaillées étape par étape

7. SETUP_PROFILES_CORRECTION_RESUME.md
   → Documentation complète avec explications


🚀 DÉMARRAGE RAPIDE (5 MINUTES)
═══════════════════════════════════════════════════════════════

ÉTAPE 1: Extraire le ZIP
─────────────────────────
Copiez tous les fichiers dans votre dossier:
/Users/iwainebenbouziane/Desktop/football-live-prediction/


ÉTAPE 2: Exécuter le diagnostic
────────────────────────────────
python diagnostic_mac.py

Ce script vérifie:
✓ Version Python
✓ Fichiers config
✓ Présence de scrape_team_stats()
✓ Modules requis
✓ Cache Python

Si tout est OK → Passez à ÉTAPE 4
Si erreurs → Passez à ÉTAPE 3


ÉTAPE 3: Nettoyer et corriger
──────────────────────────────
# A. Nettoyer cache Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# B. Appliquer corrections
cp setup_profiles_CORRECTED.py setup_profiles.py

# C. SI scrape_team_stats manquant:
cp soccerstats_historical_VERIFIED.py scrapers/soccerstats_historical.py

# D. Réexécuter diagnostic
python diagnostic_mac.py


ÉTAPE 4: Tester
───────────────
python test_setup_complete.py

Résultat attendu:
✅ Config chargée
✅ Scraper créé
✅ Analyzer créé
✅ scrape_team_stats() existe
✅ 3 équipes de test chargées


ÉTAPE 5: Générer profils
─────────────────────────
python setup_profiles.py

Choisir option 1 (équipes de test)

Résultat attendu:
📋 Équipes de test configurées:
   - Manchester United (england)
   - Paris Saint-Germain (france)
   - Real Madrid (spain)

🔄 Génération de 3 profils...
   ✅ Profile created for Manchester United
   ✅ Profile created for Paris Saint-Germain
   ✅ Profile created for Real Madrid

🎉 GÉNÉRATION TERMINÉE!


📁 RÉSULTAT
═══════════════════════════════════════════════════════════════

Profils générés dans:
data/team_profiles/
├── json/
│   ├── manchester_united_profile.json
│   ├── paris_saint_germain_profile.json
│   └── real_madrid_profile.json
└── team_profiles_YYYYMMDD_HHMMSS.xlsx


🔧 DÉPANNAGE
═══════════════════════════════════════════════════════════════

Problème: "ModuleNotFoundError"
─────────────────────────────────
pip install tenacity loguru requests beautifulsoup4 pandas pyyaml

Problème: "AttributeError: scrape_team_stats"
──────────────────────────────────────────────
cp soccerstats_historical_VERIFIED.py scrapers/soccerstats_historical.py

Problème: "KeyError: 'league'"
──────────────────────────────
cp setup_profiles_CORRECTED.py setup_profiles.py

Problème: Aucune donnée scrapée
────────────────────────────────
Vérifiez que soccerstats.com est accessible depuis votre Mac


📖 DOCUMENTATION COMPLÈTE
═══════════════════════════════════════════════════════════════

Pour plus de détails, consultez:
→ SETUP_PROFILES_CORRECTION_RESUME.md

Pour instructions pas-à-pas:
→ INSTRUCTIONS_SETUP_PROFILES.txt


✉️ SUPPORT
═══════════════════════════════════════════════════════════════

Si problème persiste:
1. Exécutez diagnostic_mac.py
2. Partagez la sortie complète
3. Incluez les logs d'erreur


═══════════════════════════════════════════════════════════════
Date: 2025-11-25
Version: 1.0 - Corrections complètes et vérifiées
Testé sur: Python 3.12, macOS
═══════════════════════════════════════════════════════════════
