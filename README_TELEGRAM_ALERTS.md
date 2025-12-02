# 🚀 Comment Recevoir les Alertes Football sur Telegram

## ⚡ TL;DR (En 5 minutes)

```bash
# 1. Créez un bot Telegram (sur @BotFather)
export TELEGRAM_BOT_TOKEN='votre_token'
export TELEGRAM_CHAT_ID='votre_chat_id'

# 2. Testez la configuration
/workspaces/paris-live/.venv/bin/python /workspaces/paris-live/test_telegram_bot_demo.py

# 3. Lancez le système
cd /workspaces/paris-live/football-live-prediction
python main_live_predictor.py

# 4. Entrez une URL de match live et profitez des alertes !
```

---

## 📖 Guide Complet

Consultez le fichier : **`TELEGRAM_SETUP.md`**

Il contient :
- ✅ Guide étape par étape pour créer le bot
- ✅ Comment obtenir le token et le Chat ID
- ✅ Comment configurer les variables d'environnement
- ✅ Comment tester et vérifier la configuration
- ✅ Troubleshooting

---

## 📱 Que Recevrez-Vous ?

### Alerte de Danger (toutes les 30 secondes)
```
🚨 ALERTE MATCH 🚨
Arsenal vs Manchester City (65 min)

Danger: ULTRA-DANGEREUX 🔴
Score de danger: 5.44/10

⏱️  Intervalle: 61-75

⚠️ Événements en direct:
🔴 Cartons rouges: Arsenal 1
🟠 Pénalités: Man City 1
```

### Notification de But
```
⚽ MAIS ⚽
Arsenal 2-1 Manchester City
Buteur: Bukayo Saka
65' de jeu
```

---

## 🎮 Commandes du Bot

Une fois le bot lancé, tapez sur Telegram :
- `/start` - Démarrer
- `/help` - Aide
- `/stats` - Statistiques
- `/stop` - Arrêter

---

## ❓ Problème ?

Consultez la section **"Troubleshooting"** dans `TELEGRAM_SETUP.md`
