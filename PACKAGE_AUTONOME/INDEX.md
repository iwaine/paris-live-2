# 📑 INDEX DE NAVIGATION - PACKAGE AUTONOME

**Bienvenue dans votre package autonome Paris-Live !**

Ce fichier vous guide vers la bonne documentation selon vos besoins.

---

## 🎯 JE VEUX...

### ➡️ Démarrer RAPIDEMENT (5 minutes)

📖 **Lire** : `QUICK_START.md`

```bash
cat QUICK_START.md
```

**Contenu** : Installation + Premier lancement en 5 étapes simples

---

### ➡️ Comprendre TOUT le système

📖 **Lire** : `GUIDE_UTILISATION_AUTONOME.md`

```bash
cat GUIDE_UTILISATION_AUTONOME.md
```

**Contenu** : 
- Installation détaillée
- Ajouter un championnat
- Configuration Telegram
- Monitoring live
- Maintenance
- Dépannage complet

**11 sections, ~500 lignes**

---

### ➡️ Comprendre la MÉTHODOLOGIE technique

📖 **Lire** : `METHODOLOGIE_COMPLETE_V2.md`

```bash
cat METHODOLOGIE_COMPLETE_V2.md
```

**Contenu** :
- Architecture de données
- Algorithmes de prédiction
- Formules mathématiques
- Pattern historique 80% + Momentum live 20%
- Exemples de calculs détaillés

**Pour les curieux de technique**

---

### ➡️ Voir le RÉSUMÉ du package

📖 **Lire** : `PACKAGE_RESUME.md`

```bash
cat PACKAGE_RESUME.md
```

**Contenu** :
- Contenu du package
- Checklist d'autonomie
- Commandes essentielles
- Métriques système
- Prochaines étapes

**Vue d'ensemble complète**

---

### ➡️ Présentation GÉNÉRALE du projet

📖 **Lire** : `README.md`

```bash
cat README.md
```

**Contenu** :
- Description du projet
- Fonctionnalités
- Technologies
- Structure

**Pour comprendre le projet en 2 minutes**

---

## 🚀 WORKFLOW RECOMMANDÉ

### Première Utilisation

1. **Lire** `README.md` (2 min) → Comprendre le projet
2. **Suivre** `QUICK_START.md` (5 min) → Lancer le système
3. **Consulter** `GUIDE_UTILISATION_AUTONOME.md` → Devenir autonome
4. **Approfondir** `METHODOLOGIE_COMPLETE_V2.md` → Maîtriser la technique

### Utilisation Quotidienne

1. **Collecter données** : `python3 scrape_PAYS_auto.py`
2. **Générer patterns** : `cd football-live-prediction && python3 build_critical_interval_recurrence.py`
3. **Lancer monitoring** : `python3 bulgaria_live_monitor.py --continuous --interval 120`

### Ajout d'un Championnat

1. **Consulter** `GUIDE_UTILISATION_AUTONOME.md` section 2
2. **Copier** `scrape_bulgaria_auto.py` → `scrape_PAYS_auto.py`
3. **Modifier** le code championnat
4. **Lancer** le scraping
5. **Régénérer** les patterns

### Résolution de Problème

1. **Consulter** `GUIDE_UTILISATION_AUTONOME.md` section 8 (Dépannage)
2. **Vérifier** les logs : `tail -f monitor.log`
3. **Tester** les composants individuellement

---

## 📁 STRUCTURE DU PACKAGE

```
PACKAGE_AUTONOME/
│
├── 📑 INDEX.md                           ← VOUS ÊTES ICI
├── 📄 README.md                          ← Présentation générale
├── 📄 QUICK_START.md                     ← Démarrage rapide 5 min
├── 📄 GUIDE_UTILISATION_AUTONOME.md      ← Guide complet détaillé
├── 📄 METHODOLOGIE_COMPLETE_V2.md        ← Documentation technique
├── 📄 PACKAGE_RESUME.md                  ← Résumé du package
│
├── 🔧 install.sh                         ← Installation automatique
├── 🔧 verify_package.sh                  ← Vérification package
├── 📋 requirements.txt                   ← Dépendances Python
├── ⚙️  .env.template                      ← Template config Telegram
│
├── 🤖 scrape_bulgaria_auto.py            ← Scraper Bulgarie
├── 🤖 scrape_bolivia_auto.py             ← Scraper Bolivie
│
├── 📨 telegram_config.py                 ← Config Telegram
├── 📨 telegram_notifier.py               ← Envoi messages
├── 📨 telegram_formatter.py              ← Formatage messages
│
└── 📁 football-live-prediction/
    ├── build_critical_interval_recurrence.py
    ├── live_predictor_v2.py
    ├── bulgaria_live_monitor.py
    ├── 📁 data/predictions.db
    └── 📁 modules/
        ├── soccerstats_live_selector.py
        └── soccerstats_live_scraper.py
```

---

## 🎯 ACTIONS RAPIDES

### Installation

```bash
./install.sh
```

### Vérification

```bash
./verify_package.sh
```

### Premier Scraping

```bash
source venv/bin/activate
python3 scrape_bulgaria_auto.py
```

### Génération Patterns

```bash
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

### Test Telegram

```bash
python3 -c "from telegram_notifier import TelegramNotifier; TelegramNotifier().send_message('✅ Test OK')"
```

### Monitoring Live

```bash
cd football-live-prediction
python3 bulgaria_live_monitor.py --once
```

---

## 🆘 AIDE RAPIDE

### Commandes Utiles

```bash
# Activer environnement
source venv/bin/activate

# Voir logs
tail -f monitor.log

# Vérifier DB
sqlite3 football-live-prediction/data/predictions.db "SELECT COUNT(*) FROM soccerstats_scraped_matches"

# Arrêter monitoring
pkill -f "live_monitor"

# Backup DB
cp football-live-prediction/data/predictions.db football-live-prediction/data/backup_$(date +%Y%m%d).db
```

### Problèmes Fréquents

| Problème | Solution | Référence |
|----------|----------|-----------|
| Telegram ne marche pas | Vérifier `.env` | GUIDE section 5.3 |
| Aucune équipe trouvée | Vérifier code championnat | GUIDE section 8.1 |
| goal_times vides | Championnat sans tooltips | GUIDE section 8.2 |
| Erreur table not found | Régénérer patterns | GUIDE section 8.4 |

---

## 📊 STATUT ACTUEL

### Championnats Configurés

- ✅ 🇧🇬 **Bulgarie** - A PFG (16 équipes, 286 matches)
- ✅ 🇧🇴 **Bolivie** - Division Profesional (16 équipes, 428 matches)

### Patterns Générés

- **Total** : 208 patterns statistiques
- **Intervalles** : 31-45' et 75-90'
- **Qualité** : 125 patterns valides (≥3 matches)

### Prêt Pour

- ✅ Monitoring live Bulgarie
- ✅ Monitoring live Bolivie
- ✅ Alertes Telegram temps réel
- ✅ Ajout de nouveaux championnats

---

## 🎓 NIVEAU D'AUTONOMIE

Après avoir suivi ce package, vous serez capable de :

| Compétence | Niveau |
|------------|--------|
| Installer le système | ⭐⭐⭐⭐⭐ Expert |
| Collecter des données | ⭐⭐⭐⭐⭐ Expert |
| Générer des patterns | ⭐⭐⭐⭐⭐ Expert |
| Configurer Telegram | ⭐⭐⭐⭐⭐ Expert |
| Lancer monitoring | ⭐⭐⭐⭐⭐ Expert |
| Ajouter championnats | ⭐⭐⭐⭐⭐ Expert |
| Maintenance système | ⭐⭐⭐⭐⭐ Expert |
| Dépannage | ⭐⭐⭐⭐⭐ Expert |

**= 100% AUTONOME ! 🚀**

---

## 🎯 POUR COMMENCER MAINTENANT

### Étape 1 : Lire le Quick Start

```bash
cat QUICK_START.md
```

### Étape 2 : Installer

```bash
./install.sh
```

### Étape 3 : Suivre le Guide

```bash
# Ouvrir dans un éditeur
nano GUIDE_UTILISATION_AUTONOME.md

# Ou lire dans le terminal
less GUIDE_UTILISATION_AUTONOME.md
```

### Étape 4 : Lancer !

Suivez les instructions du QUICK_START.md

---

**Bon monitoring ! ⚽📊🎯**

---

**Créé le** : 4 Décembre 2025  
**Version** : 2.0  
**Status** : Production Ready 🚀
