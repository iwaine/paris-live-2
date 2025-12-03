#!/bin/bash
#
# Script de Test Rapide Phase 3
# Lance les tests essentiels pour valider le système
#

set -e  # Arrêter en cas d'erreur

echo ""
echo "======================================================================"
echo "🧪 QUICK TEST - PHASE 3"
echo "======================================================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de test
run_test() {
    local name="$1"
    local command="$2"

    echo ""
    echo "----------------------------------------------------------------------"
    echo "▶️  $name"
    echo "----------------------------------------------------------------------"

    if eval "$command"; then
        echo -e "${GREEN}✅ $name - RÉUSSI${NC}"
        return 0
    else
        echo -e "${RED}❌ $name - ÉCHOUÉ${NC}"
        return 1
    fi
}

# Vérifications préalables
echo "🔍 Vérifications préalables..."
echo ""

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 non trouvé${NC}"
    exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# Dépendances
if python3 -c "import requests, bs4, yaml" 2>/dev/null; then
    echo "✅ Dépendances: OK"
else
    echo -e "${YELLOW}⚠️  Dépendances manquantes${NC}"
    echo "   Installation: pip install requests beautifulsoup4 pyyaml"
    exit 1
fi

# Internet
if curl -s --max-time 5 -I https://www.soccerstats.com > /dev/null 2>&1; then
    echo "✅ Connexion internet: OK"
else
    echo -e "${YELLOW}⚠️  Connexion à soccerstats.com impossible${NC}"
    echo "   Le site peut être bloqué ou temporairement indisponible"
    echo "   Continuer quand même? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "======================================================================"
echo "🚀 LANCEMENT DES TESTS"
echo "======================================================================"

# Test 1: Démo (sans internet)
run_test "Test 1: Démo avec données simulées" \
    "python3 test_phase3_demo.py"

# Test 2: Détection rapide
run_test "Test 2: Détection rapide (Bosnia + Bulgaria)" \
    "python3 test_live_detection.py --mode quick"

# Test 3: Extraction complète (optionnel)
echo ""
echo "----------------------------------------------------------------------"
echo "🎯 Test 3: Extraction complète des données"
echo "----------------------------------------------------------------------"
echo ""
echo "Ce test est plus long (30-60s selon nombre de matchs)"
echo "Lancer le test d'extraction? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    run_test "Test 3: Extraction complète" \
        "python3 test_live_detection.py --mode quick --extract"
else
    echo "⏭️  Test 3 ignoré"
fi

# Résumé
echo ""
echo "======================================================================"
echo "📊 RÉSUMÉ DES TESTS"
echo "======================================================================"
echo ""

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TOUS LES TESTS RÉUSSIS${NC}"
    echo ""
    echo "🎉 Phase 3 est opérationnelle!"
    echo ""
    echo "📋 Prochaines étapes:"
    echo "   1. Tester pendant heures de matchs pour plus de résultats"
    echo "   2. Lancer: python3 test_live_detection.py --mode all --extract"
    echo "   3. Passer à Phase 4: python3 auto_live_monitor.py --test"
    echo ""
else
    echo -e "${RED}❌ CERTAINS TESTS ONT ÉCHOUÉ${NC}"
    echo ""
    echo "📚 Consulter: TEST_LOCAL_GUIDE.md"
    echo ""
fi

echo "======================================================================"
