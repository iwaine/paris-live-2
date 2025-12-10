#!/bin/bash
#
# 🚀 LANCEMENT RAPIDE
# Script tout-en-un pour démarrer rapidement
#

# Activer l'environnement virtuel
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Afficher menu
echo "======================================================================"
echo "⚽ SYSTÈME DE PRÉDICTION FOOTBALL V2.0"
echo "======================================================================"
echo ""
echo "Que voulez-vous faire ?"
echo ""
echo "  1. 🌐 DASHBOARD WEB (interface graphique temps réel)"
echo "  2. 🔄 MONITORING CONTINU (scrape + suivi auto 60s)"
echo "  3. 🔍 Scanner automatique (détection unique)"
echo "  4. 🎯 Monitoring manuel d'un match"
echo "  5. 🔄 Mise à jour hebdomadaire (scraping + whitelists)"
echo "  5. 🔄 Mise à jour hebdomadaire (scraping + whitelists)"
echo "  6. 📊 Scraper une ligue spécifique"
echo "  7. 🎯 Générer/Régénérer les whitelists"
echo "  8. 📚 Lire la documentation"
echo "  9. 🔧 Configuration Telegram"
echo "  10. ❌ Quitter"
echo ""
read -p "Votre choix (1-10) : " choice

case $choice in
    1)
        echo ""
        echo "🌐 Lancement du dashboard web..."
        echo "   ➡️  Ouvrez http://localhost:5000 dans votre navigateur"
        echo "   ⏸️  Ctrl+C pour arrêter"
        echo ""
        ./start_dashboard.sh
        ;;
    2)
        echo ""
        echo "🔄 Lancement du monitoring continu..."
        echo "   ➡️  Scrape toutes les 60s + alertes automatiques"
        echo "   ⏸️  Ctrl+C pour arrêter"
        echo ""
        python3 auto_live_continuous_monitor.py
        ;;
    3)
        echo ""
        echo "🔍 Scanner automatique (détection unique)..."
        python3 auto_live_scanner.py
        ;;
    4)
        echo ""
        echo "🎯 Lancement du monitoring manuel..."
        python3 monitor_live.py
        ;;
    5)
        echo ""
        echo "🔄 Mise à jour complète (peut prendre 20-30 min)..."
        ./update_weekly.sh
        ;;
    6)
        echo ""
        echo "📊 Ligues disponibles : france, germany, germany2, england, netherlands2, bolivia, bulgaria, portugal"
        read -p "Quelle ligue ? : " league
        echo ""
        echo "🔍 Scraping de $league..."
        python3 scrape_all_leagues_auto.py --league "$league" --workers 2
        ;;
    7)
        echo ""
        echo "🎯 Génération de toutes les whitelists..."
        python3 generate_top_teams_whitelist.py --all --threshold 65 --min-matches 4
        ;;
    8)
        echo ""
        echo "📚 Documentation disponible :"
        echo "   • README.md - Guide rapide"
        echo "   • GUIDE_AUTONOME_COMPLET.md - Guide détaillé"
        echo "   • PACKAGE_CONTENU.md - Contenu du package"
        echo ""
        read -p "Ouvrir README.md ? (o/n) : " open_readme
        if [[ $open_readme == "o" || $open_readme == "O" ]]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open README.md
            else
                cat README.md
            fi
        fi
        ;;
    9)
        echo ""
        echo "🔧 Configuration Telegram..."
        ${EDITOR:-nano} telegram_config.json
        echo ""
        echo "✅ Configuration sauvegardée"
        ;;
    10)
        echo ""
        echo "👋 Au revoir !"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "======================================================================"
echo "✅ Terminé !"
echo "======================================================================"
