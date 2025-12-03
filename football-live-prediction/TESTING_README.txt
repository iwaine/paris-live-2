================================================================================
                     🧪 GUIDE DE TEST PHASE 3
================================================================================

🚀 DÉMARRAGE RAPIDE:

    cd football-live-prediction
    ./quick_test.sh

================================================================================

📁 FICHIERS DE TEST:

    ✅ quick_test.sh              - Script automatique (RECOMMANDÉ)
    ✅ test_live_detection.py     - Tests avec données réelles
    ✅ test_phase3_demo.py        - Démo avec données simulées

    📚 README_TESTING.md          - Guide rapide
    📚 TEST_LOCAL_GUIDE.md        - Guide complet (détaillé)

================================================================================

💡 COMMANDES UTILES:

    # Test automatique (facile)
    ./quick_test.sh

    # Test rapide (2 ligues)
    python3 test_live_detection.py --mode quick

    # Test avec extraction
    python3 test_live_detection.py --mode quick --extract

    # Test complet (44 ligues)
    python3 test_live_detection.py --mode all --extract

    # Test une ligue
    python3 test_live_detection.py --mode single --league Bulgaria

    # Démo (sans internet)
    python3 test_phase3_demo.py

================================================================================

🕐 MEILLEURS MOMENTS:

    - Vendredi 19h-21h : Ligue 1
    - Samedi 15h-17h   : Premier League
    - Dimanche 20h-22h : La Liga
    - Week-ends        : Plusieurs ligues

================================================================================

✅ RÉSULTAT ATTENDU:

    🎯 RÉSULTAT: X match(es) live trouvé(s)

    Avec --extract:

    ✅ DONNÉES EXTRAITES:
       Équipes : TEAM_A vs TEAM_B
       Score   : X-X
       Minute  : XX'

    📊 STATISTIQUES:
       Possession       : XX% - XX%
       Tirs totaux      : X - X
       Tirs cadrés      : X - X
       Attaques         : XX - XX
       Attaques danger. : XX - XX
       Corners          : X - X

================================================================================

🐛 EN CAS DE PROBLÈME:

    1. Vérifier Python: python3 --version
    2. Installer dépendances: pip install -r requirements.txt
    3. Tester connexion: curl -I https://www.soccerstats.com
    4. Consulter: TEST_LOCAL_GUIDE.md

================================================================================

🎯 APRÈS LES TESTS:

    Une fois Phase 3 validée → Passer à Phase 4:

    python3 auto_live_monitor.py --test

================================================================================

📚 DOCUMENTATION:

    README_TESTING.md        - Guide rapide
    TEST_LOCAL_GUIDE.md      - Guide complet
    LIVE_SCRAPING_SYSTEM.md  - Architecture
    AUTO_MONITOR_GUIDE.md    - Système automatique

================================================================================
