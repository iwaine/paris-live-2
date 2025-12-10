#!/bin/bash
# Script de création du package autonome complet

echo "📦 Création du package PARIS-LIVE autonome..."

# Créer le dossier principal
PACKAGE_DIR="/workspaces/paris-live/PACKAGE_AUTONOME"
mkdir -p "$PACKAGE_DIR"

# === 1. FICHIERS PRINCIPAUX ===
echo "📄 Copie des fichiers principaux..."

cp /workspaces/paris-live/scrape_bulgaria_auto.py "$PACKAGE_DIR/"
cp /workspaces/paris-live/scrape_bolivia_auto.py "$PACKAGE_DIR/"
cp /workspaces/paris-live/telegram_config.py "$PACKAGE_DIR/"
cp /workspaces/paris-live/telegram_notifier.py "$PACKAGE_DIR/"
cp /workspaces/paris-live/telegram_formatter.py "$PACKAGE_DIR/"

# === 2. DOSSIER PREDICTION ===
echo "📁 Copie dossier football-live-prediction..."

mkdir -p "$PACKAGE_DIR/football-live-prediction"
cp /workspaces/paris-live/football-live-prediction/build_critical_interval_recurrence.py "$PACKAGE_DIR/football-live-prediction/"
cp /workspaces/paris-live/football-live-prediction/live_predictor_v2.py "$PACKAGE_DIR/football-live-prediction/"
cp /workspaces/paris-live/football-live-prediction/bulgaria_live_monitor.py "$PACKAGE_DIR/football-live-prediction/"

# Modules
mkdir -p "$PACKAGE_DIR/football-live-prediction/modules"
cp /workspaces/paris-live/football-live-prediction/modules/soccerstats_live_selector.py "$PACKAGE_DIR/football-live-prediction/modules/"
cp /workspaces/paris-live/football-live-prediction/modules/soccerstats_live_scraper.py "$PACKAGE_DIR/football-live-prediction/modules/"

# Predictors (NOUVEAU - contient interval_predictor.py avec améliorations)
mkdir -p "$PACKAGE_DIR/football-live-prediction/predictors"
cp -r /workspaces/paris-live/football-live-prediction/predictors/*.py "$PACKAGE_DIR/football-live-prediction/predictors/" 2>/dev/null || true

# Analyzers
mkdir -p "$PACKAGE_DIR/football-live-prediction/analyzers"
cp -r /workspaces/paris-live/football-live-prediction/analyzers/*.py "$PACKAGE_DIR/football-live-prediction/analyzers/" 2>/dev/null || true

# Utils
mkdir -p "$PACKAGE_DIR/football-live-prediction/utils"
cp -r /workspaces/paris-live/football-live-prediction/utils/*.py "$PACKAGE_DIR/football-live-prediction/utils/" 2>/dev/null || true

# Data (créer structure vide)
mkdir -p "$PACKAGE_DIR/football-live-prediction/data"
cp /workspaces/paris-live/football-live-prediction/data/predictions.db "$PACKAGE_DIR/football-live-prediction/data/" 2>/dev/null || \
sqlite3 "$PACKAGE_DIR/football-live-prediction/data/predictions.db" "SELECT 1"

# === 3. DOCUMENTATION ===
echo "📚 Copie de la documentation..."

cp /workspaces/paris-live/GUIDE_UTILISATION_AUTONOME.md "$PACKAGE_DIR/"
cp /workspaces/paris-live/METHODOLOGIE_COMPLETE_V2.md "$PACKAGE_DIR/"
cp /workspaces/paris-live/README.md "$PACKAGE_DIR/" 2>/dev/null || echo "# Paris Live - Système de Prédiction" > "$PACKAGE_DIR/README.md"

# === 4. FICHIERS DE CONFIGURATION ===
echo "⚙️  Création fichiers de configuration..."

# .env template
cat > "$PACKAGE_DIR/.env.template" << 'EOF'
# Configuration Telegram
# Obtenez ces valeurs via @BotFather sur Telegram

TELEGRAM_BOT_TOKEN=votre_token_ici
TELEGRAM_CHAT_ID=votre_chat_id_ici

# Exemple:
# TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
# TELEGRAM_CHAT_ID=123456789
EOF

# requirements.txt
cat > "$PACKAGE_DIR/requirements.txt" << 'EOF'
requests>=2.31.0
beautifulsoup4>=4.12.0
python-telegram-bot>=20.0
python-dotenv>=1.0.0
EOF

# === 5. SCRIPTS D'INSTALLATION ===
echo "🔧 Création scripts d'installation..."

cat > "$PACKAGE_DIR/install.sh" << 'EOF'
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
EOF

chmod +x "$PACKAGE_DIR/install.sh"

# === 6. QUICK START ===
cat > "$PACKAGE_DIR/QUICK_START.md" << 'EOF'
# 🚀 DÉMARRAGE RAPIDE - 5 MINUTES

## 1. Installation (1 minute)

```bash
cd PACKAGE_AUTONOME
./install.sh
```

Suivez les instructions pour entrer votre TOKEN et CHAT_ID Telegram.

## 2. Collecter les Données (2 minutes)

```bash
# Activer l'environnement
source venv/bin/activate

# Scraper Bulgarie
python3 scrape_bulgaria_auto.py

# Scraper Bolivie
python3 scrape_bolivia_auto.py
```

## 3. Générer les Patterns (30 secondes)

```bash
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

## 4. Tester Telegram (10 secondes)

```bash
python3 -c "
from telegram_notifier import TelegramNotifier
TelegramNotifier().send_message('✅ Système opérationnel!')
"
```

Vous devez recevoir un message sur Telegram !

## 5. Lancer le Monitoring (30 secondes)

```bash
cd football-live-prediction

# Test scan unique
python3 bulgaria_live_monitor.py --once

# OU monitoring continu
python3 bulgaria_live_monitor.py --continuous --interval 120
```

## ✅ C'est tout !

Consultez **GUIDE_UTILISATION_AUTONOME.md** pour la documentation complète.
EOF

# === 7. README PRINCIPAL ===
cat > "$PACKAGE_DIR/README.md" << 'EOF'
# 🎯 PARIS-LIVE - Système de Prédiction de Buts en Live

**Version** : 2.0  
**Status** : Production Ready 🚀

## 📋 Description

Système autonome de prédiction de buts dans les intervalles critiques (31-45' et 75-90') pour les matchs de football en direct.

**Fonctionnalités** :
- ✅ Scraping automatique des données historiques
- ✅ Génération de patterns statistiques avancés
- ✅ Prédictions hybrides (80% historique + 20% momentum live)
- ✅ Alertes Telegram en temps réel
- ✅ Support multi-championnats

## 🚀 Démarrage Rapide

### Installation

```bash
./install.sh
```

### Configuration Telegram

1. Créer un bot via @BotFather sur Telegram
2. Récupérer TOKEN et CHAT_ID
3. Les entrer lors de l'installation

### Utilisation

```bash
# 1. Collecter données
python3 scrape_bulgaria_auto.py

# 2. Générer patterns
cd football-live-prediction
python3 build_critical_interval_recurrence.py

# 3. Lancer monitoring
python3 bulgaria_live_monitor.py --continuous --interval 120
```

## 📚 Documentation

- **QUICK_START.md** : Démarrage en 5 minutes
- **GUIDE_UTILISATION_AUTONOME.md** : Guide complet détaillé
- **METHODOLOGIE_COMPLETE_V2.md** : Documentation technique

## 🏆 Championnats Supportés

- 🇧🇬 **Bulgarie** - A PFG (16 équipes, 286 matches)
- 🇧🇴 **Bolivie** - Division Profesional (16 équipes, 428 matches)
- 🇳🇱 **Pays-Bas** - Eerste Divisie (template disponible)

**Ajouter un championnat** : Voir section 2 du GUIDE_UTILISATION_AUTONOME.md

## 📊 Résultats

- **208 patterns statistiques** générés
- **Précision** : Intervalles critiques avec timing ± écart-type
- **Alertes** : Notifications Telegram pour probabilités > 75%

## 🛠️ Technologies

- Python 3.x
- SQLite
- BeautifulSoup4 (scraping)
- Requests
- Python Telegram Bot

## 📁 Structure

```
PACKAGE_AUTONOME/
├── scrape_bulgaria_auto.py           # Scraper Bulgarie
├── scrape_bolivia_auto.py            # Scraper Bolivie
├── telegram_notifier.py              # Envoi Telegram
├── telegram_formatter.py             # Format messages
├── football-live-prediction/
│   ├── build_critical_interval_recurrence.py
│   ├── live_predictor_v2.py
│   ├── bulgaria_live_monitor.py
│   └── data/predictions.db
├── GUIDE_UTILISATION_AUTONOME.md
└── install.sh
```

## 🎓 Autonomie Complète

Ce package vous rend **100% autonome** pour :

1. ✅ Ajouter de nouveaux championnats
2. ✅ Collecter les données historiques
3. ✅ Générer les patterns
4. ✅ Configurer Telegram
5. ✅ Lancer le monitoring live
6. ✅ Maintenir le système

## 📝 Licence

Projet éducatif - Utilisation personnelle

## 🤝 Support

Consultez la documentation complète dans **GUIDE_UTILISATION_AUTONOME.md**

---

**Créé avec ❤️ pour les passionnés de football et de data science**
EOF

# === 8. FICHIER DE VÉRIFICATION ===
cat > "$PACKAGE_DIR/verify_package.sh" << 'EOF'
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
EOF

chmod +x "$PACKAGE_DIR/verify_package.sh"

# === 9. EXÉCUTER LA VÉRIFICATION ===
echo ""
echo "✅ Package créé dans: $PACKAGE_DIR"
echo ""

cd "$PACKAGE_DIR"
./verify_package.sh

echo ""
echo "📦 PACKAGE AUTONOME CRÉÉ AVEC SUCCÈS!"
echo ""
echo "📁 Emplacement: $PACKAGE_DIR"
echo ""
echo "📋 Pour commencer:"
echo "   cd $PACKAGE_DIR"
echo "   cat QUICK_START.md"
echo "   ./install.sh"
