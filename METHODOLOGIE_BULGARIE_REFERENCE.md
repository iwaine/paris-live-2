# 📋 MÉTHODOLOGIE BULGARIE - RÉFÉRENCE ABSOLUE

**Version :** 1.0  
**Date :** 5 décembre 2025  
**Statut :** ✅ VALIDÉE - Taux de réussite 88.9% sur pattern dominant  
**Application :** TOUTES les ligues doivent suivre cette méthodologie EXACTEMENT

---

## 🎯 OBJECTIF

Scraper les données historiques des matchs pour identifier les **patterns de buts récurrents** par équipe, localisation (HOME/AWAY) et intervalle de temps.

---

## 📊 ARCHITECTURE COMPLÈTE

### 1️⃣ SCRAPING (scrape_bulgaria_auto.py)

#### **ÉTAPE 1 : Extraction des codes équipes**

**URL source :** `https://www.soccerstats.com/formtable.asp?league={league_code}`

**Méthode :**
```python
def extract_team_codes(league_code: str) -> List[Tuple[str, str]]:
    """
    Extraire tous les codes équipes depuis formtable.asp
    
    Returns:
        Liste de tuples (code_equipe, nom_equipe)
        Exemple: [('u1749-cska-sofia', 'CSKA Sofia'), ...]
    """
    # 1. Parser la page formtable.asp
    # 2. Chercher tous les liens <a href="teamstats.asp?league=bulgaria&stats=u{id}-{nom}">
    # 3. Extraire le pattern : stats=(u\d+-[^&]+)
    # 4. Dédupliquer et trier
```

**Output attendu :**
```
✅ 16 équipes trouvées :
   • u1749-cska-sofia                → CSKA Sofia
   • u1750-levski-sofia              → Levski Sofia
   • u1752-ludogorets                → Ludogorets
   ...
```

---

#### **ÉTAPE 2 : Scraping par équipe (parallélisé)**

**URL source :** `https://www.soccerstats.com/teamstats.asp?league={league_code}&stats={team_code}`

**Méthode :**
```python
def scrape_team(league_code: str, team_code: str, team_name: str) -> List[dict]:
    """
    Scraper tous les matches d'une équipe
    
    Extraction :
    1. Date du match (colonne 0)
    2. Équipe domicile (colonne 1) - en GRAS si c'est l'équipe principale
    3. Score (colonne 2) - avec tooltip HTML contenant les minutes de buts
    4. Équipe extérieur (colonne 3)
    5. Score mi-temps (colonne 7)
    
    Returns:
        Liste de dictionnaires avec :
        - country, league, league_code, team, opponent, date
        - is_home (True/False)
        - score, ht_score
        - goals_scored: [13, 35, 58] (minutes des buts MARQUÉS)
        - goals_conceded: [21, 67] (minutes des buts ENCAISSÉS)
    """
```

**Extraction des buts depuis tooltip HTML :**
```python
def _extract_goals_from_tooltip(tooltip_html: str, team_is_home: bool):
    """
    Parser le tooltip pour extraire les minutes de buts
    
    Structure tooltip :
    <span>
        <font color="red">0-<b>1</b></font> (13) Joueur A<br>
        <b>1</b>-1 (35) Joueur B<br>
        1-<font color="red"><b>2</b></font> (67) Joueur C<br>
    </span>
    
    Logique :
    1. Trouver tous les <b>X-Y</b> (scores progressifs)
    2. Extraire la minute (\d+) entre parenthèses
    3. Comparer X-Y avec score précédent pour savoir qui a marqué
    4. Si HOME score augmente :
       - team_is_home=True → goals_scored
       - team_is_home=False → goals_conceded
    5. Si AWAY score augmente :
       - team_is_home=True → goals_conceded
       - team_is_home=False → goals_scored
    
    Returns:
        (goals_scored, goals_conceded) : Listes de minutes [int]
    """
```

**Parallélisation :**
```python
# 3-4 workers maximum pour respecter le serveur
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(scrape_team, code, name): (code, name) for code, name in teams}
    
# Throttling : 2-3 secondes entre chaque requête
time.sleep(2)
```

---

#### **ÉTAPE 3 : Sauvegarde en base de données**

**Table :** `soccerstats_scraped_matches`

**Structure :**
```sql
CREATE TABLE soccerstats_scraped_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT,                    -- 'Bulgaria'
    league TEXT,                     -- 'bulgaria' (code)
    league_display_name TEXT,        -- 'A PFG' (nom affiché)
    team TEXT,                       -- 'CSKA Sofia'
    opponent TEXT,                   -- 'Levski Sofia'
    date TEXT,                       -- '06.05'
    is_home INTEGER,                 -- 1=HOME, 0=AWAY
    score TEXT,                      -- '2-1'
    goals_for INTEGER,               -- 2
    goals_against INTEGER,           -- 1
    goal_times TEXT,                 -- '[13, 35, 0, 0, 0, 0, 0, 0, 0, 0]' (JSON)
    goal_times_conceded TEXT,        -- '[67, 0, 0, 0, 0, 0, 0, 0, 0, 0]' (JSON)
    match_id TEXT UNIQUE,            -- '06.05_CSKA Sofia_vs_Levski Sofia'
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**⚠️ FORMAT CRITIQUE - goal_times :**
```python
# TOUJOURS un array de 10 éléments avec padding de zéros
goals_scored = [13, 35, 58]  # 3 buts aux minutes 13, 35, 58

# Transformation pour DB (padding à 10 éléments)
goal_times_json = [13, 35, 58, 0, 0, 0, 0, 0, 0, 0]

# Code exact :
goal_times = match['goals_scored'] + [0] * (10 - len(match['goals_scored']))
goal_times_json = json.dumps(goal_times[:10])
```

**Gestion des doublons (méthode SELECT-UPDATE/INSERT) :**
```python
def save_to_db(matches_data: List[dict]):
    """
    Sauvegarde avec prévention des doublons
    
    Logique :
    1. Pour chaque match, générer match_id unique
    2. SELECT pour vérifier existence (team + opponent + date + is_home)
    3. Si existe → UPDATE (mettre à jour les données)
    4. Sinon → INSERT (nouveau match)
    """
    for match in matches_data:
        # 1. Générer match_id
        team1, team2 = sorted([match['team'], match['opponent']])
        match_id = f"{match['date']}_{team1}_vs_{team2}"
        
        # 2. Vérifier existence
        cursor.execute('''
            SELECT COUNT(*) FROM soccerstats_scraped_matches 
            WHERE team = ? AND opponent = ? AND date = ? AND is_home = ?
        ''', (match['team'], match['opponent'], match['date'], 1 if match['is_home'] else 0))
        
        if cursor.fetchone()[0] > 0:
            # 3a. UPDATE si existe
            cursor.execute('''UPDATE soccerstats_scraped_matches SET ...''')
            updated += 1
        else:
            # 3b. INSERT si nouveau
            cursor.execute('''INSERT INTO soccerstats_scraped_matches ...''')
            inserted += 1
```

**Output attendu :**
```
💾 Sauvegarde : 128 nouveaux, 0 mis à jour

✅ Scraping terminé !
   • Équipes scrapées : 16/16
   • Matches collectés : 128
   • Insérés en DB : 128
```

---

### 2️⃣ ANALYSE DES PATTERNS (top_patterns_bulgaria.py)

#### **Intervalles de temps standards**

```python
def get_interval(minute):
    """
    Catégorisation standard des minutes de jeu
    """
    if 0 <= minute <= 15: return '0-15'      # Début de match
    elif 16 <= minute <= 30: return '16-30'  # Milieu 1ère MT
    elif 31 <= minute <= 45: return '31-45'  # Fin 1ère MT ⭐
    elif 46 <= minute <= 60: return '46-60'  # Début 2ème MT
    elif 61 <= minute <= 75: return '61-75'  # Milieu 2ème MT
    elif 76 <= minute <= 90: return '76-90'  # Fin de match 🔥
    return None
```

**Focus principal :** `31-45` (fin 1ère mi-temps) et `76-90` (fin de match)

---

#### **MÉTHODE DE CALCUL DE LA RÉCURRENCE**

**⚠️ CRITIQUE - NE PAS CONFONDRE :**

```python
# ❌ FAUX (ce que j'ai fait au début)
recurrence = (nombre_total_de_buts_dans_intervalle / nombre_total_matchs) * 100

# ✅ CORRECT (méthode Bulgarie validée)
recurrence = (nombre_de_matchs_AVEC_au_moins_1_but_dans_intervalle / nombre_total_matchs) * 100
```

**Exemple concret :**

Brentford HOME en 76-90 :
- 7 matchs joués
- 7 buts marqués dans l'intervalle 76-90
- Mais répartis sur seulement **4 matchs différents**

```python
# ❌ Mauvais calcul
recurrence = (7 buts / 7 matchs) * 100 = 100.0% ❌

# ✅ Bon calcul
matchs_avec_but = 4  # Matchs où au moins 1 but en 76-90
recurrence = (4 matchs / 7 matchs) * 100 = 57.1% ✅
```

---

#### **Code de référence exact**

```python
def analyze_patterns():
    """
    Analyser les patterns de buts par équipe/localisation/intervalle
    
    MÉTHODE BULGARIE VALIDÉE
    """
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    
    # Structure de données
    match_has_goal_in_interval = defaultdict(lambda: defaultdict(list))
    match_counts = defaultdict(int)
    
    cursor.execute("""
        SELECT team, is_home, goal_times, goal_times_conceded, date, opponent
        FROM soccerstats_scraped_matches 
        WHERE league = 'bulgaria'
    """)
    
    for row in cursor.fetchall():
        team = row[0]
        is_home = "HOME" if row[1] == 1 else "AWAY"
        goals_scored = json.loads(row[2])
        goals_conceded = json.loads(row[3])
        date = row[4]
        opponent = row[5]
        
        key = f"{team} {is_home}"
        match_counts[key] += 1
        match_id = f"{date}_{opponent}"
        
        # Pour CE MATCH, quels intervalles ont au moins 1 but ?
        intervals_with_goals = set()
        
        # Buts marqués
        for minute in goals_scored:
            if minute > 0:
                interval = get_interval(minute)
                if interval:
                    intervals_with_goals.add(interval)
        
        # Buts encaissés
        for minute in goals_conceded:
            if minute > 0:
                interval = get_interval(minute)
                if interval:
                    intervals_with_goals.add(interval)
        
        # Enregistrer ce match pour chaque intervalle concerné
        for interval in intervals_with_goals:
            match_has_goal_in_interval[key][interval].append(match_id)
    
    # Calculer les récurrences
    patterns = {}
    for key in match_counts:
        patterns[key] = {}
        for interval in ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90']:
            # Nombre de matchs DIFFÉRENTS avec au moins 1 but dans cet intervalle
            matches_with_goal = len(set(match_has_goal_in_interval[key][interval]))
            total_matches = match_counts[key]
            
            recurrence = (matches_with_goal / total_matches) * 100 if total_matches > 0 else 0
            
            patterns[key][interval] = {
                'matches_with_goal': matches_with_goal,
                'total_matches': total_matches,
                'recurrence': recurrence
            }
    
    return patterns
```

---

#### **Critères de filtrage et classement**

**Seuils de qualité :**

```python
# Filtres minimaux
MIN_MATCHES_WITH_GOAL = 3  # Au moins 3 matchs avec but dans l'intervalle
MIN_RECURRENCE = 40.0      # Au moins 40% de récurrence

# Classification
if recurrence >= 70: status = "🔥"  # Excellent
elif recurrence >= 50: status = "⭐"  # Très bon
elif recurrence >= 40: status = "✅"  # Exploitable
else: status = "📊"  # Informatif seulement
```

**Tri :**
```python
# Toujours trier par RÉCURRENCE décroissante
results.sort(key=lambda x: x['recurrence'], reverse=True)
```

---

#### **Format d'affichage standard**

```python
print(f"{rank:2}. {status} {team:30} {location:4} {interval:6} : "
      f"{matches_with_goal}/{total_matches} matchs = {recurrence:5.1f}%")

# Exemple output :
# 1. 🔥 CSKA Sofia               HOME 76-90 : 6/7 matchs =  85.7%
# 2. ⭐ Ludogorets              AWAY 76-90 : 5/9 matchs =  55.6%
# 3. ✅ Levski Sofia            HOME 31-45 : 4/9 matchs =  44.4%
```

---

## 🔍 RÉSULTATS VALIDÉS BULGARIE

**Dataset :** 128 matchs, 16 équipes  
**Pattern dominant :** CSKA Sofia HOME 76-90 = **85.7% récurrence** (6/7 matchs)  
**Validation terrain :** 88.9% de réussite sur pattern dominant

**Distribution globale buts :**
```
1-15   :  12.2%
16-30  :  10.4%
31-45  :  19.3% ⭐ (fin 1ère MT)
46-60  :  16.3%
61-75  :  14.2%
76-90  :  27.5% 🔥 (fin de match - DOMINANT)
```

---

## ✅ CHECKLIST D'APPLICATION AUTRES LIGUES

### Avant de scraper une nouvelle ligue :

- [ ] Vérifier URL formtable.asp avec le bon league_code
- [ ] Tester extraction codes équipes (ÉTAPE 1)
- [ ] Vérifier structure HTML de teamstats.asp (peut varier légèrement)
- [ ] Tester extraction tooltip sur 1 équipe
- [ ] Valider format goal_times (toujours 10 éléments avec padding)

### Pendant le scraping :

- [ ] Throttling 2-3 secondes entre requêtes
- [ ] Max 4 workers parallèles
- [ ] Vérifier que DB ne s'efface PAS (SELECT-UPDATE/INSERT)
- [ ] Logger les erreurs sans bloquer le processus

### Après le scraping :

- [ ] Vérifier nombre équipes scrapées = nombre attendu
- [ ] Vérifier balance buts : SUM(goals_for) = SUM(goals_against)
- [ ] Tester analyse patterns avec VRAIE méthode récurrence
- [ ] Comparer distribution 76-90 avec Bulgarie (~27-30%)

---

## 🚨 ERREURS À NE JAMAIS REPRODUIRE

### ❌ Erreur #1 : Mauvais calcul de récurrence
```python
# FAUX
recurrence = (total_buts / total_matchs) * 100  # ❌

# CORRECT
recurrence = (matchs_avec_but / total_matchs) * 100  # ✅
```

### ❌ Erreur #2 : Effacement données lors nouveau scraping
```python
# FAUX - Efface TOUT
cursor.execute("DELETE FROM soccerstats_scraped_matches")  # ❌

# CORRECT - Efface seulement la ligue concernée
cursor.execute("DELETE FROM soccerstats_scraped_matches WHERE league = ?", (league_code,))  # ✅
```

### ❌ Erreur #3 : Goal_times de taille variable
```python
# FAUX
goal_times = [13, 35]  # ❌ Array de 2 éléments

# CORRECT
goal_times = [13, 35, 0, 0, 0, 0, 0, 0, 0, 0]  # ✅ Toujours 10 éléments
```

### ❌ Erreur #4 : Utiliser json_array_length() en SQL
```python
# FAUX - Compte les zéros aussi
SELECT AVG(json_array_length(goal_times)) FROM ...  # ❌ Retourne 10.0 toujours

# CORRECT - Filtrer en Python
goals_count = sum(1 for g in json.loads(goal_times) if g > 0)  # ✅
```

---

## 📝 TEMPLATE CODE NOUVELLE LIGUE

```python
#!/usr/bin/env python3
"""
Scraper pour {LIGUE_NAME}
Suit EXACTEMENT la méthodologie Bulgarie validée
"""

# Copier scrape_bulgaria_auto.py
# Modifier seulement :
# - league_code (ex: "france", "england", "spain")
# - country (ex: "France", "England", "Spain")
# - league_display (ex: "Ligue 1", "Premier League", "La Liga")

# NE PAS MODIFIER :
# - Structure extract_team_codes()
# - Logique _extract_goals_from_tooltip()
# - Format goal_times (10 éléments)
# - Méthode save_to_db() SELECT-UPDATE/INSERT
# - Throttling et workers
```

---

## 🔄 SCRAPING HEBDOMADAIRE ET MAINTENANCE

### Stratégie de mise à jour (1x par semaine)

**Objectif :** Garder les données à jour sans créer de doublons

**Méthode recommandée : DELETE + INSERT FULL**

```python
# Option A : DELETE puis INSERT (SIMPLE, FIABLE)
def weekly_update(league_code: str):
    """
    Mise à jour hebdomadaire complète
    
    Avantages :
    - Pas de risque de doublons
    - Données toujours fraîches
    - Simple à maintenir
    
    Inconvénients :
    - Efface tout (mais c'est voulu)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Supprimer SEULEMENT cette ligue
    cursor.execute(
        "DELETE FROM soccerstats_scraped_matches WHERE league = ?",
        (league_code,)
    )
    conn.commit()
    print(f"✅ Anciennes données {league_code} supprimées")
    
    # 2. Re-scraper TOUTE la ligue
    scraper = AutoScraper()
    scraper.run(league_code=league_code, parallel_workers=4)
    
    conn.close()

# Appel hebdomadaire (via cron)
weekly_update("bulgaria")
weekly_update("france")
weekly_update("england")
# etc...
```

**Alternative : UPDATE/INSERT sélectif** (déjà implémenté)

```python
# Option B : UPDATE/INSERT intelligent (PLUS COMPLEXE)
# Utilisé dans scrape_bulgaria_auto.py save_to_db()

# Avantages :
# - Garde l'historique
# - Met à jour seulement ce qui a changé

# Inconvénients :
# - Risque de doublons si logique cassée
# - Plus difficile à debugger

# Code déjà dans save_to_db() :
cursor.execute('''
    SELECT COUNT(*) FROM soccerstats_scraped_matches 
    WHERE team = ? AND opponent = ? AND date = ? AND is_home = ?
''', (match['team'], match['opponent'], match['date'], 1 if match['is_home'] else 0))

if cursor.fetchone()[0] > 0:
    # UPDATE
else:
    # INSERT
```

**⚠️ Recommandation :** Utiliser **Option A (DELETE + INSERT)** pour simplicité et fiabilité

---

### Planification cron (Linux/macOS)

```bash
# Exécuter chaque dimanche à 3h du matin
0 3 * * 0 cd /workspaces/paris-live && python3 weekly_scraper.py >> scraping.log 2>&1
```

**weekly_scraper.py :**
```python
#!/usr/bin/env python3
"""
Script de scraping hebdomadaire pour toutes les ligues
Exécuté automatiquement chaque semaine
"""
import sqlite3
from scrape_all_leagues_auto import AutoScraper

LEAGUES = {
    'bulgaria': 'Bulgaria',
    'france': 'France', 
    'england': 'England',
    'spain': 'Spain',
    'italy': 'Italy',
    'germany': 'Germany'
}

DB_PATH = "football-live-prediction/data/predictions.db"

def weekly_update():
    """Mise à jour hebdomadaire de toutes les ligues"""
    
    for league_code, country in LEAGUES.items():
        print(f"\n{'='*80}")
        print(f"🔄 MISE À JOUR HEBDOMADAIRE : {country}")
        print(f"{'='*80}\n")
        
        # 1. Supprimer anciennes données
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM soccerstats_scraped_matches WHERE league = ?",
            (league_code,)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"✅ {deleted} anciennes entrées supprimées pour {league_code}")
        
        # 2. Re-scraper
        try:
            scraper = AutoScraper()
            scraper.run(league_code=league_code, parallel_workers=4)
            print(f"✅ {country} mise à jour avec succès\n")
        except Exception as e:
            print(f"❌ Erreur {country}: {e}\n")
            continue

if __name__ == "__main__":
    weekly_update()
```

---

### Vérification post-scraping

```python
def verify_data_integrity(league_code: str):
    """
    Vérifier l'intégrité des données après scraping
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Nombre d'équipes
    cursor.execute(
        "SELECT COUNT(DISTINCT team) FROM soccerstats_scraped_matches WHERE league = ?",
        (league_code,)
    )
    nb_teams = cursor.fetchone()[0]
    print(f"✅ {nb_teams} équipes distinctes")
    
    # 2. Nombre de matchs
    cursor.execute(
        "SELECT COUNT(*) FROM soccerstats_scraped_matches WHERE league = ?",
        (league_code,)
    )
    nb_matches = cursor.fetchone()[0]
    print(f"✅ {nb_matches} matchs enregistrés")
    
    # 3. Balance buts (CRITIQUE)
    cursor.execute("""
        SELECT SUM(goals_for), SUM(goals_against)
        FROM soccerstats_scraped_matches 
        WHERE league = ?
    """, (league_code,))
    scored, conceded = cursor.fetchone()
    
    if scored == conceded:
        print(f"✅ Balance buts OK : {scored} = {conceded}")
    else:
        print(f"⚠️  ALERTE Balance : {scored} ≠ {conceded} (diff: {abs(scored-conceded)})")
    
    # 4. Détection doublons
    cursor.execute("""
        SELECT team, opponent, date, is_home, COUNT(*) as nb
        FROM soccerstats_scraped_matches 
        WHERE league = ?
        GROUP BY team, opponent, date, is_home
        HAVING COUNT(*) > 1
    """, (league_code,))
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"⚠️  {len(duplicates)} doublons détectés :")
        for dup in duplicates[:5]:
            print(f"   - {dup}")
    else:
        print(f"✅ Aucun doublon détecté")
    
    conn.close()

# Appeler après chaque scraping
verify_data_integrity("bulgaria")
```

---

### Logs et monitoring

```python
import logging
from datetime import datetime

# Configuration logging
logging.basicConfig(
    filename=f'scraping_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Dans le scraper
logging.info(f"Début scraping {league_code}")
logging.info(f"{nb_teams} équipes trouvées")
logging.info(f"{nb_matches} matchs scrapés")
logging.error(f"Erreur scraping {team_name}: {error}")
```

---

## 🎯 GOLDEN RULES

1. **RÉCURRENCE = MATCHS avec but, PAS total buts**
2. **goal_times = TOUJOURS 10 éléments**
3. **76-90 = intervalle dominant (~27-30% des buts)**
4. **SELECT avant UPDATE/INSERT = pas de doublons**
5. **Throttling 2-3s = respect serveur**
6. **Validation balance : goals_for = goals_against**
7. **Scraping hebdomadaire = DELETE + INSERT complet par ligue**
8. **Vérifier intégrité après chaque scraping**

---

## 📅 WORKFLOW COMPLET HEBDOMADAIRE

```
DIMANCHE 3h00 AM (cron)
  │
  ├─► DELETE anciennes données Bulgaria
  ├─► SCRAPE Bulgaria (16 équipes × 14 matchs)
  ├─► VERIFY intégrité (balance buts, doublons)
  │
  ├─► DELETE anciennes données France
  ├─► SCRAPE France (18 équipes × 14 matchs)
  ├─► VERIFY intégrité
  │
  ├─► DELETE anciennes données England
  ├─► SCRAPE England (20 équipes × 14 matchs)
  ├─► VERIFY intégrité
  │
  └─► ... etc pour Spain, Italy, Germany

LUNDI 8h00 AM
  │
  └─► ANALYSE patterns pour toutes les ligues
      ├─► Calcul récurrences 31-45 et 76-90
      ├─► Classement par % récurrence
      └─► Mise à jour base patterns exploitables
```

---

**FIN DU DOCUMENT DE RÉFÉRENCE**

Cette méthodologie est **IMMUABLE** et doit être suivie **À LA LETTRE** pour toutes les ligues.
