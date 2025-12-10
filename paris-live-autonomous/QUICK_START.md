# 🚀 GUIDE DE DÉMARRAGE ULTRA-RAPIDE

## ⚡ Installation en 3 Commandes

```bash
# 1. Décompresser
tar -xzf paris-live-autonomous-v2.tar.gz
cd paris-live-autonomous

# 2. Installation automatique
./setup.sh

# 3. Lancer le menu
./start.sh
```

**C'est tout ! Le système est prêt !** 🎉

---

## 📋 Ce qui est fait automatiquement

### ✅ `./setup.sh` fait TOUT :
- Détecte votre système (macOS/Linux/Windows)
- Crée l'environnement virtuel Python
- Installe toutes les dépendances
- Vérifie la configuration Telegram
- Configure les permissions
- Affiche un résumé complet

**Durée :** ~1 minute

### ✅ `./start.sh` - Menu interactif :
```
⚽ SYSTÈME DE PRÉDICTION FOOTBALL V2.0
======================================================================

Que voulez-vous faire ?

  1. 🎯 Monitoring d'un match en direct
  2. 🔄 Mise à jour hebdomadaire (scraping + whitelists)
  3. 📊 Scraper une ligue spécifique
  4. 🎯 Générer/Régénérer les whitelists
  5. 📚 Lire la documentation
  6. 🔧 Configuration Telegram
  7. ❌ Quitter

Votre choix (1-7) :
```

---

## 🎯 Utilisation Quotidienne

### Match en direct ? 3 options :

**Option 1 - Menu interactif (Recommandé) :**
```bash
./start.sh
# Choisir option 1
```

**Option 2 - Monitoring direct :**
```bash
./auto_monitor.sh
```

**Option 3 - Commande directe :**
```bash
source .venv/bin/activate
python3 monitor_live.py
```

---

## 🔄 Mise à Jour Hebdomadaire

**Chaque lundi matin (après les matchs du weekend) :**

```bash
./start.sh
# Choisir option 2
```

**Ou directement :**
```bash
./update_weekly.sh
```

**Durée :** 20-30 minutes (automatique)

---

## 📱 Configuration Telegram (Une seule fois)

### Si pas encore fait lors de `./setup.sh` :

```bash
./start.sh
# Choisir option 6
```

**Ou manuellement :**
```bash
nano telegram_config.json
```

**Remplir :**
```json
{
  "bot_token": "8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c",
  "chat_id": "6942358056"
}
```

**Obtenir ces infos :**
- **Token** : @BotFather sur Telegram → `/newbot`
- **Chat ID** : @userinfobot sur Telegram → `/start`

---

## 🔥 EXEMPLE COMPLET - PREMIER MATCH

### Vous venez de télécharger l'archive :

```bash
# 1. Décompresser et installer (1 fois)
tar -xzf paris-live-autonomous-v2.tar.gz
cd paris-live-autonomous
./setup.sh

# 2. Configurer Telegram (1 fois)
# Suivre les instructions de setup.sh
# Ou : nano telegram_config.json

# 3. Match en cours ? Lancer le monitoring !
./start.sh
# Choisir option 1

# Exemple : Portugal - Benfica vs Sporting CP (86', 1-1)
Ligue : portugal
Équipe domicile : Benfica
Équipe extérieure : Sporting CP
Minute actuelle : 86
Buts domicile : 1
Buts extérieur : 1

# 4. Résultat immédiat sur Telegram ! 🎉
```

---

## 🛠️ Scripts Disponibles

| Script | Description | Utilisation |
|--------|-------------|-------------|
| `setup.sh` | Installation automatique complète | `./setup.sh` |
| `start.sh` | Menu interactif tout-en-un | `./start.sh` |
| `auto_monitor.sh` | Monitoring en continu | `./auto_monitor.sh` |
| `update_weekly.sh` | Mise à jour hebdomadaire | `./update_weekly.sh` |
| `monitor_live.py` | Monitoring manuel (direct) | `python3 monitor_live.py` |

---

## ✅ Vérification Post-Installation

**Après `./setup.sh`, vérifiez :**

```bash
# 1. Environnement virtuel créé
ls -la .venv/
# Doit exister

# 2. Dépendances installées
source .venv/bin/activate
pip list | grep -E "requests|beautifulsoup4|lxml"
# Doit afficher les 3 packages

# 3. Base de données présente
sqlite3 football-live-prediction/data/predictions.db "SELECT COUNT(*) FROM soccerstats_scraped_matches;"
# Doit afficher : 2288

# 4. Whitelists présentes
ls whitelists/*.json | wc -l
# Doit afficher : 8

# 5. Configuration Telegram
cat telegram_config.json
# Doit contenir vos vrais identifiants
```

**Si tout est ✅ : Vous êtes prêt !**

---

## 🆘 Dépannage Express

### Problème : "command not found: ./setup.sh"
```bash
chmod +x setup.sh
./setup.sh
```

### Problème : "externally-managed-environment"
```bash
# C'est normal sur macOS avec Homebrew
# setup.sh gère ça automatiquement avec l'environnement virtuel
./setup.sh
```

### Problème : "No module named 'requests'"
```bash
# Vous avez oublié d'activer l'environnement virtuel
source .venv/bin/activate
python3 monitor_live.py
```

### Problème : "Unable to open database"
```bash
# Vous êtes dans le mauvais dossier
pwd
# Doit afficher : .../paris-live-autonomous
cd paris-live-autonomous
./start.sh
```

---

## 🎯 Commandes Essentielles - Aide-Mémoire

```bash
# Installation (1 fois)
./setup.sh

# Lancer le menu
./start.sh

# Monitoring direct
./auto_monitor.sh

# Mise à jour hebdo
./update_weekly.sh

# Activer l'environnement (si nouveau terminal)
source .venv/bin/activate

# Scraper une ligue
python3 scrape_all_leagues_auto.py --league portugal --workers 2

# Générer whitelists
python3 generate_top_teams_whitelist.py --all
```

---

## 📚 Documentation Complète

- **QUICK_START.md** (ce fichier) - Démarrage rapide
- **README.md** - Guide de référence
- **GUIDE_AUTONOME_COMPLET.md** - Guide détaillé (500+ lignes)
- **PACKAGE_CONTENU.md** - Contenu du package

---

## 🎉 Vous êtes prêt !

**Workflow quotidien :**

1. **Ouvrir terminal** → `cd paris-live-autonomous`
2. **Lancer menu** → `./start.sh`
3. **Choisir action** → Option 1 pour monitoring
4. **Recevoir alertes** → Sur Telegram !

**C'est tout ! Profitez du système ! ⚽🚀**
