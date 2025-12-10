#!/bin/bash
#
# 🌐 LANCEMENT DU DASHBOARD WEB
# Démarre le serveur Flask avec le dashboard en temps réel
#

# Activer l'environnement virtuel si disponible
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "======================================================================"
echo "🌐 DASHBOARD WEB - Lancement"
echo "======================================================================"
echo ""
echo "📡 URL d'accès:"
echo "   • Local:    http://localhost:5000"
echo "   • Réseau:   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "🎯 Fonctionnalités:"
echo "   • Visualisation des matchs live en temps réel"
echo "   • Graphiques d'évolution des probabilités"
echo "   • Statistiques de monitoring"
echo "   • Contrôle démarrage/arrêt du monitoring"
echo ""
echo "⏸️  Ctrl+C pour arrêter le serveur"
echo "======================================================================"
echo ""

# Lancer le dashboard
python3 dashboard_web.py
