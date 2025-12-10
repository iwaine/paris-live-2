# 🚀 GUIDE D'UTILISATION AUTONOME - SYSTÈME DE PRÉDICTION LIVE

**Version** : 2.0  
**Date** : 4 Décembre 2025  
**Objectif** : Être 100% autonome de la collecte de données au monitoring live avec alertes Telegram

---

## 📋 TABLE DES MATIÈRES

1. [Prérequis & Installation](#1-prérequis--installation)
2. [Ajouter un Nouveau Championnat](#2-ajouter-un-nouveau-championnat)
3. [Collecter les Données Historiques](#3-collecter-les-données-historiques)
4. [Générer les Patterns Statistiques](#4-générer-les-patterns-statistiques)
5. [Configurer Telegram](#5-configurer-telegram)
6. [Lancer le Monitoring Live](#6-lancer-le-monitoring-live)
7. [Maintenance & Mises à Jour](#7-maintenance--mises-à-jour)
8. [Dépannage](#8-dépannage)
9. [Structure Complète du Projet](#9-structure-complète-du-projet)

---

## 1. PRÉREQUIS & INSTALLATION

### 1.1 Dépendances Python

```bash
cd /workspaces/paris-live

# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les packages nécessaires
pip install requests beautifulsoup4 python-telegram-bot python-dotenv
```

### 1.2 Vérifier l'Installation

```bash
# Tester Python
python3 --version  # Doit afficher Python 3.x

# Vérifier les packages
python3 -c "import requests, bs4, telegram; print('✅ Tous les packages sont installés')"
```

### 1.3 Base de Données

La base de données SQLite est déjà créée :
```
/workspaces/paris-live/football-live-prediction/data/predictions.db
```

**Tables principales** :
- `soccerstats_scraped_matches` : Matches historiques
- `team_critical_intervals` : Patterns statistiques

---

## 2. AJOUTER UN NOUVEAU CHAMPIONNAT

### 2.1 Identifier le Code Championnat

1. Aller sur https://www.soccerstats.com
2. Chercher votre championnat
3. Noter le code dans l'URL (ex: `league=bolivia`, `league=bulgaria`)

### 2.2 Créer le Scraper

**Template** : Copier `scrape_bulgaria_auto.py` ou `scrape_bolivia_auto.py`

```bash
# Exemple pour ajouter la France Ligue 1
cp scrape_bulgaria_auto.py scrape_france_auto.py
```

**Modifications à faire** dans le nouveau fichier :

```python
# Ligne ~18-20 : Changer le nom de la classe
class FranceAutoScraper:  # Au lieu de BulgariaAutoScraper
    BASE_URL = "https://www.soccerstats.com"
    DB_PATH = "/workspaces/paris-live/football-live-prediction/data/predictions.db"

# Ligne ~32 : Changer le code championnat par défaut
def extract_team_codes(self, league_code: str = "france") -> List[Tuple[str, str]]:

# Ligne ~152 : Adapter le pays
def scrape_team(self, team_code: str, team_name: str, league_code: str = "france") -> List[dict]:
    # ...
    match_data = {
        'country': 'France',  # Changer ici
        'league': league_code,
        # ...
    }

# Ligne ~309 : Adapter le titre
def run(self):
    print("🇫🇷 SCRAPING AUTOMATIQUE - FRANCE LIGUE 1")  # Changer ici
    # ...
    teams = self.extract_team_codes("france")  # Code championnat
```

### 2.3 Codes Championnats Disponibles

| Championnat | Code | Pays |
|------------|------|------|
| Bulgarie A PFG | `bulgaria` | 🇧🇬 Bulgaria |
| Bolivie Division Profesional | `bolivia` | 🇧🇴 Bolivia |
| Pays-Bas Eerste Divisie | `netherlands2` | 🇳🇱 Netherlands |
| France Ligue 1 | `france` | 🇫🇷 France |
| Espagne La Liga | `spain` | 🇪🇸 Spain |
| Angleterre Championship | `england2` | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England |

**Trouver d'autres championnats** : Naviguez sur soccerstats.com et regardez l'URL.

---

## 3. COLLECTER LES DONNÉES HISTORIQUES

### 3.1 Lancer le Scraping

```bash
cd /workspaces/paris-live

# Pour la Bulgarie
python3 scrape_bulgaria_auto.py

# Pour la Bolivie
python3 scrape_bolivia_auto.py

# Pour votre nouveau championnat (exemple France)
python3 scrape_france_auto.py
```

### 3.2 Sortie Attendue

```
================================================================================
🇧🇬 SCRAPING AUTOMATIQUE - BULGARIA A PFG
================================================================================

🔍 ÉTAPE 1 : Extraction des codes équipes...
✅ 16 équipes trouvées :
   • u1751-arda                     → Arda
   • u1759-beroe                    → Beroe
   ...

📥 ÉTAPE 2 : Scraping des matches
    ✅ Arda: 18 matches
    ✅ Beroe: 17 matches
    ...

💾 Sauvegarde DB: 286 matches insérés/mis à jour

✅ TOTAL: 286 matches collectés pour 16 équipes
```

### 3.3 Vérifier les Données

```bash
# Compter les matches par pays
sqlite3 football-live-prediction/data/predictions.db "
SELECT country, COUNT(*) as total_matches, COUNT(DISTINCT team) as nb_equipes
FROM soccerstats_scraped_matches
GROUP BY country
"
```

**Résultat attendu** :
```
Bulgaria|286|16
Bolivia|428|16
```

### 3.4 Vérifier les Minutes de Buts

```bash
# Voir des exemples avec goal_times
sqlite3 football-live-prediction/data/predictions.db "
SELECT team, opponent, score, goal_times, goal_times_conceded
FROM soccerstats_scraped_matches
WHERE country='Bulgaria' 
  AND goal_times != '[0,0,0,0,0,0,0,0,0,0]'
LIMIT 3
"
```

**Résultat attendu** :
```
Spartak Varna|CSKA Sofia|2-1|[42, 78, 0, 0, ...]|[89, 0, 0, ...]
```

---

## 4. GÉNÉRER LES PATTERNS STATISTIQUES

### 4.1 Lancer la Génération

```bash
cd /workspaces/paris-live/football-live-prediction

# Générer tous les patterns (tous les championnats en DB)
python3 build_critical_interval_recurrence.py
```

### 4.2 Sortie Attendue

```
================================================================================
🔄 BUILDING CRITICAL INTERVAL RECURRENCE
================================================================================

Processing 714 matches...  # Bulgaria (286) + Bolivia (428)
Found 208 team-context-interval combinations
✅ Inserted 208 recurrence records

📊 RECURRENCE QUALITY CHECK
✅ Valid recurrence patterns: 125 (≥3 matches with goals)
⚠️  Weak patterns: 83 (<3 matches with goals)

📊 TOP TEAMS - GOALS SCORED IN CRITICAL INTERVALS
Team               Loc    Interval   Goals   Matches+  Freq    Avg Min
------------------------------------------------------------------
SA Bulo Bulo       AWAY   75-90+     12      10        0.86    87.6
Bolivar            HOME   75-90+     11      8         0.85    85.0
...
```

### 4.3 Vérifier les Patterns Générés

```bash
# Compter les patterns par pays
sqlite3 football-live-prediction/data/predictions.db "
SELECT country, COUNT(*) as nb_patterns
FROM team_critical_intervals
GROUP BY country
"
```

**Résultat attendu** :
```
Bulgaria|64
Bolivia|144
Total: 208 patterns
```

### 4.4 Voir un Pattern Spécifique

```bash
# Exemple : Spartak Varna à domicile, intervalle 75-90
sqlite3 football-live-prediction/data/predictions.db "
SELECT 
  team_name,
  is_home,
  interval_name,
  freq_any_goal,
  matches_with_any_goal,
  total_matches,
  confidence_level,
  avg_minute_any_goal,
  std_minute_any_goal
FROM team_critical_intervals
WHERE team_name='Spartak Varna' AND is_home=1 AND interval_name='75-90+'
"
```

---

## 5. CONFIGURER TELEGRAM

### 5.1 Créer un Bot Telegram

1. **Ouvrir Telegram** et chercher `@BotFather`

2. **Créer le bot** :
   ```
   /newbot
   Nom : Football Live Predictor
   Username : votre_nom_unique_bot
   ```

3. **Copier le TOKEN** fourni :
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### 5.2 Obtenir votre Chat ID

1. **Démarrer une conversation** avec votre bot

2. **Envoyer un message** : `/start`

3. **Récupérer le Chat ID** :
   ```bash
   # Remplacez YOUR_BOT_TOKEN
   curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```

4. **Chercher** `"chat":{"id":123456789` dans la réponse

### 5.3 Créer le Fichier de Configuration

```bash
cd /workspaces/paris-live

# Créer le fichier .env
cat > .env << 'EOF'
# Configuration Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
EOF
```

**Remplacez** les valeurs par vos vraies informations !

### 5.4 Vérifier le Fichier telegram_config.py

Assurez-vous que le fichier existe :

```bash
cat telegram_config.py
```

**Contenu attendu** :
```python
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
```

### 5.5 Tester l'Envoi de Message

```bash
# Test rapide
python3 -c "
from telegram_notifier import TelegramNotifier
notifier = TelegramNotifier()
notifier.send_message('✅ Test : Système opérationnel!')
"
```

**Vous devez recevoir** le message sur Telegram !

---

## 6. LANCER LE MONITORING LIVE

### 6.1 Comprendre les Moniteurs

Chaque championnat a son propre moniteur :

```
bulgaria_live_monitor.py    → Bulgarie
bolivia_live_monitor.py     → Bolivie (à créer)
france_live_monitor.py      → France (à créer)
```

### 6.2 Créer un Moniteur pour la Bolivie

```bash
cd /workspaces/paris-live

# Copier le template bulgare
cp football-live-prediction/bulgaria_live_monitor.py football-live-prediction/bolivia_live_monitor.py
```

**Modifications à faire** :

```python
# Ligne ~40-50 : Mapping noms équipes boliviennes
BOLIVIA_TEAM_MAPPINGS = {
    "always ready": "Always Ready",
    "the strongest": "The Strongest",
    "bolivar": "Bolivar",
    # ... ajouter tous les mappings nécessaires
}

# Ligne ~60 : Fonction de normalisation
def normalize_team_name_bolivia(name: str) -> str:
    normalized = name.lower().strip()
    return BOLIVIA_TEAM_MAPPINGS.get(normalized, name)

# Ligne ~100-120 : Adapter la fonction principale
def monitor_bolivia_live():
    print("🇧🇴 BOLIVIA LIVE MONITOR")
    
    # Détecter matches live
    live_matches = detect_live_matches("bolivia")
    
    for match in live_matches:
        # Normaliser noms
        home = normalize_team_name_bolivia(match['home_team'])
        away = normalize_team_name_bolivia(match['away_team'])
        
        # Créer contexte
        context = LiveMatchContext(
            home_team=home,
            away_team=away,
            current_minute=match['minute'],
            home_score=match['home_score'],
            away_score=match['away_score'],
            country='Bolivia',
            league='bolivia',
            # ... stats live
        )
        
        # Prédire
        predictor = LivePredictorV2()
        predictions = predictor.predict_intervals(context)
        
        # Alertes Telegram si intervalle critique actif
        for pred in predictions:
            if pred.is_active and pred.probability >= 0.75:
                send_telegram_alert(context, pred)

# Ligne ~200 : Point d'entrée
if __name__ == "__main__":
    monitor_bolivia_live()
```

### 6.3 Lancer le Monitoring - Mode Scan Unique

```bash
cd /workspaces/paris-live/football-live-prediction

# Bulgarie - 1 scan
python3 bulgaria_live_monitor.py --once

# Bolivie - 1 scan
python3 bolivia_live_monitor.py --once
```

### 6.4 Lancer le Monitoring - Mode Continu

```bash
# Scan continu toutes les 2 minutes (120 secondes)
python3 bulgaria_live_monitor.py --continuous --interval 120

# Ou en arrière-plan
nohup python3 bulgaria_live_monitor.py --continuous --interval 120 > monitor.log 2>&1 &
```

### 6.5 Sortie Attendue

```
🇧🇬 BULGARIA LIVE MONITOR
================================================================================

📡 Scan #1 - 2025-12-04 22:30:00

🔍 Détection matches live...
✅ 2 matches en cours :
   • Spartak Varna vs Slavia Sofia (78', score 1-1)
   • CSKA Sofia vs Levski Sofia (42', score 0-0)

📊 Match 1 : Spartak Varna vs Slavia Sofia
   Minute : 78' (Intervalle 75-90 ACTIF ⚡)
   Score : 1-1
   
   🏠 Spartak Varna (HOME)
      Probabilité : 87.4% (EXCELLENT 🔥)
      Timing : 83.8 ± 6.5 → Buts attendus entre 77'-90'
   
   ✈️  Slavia Sofia (AWAY)
      Probabilité : 71.8% (TRES_BON 🟢)
      Timing : 82.8 ± 3.7 → Buts attendus entre 79'-86'
   
   🎯 PROBABILITÉ COMBINÉE : 96.5% - 🟢 SIGNAL TRÈS FORT
   
   📨 Alerte Telegram envoyée !

================================================================================
⏳ Prochain scan dans 120 secondes...
```

### 6.6 Message Telegram Reçu

```
🚨 ALERTE INTERVALLE CRITIQUE !

🇧🇬 Bulgaria - A PFG
Spartak Varna 🆚 Slavia Sofia
⏱ Minute 78' | Score 1-1

📊 INTERVALLE 75-90' ACTIF

🎯 Probabilité But : 96.5%
Signal : 🟢 TRÈS FORT

🏠 Spartak Varna : 87.4%
✈️ Slavia Sofia : 71.8%

⏰ Timing attendu : 77'-90'
💡 Écart-type faible = Timing précis

#Bulgaria #Live #Prediction
```

---

## 7. MAINTENANCE & MISES À JOUR

### 7.1 Mettre à Jour les Données (Hebdomadaire)

```bash
# Re-scraper tous les championnats
python3 scrape_bulgaria_auto.py
python3 scrape_bolivia_auto.py

# Régénérer les patterns
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

### 7.2 Nettoyer les Anciennes Données

```bash
# Supprimer matches > 1 an
sqlite3 football-live-prediction/data/predictions.db "
DELETE FROM soccerstats_scraped_matches
WHERE date < date('now', '-1 year')
"

# Régénérer les patterns
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

### 7.3 Backup de la Base de Données

```bash
# Créer un backup
cp football-live-prediction/data/predictions.db \
   football-live-prediction/data/predictions_backup_$(date +%Y%m%d).db

# Vérifier les backups
ls -lh football-live-prediction/data/predictions*.db
```

### 7.4 Ajouter de Nouvelles Équipes

Si un championnat ajoute des équipes en cours de saison :

```bash
# Re-scraper (détecte automatiquement les nouvelles équipes)
python3 scrape_bulgaria_auto.py

# Régénérer patterns
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

---

## 8. DÉPANNAGE

### 8.1 Problème : Aucune Équipe Trouvée

**Symptôme** :
```
✅ 0 équipes trouvées
❌ Aucune équipe trouvée!
```

**Solutions** :

1. **Vérifier le code championnat** :
   ```bash
   # Tester l'URL manuellement
   curl -s "https://www.soccerstats.com/formtable.asp?league=VOTRE_CODE" | grep -i "teamstats"
   ```

2. **Vérifier la connexion** :
   ```bash
   ping soccerstats.com
   ```

3. **Regarder le HTML** :
   ```bash
   curl -s "https://www.soccerstats.com/formtable.asp?league=bulgaria" > test.html
   # Ouvrir test.html dans un navigateur
   ```

### 8.2 Problème : goal_times Vides

**Symptôme** :
```sql
goal_times: [0,0,0,0,0,0,0,0,0,0]
goal_times_conceded: [0,0,0,0,0,0,0,0,0,0]
```

**Cause** : Le championnat n'a pas de tooltips avec les minutes de buts sur soccerstats.com.

**Solution** : Utiliser une source alternative ou accepter de ne pas avoir les minutes (patterns basés uniquement sur fréquence).

### 8.3 Problème : Telegram Ne Reçoit Pas de Messages

**Vérifications** :

1. **Token correct** :
   ```bash
   cat .env | grep TOKEN
   ```

2. **Chat ID correct** :
   ```bash
   cat .env | grep CHAT_ID
   ```

3. **Test API Telegram** :
   ```bash
   TOKEN="votre_token"
   CHAT_ID="votre_chat_id"
   
   curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=Test"
   ```

4. **Vérifier les logs** :
   ```bash
   tail -f monitor.log  # Si lancé en background
   ```

### 8.4 Problème : Erreur "Table Not Found"

**Symptôme** :
```
sqlite3.OperationalError: no such table: team_critical_intervals
```

**Solution** :
```bash
# Régénérer la table
cd football-live-prediction
python3 build_critical_interval_recurrence.py
```

### 8.5 Problème : Noms d'Équipes Non Reconnus

**Symptôme** :
```
⚠️  Équipe non trouvée dans DB : Sp. Varna
```

**Solution** : Ajouter le mapping dans le moniteur :

```python
TEAM_MAPPINGS = {
    "sp. varna": "Spartak Varna",
    "lok. plovdiv": "Lok. Plovdiv",
    # Ajouter ici...
}
```

### 8.6 Problème : Processus Bloqué

```bash
# Trouver le processus
ps aux | grep python | grep monitor

# Tuer le processus
kill -9 PID

# Ou tuer tous les moniteurs
pkill -f "live_monitor"
```

---

## 9. STRUCTURE COMPLÈTE DU PROJET

### 9.1 Arborescence Fichiers

```
/workspaces/paris-live/
│
├── 📄 .env                              # Config Telegram (PRIVÉ)
├── 📄 telegram_config.py                # Chargement config Telegram
├── 📄 telegram_notifier.py              # Envoi messages Telegram
├── 📄 telegram_formatter.py             # Formatage messages riches
│
├── 📄 scrape_bulgaria_auto.py           # Scraper Bulgarie
├── 📄 scrape_bolivia_auto.py            # Scraper Bolivie
├── 📄 scrape_PAYS_auto.py               # Template pour nouveau pays
│
├── 📁 football-live-prediction/
│   │
│   ├── 📁 data/
│   │   └── 📄 predictions.db            # Base de données SQLite
│   │
│   ├── 📄 build_critical_interval_recurrence.py  # Génération patterns
│   ├── 📄 live_predictor_v2.py                   # Moteur prédiction
│   │
│   ├── 📄 bulgaria_live_monitor.py      # Moniteur Bulgarie
│   ├── 📄 bolivia_live_monitor.py       # Moniteur Bolivie
│   ├── 📄 PAYS_live_monitor.py          # Template moniteur
│   │
│   └── 📁 modules/
│       ├── 📄 soccerstats_live_selector.py  # Détection matches live
│       └── 📄 soccerstats_live_scraper.py   # Scraping stats live
│
├── 📄 GUIDE_UTILISATION_AUTONOME.md     # Ce guide
├── 📄 METHODOLOGIE_COMPLETE_V2.md       # Documentation technique
├── 📄 QUICK_START_v2.md                 # Guide démarrage rapide
└── 📄 README.md                         # Présentation projet
```

### 9.2 Fichiers Essentiels par Fonction

**Pour AJOUTER un championnat** :
- ✅ Copier `scrape_bulgaria_auto.py`
- ✅ Modifier le code championnat
- ✅ Lancer le scraping
- ✅ Générer les patterns

**Pour MONITORING LIVE** :
- ✅ `.env` (config Telegram)
- ✅ `telegram_notifier.py`
- ✅ `telegram_formatter.py`
- ✅ `PAYS_live_monitor.py`
- ✅ `live_predictor_v2.py`

**Pour ANALYSE** :
- ✅ `predictions.db` (données)
- ✅ `team_critical_intervals` (patterns)
- ✅ Scripts Python d'analyse

### 9.3 Commandes Récapitulatives

```bash
# === SETUP INITIAL ===
cd /workspaces/paris-live
source .venv/bin/activate
pip install requests beautifulsoup4 python-telegram-bot python-dotenv

# === COLLECTER DONNÉES ===
python3 scrape_bulgaria_auto.py
python3 scrape_bolivia_auto.py

# === GÉNÉRER PATTERNS ===
cd football-live-prediction
python3 build_critical_interval_recurrence.py

# === CONFIGURER TELEGRAM ===
# 1. Créer bot via @BotFather
# 2. Récupérer TOKEN et CHAT_ID
# 3. Créer fichier .env

cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id
EOF

# === TESTER TELEGRAM ===
python3 -c "
from telegram_notifier import TelegramNotifier
TelegramNotifier().send_message('✅ Test OK!')
"

# === LANCER MONITORING ===
# Scan unique
python3 bulgaria_live_monitor.py --once

# Continu (arrière-plan)
nohup python3 bulgaria_live_monitor.py --continuous --interval 120 > monitor.log 2>&1 &

# === MAINTENANCE ===
# Mettre à jour données
python3 scrape_bulgaria_auto.py && cd football-live-prediction && python3 build_critical_interval_recurrence.py

# Backup DB
cp football-live-prediction/data/predictions.db football-live-prediction/data/backup_$(date +%Y%m%d).db

# Vérifier processus
ps aux | grep monitor

# Arrêter monitoring
pkill -f "live_monitor"
```

---

## 10. CHECKLIST AUTONOMIE COMPLÈTE

### ✅ Je sais collecter les données

- [ ] J'ai testé le scraping sur Bulgaria
- [ ] J'ai testé le scraping sur Bolivia
- [ ] Je sais vérifier les données en DB
- [ ] Je sais créer un scraper pour un nouveau championnat

### ✅ Je sais gérer les patterns

- [ ] J'ai généré les patterns avec `build_critical_interval_recurrence.py`
- [ ] Je sais vérifier les patterns en DB
- [ ] Je comprends les métriques (freq_any_goal, recurrence, confidence)

### ✅ Je sais configurer Telegram

- [ ] J'ai créé mon bot Telegram
- [ ] J'ai récupéré mon TOKEN
- [ ] J'ai récupéré mon CHAT_ID
- [ ] J'ai créé le fichier `.env`
- [ ] J'ai testé l'envoi de messages

### ✅ Je sais lancer le monitoring

- [ ] J'ai testé un scan unique
- [ ] J'ai lancé le monitoring continu
- [ ] Je sais arrêter le monitoring
- [ ] Je reçois les alertes Telegram

### ✅ Je sais maintenir le système

- [ ] Je sais mettre à jour les données
- [ ] Je sais faire un backup
- [ ] Je sais dépanner les problèmes courants
- [ ] Je sais ajouter un nouveau championnat

---

## 11. SUPPORT & RESSOURCES

### Documentation Complète

- **`METHODOLOGIE_COMPLETE_V2.md`** : Explications techniques détaillées
- **`QUICK_START_v2.md`** : Démarrage rapide
- **`GUIDE_UTILISATION_AUTONOME.md`** : Ce guide

### Commandes Utiles

```bash
# Aide sur un script
python3 scrape_bulgaria_auto.py --help

# Logs en temps réel
tail -f monitor.log

# Compter lignes DB
sqlite3 football-live-prediction/data/predictions.db "SELECT COUNT(*) FROM soccerstats_scraped_matches"

# Voir tous les patterns
sqlite3 football-live-prediction/data/predictions.db "SELECT * FROM team_critical_intervals LIMIT 10"
```

### Contacts & Liens

- **Telegram** : @BotFather pour créer des bots
- **SoccerStats** : https://www.soccerstats.com
- **Documentation Python Telegram Bot** : https://python-telegram-bot.org

---

## 🎉 FÉLICITATIONS !

Vous êtes maintenant **100% AUTONOME** pour :

1. ✅ Ajouter de nouveaux championnats
2. ✅ Collecter les données historiques
3. ✅ Générer les patterns statistiques
4. ✅ Configurer Telegram
5. ✅ Lancer le monitoring live
6. ✅ Recevoir des alertes en temps réel
7. ✅ Maintenir le système

**Prochaines étapes suggérées** :

1. Tester sur 2-3 championnats différents
2. Affiner les mappings de noms d'équipes
3. Optimiser les seuils d'alerte selon vos besoins
4. Créer des backups automatiques (cron)
5. Analyser les résultats pour améliorer les prédictions

---

**Version** : 2.0  
**Dernière mise à jour** : 4 Décembre 2025  
**Status** : Production Ready 🚀
