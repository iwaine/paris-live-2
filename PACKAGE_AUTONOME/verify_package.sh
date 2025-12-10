#!/bin/bash
# Script de vérification du package

echo "🔍 Vérification du package Paris-Live..."
echo ""

ERRORS=0

# Vérifier fichiers principaux
echo "📄 Fichiers principaux:"
for file in scrape_bulgaria_auto.py scrape_bolivia_auto.py telegram_notifier.py telegram_config.py telegram_formatter.py; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file MANQUANT"
        ((ERRORS++))
    fi
done

echo ""
echo "📁 Dossier football-live-prediction:"
for file in football-live-prediction/build_critical_interval_recurrence.py \
            football-live-prediction/live_predictor_v2.py \
            football-live-prediction/bulgaria_live_monitor.py; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file MANQUANT"
        ((ERRORS++))
    fi
done

echo ""
echo "📚 Documentation:"
for file in GUIDE_UTILISATION_AUTONOME.md QUICK_START.md README.md; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file MANQUANT"
        ((ERRORS++))
    fi
done

echo ""
echo "⚙️  Configuration:"
for file in .env.template requirements.txt install.sh; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file MANQUANT"
        ((ERRORS++))
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ Package complet et prêt à l'emploi!"
    echo ""
    echo "📋 Prochaines étapes:"
    echo "1. Lire QUICK_START.md"
    echo "2. Exécuter ./install.sh"
    echo "3. Suivre le guide d'utilisation"
else
    echo "❌ $ERRORS fichier(s) manquant(s)"
    echo "Veuillez vérifier la création du package"
fi
