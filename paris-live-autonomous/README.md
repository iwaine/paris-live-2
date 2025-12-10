# ⚽ Système de Prédiction Football V2.0

## 🚀 Démarrage Rapide

### Installation Automatique (Recommandé)

```bash
# 1. Rendre le script exécutable
chmod +x setup.sh

# 2. Lancer l'installation automatique
./setup.sh
```

Le script fait TOUT automatiquement :
- ✅ Crée l'environnement virtuel
- ✅ Installe les dépendances
- ✅ Vérifie la configuration
- ✅ Configure les permissions

### Lancement Rapide

```bash
# Menu interactif tout-en-un
./start.sh
```

### Installation Manuelle (Alternative)

```bash
# 1. Créer environnement virtuel
python3 -m venv .venv

# 2. Activer l'environnement
source .venv/bin/activate

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Éditer configuration Telegram
nano telegram_config.json

# 5. Tester
python3 monitor_live.py
```

## 📚 Documentation complète

Consultez `GUIDE_AUTONOME_COMPLET.md` pour le guide détaillé.

## 🔄 Mise à jour hebdomadaire

```bash
# Automatique
./update_weekly.sh

# Ou via le menu
./start.sh
# Puis choisir option 2
```

## 🎯 Commandes Rapides

```bash
# Menu interactif
./start.sh

# Monitoring direct
./auto_monitor.sh

# Installation/Réinstallation
./setup.sh

# Mise à jour données
./update_weekly.sh
```

## 📊 Ligues supportées

- france (Ligue 1)
- germany (Bundesliga)
- germany2 (Bundesliga 2)
- england (Premier League)
- netherlands2 (Eredivisie)
- bolivia (Liga Boliviana)
- bulgaria (Bulgarian League)
- portugal (Liga Portugal)

## 🎯 Méthodologie

- **Intervalles surveillés :** 31-45' et 76-90'
- **Seuil de validation :** 65%
- **Formula MAX :** Meilleur pattern entre HOME/AWAY
- **Récurrence :** Totale + Récente (3 derniers matchs)
- **Buts comptés :** Marqués + Encaissés
