# 🚀 TRANSFERT VERS VOTRE MAC - GUIDE COMPLET

**Date** : 4 Décembre 2025  
**Package** : PARIS-LIVE v2.0 AUTONOME  
**Plateforme cible** : macOS

---

## 📦 FICHIERS DISPONIBLES

Deux archives ont été créées dans `/workspaces/paris-live/` :

1. **PARIS_LIVE_AUTONOME_macOS.zip** (246 Ko) ⭐ **RECOMMANDÉ pour Mac**
2. **PARIS_LIVE_AUTONOME_macOS.tar.gz** (216 Ko)

---

## 📥 MÉTHODE 1 : TÉLÉCHARGER DEPUIS VS CODE (Le plus simple)

### Option A : Interface VS Code

1. Dans l'explorateur VS Code (barre latérale gauche)
2. Naviguez vers `/workspaces/paris-live/`
3. Clic droit sur `PARIS_LIVE_AUTONOME_macOS.zip`
4. Sélectionnez **"Download..."**
5. Le fichier sera téléchargé dans votre dossier `~/Downloads/`

### Option B : Terminal VS Code

Si vous avez accès au terminal de votre machine locale :

```bash
# Depuis votre Mac, ouvrir Terminal et exécuter :
# (Remplacez USERNAME par votre nom d'utilisateur du devcontainer)

scp username@devcontainer:/workspaces/paris-live/PARIS_LIVE_AUTONOME_macOS.zip ~/Downloads/
```

---

## 📥 MÉTHODE 2 : VIA GITHUB

Si ce workspace est connecté à GitHub :

```bash
# Dans le terminal du devcontainer
cd /workspaces/paris-live
git add PARIS_LIVE_AUTONOME_macOS.zip INSTALLATION_macOS.md
git commit -m "Package autonome pour macOS"
git push origin main
```

Puis sur votre Mac :
```bash
# Ouvrir Terminal
cd ~/Downloads
git clone https://github.com/iwaine/paris-live.git
cd paris-live
unzip PARIS_LIVE_AUTONOME_macOS.zip
```

---

## 📥 MÉTHODE 3 : VIA CLOUD (Dropbox, Google Drive, etc.)

### Depuis le devcontainer :

```bash
# Installer rclone si disponible ou utiliser curl pour upload
cd /workspaces/paris-live

# Exemple avec transfer.sh (service temporaire)
curl --upload-file PARIS_LIVE_AUTONOME_macOS.zip https://transfer.sh/PARIS_LIVE_AUTONOME_macOS.zip
```

Le service retournera une URL que vous pourrez ouvrir sur votre Mac.

---

## 🍎 INSTALLATION SUR VOTRE MAC

Une fois le fichier `PARIS_LIVE_AUTONOME_macOS.zip` téléchargé sur votre Mac :

### 1. Extraire l'archive

```bash
# Ouvrir Terminal (Cmd + Espace, tapez "Terminal")
cd ~/Downloads

# Double-clic sur le ZIP dans Finder, OU :
unzip PARIS_LIVE_AUTONOME_macOS.zip

# Naviguer dans le dossier
cd PACKAGE_AUTONOME
```

### 2. Lire le guide d'installation

```bash
cat INSTALLATION_macOS.md
# OU ouvrir dans un éditeur de texte
open -a TextEdit INSTALLATION_macOS.md
```

### 3. Installation automatique (3 commandes)

```bash
# 1. Rendre le script exécutable
chmod +x install.sh

# 2. Lancer l'installation
./install.sh
# (Vous devrez entrer votre TOKEN et CHAT_ID Telegram)

# 3. Lire le Quick Start
cat QUICK_START.md
```

### 4. Premier test (30 secondes)

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Tester Telegram
python3 -c "
from telegram_notifier import TelegramNotifier
TelegramNotifier().send_message('✅ Mac setup réussi!')
"
```

Vous devez recevoir un message sur Telegram ! 🎉

---

## 📊 CONTENU DU PACKAGE

Le package `PACKAGE_AUTONOME/` contient :

### ✅ Scripts principaux
- `scrape_bulgaria_auto.py` - Collecte données Bulgarie
- `scrape_bolivia_auto.py` - Collecte données Bolivie
- `telegram_notifier.py` - Envoi alertes Telegram
- `telegram_config.py` - Configuration Telegram
- `telegram_formatter.py` - Formatage messages

### ✅ Module de prédiction `football-live-prediction/`
- `predictors/interval_predictor.py` ⭐ **AMÉLIORÉ** (forme par intervalle)
- `analyzers/` - Analyseurs de patterns
- `utils/` - Utilitaires (DB, logs, config)
- `modules/` - Scrapers SoccerStats
- `bulgaria_live_monitor.py` - Monitoring live Bulgarie
- `build_critical_interval_recurrence.py` - Génération patterns

### ✅ Documentation
- `INSTALLATION_macOS.md` ⭐ **GUIDE SPÉCIFIQUE MAC**
- `GUIDE_UTILISATION_AUTONOME.md` - Guide complet 
- `QUICK_START.md` - Démarrage rapide (5 min)
- `METHODOLOGIE_COMPLETE_V2.md` - Documentation technique
- `README.md` - Présentation
- `INDEX.md` - Navigation

### ✅ Configuration
- `.env.template` - Template pour vos clés Telegram
- `requirements.txt` - Dépendances Python
- `install.sh` - Script d'installation automatique
- `verify_package.sh` - Vérification intégrité

---

## 🎯 UTILISATION QUOTIDIENNE SUR MAC

### Démarrage rapide
```bash
cd ~/Downloads/PACKAGE_AUTONOME/football-live-prediction
source ../venv/bin/activate
python3 bulgaria_live_monitor.py --continuous --interval 120
```

### En arrière-plan (optionnel)
```bash
nohup python3 bulgaria_live_monitor.py --continuous --interval 120 > monitor.log 2>&1 &
```

### Arrêter le monitoring
```bash
# Si en premier plan : Ctrl + C
# Si en arrière-plan :
ps aux | grep bulgaria_live_monitor
kill PID_DU_PROCESS
```

---

## 🔄 MISES À JOUR

Pour mettre à jour le package sur votre Mac :

1. Re-téléchargez la nouvelle archive
2. Sauvegardez votre `.env` actuel :
   ```bash
   cp PACKAGE_AUTONOME/.env ~/backup_env
   ```
3. Extrayez la nouvelle version
4. Restaurez votre `.env` :
   ```bash
   cp ~/backup_env PACKAGE_AUTONOME/.env
   ```

---

## ✅ RÉSUMÉ DES ÉTAPES

1. ✅ **Télécharger** : `PARIS_LIVE_AUTONOME_macOS.zip` (depuis VS Code ou GitHub)
2. ✅ **Extraire** : Double-clic ou `unzip`
3. ✅ **Installer** : `./install.sh`
4. ✅ **Configurer Telegram** : TOKEN + CHAT_ID
5. ✅ **Tester** : Envoyer un message test
6. ✅ **Collecter données** : `python3 scrape_bulgaria_auto.py`
7. ✅ **Générer patterns** : `python3 build_critical_interval_recurrence.py`
8. ✅ **Monitorer** : `python3 bulgaria_live_monitor.py --continuous`

---

## 📞 AIDE

Consultez les guides dans le package :
- `INSTALLATION_macOS.md` - Guide complet macOS
- `GUIDE_UTILISATION_AUTONOME.md` - Documentation détaillée
- `QUICK_START.md` - Démarrage rapide

---

## 🎉 VOUS ÊTES 100% AUTONOME !

Le package contient TOUT ce dont vous avez besoin :
- ✅ Collecte de données automatisée
- ✅ Génération de patterns statistiques
- ✅ Monitoring live avec alertes Telegram
- ✅ Prédictions par intervalles (31-45', 75-90')
- ✅ Tous les outils et documentation
- ✅ Compatible macOS out-of-the-box

**Bon paris ! 🎯⚽💰**
