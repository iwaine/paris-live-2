# ⚡ QUICK START - DÉMARRAGE RAPIDE PARIS LIVE

## 🚀 En 3 Étapes - Démarrer le Système Production

### Étape 1️⃣: Configurer Telegram (2 min)

**Vous avez besoin de deux informations:**

#### 1. Le TOKEN du Bot (✅ Vous l'avez)
```
8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c
```

#### 2. Votre Chat ID (⚠️ À obtenir)

Deux options:

**Option A: Obtenir directement votre ID Telegram**
1. Ouvrez Telegram → Tapez **`@userinfobot`** → `/start`
2. Vous recevrez un message avec votre **User ID** (ex: 123456789)
3. Configurez dans le terminal:
   ```bash
   export TELEGRAM_CHAT_ID='123456789'  # Remplacez par votre ID
   ```

**Option B: Via un bot test (Plus simple)**
```bash
# Trouvez @Direct_goal_bot sur Telegram
# Tapez /start
# Le bot vous confirmera la connexion
```

Vérifiez la configuration:
```bash
echo "Token: $TELEGRAM_BOT_TOKEN"
echo "Chat ID: $TELEGRAM_CHAT_ID"
```

---

### Étape 2️⃣: Lancer le Déploiement (10 min)

```bash
cd /workspaces/paris-live

# Configurer les variables d'environnement
export TELEGRAM_BOT_TOKEN='8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c'
export TELEGRAM_CHAT_ID='votre_id_ici'  # Remplacez par votre ID

# Lancer le déploiement (8 étapes automatisées)
bash deploy_production.sh
```

**Le script effectue automatiquement:**
1. ✅ Vérification Python
2. ✅ Création des répertoires
3. ✅ Initialisation base de données
4. ✅ Vérification configuration
5. ✅ Test Telegram
6. ✅ Exécution des 18 tests
7. ✅ Génération documentation
8. ✅ Lancement du monitoring

---

### Étape 3️⃣: Monitorer le Système (Continu)

Une fois le déploiement terminé:

```bash
# Voir les logs en temps réel
tail -f /workspaces/paris-live/football-live-prediction/logs/production_*.log

# Vérifier que le monitoring est actif
ps aux | grep monitoring_production

# Vérifier que vous recevez les alertes Telegram ✅
# (Vous devriez recevoir un message de test)
```

---

## ✅ Checklist - Avant de Démarrer

- [ ] Python 3.12: `python3 --version` → Python 3.12+
- [ ] Virtualenv: `ls /workspaces/paris-live/.venv` → ✅ Existe
- [ ] Dépendances: `pip list | grep telegram` → ✅ python-telegram-bot
- [ ] Configuration: `cat /workspaces/paris-live/football-live-prediction/config/config.yaml | head -10` → ✅ Voir config
- [ ] Tests: `pytest -q 2>&1 | tail -1` → **18 passed**

---

## 📊 À Quoi S'Attendre

### Au Lancement
```
✅ Python trouvé: Python 3.12.7
✅ Répertoires créés
✅ Base de données initialisée
✅ Configuration YAML valide
   - Équipes: 243
   - Ligues: france, germany, italy, spain, england, ...
✅ Référence des ligues valide (40+ ligues)
✅ Connexion Telegram réussie
   - Bot: @Direct_goal_bot
✅ Message de test envoyé
✅ Tests: 18 passed in 10.95s
✅ Documentation générée
✅ Monitoring lancé (PID: XXXXX)
```

### Sur Telegram
```
🚀 Déploiement Production démarré avec succès!

📊 System Status:
✅ Database initialized
✅ Telegram connected
✅ 243 teams configured
✅ 40+ leagues available
```

### En Production
```
🚀 **PARIS LIVE - PRODUCTION MONITORING STARTED**

📊 System Status:
✅ Database initialized
✅ Telegram connected
✅ 243 teams configured
✅ 40+ leagues available

🎯 Monitoring:
• Real-time match tracking
• Live statistics analysis
• Event detection (goals, cards, injuries)
• Automated alerts via Telegram
```

---

## 🔧 Commandes Utiles

### Status du Système
```bash
# Voir si le monitoring est actif
ps aux | grep "python.*monitoring"

# Voir le nombre de matches surveillés
sqlite3 /workspaces/paris-live/football-live-prediction/data/production.db \
  "SELECT COUNT(*) FROM matches;"

# Voir les événements détectés
sqlite3 /workspaces/paris-live/football-live-prediction/data/production.db \
  "SELECT * FROM stats LIMIT 5;"
```

### Logs
```bash
# Voir tous les logs
ls -lh /workspaces/paris-live/football-live-prediction/logs/

# Voir les 50 dernières lignes
tail -50 /workspaces/paris-live/football-live-prediction/logs/production_*.log

# Filtrer par niveau
grep "ERROR" /workspaces/paris-live/football-live-prediction/logs/production_*.log
grep "INFO" /workspaces/paris-live/football-live-prediction/logs/production_*.log

# Suivre en direct
tail -f /workspaces/paris-live/football-live-prediction/logs/production_*.log | grep -E "Match|Event|ERROR"
```

### Tests
```bash
# Lancer tous les tests
cd /workspaces/paris-live/football-live-prediction
pytest -v

# Lancer un test spécifique
pytest test_telegram_alerts.py::test_send_match_alert_with_no_events -v

# Voir la couverture
pytest --cov=. --cov-report=html
```

### Base de Données
```bash
# Voir la structure
sqlite3 /workspaces/paris-live/football-live-prediction/data/production.db ".schema"

# Voir les matchs
sqlite3 /workspaces/paris-live/football-live-prediction/data/production.db \
  "SELECT match_id, home_team, away_team, status FROM matches ORDER BY created_at DESC LIMIT 10;"

# Exporter les données
sqlite3 /workspaces/paris-live/football-live-prediction/data/production.db \
  ".mode csv" \
  "SELECT * FROM matches;" > matches_export.csv
```

---

## ⚠️ Troubleshooting

### Erreur: "Chat not found"
```bash
# Le Chat ID est incorrect
# 1. Obtenez le bon Chat ID auprès de @userinfobot
# 2. Mettez à jour:
export TELEGRAM_CHAT_ID='votre_bon_id'

# 3. Relancez
bash /workspaces/paris-live/deploy_production.sh
```

### Erreur: "ModuleNotFoundError"
```bash
# Les dépendances ne sont pas installées
cd /workspaces/paris-live
source .venv/bin/activate
pip install -r football-live-prediction/requirements.txt

# Puis relancez
bash deploy_production.sh
```

### Erreur: "Database is locked"
```bash
# Tuer tous les processus Python actifs
pkill -f "python.*monitoring"
pkill -f "python.*prediction"

# Supprimer les fichiers de verrou
rm -f /workspaces/paris-live/football-live-prediction/data/*.db-journal

# Relancer
bash /workspaces/paris-live/deploy_production.sh
```

### Pas de message Telegram
```bash
# 1. Vérifier que le token est correct
echo $TELEGRAM_BOT_TOKEN

# 2. Vérifier que le Chat ID est correct (doit être un nombre)
echo $TELEGRAM_CHAT_ID

# 3. Vérifier que @Direct_goal_bot est accessible sur Telegram
# 4. Vérifier les logs pour les erreurs
tail -f /workspaces/paris-live/football-live-prediction/logs/production_*.log | grep -i telegram
```

---

## 📚 Documentation Complète

- **README.md** - Vue d'ensemble du projet
- **TELEGRAM_SETUP.md** - Configuration Telegram détaillée
- **LEAGUE_IDS_REFERENCE.md** - Toutes les ligues supportées
- **PRODUCTION_READY.md** - Checklist de production
- **PROJECT_SUMMARY.md** - Résumé technique

---

## 🎯 Résumé - Prêt pour le Déploiement Production

| Composant | Status | Notes |
|-----------|--------|-------|
| Python 3.12 | ✅ Prêt | Configuré à `/workspaces/paris-live/.venv` |
| Dépendances | ✅ Prêt | 21 packages installés |
| Configuration | ✅ Prêt | 243 équipes, 40+ ligues |
| Tests | ✅ 18/18 | Tous passants |
| Base Données | ✅ Prêt | SQLite production.db |
| Bot Telegram | ✅ Connecté | @Direct_goal_bot |
| Chat ID | ⏳ À configurer | Obtenir auprès de @userinfobot |
| Déploiement | ✅ Prêt | Script deploy_production.sh |
| Monitoring | ✅ Prêt | monitoring_production.py |

**Status Global: 🟢 PRÊT POUR DÉPLOIEMENT PRODUCTION**

---

## 🚀 Lancer Maintenant!

```bash
cd /workspaces/paris-live

# 1. Configurer le Chat ID
export TELEGRAM_CHAT_ID='123456789'  # Remplacez par votre ID

# 2. Lancer le déploiement
bash deploy_production.sh

# 3. Suivre les logs
tail -f football-live-prediction/logs/production_*.log

# 4. 🎉 Recevoir les alertes Telegram en temps réel!
```

---

**Besoin d'aide?** Consultez les logs: `tail -f /workspaces/paris-live/football-live-prediction/logs/production_*.log`
