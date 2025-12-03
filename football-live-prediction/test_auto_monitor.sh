#!/bin/bash
# Script de test rapide pour le système de surveillance automatique

echo "======================================================================"
echo "🧪 TEST AUTO LIVE MONITOR"
echo "======================================================================"
echo ""

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé"
    exit 1
fi

echo "✅ Python 3 OK"

# Vérifier les dépendances
echo ""
echo "📦 Vérification des dépendances..."

python3 -c "import requests; import bs4; import yaml" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dépendances de base OK"
else
    echo "❌ Dépendances manquantes"
    echo "   Installer avec: pip install -r requirements.txt"
    exit 1
fi

# Vérifier Telegram (optionnel)
python3 -c "import telegram" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Telegram disponible"
else
    echo "⚠️  Telegram non disponible (optionnel)"
fi

# Vérifier la structure
echo ""
echo "📁 Vérification de la structure..."

files=(
    "auto_live_monitor.py"
    "scrapers/live_match_detector.py"
    "soccerstats_live_scraper.py"
    "utils/match_monitor.py"
    "utils/database_manager.py"
    "config.yaml"
)

all_ok=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file manquant"
        all_ok=false
    fi
done

if [ "$all_ok" = false ]; then
    echo ""
    echo "❌ Fichiers manquants"
    exit 1
fi

echo ""
echo "======================================================================"
echo "🚀 LANCEMENT DU TEST (1 cycle de détection)"
echo "======================================================================"
echo ""
echo "Le système va:"
echo "  1. Scanner les 44 ligues pour des matchs live"
echo "  2. Extraire les données complètes de chaque match"
echo "  3. Faire des prédictions"
echo "  4. Afficher les résultats"
echo ""
echo "Cela peut prendre 1-3 minutes..."
echo ""

# Lancer le test
python3 auto_live_monitor.py --test --no-telegram

exit_code=$?

echo ""
echo "======================================================================"
if [ $exit_code -eq 0 ]; then
    echo "✅ TEST RÉUSSI"
else
    echo "❌ TEST ÉCHOUÉ (code: $exit_code)"
fi
echo "======================================================================"
echo ""

# Afficher les prochaines étapes
if [ $exit_code -eq 0 ]; then
    echo "📋 PROCHAINES ÉTAPES:"
    echo ""
    echo "1. Mode Production (surveillance continue):"
    echo "   python3 auto_live_monitor.py"
    echo ""
    echo "2. Avec Telegram (pour recevoir des alertes):"
    echo "   export TELEGRAM_BOT_TOKEN='ton_token'"
    echo "   export TELEGRAM_CHAT_ID='ton_chat_id'"
    echo "   python3 auto_live_monitor.py"
    echo ""
    echo "3. Options personnalisées:"
    echo "   python3 auto_live_monitor.py --detection-interval 180 --max-cycles 20"
    echo ""
    echo "📚 Documentation complète: AUTO_MONITOR_GUIDE.md"
    echo ""
fi

exit $exit_code
