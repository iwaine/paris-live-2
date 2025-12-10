#!/bin/bash
# Script d'installation automatique

echo "🚀 Installation du système Paris-Live..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé!"
    exit 1
fi

echo "✅ Python 3 détecté"

# Créer environnement virtuel
echo "📦 Création environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
echo "📥 Installation des dépendances..."
pip install -r requirements.txt

# Configurer Telegram
echo ""
echo "⚙️  Configuration Telegram"
echo "=========================="

if [ ! -f .env ]; then
    echo "📝 Création fichier .env..."
    
    echo ""
    echo "Veuillez entrer votre TELEGRAM_BOT_TOKEN:"
    read -r BOT_TOKEN
    
    echo "Veuillez entrer votre TELEGRAM_CHAT_ID:"
    read -r CHAT_ID
    
    cat > .env << ENVEOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
ENVEOF
    
    echo "✅ Fichier .env créé"
else
    echo "✅ Fichier .env existe déjà"
fi

echo ""
echo "✅ Installation terminée!"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Collecter les données: python3 scrape_bulgaria_auto.py"
echo "2. Générer patterns: cd football-live-prediction && python3 build_critical_interval_recurrence.py"
echo "3. Tester Telegram: python3 -c 'from telegram_notifier import TelegramNotifier; TelegramNotifier().send_message(\"Test\")'"
echo "4. Lancer monitoring: cd football-live-prediction && python3 bulgaria_live_monitor.py --once"
echo ""
echo "📖 Consultez GUIDE_UTILISATION_AUTONOME.md pour plus d'informations"
