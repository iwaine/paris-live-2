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
