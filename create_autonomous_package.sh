#!/bin/bash
#
# Script de création du package autonome
# Crée un dossier "paris-live-autonomous" avec TOUS les fichiers nécessaires
#

DEST_DIR="paris-live-autonomous"

echo "📦 CRÉATION DU PACKAGE AUTONOME"
echo "======================================================================"
echo ""

# Nettoyer ancien dossier si existe
if [ -d "$DEST_DIR" ]; then
    echo "🗑️  Suppression ancien dossier..."
    rm -rf "$DEST_DIR"
fi

# Créer structure
echo "📁 Création de la structure..."
mkdir -p "$DEST_DIR"
mkdir -p "$DEST_DIR/football-live-prediction/data"
mkdir -p "$DEST_DIR/whitelists"

echo ""
echo "📋 COPIE DES FICHIERS ESSENTIELS"
echo "======================================================================"

# 1. Scripts de scraping
echo "   ✓ Scripts de scraping..."
cp scrape_all_leagues_auto.py "$DEST_DIR/"

# 2. Scripts de génération
echo "   ✓ Scripts de génération..."
cp generate_top_teams_whitelist.py "$DEST_DIR/"
cp football-live-prediction/build_team_recurrence_stats.py "$DEST_DIR/football-live-prediction/"

# 3. Base de données
echo "   ✓ Base de données..."
if [ -f "football-live-prediction/data/predictions.db" ]; then
    cp football-live-prediction/data/predictions.db "$DEST_DIR/football-live-prediction/data/"
fi

# 4. Whitelists
echo "   ✓ Whitelists..."
if [ -d "whitelists" ]; then
    cp whitelists/*.json "$DEST_DIR/whitelists/" 2>/dev/null
fi

if [ -d "football-live-prediction/whitelists" ]; then
    cp football-live-prediction/whitelists/*.json "$DEST_DIR/whitelists/" 2>/dev/null
fi

# 5. Configuration Telegram (template)
echo "   ✓ Configuration Telegram..."
cat > "$DEST_DIR/telegram_config.json" << 'EOF'
{
  "bot_token": "VOTRE_TOKEN_ICI",
  "chat_id": "VOTRE_CHAT_ID_ICI"
}
EOF

# 6. Script de monitoring manuel
echo "   ✓ Script de monitoring..."
cat > "$DEST_DIR/monitor_live.py" << 'EOFPYTHON'
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
whitelist_path = f"whitelists/{league}_whitelist.json"

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
EOFPYTHON

chmod +x "$DEST_DIR/monitor_live.py"

# 7. Script de mise à jour hebdomadaire
echo "   ✓ Script de mise à jour..."
cat > "$DEST_DIR/update_weekly.sh" << 'EOFBASH'
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
EOFBASH

chmod +x "$DEST_DIR/update_weekly.sh"

# 8. README
echo "   ✓ Documentation..."
cat > "$DEST_DIR/README.md" << 'EOFREADME'
# ⚽ Système de Prédiction Football V2.0

## 🚀 Démarrage Rapide

### 1. Installation des dépendances
```bash
pip3 install requests beautifulsoup4 lxml
```

### 2. Configuration Telegram
Éditez `telegram_config.json` avec vos identifiants Telegram

### 3. Première utilisation
```bash
# Scraper une ligue
python3 scrape_all_leagues_auto.py --league portugal --workers 2

# Générer les patterns
cd football-live-prediction
python3 build_team_recurrence_stats.py
cd ..

# Générer la whitelist
python3 generate_top_teams_whitelist.py --league portugal
```

### 4. Monitoring en direct
```bash
python3 monitor_live.py
```

## 📚 Documentation complète

Consultez `GUIDE_AUTONOME_COMPLET.md` pour le guide détaillé.

## 🔄 Mise à jour hebdomadaire

```bash
./update_weekly.sh
```

## 📊 Ligues supportées

- france (Ligue 1)
- germany (Bundesliga)
- germany2 (Bundesliga 2)
- england (Premier League)
- netherlands2 (Eredivisie)
- bolivia (Liga Boliviana)
- bulgaria (Bulgarian League)
- portugal (Liga Portugal)

## 🎯 Méthodologie

- **Intervalles surveillés :** 31-45' et 76-90'
- **Seuil de validation :** 65%
- **Formula MAX :** Meilleur pattern entre HOME/AWAY
- **Récurrence :** Totale + Récente (3 derniers matchs)
- **Buts comptés :** Marqués + Encaissés
EOFREADME

# 9. Guide complet
echo "   ✓ Guide complet..."
cp GUIDE_AUTONOME_COMPLET.md "$DEST_DIR/"

# 10. requirements.txt
echo "   ✓ Requirements..."
cat > "$DEST_DIR/requirements.txt" << 'EOFREQ'
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
EOFREQ

# 11. .gitignore
cat > "$DEST_DIR/.gitignore" << 'EOFGIT'
# Données sensibles
telegram_config.json

# Base de données
*.db
*.db-journal

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# Whitelists (seront regénérées)
whitelists/*.json

# Logs
*.log
EOFGIT

echo ""
echo "📊 STATISTIQUES DU PACKAGE"
echo "======================================================================"

# Compter les fichiers
nb_scripts=$(find "$DEST_DIR" -name "*.py" -o -name "*.sh" | wc -l)
nb_whitelists=$(ls "$DEST_DIR"/whitelists/*.json 2>/dev/null | wc -l)
nb_matches=$(sqlite3 "$DEST_DIR/football-live-prediction/data/predictions.db" "SELECT COUNT(*) FROM soccerstats_scraped_matches;" 2>/dev/null || echo "0")

echo "   Scripts Python/Bash : $nb_scripts"
echo "   Whitelists incluses : $nb_whitelists"
echo "   Matchs en DB : $nb_matches"
echo "   Documentation : README.md + Guide complet"
echo ""

# Taille du package
size=$(du -sh "$DEST_DIR" | cut -f1)
echo "   Taille totale : $size"

echo ""
echo "✅ PACKAGE CRÉÉ AVEC SUCCÈS !"
echo "======================================================================"
echo "📁 Dossier : $DEST_DIR/"
echo ""
echo "📦 COPIER SUR VOTRE ORDINATEUR :"
echo "   1. Compresser :"
echo "      tar -czf paris-live-autonomous.tar.gz $DEST_DIR/"
echo ""
echo "   2. Ou copier directement le dossier :"
echo "      cp -r $DEST_DIR ~/Bureau/"
echo ""
echo "   3. Sur votre machine locale :"
echo "      cd $DEST_DIR"
echo "      pip3 install -r requirements.txt"
echo "      # Éditer telegram_config.json"
echo "      python3 monitor_live.py"
echo ""
echo "📚 Lire le guide : $DEST_DIR/GUIDE_AUTONOME_COMPLET.md"
echo "======================================================================"
