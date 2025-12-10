#!/bin/bash
#
# 🚀 INSTALLATION ET CONFIGURATION AUTOMATIQUE
# Script d'installation complète pour macOS/Linux
#

set -e  # Arrêter en cas d'erreur

echo "🚀 INSTALLATION AUTOMATIQUE DU SYSTÈME V2.0"
echo "======================================================================"
echo ""

# Détecter l'OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    PYTHON="python3"
    PIP="pip3"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    PYTHON="python3"
    PIP="pip3"
else
    OS="Windows"
    PYTHON="python"
    PIP="pip"
fi

echo "📋 Système détecté : $OS"
echo ""

# Vérifier Python
echo "🔍 Vérification de Python..."
if ! command -v $PYTHON &> /dev/null; then
    echo "❌ Python n'est pas installé !"
    echo "   Installez Python 3.8+ depuis https://python.org"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION détecté"
echo ""

# Créer environnement virtuel
if [ ! -d ".venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    $PYTHON -m venv .venv
    echo "✅ Environnement virtuel créé"
else
    echo "✅ Environnement virtuel existant trouvé"
fi
echo ""

# Activer environnement virtuel
echo "🔌 Activation de l'environnement virtuel..."
source .venv/bin/activate
echo "✅ Environnement activé"
echo ""

# Installer dépendances
echo "📥 Installation des dépendances..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✅ Dépendances installées"
echo ""

# Vérifier configuration Telegram
echo "🔐 Vérification configuration Telegram..."
if [ -f "telegram_config.json" ]; then
    if grep -q "VOTRE_TOKEN_ICI" telegram_config.json; then
        echo "⚠️  Configuration Telegram non complétée"
        echo ""
        echo "📝 ÉDITER telegram_config.json :"
        echo "   1. Créer un bot avec @BotFather sur Telegram"
        echo "   2. Obtenir votre Chat ID avec @userinfobot"
        echo "   3. Éditer le fichier :"
        echo ""
        echo "      nano telegram_config.json"
        echo ""
        read -p "   Voulez-vous l'éditer maintenant ? (o/n) : " edit_config
        if [[ $edit_config == "o" || $edit_config == "O" ]]; then
            ${EDITOR:-nano} telegram_config.json
        fi
    else
        echo "✅ Configuration Telegram complète"
    fi
else
    echo "❌ telegram_config.json manquant !"
    exit 1
fi
echo ""

# Vérifier base de données
echo "💾 Vérification de la base de données..."
if [ -f "football-live-prediction/data/predictions.db" ]; then
    nb_matches=$(sqlite3 football-live-prediction/data/predictions.db "SELECT COUNT(*) FROM soccerstats_scraped_matches;" 2>/dev/null || echo "0")
    echo "✅ Base de données : $nb_matches matchs"
else
    echo "⚠️  Base de données non trouvée"
fi
echo ""

# Vérifier whitelists
echo "🎯 Vérification des whitelists..."
nb_whitelists=$(ls whitelists/*.json 2>/dev/null | wc -l | tr -d ' ')
if [ "$nb_whitelists" -gt 0 ]; then
    echo "✅ $nb_whitelists whitelists trouvées"
else
    echo "⚠️  Aucune whitelist trouvée"
    echo "   Générez-les avec : ./update_weekly.sh"
fi
echo ""

# Rendre les scripts exécutables
chmod +x monitor_live.py 2>/dev/null || true
chmod +x update_weekly.sh 2>/dev/null || true

echo "======================================================================"
echo "✅ INSTALLATION TERMINÉE AVEC SUCCÈS !"
echo "======================================================================"
echo ""
echo "🎯 COMMANDES DISPONIBLES :"
echo ""
echo "   1. Monitoring en direct :"
echo "      ./monitor_live.py"
echo ""
echo "   2. Mise à jour hebdomadaire :"
echo "      ./update_weekly.sh"
echo ""
echo "   3. Scraper une ligue :"
echo "      python3 scrape_all_leagues_auto.py --league portugal --workers 2"
echo ""
echo "   4. Générer whitelists :"
echo "      python3 generate_top_teams_whitelist.py --all"
echo ""
echo "⚠️  IMPORTANT : À chaque nouveau terminal, activez l'environnement :"
echo "   source .venv/bin/activate"
echo ""
echo "📚 Documentation : GUIDE_AUTONOME_COMPLET.md"
echo "======================================================================"
