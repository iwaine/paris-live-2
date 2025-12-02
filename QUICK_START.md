# 🎯 Démarrage Rapide - Système de Prédiction Live

## 📋 Prérequis
- Python 3.12
- Virtualenv ✅ (déjà configurée)
- Compte Telegram ✅

## 🚀 Étape 1 : Installation (1 minute)

Les dépendances sont déjà installées ! Vérifiez :
```bash
cd /workspaces/paris-live
python -m pytest football-live-prediction/ -q
```

**Vous devriez voir: `18 passed`** ✅

## 🤖 Étape 2 : Configurer Telegram (5 minutes)

### A. Créer le Bot
1. Ouvrez Telegram → Cherchez **@BotFather**
2. Tapez `/newbot`
3. Suivez les instructions
4. **Notez votre TOKEN** (format: `123456:ABC...`)

### B. Obtenir votre Chat ID
1. Cherchez **@userinfobot** sur Telegram
2. Tapez `/start`
3. **Notez votre USER ID** (ex: `987654321`)

### C. Configurer les Variables
```bash
export TELEGRAM_BOT_TOKEN='votre_token_ici'
export TELEGRAM_CHAT_ID='votre_chat_id_ici'
```

### D. Tester
```bash
python test_telegram_bot_demo.py
```

## ⚽ Étape 3 : Lancer le Système (2 minutes)

```bash
cd /workspaces/paris-live/football-live-prediction
python main_live_predictor.py
```

Puis entrez une URL de match live de SoccerStats.com

## 📲 Résultat

Vous recevrez sur Telegram :
- ✅ Alertes de danger (toutes les 30 sec)
- ✅ Notifications de but
- ✅ Événements en direct (cartons, penalties)

---

## 📚 Documentation Complète

| Fichier | Contenu |
|---------|---------|
| `TELEGRAM_SETUP.md` | Guide détaillé Telegram |
| `PRODUCTION_READY.md` | Architecture et déploiement |
| `PROJECT_SUMMARY.md` | Vue d'ensemble du système |
| `README_TELEGRAM_ALERTS.md` | Alertes Telegram |
| `QUICK_START.md` | Ce fichier ! |

## 🆘 Problèmes ?

### Les dépendances ne sont pas installées ?
```bash
pip install -r football-live-prediction/requirements.txt
```

### Le bot ne reçoit rien ?
1. Vérifiez votre Token et Chat ID
2. Lancez: `python test_telegram_bot_demo.py`
3. Lisez "Troubleshooting" dans `TELEGRAM_SETUP.md`

### Vous voulez vérifier que tout marche ?
```bash
python -m pytest football-live-prediction/ -q
```

---

**Prêt ? C'est parti ! 🚀**
