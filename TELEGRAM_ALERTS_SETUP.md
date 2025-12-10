# 📱 Configuration Alertes Telegram - Guide Rapide

## 🎯 Objectif
Recevoir des notifications instantanées sur Telegram quand un intervalle critique est détecté avec probabilité élevée.

---

## 📋 Étape 1 : Créer un Bot Telegram

### 1.1 Ouvrir Telegram et chercher **@BotFather**

### 1.2 Créer votre bot
```
/newbot
```

### 1.3 Donner un nom à votre bot
```
Exemple : Paris Live Predictor
```

### 1.4 Donner un username (doit finir par "bot")
```
Exemple : paris_live_pred_bot
```

### 1.5 **IMPORTANT** : Récupérer le Token
```
BotFather vous donnera un token comme :
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**⚠️ GARDEZ CE TOKEN SECRET !**

---

## 📋 Étape 2 : Obtenir votre Chat ID

### 2.1 Démarrer une conversation avec votre bot
- Cherchez votre bot dans Telegram (username donné précédemment)
- Cliquez sur **START**
- Envoyez un message (n'importe quoi, ex: "Hello")

### 2.2 Récupérer votre Chat ID
Ouvrez cette URL dans votre navigateur (remplacez `YOUR_BOT_TOKEN`) :
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

**Exemple** :
```
https://api.telegram.org/bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
```

### 2.3 Chercher votre Chat ID dans la réponse JSON
```json
{
  "result": [
    {
      "message": {
        "chat": {
          "id": 987654321,  ← VOTRE CHAT ID
          "first_name": "Votre Nom"
        }
      }
    }
  ]
}
```

---

## 📋 Étape 3 : Configuration du Système

### 3.1 Installer la dépendance Python
```bash
pip install python-telegram-bot
```

### 3.2 Créer fichier de configuration
Créez `/workspaces/paris-live/telegram_config.py` :

```python
# Configuration Telegram Bot
TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Votre token
TELEGRAM_CHAT_ID = "987654321"  # Votre chat ID

# Seuils d'alerte
ALERT_THRESHOLD_COMBINED = 0.80  # Alerte si probabilité combinée ≥ 80%
ALERT_THRESHOLD_SINGLE = 0.75    # Alerte si une équipe ≥ 75%

# Activer/désactiver alertes
ALERTS_ENABLED = True
```

---

## 📋 Étape 4 : Tester l'Envoi

### 4.1 Script de test
```python
import requests

BOT_TOKEN = "VOTRE_TOKEN"
CHAT_ID = "VOTRE_CHAT_ID"

message = """
🚨 TEST ALERTE

Match : Test vs Test
Probabilité : 95%

C'est un test !
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
data = {
    "chat_id": CHAT_ID,
    "text": message,
    "parse_mode": "HTML"
}

response = requests.post(url, data=data)
print(response.json())
```

### 4.2 Exécuter le test
```bash
python3 test_telegram.py
```

Si vous recevez le message sur Telegram → **✅ Configuration OK !**

---

## 🚀 Étape 5 : Intégration dans les Moniteurs

Les moniteurs `bulgaria_live_monitor.py` et `netherlands_live_monitor.py` vont automatiquement envoyer des alertes quand :

1. **Intervalle critique actif** (31-45 ou 75-90)
2. **Probabilité combinée ≥ 80%** OU **Une équipe ≥ 75%**

### Exemple d'alerte :

```
🚨 ALERTE PAYS-BAS - SIGNAL FORT

🏟️ Vitesse Arnhem vs De Graafschap
⏱️ Minute 45 | Intervalle 31-45 ACTIF
⚽ Score : 1-1

📊 PROBABILITÉS :
  🏡 Vitesse Arnhem : 81.3%
  ✈️ De Graafschap : 92.4%
  🎯 COMBINÉ : 98.6%

✅ SIGNAL TRÈS FORT
Recommandation : Pari "But dans l'intervalle"

🔗 https://www.soccerstats.com/pmatch.asp?league=netherlands2&stats=381-12-1-2026
```

---

## 🔧 Commandes Utiles

### Démarrer le monitoring avec alertes Telegram
```bash
# Bulgarie - mode continu
cd /workspaces/paris-live/football-live-prediction
python3 bulgaria_live_monitor.py

# Pays-Bas - mode continu
python3 netherlands_live_monitor.py

# Scan unique (test)
python3 netherlands_live_monitor.py --once
```

### Arrêter le monitoring
```
Ctrl + C
```

---

## ⚙️ Paramètres Avancés

### Modifier les seuils d'alerte
Éditez `telegram_config.py` :

```python
# Alertes très sélectives (seulement signaux excellents)
ALERT_THRESHOLD_COMBINED = 0.90
ALERT_THRESHOLD_SINGLE = 0.85

# Alertes plus fréquentes (tous signaux moyens+)
ALERT_THRESHOLD_COMBINED = 0.70
ALERT_THRESHOLD_SINGLE = 0.65
```

### Désactiver temporairement les alertes
```python
ALERTS_ENABLED = False
```

---

## 📊 Statistiques d'Alertes

Le système peut logger toutes les alertes envoyées dans un fichier :

```
/workspaces/paris-live/logs/telegram_alerts.log
```

Format :
```
2025-12-04 20:45:32 | ALERT | Netherlands | Vitesse vs De Graafschap | 98.6% | SENT
2025-12-04 21:12:15 | ALERT | Bulgaria | Spartak vs Slavia | 89.3% | SENT
```

---

## 🔒 Sécurité

**⚠️ IMPORTANT** :

1. **Ne JAMAIS commit** `telegram_config.py` sur GitHub
2. Ajouter à `.gitignore` :
   ```
   telegram_config.py
   logs/telegram_alerts.log
   ```

3. Si token compromis : 
   - Aller sur @BotFather
   - `/revoke` pour révoquer le token
   - Créer un nouveau bot

---

## ✅ Checklist Finale

- [ ] Bot créé via @BotFather
- [ ] Token récupéré
- [ ] Conversation démarrée avec le bot
- [ ] Chat ID récupéré
- [ ] `telegram_config.py` configuré
- [ ] Test d'envoi réussi
- [ ] Moniteur démarré en mode continu
- [ ] Première alerte reçue

---

## 🆘 Troubleshooting

### Problème : "Unauthorized"
→ Token incorrect, vérifiez la copie du token

### Problème : "Chat not found"
→ Vous n'avez pas envoyé de message au bot, faites /start

### Problème : Pas d'alerte reçue
→ Vérifiez `ALERTS_ENABLED = True` dans config
→ Vérifiez les seuils (peut-être trop élevés)

### Problème : Trop d'alertes
→ Augmentez les seuils dans `telegram_config.py`

---

**Date** : 4 Décembre 2025  
**Version** : 1.0  
**Status** : Production-ready 🚀
