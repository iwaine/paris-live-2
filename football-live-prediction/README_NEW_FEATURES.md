# 🚀 Football Live Prediction - Système Complet

## ✅ Développement Complété

Ce document résume les **4 grandes étapes** qui viennent d'être implémentées :

### **A) 🤖 Telegram Bot pour Notifications**

**Fichier:** `utils/telegram_bot.py`

#### Fonctionnalités:
- ✅ **TelegramNotifier**: Envoie des messages formatés en HTML
- ✅ **TelegramBotApp**: Bot interactif avec commandes
- ✅ Configuration via `config/telegram_config.yaml`

#### Commandes disponibles:
```
/start       → Démarrer le bot
/help        → Afficher l'aide
/match URL   → Analyser un match
/stats       → Voir les statistiques
/stop        → Arrêter la surveillance
```

#### Types de notifications:
- 🔴 **Alerte danger**: Quand danger_score ≥ 3.5
- ⚽ **But marqué**: Notification immédiate
- 🏟️ **Début/fin de match**: Notifications de timing
- 📊 **Mise à jour**: Toutes les 15 min par défaut

#### Installation:
```bash
pip install python-telegram-bot

# Créer un bot
# 1. Ouvrez Telegram → @BotFather
# 2. Tapez /newbot
# 3. Copiez le token

# Configurer l'environnement
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstUVwxyz"
export TELEGRAM_CHAT_ID="987654321"
```

---

### **B) 🔄 Surveillance Live en Temps Réel**

**Fichier:** `utils/match_monitor.py`

#### Fonctionnalités:
- ✅ **MatchMonitor**: Surveille 1 match en continu
- ✅ **MultiMatchMonitor**: Gère plusieurs matchs
- ✅ Scrape toutes les 30 secondes (configurable)
- ✅ Détection automatique de buts
- ✅ Système de callbacks pour les événements

#### Événements détectés:
```python
on_new_goal         → But marqué
on_danger_alert     → Danger score élevé
on_update           → Mise à jour standard
on_match_start      → Début du match
on_match_end        → Fin du match
```

#### Exemple d'utilisation:
```python
from utils.match_monitor import MatchMonitor, create_telegram_callbacks
from utils.telegram_bot import TelegramNotifier

notifier = TelegramNotifier()
monitor = MatchMonitor("http://example.com/match", interval=30)

# Connecter les callbacks Telegram
callbacks = create_telegram_callbacks(notifier)
monitor.set_callbacks(**callbacks)

# Lancer la surveillance
monitor.monitor(max_duration=5400)  # 90 min max
```

---

### **C) 💾 Base de Données pour l'Historique**

**Fichier:** `utils/database_manager.py`

#### Structure de la BD:
```sql
-- Stocke tous les matchs
matches:
  ├─ home_team
  ├─ away_team
  ├─ final_score
  ├─ red_cards_home / away
  ├─ penalties_home / away
  ├─ injuries_home / away
  └─ status

-- Stocke toutes les prédictions
predictions:
  ├─ match_id
  ├─ minute
  ├─ interval
  ├─ danger_score
  ├─ interpretation
  ├─ confidence
  └─ result_correct (pour validation)

-- Notifications envoyées
notifications:
  ├─ match_id
  ├─ prediction_id
  ├─ notification_type
  └─ message

-- Cache des statistiques
stats:
  ├─ total_predictions
  ├─ correct_predictions
  ├─ accuracy
  ├─ roi
  └─ avg_danger_score
```

#### Méthodes principales:
```python
from utils.database_manager import DatabaseManager

db = DatabaseManager()

# Insérer
match_id = db.insert_match({...})
pred_id = db.insert_prediction({...})

# Requêtes
predictions = db.get_predictions_for_match(match_id)
stats = db.get_stats(days=30)
accuracy = db.get_accuracy_by_interval()

# Marquer résultat
db.mark_prediction_correct(pred_id, correct=True)

db.close()
```

#### Base de données:
```
data/predictions.db
└─ Accessible via:
   - Database Manager
   - SQLite CLI: sqlite3 data/predictions.db
   - Outils Web: sqlitebrowser
```

---

### **E) 🎯 Optimisation des Poids du Danger Score**

**Prochaine étape**: Améliorer la précision en intégrant:
- 🔴 **Cartons rouges**: Impact sur l'attaque/défense
- 📋 **Pénalités**: Augmente temporairement le danger
- 🤕 **Blessures**: Réduit les capacités offensives

#### Données à collecter:
```python
# Étendre la BD avec ces infos
match_data = {
    'red_cards_home': 1,      # Impact -30% à l'attaque
    'red_cards_away': 0,
    'penalties_home': 1,      # Impact +40% danger temporaire
    'penalties_away': 0,
    'injuries_home': ['Saka'],  # Données qualitatives
    'injuries_away': []
}
```

#### Approche d'optimisation:
1. **Collecter 50+ matchs d'historique**
2. **Analyser les corrélations**:
   - Cartons rouges → réduction danger de X%
   - Pénalités → augmentation danger de Y%
   - Blessures d'attaquants → réduction de Z%
3. **Recalculer les poids**:
   ```python
   # Actuellement: 60% attaque + 40% défense
   # Ajuster en fonction des données réelles
   ```
4. **Valider le modèle** sur les anciens matchs

---

## 📊 Résumé du Développement

### Fichiers créés:

| Fichier | Description | Status |
|---------|-------------|--------|
| `utils/telegram_bot.py` | Bot Telegram + notifications | ✅ |
| `utils/match_monitor.py` | Surveillance live | ✅ |
| `utils/database_manager.py` | Base de données | ✅ |
| `config/telegram_config.yaml` | Config Telegram | ✅ |
| `deploy_and_test.py` | Script de test | ✅ |
| `COMPLETE_SYSTEM_GUIDE.py` | Documentation complète | ✅ |

### Tests réussis:

```
✅ Base de Données: 4 prédictions stockées
✅ Prédicteur: Danger score 4.86 (ULTRA-DANGEREUX)
✅ Moniteur: Callbacks configurés et testés
✅ Intégration: Tous les composants connectés
```

---

## 🚀 Démarrage Rapide

### 1️⃣ Installation

```bash
# Installer les packages
pip install python-telegram-bot

# Créer le bot Telegram
# → Ouvrez Telegram et trouvez @BotFather
# → Tapez /newbot et suivez les instructions

# Configurer l'environnement
export TELEGRAM_BOT_TOKEN="votre_token"
export TELEGRAM_CHAT_ID="votre_chat_id"
```

### 2️⃣ Test du système

```bash
# Lancer les tests
python deploy_and_test.py

# Vérifier les logs
tail -f logs/telegram_bot.log
```

### 3️⃣ Utilisation

```bash
# Surveillance simple
python test_main_predictor.py

# Surveillance live complète (avec BD + Telegram)
python main_live_predictor.py

# Analyser l'historique
python -c "
from utils.database_manager import DatabaseManager
db = DatabaseManager()
stats = db.get_stats(30)
print(f'Accuracy: {stats[\"accuracy\"]}%')
"
```

---

## 💡 Cas d'Usage

### Scénario 1: Prédiction Simple
```python
from predictors.interval_predictor import IntervalPredictor

predictor = IntervalPredictor()
result = predictor.predict_match("Arsenal", "Manchester City", 65)
print(f"Danger: {result['danger_score']}")  # 4.86
```

### Scénario 2: Surveillance Complète
```python
from utils.telegram_bot import TelegramNotifier
from utils.match_monitor import MatchMonitor, create_telegram_callbacks
from utils.database_manager import DatabaseManager

notifier = TelegramNotifier()
db = DatabaseManager()
monitor = MatchMonitor("http://example.com/match")

# Callbacks
callbacks = create_telegram_callbacks(notifier)
monitor.set_callbacks(**callbacks)

# Insérer en BD
match_id = db.insert_match({...})

# Surveiller
monitor.monitor()
db.close()
```

### Scénario 3: Analyse Historique
```python
from utils.database_manager import DatabaseManager

db = DatabaseManager()

# Stats globales
stats = db.get_stats(days=30)
print(f"Accuracy: {stats['accuracy']}%")

# Par intervalle
by_interval = db.get_accuracy_by_interval()
for interval, data in by_interval.items():
    print(f"{interval}: {data['accuracy']}%")
```

---

## 🎯 Prochaines Étapes

### Court terme:
1. ✅ Configurer Telegram Bot (optionnel)
2. ✅ Tester sur vrai match live
3. ✅ Analyser l'historique des prédictions

### Moyen terme:
1. 🔄 Optimiser les poids du danger score
2. 🔄 Intégrer les données de cartons/pénalités
3. 🔄 Valider sur 100+ matchs

### Long terme:
1. 📈 Dashboard web
2. 🤖 Machine Learning
3. 💰 Intégration API bourses de paris

---

## ⚙️ Configuration

### Fichier: `config/telegram_config.yaml`

```yaml
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"
  
  notifications:
    danger_threshold: 3.5      # Alerte si >= 3.5
    update_interval_minutes: 15
    
    types:
      match_start: true
      danger_alert: true
      goal: true
      match_end: true
```

### Variables d'environnement:

```bash
# Tokens Telegram
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstUVwxyz"
export TELEGRAM_CHAT_ID="987654321"

# Base de données (optionnel)
export DB_PATH="data/predictions.db"
```

---

## 📈 Niveaux de Danger

```
🔴 4.0+     → ULTRA-DANGEREUX  (parier maintenant!)
🟠 3.0-4.0  → DANGEREUX        (haute probabilité)
🟡 2.0-3.0  → MODÉRÉ           (surveiller)
🟢 < 2.0    → FAIBLE           (passer)
```

---

## 🔍 Diagnostic

### Vérifier les logs:
```bash
tail -f logs/telegram_bot.log
tail -f logs/match_monitor.log
```

### Tester la BD:
```bash
sqlite3 data/predictions.db ".tables"
sqlite3 data/predictions.db "SELECT COUNT(*) FROM predictions;"
```

### Tester Telegram:
```bash
python -c "
import os
from utils.telegram_bot import TelegramNotifier
notifier = TelegramNotifier()
if notifier.bot:
    print('✅ Telegram Bot connected')
else:
    print('❌ Telegram Bot not connected')
"
```

---

## 📚 Documentation Complète

Consultez `COMPLETE_SYSTEM_GUIDE.py` pour:
- Architecture complète
- Exemples détaillés
- Checklist de déploiement
- Tips d'optimisation

---

## 🎉 Status

```
✅ A) Telegram Bot         → COMPLÉTÉ
✅ B) Surveillance Live    → COMPLÉTÉ
✅ C) Base de Données      → COMPLÉTÉ
⏳ E) Optimisation Poids   → PRÊT POUR DÉVELOPPEMENT
```

**Le système est prêt pour la production! 🚀**
