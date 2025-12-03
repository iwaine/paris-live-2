# 🤖 Guide du Système de Surveillance Automatique

## 📋 Vue d'ensemble

`auto_live_monitor.py` est un système **100% automatique** qui:

1. ✅ **Détecte** tous les matchs live sur 44+ ligues (toutes les 5 min)
2. ✅ **Extrait** les données complètes (équipes, score, minute, stats)
3. ✅ **Prédit** le danger score en temps réel
4. ✅ **Alerte** via Telegram si danger élevé
5. ✅ **Stocke** tout en base de données

**Résultat**: Tu n'as plus à chercher les matchs manuellement! Le système fait tout automatiquement.

---

## 🚀 Démarrage Rapide

### Installation

```bash
# 1. S'assurer que toutes les dépendances sont installées
pip install -r requirements.txt
pip install python-telegram-bot

# 2. Configurer Telegram (optionnel mais recommandé)
export TELEGRAM_BOT_TOKEN="ton_token"
export TELEGRAM_CHAT_ID="ton_chat_id"
```

### Usage Simple

```bash
# Lancer en mode test (1 cycle uniquement)
python3 auto_live_monitor.py --test

# Lancer en mode production (surveillance continue)
python3 auto_live_monitor.py

# Lancer avec options personnalisées
python3 auto_live_monitor.py --detection-interval 180 --max-cycles 10
```

---

## 📊 Modes d'Utilisation

### Mode 1: Test (Recommandé pour débuter)

Lance **un seul cycle** de détection pour tester:

```bash
python3 auto_live_monitor.py --test
```

**Résultat**:
- Scan des 44 ligues
- Détection des matchs live
- Extraction des données
- Prédictions
- Puis arrêt automatique

**Utilité**: Vérifier que tout fonctionne avant de lancer en continu.

---

### Mode 2: Production (Surveillance Continue)

Lance la surveillance en **continu**:

```bash
python3 auto_live_monitor.py
```

**Comportement**:
- Détection toutes les 5 minutes (par défaut)
- Surveillance de chaque match détecté
- Alertes Telegram automatiques
- Stockage en BD
- Tourne jusqu'à Ctrl+C

---

### Mode 3: Personnalisé

```bash
# Scan toutes les 3 minutes (180s)
python3 auto_live_monitor.py --detection-interval 180

# Limiter à 20 cycles (environ 1h40 si interval=300s)
python3 auto_live_monitor.py --max-cycles 20

# Sans Telegram
python3 auto_live_monitor.py --no-telegram

# Sans Base de Données
python3 auto_live_monitor.py --no-database

# Combinaison
python3 auto_live_monitor.py --detection-interval 180 --max-cycles 10 --no-telegram
```

---

## 🎯 Options de la Ligne de Commande

| Option | Description | Défaut |
|--------|-------------|--------|
| `--config PATH` | Chemin vers config.yaml | `config.yaml` |
| `--detection-interval N` | Intervalle de détection (secondes) | `300` (5 min) |
| `--monitor-interval N` | Intervalle de surveillance par match | `60` (1 min) |
| `--max-cycles N` | Nombre maximum de cycles | Illimité |
| `--no-telegram` | Désactiver Telegram | Non |
| `--no-database` | Désactiver BD | Non |
| `--test` | Mode test (1 cycle) | Non |

---

## 📈 Fonctionnement Détaillé

### Cycle de Détection (toutes les 5 min)

```
┌─ CYCLE 1 ──────────────────────────────────────┐
│                                                 │
│  1. Scan 44 ligues pour matchs live            │
│     ├─ France Ligue 1                          │
│     ├─ England Premier League                  │
│     ├─ Spain LaLiga                            │
│     └─ ... (41 autres)                         │
│                                                 │
│  2. Pour chaque match NOUVEAU détecté:         │
│     ├─ Extraire données complètes              │
│     │   (équipes, score, minute, stats)        │
│     ├─ Stocker en BD                           │
│     ├─ Faire prédiction                        │
│     ├─ Alerte Telegram si danger >= 3.5        │
│     └─ Ajouter aux matchs actifs               │
│                                                 │
│  3. Nettoyer matchs terminés                   │
│                                                 │
└─────────────────────────────────────────────────┘
         ↓
      Wait 5 min
         ↓
┌─ CYCLE 2 ──────────────────────────────────────┐
│  ...                                            │
└─────────────────────────────────────────────────┘
```

---

## 🔔 Notifications Telegram

Le système envoie **3 types d'alertes**:

### 1. Nouveau Match Détecté

```
🏟️  NOUVEAU MATCH LIVE DÉTECTÉ

Ligue: France – Ligue 1
Match: PSG vs Marseille
Score: 1-1
Minute: 38'

📊 Surveillance en cours...
```

### 2. Alerte Danger (si danger_score >= 3.5)

```
🔴 ALERTE DANGER ÉLEVÉ

PSG vs Marseille (65')
Score: 1-1
Danger Score: 4.25 → ULTRA-DANGEREUX

⚡ RECOMMANDATION: PARIER MAINTENANT
Confidence: TRÈS HAUTE
```

### 3. Nouveau But (si détecté)

```
⚽ BUT MARQUÉ!

PSG 2-1 Marseille
Buteur: PSG
Minute: 67'
```

---

## 💾 Base de Données

Toutes les données sont stockées dans `data/predictions.db`:

### Tables

```sql
-- Matchs détectés
matches:
  id, home_team, away_team, league, final_score
  status, created_at

-- Prédictions faites
predictions:
  id, match_id, minute, interval
  danger_score, interpretation, confidence
  predicted_at

-- Notifications envoyées
notifications:
  id, match_id, prediction_id
  notification_type, message, sent_at
```

### Consulter les Données

```bash
# Via SQLite
sqlite3 data/predictions.db "SELECT * FROM matches LIMIT 5;"

# Via Python
python3 -c "
from utils.database_manager import DatabaseManager
db = DatabaseManager()
stats = db.get_stats(days=7)
print(f'Accuracy: {stats[\"accuracy\"]}%')
db.close()
"
```

---

## 🔍 Exemple de Session

```bash
$ python3 auto_live_monitor.py --test

======================================================================
🚀 AUTO LIVE MONITOR INITIALIZED
======================================================================
📊 Leagues: 44
🔍 Detection interval: 300s
👁️  Monitor interval: 60s
💾 Database: ✅
📱 Telegram: ✅
======================================================================

======================================================================
🔍 SCANNING 44 LEAGUES FOR LIVE MATCHES
======================================================================
[1/44] Scanning: France – Ligue 1
   ⚪ No live matches
[2/44] Scanning: France – Ligue 2
   ⚪ No live matches
[3/44] Scanning: Germany – Bundesliga
   ⚪ No live matches
...
[29/44] Scanning: Bulgaria – Parva liga
   ✅ Found 1 live match(es)
[30/44] Scanning: Bosnia and Herzegovina – Premier League
   ✅ Found 2 live match(es)
...
======================================================================
🎯 TOTAL LIVE MATCHES FOUND: 3
======================================================================

[1/3] 🆕 NEW LIVE MATCH DETECTED

======================================================================
👁️  MONITORING MATCH: Bulgaria – Parva liga
🔗 URL: https://www.soccerstats.com/pmatch.asp?league=bulgaria&stats=...
======================================================================
✅ Data extracted: BEROE 1-1 CHERNO MORE (75')
💾 Match stored in DB (ID: 1)
📊 Prediction: Danger=4.12 (ULTRA-DANGEREUX) | Confidence=TRÈS HAUTE
💾 Prediction stored (ID: 1)
📱 Telegram alert sent

[2/3] 🆕 NEW LIVE MATCH DETECTED
...

🧹 Cleaning up...
✅ AUTO LIVE MONITOR STOPPED
```

---

## 🎛️ Configuration Avancée

### Fichier: `config/auto_monitor_config.yaml`

```yaml
# Intervalles
intervals:
  detection: 300        # Scan toutes les 5 min
  monitor: 60          # Update toutes les 60s

# Seuils
thresholds:
  danger_score: 3.5    # Alerte si >= 3.5
  high_danger: 4.0

# Telegram
telegram:
  enabled: true
  alerts:
    new_match: true
    danger: true
    goals: true

# Base de données
database:
  enabled: true
  path: "data/predictions.db"
  retention_days: 30
```

---

## 🐛 Troubleshooting

### Problème 1: Aucun match détecté

**Causes possibles**:
- Aucun match live actuellement
- Problème de connexion internet
- Site SoccerStats en maintenance

**Solution**:
```bash
# Test manuel de détection
python3 -c "
from scrapers.live_match_detector import LiveMatchDetector
detector = LiveMatchDetector()
matches = detector.scrape('https://www.soccerstats.com/latest.asp?league=bulgaria', 'Bulgaria')
print(f'Matches: {len(matches)}')
"
```

---

### Problème 2: Telegram ne fonctionne pas

**Vérifier**:
```bash
# Token et Chat ID configurés?
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Test manuel
python3 -c "
from utils.telegram_bot import TelegramNotifier
notifier = TelegramNotifier()
print('Connected!' if notifier.bot else 'Not connected')
"
```

**Solution**: Revoir le setup Telegram via `manage_telegram.py`

---

### Problème 3: Base de données corrompue

```bash
# Sauvegarder
cp data/predictions.db data/predictions.db.backup

# Recréer
rm data/predictions.db
python3 -c "
from utils.database_manager import DatabaseManager
db = DatabaseManager()
print('Database recreated')
db.close()
"
```

---

## 📊 Métriques & Performance

### Ressources

- **CPU**: ~5-10% en continu
- **RAM**: ~200-300 MB
- **Réseau**: ~10-20 KB/s (scan de 44 ligues)
- **Disque**: ~1 MB/jour (base de données)

### Timing

```
Scan complet (44 ligues): ~30-60 secondes
Extraction par match: ~1-2 secondes
Prédiction: <1 seconde
Cycle complet: ~1-3 minutes
```

---

## 🎯 Cas d'Usage Recommandés

### 1. Surveillance 24/7 (Serveur)

```bash
# Lancer en arrière-plan
nohup python3 auto_live_monitor.py > auto_monitor.log 2>&1 &

# Vérifier
ps aux | grep auto_live_monitor

# Arrêter
pkill -f auto_live_monitor
```

---

### 2. Surveillance Journée de Matchs

```bash
# Lancer le matin
python3 auto_live_monitor.py --max-cycles 50

# ~4h de surveillance (50 cycles × 5 min)
# S'arrête automatiquement après
```

---

### 3. Mode Debug

```bash
# Test avec logs détaillés
python3 -c "
from loguru import logger
logger.remove()
logger.add('debug.log', level='DEBUG')
" && python3 auto_live_monitor.py --test
```

---

## 🔮 Évolutions Futures

Fonctionnalités prévues:

- [ ] **Surveillance parallèle** (threading pour plusieurs matchs)
- [ ] **Filtres avancés** (ligues prioritaires, min/max minute)
- [ ] **Webhooks** pour intégrations externes
- [ ] **Dashboard web** en temps réel
- [ ] **API REST** pour accès aux données
- [ ] **Export automatique** (CSV, Excel)
- [ ] **Machine Learning** pour améliorer prédictions

---

## 📚 Documentation Connexe

- `LIVE_SCRAPING_SYSTEM.md` - Documentation du système de détection
- `README_NEW_FEATURES.md` - Guide des fonctionnalités
- `PROJECT_SUMMARY.md` - Vue d'ensemble du projet
- `manage_telegram.py` - Setup Telegram interactif

---

## 🎉 Résumé

**Avant**: Tu devais manuellement chercher les matchs, les scraper un par un, faire les prédictions...

**Maintenant**:
```bash
python3 auto_live_monitor.py
```

Et le système fait **TOUT automatiquement**! 🚀

---

**Développé**: Décembre 2025
**Status**: ✅ Production Ready
**Ligues**: 44+
**Automatisation**: 100%

🎯 **Let's automate football predictions!**
