# 📱 Guide Configuration Bot Telegram

## 🎯 Objectif
Recevoir les alertes de matchs en temps réel sur votre téléphone Telegram.

---

## 📋 Étape 1 : Créer un Bot avec BotFather

### Sur Telegram :
1. **Ouvrez Telegram** et cherchez **@BotFather**
2. Cliquez sur "Démarrer" (Start)
3. Tapez la commande : `/newbot`
4. **Donnez un nom au bot** :
   - Exemple: "FootballPredictorBot"
   - Ce nom s'affichera dans les conversations
5. **Donnez un username unique** :
   - Exemple: "football_predictor_bot_2025"
   - Format: doit finir par "_bot"
6. **BotFather vous donnera un TOKEN** 🔑
   - Ressemble à: `123456789:ABCDefGhIjKlMnOpQrStUvWxYz0123456`
   - **⚠️ Gardez-le SECRET ! C'est la clé de votre bot**

---

## 🔍 Étape 2 : Obtenir votre User ID

### Sur Telegram :
1. Cherchez **@userinfobot**
2. Cliquez sur "Démarrer" (Start)
3. **Bot affichera votre User ID** 📌
   - Exemple: `987654321`
   - C'est un nombre, rien d'autre

---

## 🚀 Étape 3 : Configurer les Variables d'Environnement

### Méthode 1 : En ligne de commande (temporaire)
```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCDefGhIjKlMnOpQrStUvWxYz0123456'
export TELEGRAM_CHAT_ID='987654321'
```

### Méthode 2 : Fichier .env (persistant)
1. Créez un fichier `.env` à la racine :
```bash
cat > /workspaces/paris-live/.env << 'EOF'
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIjKlMnOpQrStUvWxYz0123456
TELEGRAM_CHAT_ID=987654321
EOF
```

2. Ou éditez le fichier manuellement dans VS Code

---

## ✅ Étape 4 : Tester la Configuration

### Test simple (affiche les messages dans le terminal)
```bash
cd /workspaces/paris-live
python test_telegram_bot_demo.py
```

### Vous devriez voir :
```
======================================================================
🤖 DÉMONSTRATION BOT TELEGRAM
======================================================================

✅ Configuration trouvée:
   Token: 123456789:ABCDefGhIjKlMnOpQr...
   Chat ID: 987654321

======================================================================
📤 ENVOI DE NOTIFICATIONS DE TEST
======================================================================

1️⃣  Envoi d'une alerte simple...
   Résultat: ✅ Succès

2️⃣  Envoi d'une alerte avec CARTON ROUGE...
   Résultat: ✅ Succès

3️⃣  Envoi d'une notification de BUT...
   Résultat: ✅ Succès
```

### Sur Telegram, vous recevrez :
```
🚨 ALERTE MATCH 🚨
Arsenal vs Manchester City (35 min)

Danger: ULTRA-DANGEREUX 🔴
Score de danger: 4.62/10

⏱️  Intervalle: 31-45
```

---

## 🎮 Étape 5 : Lancer le Système Complet

### Option A : Interface Interactif (recommandé)
```bash
cd /workspaces/paris-live/football-live-prediction
python main_live_predictor.py
```

**Puis entrez une URL de match live** (exemple):
```
https://www.soccerstats.com/pmatch.asp?league=england&stats=...
```

### Option B : Monitoring Automatique
```bash
cd /workspaces/paris-live/football-live-prediction
python manage_telegram.py monitor https://www.soccerstats.com/pmatch.asp?...
```

### Option C : Mode Démon (en arrière-plan)
```bash
cd /workspaces/paris-live/football-live-prediction
nohup python main_live_predictor.py > bot.log 2>&1 &

# Pour voir les logs :
tail -f bot.log
```

---

## 📲 Que Recevrez-Vous ?

### 1️⃣ Alerte de Danger (toutes les 30 secondes)
```
🚨 ALERTE MATCH 🚨
Arsenal vs Manchester City (65 min)

Danger: ULTRA-DANGEREUX 🔴
Score de danger: 5.44/10

⏱️  Intervalle: 61-75

⚠️ Événements en direct:
🔴 Cartons rouges: Arsenal 1
🟠 Pénalités: Man City 1

Modificateurs:
• Arsenal: ×0.7 (effet carton rouge)
• Man City: ×1.4 (effet penalty)
```

### 2️⃣ Notification de But
```
⚽ MAIS ⚽
Arsenal 2-1 Manchester City

Buteur: Bukayo Saka
65' de jeu

Événements: 1 carton rouge, 1 penalty
```

### 3️⃣ Fin de Match
```
🏁 MATCH TERMINÉ
Arsenal 2-2 Manchester City

⏱️  Durée totale: 90 minutes
📊 Stats: 18 tirs vs 15 tirs
```

---

## 🔧 Commandes du Bot

Une fois le bot lancé, vous pouvez utiliser sur Telegram :

| Commande | Description |
|----------|-------------|
| `/start` | Démarrer le bot |
| `/help` | Afficher l'aide |
| `/match` | Info du match en cours |
| `/stats` | Statistiques de précision |
| `/stop` | Arrêter le bot |

---

## ❓ Troubleshooting

### Problème : "No module named 'loguru'"
**Solution :**
```bash
pip install loguru
```

### Problème : "TELEGRAM_BOT_TOKEN not found"
**Solution :** Vérifiez que vous avez configuré les variables :
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

Si vides, relancez les exports :
```bash
export TELEGRAM_BOT_TOKEN='votre_token'
export TELEGRAM_CHAT_ID='votre_chat_id'
```

### Problème : "Failed to send message"
**Causes possibles :**
1. Pas de connexion Internet
2. Token ou Chat ID invalides
3. Bot n'a pas les permissions
4. Rate limit Telegram (attendre quelques secondes)

### Problème : Les messages n'arrivent pas
**Vérifications :**
1. Vérifiez que vous avez démarré une conversation avec le bot (@username_bot)
2. Vérifiez le Chat ID (doit être un nombre)
3. Lançez le test : `python test_telegram_bot_demo.py`

---

## 📚 Fichiers Clés

| Fichier | Description |
|---------|-------------|
| `football-live-prediction/main_live_predictor.py` | Programme principal |
| `football-live-prediction/utils/telegram_bot.py` | Code du bot Telegram |
| `football-live-prediction/utils/match_monitor.py` | Monitoring en temps réel |
| `test_telegram_bot_demo.py` | Démonstration du bot |

---

## 💡 Exemple Complet

```bash
# 1. Configuration
export TELEGRAM_BOT_TOKEN='123456789:ABCDefGhIjKlMnOpQrStUvWxYz0123456'
export TELEGRAM_CHAT_ID='987654321'

# 2. Test
python test_telegram_bot_demo.py
# ✅ Vérifiez que les messages arrivent sur Telegram

# 3. Lancer le système
cd football-live-prediction
python main_live_predictor.py

# 4. Entrez une URL de match live quand demandé
# 5. Recevez les alertes sur Telegram !
```

---

## 🎓 Pour en Savoir Plus

- **Documentation complète**: voir `PRODUCTION_READY.md`
- **Architecture**: voir `PROJECT_SUMMARY.md`
- **API Bot Telegram**: https://core.telegram.org/bots/api

---

**Prêt à recevoir des alertes ? 🚀**
