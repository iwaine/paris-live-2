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
