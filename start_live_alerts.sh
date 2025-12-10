#!/bin/bash
# Script de lancement des alertes Telegram live
# Usage: ./start_live_alerts.sh [bulgaria|netherlands|both] [duration_minutes]

CHAMPIONSHIP=${1:-both}
DURATION=${2:-}  # Durée en minutes (vide = infini)

echo "🚀 Démarrage système d'alertes Telegram"
echo "📊 Championnat: $CHAMPIONSHIP"
if [ -n "$DURATION" ]; then
    echo "⏱️  Durée: $DURATION minutes"
else
    echo "⏱️  Durée: INFINI (Ctrl+C pour arrêter)"
fi
echo "================================"
echo ""

cd /workspaces/paris-live/football-live-prediction

# Préparer les arguments
DURATION_ARG=""
if [ -n "$DURATION" ]; then
    DURATION_ARG="--duration $DURATION"
fi

case $CHAMPIONSHIP in
  bulgaria)
    echo "🇧🇬 Monitoring Bulgarie uniquement..."
    echo "Scan toutes les 30 secondes..."
    echo ""
    python3 bulgaria_live_monitor.py $DURATION_ARG
    ;;
  netherlands)
    echo "🇳🇱 Monitoring Pays-Bas uniquement..."
    echo "Scan toutes les 30 secondes..."
    echo ""
    python3 netherlands_live_monitor.py $DURATION_ARG
    ;;
  both)
    echo "🌍 Monitoring Bulgarie + Pays-Bas..."
    echo "Scan toutes les 30 secondes..."
    echo ""
    echo "⚠️  Lancement en parallèle..."
    echo ""
    
    # Lancer Bulgarie en background
    python3 bulgaria_live_monitor.py $DURATION_ARG > /tmp/bulgaria_monitor.log 2>&1 &
    PID_BG=$!
    
    # Lancer Pays-Bas en background
    python3 netherlands_live_monitor.py $DURATION_ARG > /tmp/netherlands_monitor.log 2>&1 &
    PID_NL=$!
    
    echo "✅ Bulgarie lancé (PID: $PID_BG)"
    echo "   📄 Logs: tail -f /tmp/bulgaria_monitor.log"
    echo ""
    echo "✅ Pays-Bas lancé (PID: $PID_NL)"
    echo "   📄 Logs: tail -f /tmp/netherlands_monitor.log"
    echo ""
    echo "🛑 Pour arrêter:"
    echo "   kill $PID_BG $PID_NL"
    echo ""
    echo "📊 Voir les logs combinés:"
    echo "   tail -f /tmp/bulgaria_monitor.log /tmp/netherlands_monitor.log"
    echo ""
    
    # Attendre les processus
    wait
    ;;
  *)
    echo "❌ Usage: $0 [bulgaria|netherlands|both] [duration_minutes]"
    echo ""
    echo "Exemples:"
    echo "  $0 both          # Les deux championnats, durée infinie"
    echo "  $0 both 60       # Les deux championnats, 60 minutes"
    echo "  $0 bulgaria      # Bulgarie uniquement, durée infinie"
    echo "  $0 netherlands 30  # Pays-Bas uniquement, 30 minutes"
    exit 1
    ;;
esac
