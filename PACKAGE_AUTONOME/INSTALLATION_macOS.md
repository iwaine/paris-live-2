# 🍎 INSTALLATION SUR macOS - PARIS-LIVE

**Version** : 2.0  
**Date** : 4 Décembre 2025  
**Système** : macOS (testé sur macOS 10.15+)

---

## 📥 ÉTAPE 1 : TÉLÉCHARGER LE PACKAGE

### Option A : Depuis GitHub (si le dépôt est accessible)
```bash
# Ouvrir Terminal (Cmd + Espace, tapez "Terminal")
cd ~/Downloads
git clone https://github.com/iwaine/paris-live.git
cd paris-live
```

### Option B : Télécharger l'archive ZIP
1. Téléchargez le fichier `PARIS_LIVE_AUTONOME_macOS.zip` depuis votre workspace
2. Double-cliquez sur le fichier ZIP pour l'extraire
3. Ouvrez Terminal (Cmd + Espace, tapez "Terminal")
4. Naviguez vers le dossier :
```bash
cd ~/Downloads/PACKAGE_AUTONOME
```

---

## 🔧 ÉTAPE 2 : INSTALLER PYTHON (si non installé)

macOS a Python 2.7 par défaut, mais vous avez besoin de Python 3.8+.

### Vérifier si Python 3 est installé
```bash
python3 --version
```

### Si Python 3 n'est pas installé, utilisez Homebrew :
```bash
# Installer Homebrew (si pas déjà installé)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer Python 3
brew install python3

# Vérifier l'installation
python3 --version
```

---

## ⚡ ÉTAPE 3 : INSTALLATION AUTOMATIQUE

Le script `install.sh` gère tout automatiquement :

```bash
cd ~/Downloads/PACKAGE_AUTONOME

# Rendre le script exécutable
chmod +x install.sh

# Lancer l'installation
./install.sh
```

**Le script va :**
1. ✅ Vérifier Python 3
2. ✅ Créer un environnement virtuel (`venv/`)
3. ✅ Installer toutes les dépendances
4. ✅ Vous demander votre **TOKEN** et **CHAT_ID** Telegram
5. ✅ Créer le fichier `.env` avec vos identifiants

---

## 🤖 ÉTAPE 4 : CONFIGURER TELEGRAM

### 4.1 Créer un Bot Telegram

1. Ouvrez Telegram sur votre téléphone/ordinateur
2. Cherchez `@BotFather`
3. Envoyez `/newbot`
4. Suivez les instructions :
   - Nom du bot : `Paris Live Bot` (ou autre)
   - Username : `parislive_bot` (doit finir par `_bot`)
5. **Copiez le TOKEN** reçu (ex: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 4.2 Obtenir votre CHAT_ID

```bash
# Envoyez un message à votre bot sur Telegram (ex: "Hello")

# Puis exécutez cette commande (remplacez YOUR_TOKEN)
curl -s "https://api.telegram.org/botYOUR_TOKEN/getUpdates" | grep -o '"chat":{"id":[0-9]*' | grep -o '[0-9]*'
```

**Ou utilisez ce script Python :**
```bash
cd ~/Downloads/PACKAGE_AUTONOME
source venv/bin/activate

python3 << 'EOF'
from telegram_config import TelegramConfig
config = TelegramConfig()
print(f"Votre CHAT_ID : {config.chat_id}")
EOF
```

### 4.3 Tester Telegram

```bash
cd ~/Downloads/PACKAGE_AUTONOME
source venv/bin/activate

python3 -c "
from telegram_notifier import TelegramNotifier
TelegramNotifier().send_message('✅ Installation macOS réussie!')
"
```

Vous devez recevoir un message sur Telegram ! 🎉

---

## 📊 ÉTAPE 5 : COLLECTER LES DONNÉES

### 5.1 Scraper la Bulgarie (recommandé pour commencer)

```bash
cd ~/Downloads/PACKAGE_AUTONOME
source venv/bin/activate

python3 scrape_bulgaria_auto.py
```

**Durée** : ~2-3 minutes  
**Résultat** : Données historiques des équipes bulgares

### 5.2 Scraper la Bolivie (optionnel)

```bash
python3 scrape_bolivia_auto.py
```

---

## 🧠 ÉTAPE 6 : GÉNÉRER LES PATTERNS STATISTIQUES

```bash
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

**Durée** : ~10-30 secondes  
**Résultat** : Patterns d'intervalles critiques (31-45' et 75-90')

---

## 🚀 ÉTAPE 7 : LANCER LE MONITORING LIVE

### Test rapide (scan unique)
```bash
cd ~/Downloads/PACKAGE_AUTONOME/football-live-prediction
source ../venv/bin/activate

python3 bulgaria_live_monitor.py --once
```

### Monitoring continu (toutes les 2 minutes)
```bash
python3 bulgaria_live_monitor.py --continuous --interval 120
```

**Pour arrêter** : Appuyez sur `Ctrl + C`

---

## 🍎 SPÉCIFICITÉS macOS

### Lancer au démarrage (optionnel)

Créez un fichier `~/Library/LaunchAgents/com.parislive.monitor.plist` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.parislive.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/VOTRE_NOM/Downloads/PACKAGE_AUTONOME/venv/bin/python3</string>
        <string>/Users/VOTRE_NOM/Downloads/PACKAGE_AUTONOME/football-live-prediction/bulgaria_live_monitor.py</string>
        <string>--continuous</string>
        <string>--interval</string>
        <string>120</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Charger le service :**
```bash
launchctl load ~/Library/LaunchAgents/com.parislive.monitor.plist
```

**Arrêter le service :**
```bash
launchctl unload ~/Library/LaunchAgents/com.parislive.monitor.plist
```

---

## 📁 STRUCTURE FINALE

```
~/Downloads/PACKAGE_AUTONOME/
├── venv/                              # Environnement virtuel Python
├── .env                               # Vos clés Telegram (SECRET!)
├── scrape_bulgaria_auto.py            # Scraper Bulgarie
├── scrape_bolivia_auto.py             # Scraper Bolivie
├── telegram_notifier.py               # Envoi alertes Telegram
├── football-live-prediction/
│   ├── data/
│   │   └── predictions.db             # Base de données SQLite
│   ├── predictors/
│   │   └── interval_predictor.py      # Prédictions par intervalles (AMÉLIORÉ)
│   ├── analyzers/
│   ├── utils/
│   ├── modules/
│   ├── build_critical_interval_recurrence.py
│   └── bulgaria_live_monitor.py       # Monitoring live
└── GUIDE_UTILISATION_AUTONOME.md
```

---

## ❓ DÉPANNAGE macOS

### Erreur "Permission denied" sur install.sh
```bash
chmod +x install.sh
./install.sh
```

### Erreur SSL/Certificats
```bash
# Installer les certificats Python
cd /Applications/Python\ 3.*/
./Install\ Certificates.command
```

### Erreur "command not found: python3"
```bash
# Créer un alias (ajouter à ~/.zshrc ou ~/.bash_profile)
echo 'alias python3="/usr/local/bin/python3"' >> ~/.zshrc
source ~/.zshrc
```

### Problème avec venv
```bash
# Supprimer et recréer
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Telegram ne fonctionne pas
```bash
# Vérifier .env
cat .env

# Tester manuellement
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()
print(f"TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
print(f"CHAT_ID: {os.getenv('TELEGRAM_CHAT_ID')}")
EOF
```

---

## 🎯 COMMANDES RAPIDES

### Démarrage quotidien
```bash
cd ~/Downloads/PACKAGE_AUTONOME/football-live-prediction
source ../venv/bin/activate
python3 bulgaria_live_monitor.py --continuous --interval 120
```

### Mise à jour des données (1x par semaine)
```bash
cd ~/Downloads/PACKAGE_AUTONOME
source venv/bin/activate
python3 scrape_bulgaria_auto.py
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

### Voir les logs
```bash
tail -f football-live-prediction/logs/live_monitor.log
```

---

## ✅ RÉSUMÉ - VOUS ÊTES AUTONOME !

Vous pouvez maintenant :
- ✅ Collecter des données de matchs historiques (Bulgarie, Bolivie, autres)
- ✅ Générer des patterns statistiques par intervalles
- ✅ Monitorer les matchs en direct
- ✅ Recevoir des alertes Telegram automatiques
- ✅ Ajouter de nouveaux championnats
- ✅ Tout faire depuis votre Mac !

---

**📞 Support** : Consultez `GUIDE_UTILISATION_AUTONOME.md` pour la documentation complète

**🚀 Quick Start** : `cat QUICK_START.md`

**🔄 Version** : 2.0 (4 Décembre 2025)
