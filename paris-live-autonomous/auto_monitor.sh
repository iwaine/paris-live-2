#!/bin/bash
#
# 🤖 MONITORING AUTOMATIQUE
# Lance le monitoring en continu avec détection automatique
#

# Activer l'environnement virtuel si nécessaire
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Exécutez d'abord : ./setup.sh"
    exit 1
fi

source .venv/bin/activate

echo "🤖 MONITORING AUTOMATIQUE V2.0"
echo "======================================================================"
echo ""
echo "⚠️  MODE ACTUEL : MANUEL (vous entrez les infos)"
echo ""
echo "📋 Pour chaque match en cours :"
echo "   1. Vérifier les matchs sur un site de scores (Flashscore, etc.)"
echo "   2. Identifier ceux dans les intervalles 31-45' ou 76-90'"
echo "   3. Entrer les infos quand demandé"
echo ""
echo "🛑 Pour arrêter : Ctrl+C"
echo "======================================================================"
echo ""

# Boucle infinie pour monitoring continu
while true; do
    echo "🎯 Nouveau monitoring"
    echo "----------------------------------------------------------------------"
    
    python3 monitor_live.py
    
    echo ""
    read -p "🔄 Analyser un autre match ? (o/n) : " continue_monitoring
    
    if [[ $continue_monitoring != "o" && $continue_monitoring != "O" ]]; then
        echo ""
        echo "✋ Monitoring arrêté"
        break
    fi
    
    echo ""
done

echo "======================================================================"
echo "👋 Au revoir !"
echo "======================================================================"
