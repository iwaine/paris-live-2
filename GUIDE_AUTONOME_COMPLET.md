# 🎯 GUIDE COMPLET - SYSTÈME DE PRÉDICTION FOOTBALL V2.0
## Mode Autonome - Étape par Étape

---

## 📋 TABLE DES MATIÈRES

1. [Installation et Configuration](#1-installation-et-configuration)
2. [Scraping des Données](#2-scraping-des-données)
3. [Génération des Patterns](#3-génération-des-patterns)
4. [Génération des Whitelists](#4-génération-des-whitelists)
5. [Monitoring en Direct](#5-monitoring-en-direct)
6. [Comprendre les Calculs](#6-comprendre-les-calculs)
7. [Maintenance Hebdomadaire](#7-maintenance-hebdomadaire)
8. [Dépannage](#8-dépannage)

---

## 1. INSTALLATION ET CONFIGURATION

### 1.1 Prérequis
```bash
# Vérifier Python (version 3.8 minimum)
python3 --version
# Exemple de sortie : Python 3.12.0

# Vérifier pip
pip3 --version
# Exemple de sortie : pip 24.0
```

### 1.2 Installation des dépendances
```bash
# Installer les bibliothèques nécessaires
pip3 install requests beautifulsoup4 lxml

# Vérifier l'installation
python3 -c "import requests; import bs4; print('✓ Tout est installé')"
# Sortie attendue : ✓ Tout est installé
```

### 1.3 Configuration Telegram

**Étape A : Créer un bot Telegram**
1. Ouvrir Telegram
2. Chercher `@BotFather`
3. Envoyer `/newbot`
4. Suivre les instructions
5. **Copier le token** (ex: `8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c`)

**Étape B : Obtenir votre Chat ID**
1. Chercher `@userinfobot` sur Telegram
2. Envoyer `/start`
3. **Copier votre ID** (ex: `6942358056`)

**Étape C : Créer le fichier de configuration**
```bash
# Créer le fichier telegram_config.json
cat > telegram_config.json << 'EOF'
{
  "bot_token": "VOTRE_TOKEN_ICI",
  "chat_id": "VOTRE_CHAT_ID_ICI"
}
EOF
```

**Exemple concret :**
```json
{
  "bot_token": "8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c",
  "chat_id": "6942358056"
}
```

### 1.4 Vérifier la structure des dossiers
```bash
# Créer les dossiers nécessaires
mkdir -p football-live-prediction/data
mkdir -p whitelists

# Vérifier
ls -la
# Vous devez voir :
# - football-live-prediction/
# - whitelists/
# - telegram_config.json
```

---

## 2. SCRAPING DES DONNÉES

### 2.1 Scraper une ligue

**Commande de base :**
```bash
python3 scrape_all_leagues_auto.py --league LEAGUE_NAME --workers 2
```

**Ligues disponibles :**
- `france` → Ligue 1
- `germany` → Bundesliga
- `germany2` → Bundesliga 2
- `england` → Premier League
- `netherlands2` → Eredivisie
- `bolivia` → Liga Boliviana
- `bulgaria` → Bulgarian League
- `portugal` → Liga Portugal

**Exemple concret - Scraper la France :**
```bash
python3 scrape_all_leagues_auto.py --league france --workers 2
```

**Sortie attendue :**
```
🔍 SCRAPING : france
================================================
✓ URL cible : https://www.soccerstats.com/latest.asp?league=france

📊 ÉQUIPES TROUVÉES : 18
   • PSG
   • Marseille
   • Lyon
   ...

⏳ Scraping des 18 équipes (2 workers)...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 18/18

✅ SCRAPING TERMINÉ !
   • Équipes scrapées : 18/18
   • Matches collectés : 252
   • Insérés en DB : 252
   • Doublons évités : 0
```

### 2.2 Scraper toutes les ligues

**Méthode automatique :**
```bash
# Scraper les 8 ligues d'un coup
for league in france germany germany2 england netherlands2 bolivia bulgaria portugal; do
    echo "📥 Scraping $league..."
    python3 scrape_all_leagues_auto.py --league $league --workers 2
    echo ""
done
```

**Temps estimé :** 20-30 minutes pour les 8 ligues

### 2.3 Vérifier les données

```bash
# Compter les matchs dans la base de données
sqlite3 football-live-prediction/data/predictions.db "SELECT COUNT(*) FROM soccerstats_scraped_matches;"
# Exemple de sortie : 2288

# Voir les ligues présentes
sqlite3 football-live-prediction/data/predictions.db "SELECT DISTINCT league, COUNT(*) as matches FROM soccerstats_scraped_matches GROUP BY league;"
# Sortie exemple :
# france|252
# germany|306
# portugal|216
```

---

## 3. GÉNÉRATION DES PATTERNS

### 3.1 Construire les patterns historiques

**Commande :**
```bash
cd football-live-prediction
python3 build_team_recurrence_stats.py
```

**Sortie attendue :**
```
================================================================================
🔄 BUILDING TEAM-SPECIFIC RECURRENCE STATISTICS
================================================================================
✅ Created team_goal_recurrence table
Processing 2288 matches (buts marqués + encaissés)...
Found 576 team-context-period combinations
✅ Inserted 576 recurrence records

================================================================================
📊 SUMMARY - TOP TEAMS BY GOAL COUNT
================================================================================

Team            Loc    Period     Avg Min      SEM          IQR          Goals  Matches
------------------------------------------------------------------------------------
Aurora          AWAY   2nd half   72.3         2.3          [voir DB]    38     12
Bayern Munich   HOME   1st half   26.4         3.1          [voir DB]    19     7
Benfica         HOME   2nd half   74.2         2.8          [voir DB]    15     6
```

**Ce que fait ce script :**
- Analyse tous les matchs dans la base de données
- Calcule pour chaque équipe :
  - Récurrence en 1ère mi-temps (1-45')
  - Récurrence en 2ème mi-temps (46-90')
  - Domicile vs Extérieur
  - Moyenne des minutes de but
- Stocke tout dans la table `team_goal_recurrence`

---

## 4. GÉNÉRATION DES WHITELISTS

### 4.1 Qu'est-ce qu'une whitelist ?

Une **whitelist** est une liste d'équipes qui ont des **patterns fiables** (≥65% de probabilité) sur les intervalles 31-45' et 76-90'.

**Critères de qualification :**
- Probabilité ≥ 65%
- Minimum 4 matchs joués
- Au moins 1 but dans l'intervalle

### 4.2 Générer une whitelist pour une ligue

**Commande :**
```bash
python3 generate_top_teams_whitelist.py --league LEAGUE_NAME --threshold 65 --min-matches 4
```

**Exemple - Générer whitelist France :**
```bash
python3 generate_top_teams_whitelist.py --league france --threshold 65 --min-matches 4
```

**Sortie attendue :**
```
🔍 ANALYSE DE 18 ÉQUIPES - FRANCE
======================================================================

💾 Whitelist sauvegardée: whitelists/france_whitelist.json

📊 RAPPORT - FRANCE
======================================================================
Seuil: 65% | Min matchs: 4
Équipes analysées: 18
Équipes qualifiées: 10
Généré le: 2025-12-05T22:00:00.000000

✅ TOP ÉQUIPES (≥ 65%):
======================================================================
 1. Monaco                    AWAY  76-90  | 100.0% (7/7 matchs) | 8 buts
 2. PSG                       HOME  31-45  |  85.7% (6/7 matchs) | 9 buts
 3. Marseille                 AWAY  76-90  |  71.4% (5/7 matchs) | 6 buts
 ...

❌ ÉQUIPES FAIBLES (< 50%) - À IGNORER:
======================================================================
   Le Havre                  HOME  31-45  |  28.6%
   Montpellier               AWAY  76-90  |  42.9%
```

### 4.3 Générer toutes les whitelists

**Commande automatique :**
```bash
python3 generate_top_teams_whitelist.py --all --threshold 65 --min-matches 4
```

**Sortie attendue :**
```
🚀 GÉNÉRATION WHITELISTS POUR 8 LIGUES
======================================================================

📊 FRANCE (france)
   ✓ 18 équipes analysées
   ✓ 10 patterns qualifiés
   ✓ Sauvegardé: whitelists/france_whitelist.json

📊 GERMANY (germany)
   ✓ 18 équipes analysées
   ✓ 28 patterns qualifiés
   ✓ Sauvegardé: whitelists/germany_whitelist.json

...

📊 RÉSUMÉ GLOBAL
======================================================================
Total ligues : 8
Total équipes analysées : 126
Total patterns qualifiés : 131
```

### 4.4 Comprendre le fichier whitelist

**Ouvrir une whitelist :**
```bash
cat whitelists/france_whitelist.json | head -50
```

**Structure :**
```json
{
  "league": "france",
  "threshold": 65,
  "min_matches": 4,
  "total_teams_analyzed": 18,
  "qualified_teams": [
    {
      "team": "Monaco",
      "location": "AWAY",
      "interval": "76-90",
      "probability": 100.0,
      "recurrence": 100.0,
      "matches": 7,
      "matches_with_goal": 7,
      "total_goals": 8
    }
  ],
  "all_stats": [...],
  "generated_at": "2025-12-05T22:00:00"
}
```

**Explication des champs :**
- `team` : Nom de l'équipe
- `location` : HOME (domicile) ou AWAY (extérieur)
- `interval` : 31-45 ou 76-90
- `probability` : % de matchs avec au moins 1 but dans l'intervalle
- `matches` : Nombre total de matchs
- `matches_with_goal` : Matchs avec but dans l'intervalle
- `total_goals` : Nombre total de buts dans l'intervalle

---

## 6. COMPRENDRE LES CALCULS

### 6.1 Calcul de la Récurrence (Probability)

**Formule :**
```
Récurrence (%) = (Matchs avec but dans intervalle / Total matchs) × 100
```

**Exemple concret - Monaco AWAY 76-90 :**

**Données :**
- Total matchs joués à l'extérieur : 7
- Matchs avec but entre 76-90' : 7
- Buts marqués dans intervalle : 8

**Calcul :**
```
Récurrence = (7 / 7) × 100 = 100.0%
```

**Interprétation :** Monaco marque dans 100% de ses matchs à l'extérieur entre 76-90'

### 6.2 Calcul de la Formula MAX

**Principe :** On prend le MEILLEUR pattern entre les 2 équipes

**Exemple - Match Benfica (HOME) vs Sporting CP (AWAY) :**

**Patterns disponibles :**
- Benfica HOME 76-90 : 83.3% (5/6 matchs)
- Sporting CP AWAY 76-90 : 50.0% (3/6 matchs)

**Formula MAX :**
```
MAX(83.3%, 50.0%) = 83.3%
```

**Décision :** Signal validé car 83.3% ≥ 65%

### 6.3 Récurrence Récente (3 derniers matchs)

**Objectif :** Vérifier que la tendance est ACTIVE (pas seulement historique)

**Exemple - Benfica HOME 76-90 :**

**3 derniers matchs à domicile :**
1. Match vs Porto : Buts 76-90' → 1 but marqué (78'), 0 encaissé = ✅ OUI
2. Match vs Braga : Buts 76-90' → 0 marqué, 1 encaissé (82') = ✅ OUI
3. Match vs Sporting : Buts 76-90' → 0 marqué, 0 encaissé = ❌ NON

**Calcul :**
```
Récurrence Récente = (2 / 3) × 100 = 66.7%
Total buts (marqués + encaissés) = 1 + 1 = 2
```

**Tendance :**
- ≥ 80% → 🟢 Excellente
- 50-79% → 🟡 Correcte
- < 50% → 🔴 Faible

Dans cet exemple : 66.7% → 🟡 Tendance correcte

### 6.4 Calcul complet - Exemple réel

**Match : Benfica vs Sporting CP (86', score 1-1)**

**Étape 1 - Récupérer les patterns**
```
Benfica HOME 76-90 :
  • Récurrence totale : 83.3% (5/6 matchs)
  • Buts marqués : 6
  
Sporting CP AWAY 76-90 :
  • Récurrence totale : 50.0% (3/6 matchs)
  • Buts marqués : 5
```

**Étape 2 - Formula MAX**
```
MAX(83.3%, 50.0%) = 83.3%
```

**Étape 3 - Récurrence récente (Benfica)**
```
3 derniers matchs HOME : 2/3 avec but = 66.7%
Tendance : 🟡
```

**Étape 4 - Décision**
```
Probabilité MAX : 83.3%
Seuil requis : 65%
83.3% ≥ 65% → ✅ SIGNAL VALIDÉ
```

**Étape 5 - Message Telegram envoyé**
```
🚨 SIGNAL V2.0 - PORTUGAL

⚽ Benfica vs Sporting CP
🏆 Portugal - Liga Portugal
⏱️ 86' | Score: 1-1

📊 INTERVALLE: 76-90 minutes
🎯 PROBABILITÉ: 83.3%

📈 FORMULA MAX:
• Benfica À DOMICILE:
  → Récurrence: 83.3% (5/6 matchs)
  → 6 buts marqués dans intervalle

• Sporting CP À L'EXTÉRIEUR:
  → Récurrence: 50.0% (3/6 matchs) ❌ < 65%
  → 5 buts marqués dans intervalle

🔢 RÉCURRENCE RÉCENTE (3 derniers matchs):
• Benfica HOME 76-90: 66.7% (2/3 matchs) - 2 buts (marqués + encaissés)
• Tendance: 🟡

✅ SIGNAL VALIDÉ
```

---

## 5. MONITORING EN DIRECT

### 5.1 Créer un script de monitoring manuel

**Fichier : `monitor_live.py`**
```python
#!/usr/bin/env python3
"""
Monitoring manuel - Vous entrez les infos du match
"""

import json
import requests
import sqlite3

# Configuration
TELEGRAM_CONFIG = "telegram_config.json"
DB_PATH = "football-live-prediction/data/predictions.db"

# Charger config Telegram
with open(TELEGRAM_CONFIG, "r") as f:
    config = json.load(f)

BOT_TOKEN = config['bot_token']
CHAT_ID = config['chat_id']

# ÉTAPE 1 : Entrer les infos du match
print("="*70)
print("🎯 MONITORING MANUEL - ENTREZ LES INFOS DU MATCH")
print("="*70)

league = input("Ligue (ex: portugal, france, germany) : ")
home_team = input("Équipe domicile (ex: Benfica) : ")
away_team = input("Équipe extérieure (ex: Sporting CP) : ")
minute = int(input("Minute actuelle (ex: 86) : "))
score_home = int(input("Buts domicile (ex: 1) : "))
score_away = int(input("Buts extérieur (ex: 1) : "))

# ÉTAPE 2 : Déterminer l'intervalle actif
if 31 <= minute <= 45:
    interval = "31-45"
elif 76 <= minute <= 90:
    interval = "76-90"
else:
    print(f"\n⚠️  Minute {minute} hors des intervalles surveillés (31-45 ou 76-90)")
    print("Aucun signal à envoyer.")
    exit()

print(f"\n✅ Intervalle actif : {interval}")

# ÉTAPE 3 : Charger la whitelist
whitelist_path = f"football-live-prediction/whitelists/{league}_whitelist.json"

try:
    with open(whitelist_path, "r", encoding="utf-8") as f:
        whitelist = json.load(f)
except FileNotFoundError:
    print(f"\n❌ Whitelist non trouvée : {whitelist_path}")
    print(f"Générez-la avec : python3 generate_top_teams_whitelist.py --league {league}")
    exit()

# ÉTAPE 4 : Récupérer les patterns
home_pattern = None
away_pattern = None

for team in whitelist['qualified_teams']:
    if team['team'] == home_team and team['location'] == 'HOME' and team['interval'] == interval:
        home_pattern = team
    if team['team'] == away_team and team['location'] == 'AWAY' and team['interval'] == interval:
        away_pattern = team

# Chercher aussi dans all_stats si pas dans qualified
if not away_pattern:
    for team in whitelist.get('all_stats', []):
        if team['team'] == away_team and team['location'] == 'AWAY' and team['interval'] == interval:
            away_pattern = team
            break

# ÉTAPE 5 : Calculer stats complètes pour away_team
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

if away_pattern:
    cursor.execute("""
        SELECT match_id, goal_times
        FROM soccerstats_scraped_matches
        WHERE team = ? AND is_home = 0
    """, (away_team,))
    
    away_matches = cursor.fetchall()
    away_total = len(away_matches)
    away_with_goal = 0
    away_goals = 0
    
    interval_min, interval_max = map(int, interval.split('-'))
    
    for match in away_matches:
        if match[1]:
            goals = [int(g.strip()) for g in match[1].split(',') if g.strip().isdigit()]
            interval_goals = [g for g in goals if interval_min <= g <= interval_max]
            away_goals += len(interval_goals)
            if interval_goals:
                away_with_goal += 1
    
    away_prob = (away_with_goal / away_total * 100) if away_total > 0 else 0
else:
    away_total = 0
    away_with_goal = 0
    away_goals = 0
    away_prob = 0

# ÉTAPE 6 : Calculer récurrence récente HOME
cursor.execute("""
    SELECT match_id, goal_times, goal_times_conceded
    FROM soccerstats_scraped_matches
    WHERE team = ? AND is_home = 1
    ORDER BY match_id DESC
    LIMIT 3
""", (home_team,))

recent_matches = cursor.fetchall()
recent_with_goal = 0
recent_total_goals = 0
interval_min, interval_max = map(int, interval.split('-'))

for match in recent_matches:
    has_goal = False
    
    # Buts marqués
    if match[1]:
        goals_for = [int(g.strip()) for g in match[1].split(',') if g.strip().isdigit()]
        interval_goals = [g for g in goals_for if interval_min <= g <= interval_max]
        recent_total_goals += len(interval_goals)
        if interval_goals:
            has_goal = True
    
    # Buts encaissés
    if match[2]:
        goals_against = [int(g.strip()) for g in match[2].split(',') if g.strip().isdigit()]
        interval_goals = [g for g in goals_against if interval_min <= g <= interval_max]
        recent_total_goals += len(interval_goals)
        if interval_goals:
            has_goal = True
    
    if has_goal:
        recent_with_goal += 1

recent_total = len(recent_matches)
recent_recurrence = (recent_with_goal / recent_total * 100) if recent_total > 0 else 0

conn.close()

# Tendance
if recent_recurrence >= 80:
    trend = "🟢"
elif recent_recurrence >= 50:
    trend = "🟡"
else:
    trend = "🔴"

# ÉTAPE 7 : Afficher résultats
print("\n" + "="*70)
print("📊 ANALYSE DES PATTERNS")
print("="*70)

if home_pattern:
    print(f"\n✅ {home_team} HOME {interval}:")
    print(f"   Récurrence: {home_pattern['probability']:.1f}%")
    print(f"   Matchs: {home_pattern['matches_with_goal']}/{home_pattern['matches']}")
    print(f"   Buts: {home_pattern['total_goals']}")
    home_prob = home_pattern['probability']
else:
    print(f"\n❌ {home_team} HOME {interval}: Aucun pattern")
    home_prob = 0

print(f"\n{'✅' if away_prob >= 65 else '⚠️'} {away_team} AWAY {interval}:")
print(f"   Récurrence: {away_prob:.1f}%")
print(f"   Matchs: {away_with_goal}/{away_total}")
print(f"   Buts: {away_goals}")

print(f"\n📈 FORMULA MAX:")
max_prob = max(home_prob, away_prob)
print(f"   MAX({home_prob:.1f}%, {away_prob:.1f}%) = {max_prob:.1f}%")

print(f"\n🔢 RÉCURRENCE RÉCENTE ({home_team} HOME):")
print(f"   {recent_recurrence:.1f}% ({recent_with_goal}/{recent_total} matchs)")
print(f"   {recent_total_goals} buts - Tendance: {trend}")

# ÉTAPE 8 : Décision
print("\n" + "="*70)
if max_prob >= 65:
    print("✅ SIGNAL VALIDÉ (≥ 65%)")
    print("="*70)
    
    # ÉTAPE 9 : Construire message Telegram
    if home_pattern:
        message = f"""🚨 SIGNAL V2.0 - {league.upper()}

⚽ {home_team} vs {away_team}
⏱️ {minute}' | Score: {score_home}-{score_away}

📊 INTERVALLE: {interval} minutes
🎯 PROBABILITÉ: {max_prob:.1f}%

📈 FORMULA MAX:
• {home_team} À DOMICILE:
  → Récurrence: {home_prob:.1f}% ({home_pattern['matches_with_goal']}/{home_pattern['matches']} matchs)
  → {home_pattern['total_goals']} buts marqués dans intervalle

• {away_team} À L'EXTÉRIEUR:
  → Récurrence: {away_prob:.1f}% ({away_with_goal}/{away_total} matchs) {'❌ < 65%' if away_prob < 65 else '✅'}
  → {away_goals} buts marqués dans intervalle

🔢 RÉCURRENCE RÉCENTE (3 derniers matchs):
• {home_team} HOME {interval}: {recent_recurrence:.1f}% ({recent_with_goal}/{recent_total} matchs) - {recent_total_goals} buts (marqués + encaissés)
• Tendance: {trend}

✅ SIGNAL VALIDÉ
"""
    
        # ÉTAPE 10 : Envoyer sur Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': message}
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            print("\n✅ Message envoyé sur Telegram !")
        except Exception as e:
            print(f"\n❌ Erreur Telegram: {e}")
    else:
        print("\n❌ Pattern HOME manquant, impossible d'envoyer le signal")
else:
    print(f"❌ SIGNAL REJETÉ (< 65%)")
    print("="*70)
```

### 5.2 Utiliser le monitoring manuel

**Commande :**
```bash
python3 monitor_live.py
```

**Exemple d'utilisation :**
```
======================================================================
🎯 MONITORING MANUEL - ENTREZ LES INFOS DU MATCH
======================================================================
Ligue (ex: portugal, france, germany) : portugal
Équipe domicile (ex: Benfica) : Benfica
Équipe extérieure (ex: Sporting CP) : Sporting CP
Minute actuelle (ex: 86) : 86
Buts domicile (ex: 1) : 1
Buts extérieur (ex: 1) : 1

✅ Intervalle actif : 76-90

======================================================================
📊 ANALYSE DES PATTERNS
======================================================================

✅ Benfica HOME 76-90:
   Récurrence: 83.3%
   Matchs: 5/6
   Buts: 6

⚠️ Sporting CP AWAY 76-90:
   Récurrence: 50.0%
   Matchs: 3/6
   Buts: 5

📈 FORMULA MAX:
   MAX(83.3%, 50.0%) = 83.3%

🔢 RÉCURRENCE RÉCENTE (Benfica HOME):
   66.7% (2/3 matchs)
   2 buts - Tendance: 🟡

======================================================================
✅ SIGNAL VALIDÉ (≥ 65%)
======================================================================

✅ Message envoyé sur Telegram !
```

---

## 7. MAINTENANCE HEBDOMADAIRE

### 7.1 Workflow complet automatique

**Créer le script `update_weekly.sh` :**
```bash
#!/bin/bash

echo "🚀 MISE À JOUR HEBDOMADAIRE"
echo "======================================================================"

# ÉTAPE 1 : Scraping
echo ""
echo "📥 ÉTAPE 1/3 : Scraping des nouvelles données..."
echo "----------------------------------------------------------------------"
for league in france germany germany2 england netherlands2 bolivia bulgaria portugal; do
    echo "   → Scraping $league..."
    python3 scrape_all_leagues_auto.py --league $league --workers 2
done

# ÉTAPE 2 : Génération patterns
echo ""
echo "📊 ÉTAPE 2/3 : Génération des patterns..."
echo "----------------------------------------------------------------------"
cd football-live-prediction
python3 build_team_recurrence_stats.py
cd ..

# ÉTAPE 3 : Génération whitelists
echo ""
echo "🎯 ÉTAPE 3/3 : Génération des whitelists..."
echo "----------------------------------------------------------------------"
python3 generate_top_teams_whitelist.py --all --threshold 65 --min-matches 4

# RÉSUMÉ
echo ""
echo "✅ MISE À JOUR TERMINÉE"
echo "======================================================================"
echo "Date : $(date '+%Y-%m-%d %H:%M:%S')"
echo "Whitelists générées : $(ls whitelists/*_whitelist.json 2>/dev/null | wc -l)"
echo ""
```

**Rendre le script exécutable :**
```bash
chmod +x update_weekly.sh
```

**Exécuter la mise à jour :**
```bash
./update_weekly.sh
```

### 7.2 Quand faire la mise à jour ?

**Recommandé : Chaque lundi matin**

Les matchs du weekend sont terminés, vous aurez :
- Nouvelles données fraîches
- Patterns mis à jour
- Whitelists actualisées

**Exemple de calendrier :**
- **Lundi** : Mise à jour complète (`./update_weekly.sh`)
- **Mardi-Dimanche** : Monitoring des matchs en direct

---

## 8. DÉPANNAGE

### 8.1 Problème : "No module named 'requests'"

**Solution :**
```bash
pip3 install requests beautifulsoup4 lxml
```

### 8.2 Problème : "Unable to open database file"

**Cause :** Vous n'êtes pas dans le bon dossier

**Solution :**
```bash
# Vérifier où vous êtes
pwd

# Si vous êtes dans football-live-prediction/, remontez
cd ..

# Relancer la commande
python3 football-live-prediction/build_team_recurrence_stats.py
```

### 8.3 Problème : "Telegram 400 Bad Request"

**Cause :** Caractères spéciaux dans le message

**Solution :** Déjà corrigé dans le script (pas de `parse_mode: HTML`)

### 8.4 Problème : "Whitelist not found"

**Solution :**
```bash
# Vérifier si la whitelist existe
ls -la whitelists/

# Si manquante, la générer
python3 generate_top_teams_whitelist.py --league portugal --threshold 65 --min-matches 4
```

### 8.5 Problème : Scraping échoue avec "500 Error"

**Cause :** Le site soccerstats.com peut être temporairement indisponible

**Solution :**
```bash
# Attendre 5-10 minutes et réessayer
python3 scrape_all_leagues_auto.py --league portugal --workers 2
```

### 8.6 Problème : Aucune équipe qualifiée dans une ligue

**Cause :** Pas assez de données ou seuil trop élevé

**Solution :**
```bash
# Baisser le seuil à 60% ou min-matches à 3
python3 generate_top_teams_whitelist.py --league bolivia --threshold 60 --min-matches 3
```

---

## 📝 RÉSUMÉ - CHECKLIST QUOTIDIENNE

### Chaque jour de match :

1. ✅ Vérifier qu'il y a des matchs en cours (sites de scores)
2. ✅ Identifier la ligue du match
3. ✅ Lancer le monitoring manuel :
   ```bash
   python3 monitor_live.py
   ```
4. ✅ Entrer les infos du match quand minute ≥ 31 ou ≥ 76
5. ✅ Recevoir l'alerte Telegram si signal validé

### Chaque lundi (mise à jour) :

1. ✅ Exécuter le script de mise à jour :
   ```bash
   ./update_weekly.sh
   ```
2. ✅ Vérifier que tout s'est bien passé (regarder les logs)
3. ✅ Prêt pour la semaine de matchs

---

## 🎯 EXEMPLE COMPLET DE A À Z

### Scénario : Vous voulez monitorer la Bundesliga

**Jour 1 (Lundi) - Préparation**

```bash
# 1. Scraper les données Bundesliga
python3 scrape_all_leagues_auto.py --league germany --workers 2
# Sortie : ✅ 306 matchs collectés

# 2. Générer les patterns
cd football-live-prediction
python3 build_team_recurrence_stats.py
cd ..
# Sortie : ✅ 576 patterns créés

# 3. Générer la whitelist
python3 generate_top_teams_whitelist.py --league germany --threshold 65 --min-matches 4
# Sortie : ✅ 28 équipes qualifiées
```

**Jour 5 (Vendredi soir) - Match en direct**

Match : Bayern Munich vs Borussia Dortmund
Minute actuelle : 78'
Score : 2-1

```bash
# Lancer le monitoring
python3 monitor_live.py
```

**Entrées :**
```
Ligue : germany
Équipe domicile : Bayern Munich
Équipe extérieure : Dortmund
Minute actuelle : 78
Buts domicile : 2
Buts extérieur : 1
```

**Résultat :**
```
✅ SIGNAL VALIDÉ (≥ 65%)
✅ Message envoyé sur Telegram !
```

**Message Telegram reçu :**
```
🚨 SIGNAL V2.0 - GERMANY

⚽ Bayern Munich vs Dortmund
⏱️ 78' | Score: 2-1

📊 INTERVALLE: 76-90 minutes
🎯 PROBABILITÉ: 92.3%

📈 FORMULA MAX:
• Bayern Munich À DOMICILE:
  → Récurrence: 92.3% (12/13 matchs)
  → 14 buts marqués dans intervalle

• Dortmund À L'EXTÉRIEUR:
  → Récurrence: 58.3% (7/12 matchs) ❌ < 65%
  → 9 buts marqués dans intervalle

🔢 RÉCURRENCE RÉCENTE (3 derniers matchs):
• Bayern Munich HOME 76-90: 100.0% (3/3 matchs) - 4 buts
• Tendance: 🟢

✅ SIGNAL VALIDÉ
```

---

## 📚 FICHIERS ESSENTIELS

### Structure finale de votre dossier :

```
votre-dossier/
│
├── telegram_config.json           # Config Telegram
├── monitor_live.py                # Script monitoring manuel
├── update_weekly.sh               # Mise à jour hebdomadaire
│
├── scrape_all_leagues_auto.py     # Scraper
├── generate_top_teams_whitelist.py # Générateur whitelists
│
├── football-live-prediction/
│   ├── data/
│   │   └── predictions.db         # Base de données
│   ├── build_team_recurrence_stats.py
│   └── whitelists/
│       ├── france_whitelist.json
│       ├── germany_whitelist.json
│       ├── portugal_whitelist.json
│       └── ...
│
└── whitelists/                    # Copie des whitelists
    ├── france_whitelist.json
    ├── germany_whitelist.json
    └── ...
```

---

## ✅ VALIDATION - Êtes-vous prêt ?

Cochez chaque point :

- [ ] Python 3.8+ installé et fonctionnel
- [ ] Dépendances installées (requests, beautifulsoup4)
- [ ] Telegram bot créé avec token
- [ ] Fichier telegram_config.json configuré
- [ ] Au moins 1 ligue scrapée avec succès
- [ ] Patterns générés (table team_goal_recurrence)
- [ ] Au moins 1 whitelist générée
- [ ] Script monitor_live.py créé
- [ ] Test de monitoring manuel réussi
- [ ] Message Telegram reçu avec succès

**Si tous les points sont cochés : 🎉 VOUS ÊTES AUTONOME !**

---

## 🆘 SUPPORT

En cas de problème :

1. Relire la section [8. Dépannage](#8-dépannage)
2. Vérifier les logs d'erreur
3. Vérifier que vous êtes dans le bon dossier (`pwd`)
4. Vérifier que les fichiers existent (`ls -la`)

---

**Version du guide :** 2.0
**Date :** 2025-12-05
**Testé sur :** Ubuntu 24.04, macOS, Windows WSL
