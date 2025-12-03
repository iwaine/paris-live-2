# 📊 DONNÉES HISTORIQUES - LOCALISATION ET STRUCTURE

## 🗂️ OÙ SONT LES DONNÉES?

### 1. Profils des Équipes (Format JSON)

**Emplacement**: `/data/team_profiles/`

```
football-live-prediction/
└── data/
    └── team_profiles/
        ├── arsenal_profile.json
        ├── manchester_city_profile.json
        ├── psg_profile.json
        └── ... (un fichier par équipe)
```

**Format**: JSON (1 fichier par équipe)

---

## 📋 STRUCTURE DES DONNÉES

### Exemple: `arsenal_profile.json`

```json
{
  "team": "Arsenal",
  "league": "England - Premier League",

  "overall": {
    "gp": "13",                    // Games played (matchs joués)
    "goals_by_interval": {
      "0-15": {
        "scored": 2,               // Buts marqués dans l'intervalle
        "conceded": 1              // Buts encaissés dans l'intervalle
      },
      "16-30": { "scored": 0, "conceded": 0 },
      "31-45": { "scored": 8, "conceded": 2 },
      "46-60": { "scored": 7, "conceded": 2 },
      "61-75": { "scored": 2, "conceded": 0 },
      "76-90": { "scored": 6, "conceded": 2 }
    }
  },

  "home": {
    "gp": "6",
    "goals_by_interval": {
      "0-15": { "scored": 0, "conceded": 1 },
      "16-30": { "scored": 0, "conceded": 0 },
      "31-45": { "scored": 7, "conceded": 0 },
      "46-60": { "scored": 4, "conceded": 1 },
      "61-75": { "scored": 1, "conceded": 0 },
      "76-90": { "scored": 4, "conceded": 0 }
    },

    "recent_form_by_interval": {
      "0-15": {
        "scored": 0,               // Total buts marqués (5 derniers matchs)
        "conceded": 1,             // Total buts encaissés (5 derniers matchs)
        "scored_avg": 0.0,         // Moyenne buts marqués
        "conceded_avg": 0.25,      // Moyenne buts encaissés
        "matches": 4               // Nombre de matchs analysés
      },
      "31-45": {
        "scored": 4,
        "conceded": 0,
        "scored_avg": 1.0,         // ← Utilisé pour le danger score!
        "conceded_avg": 0.0,
        "matches": 4
      },
      // ... autres intervalles
    }
  },

  "away": {
    "gp": "7",
    "goals_by_interval": {
      "0-15": { "scored": 2, "conceded": 0 },
      "16-30": { "scored": 0, "conceded": 0 },
      "31-45": { "scored": 1, "conceded": 2 },
      "46-60": { "scored": 3, "conceded": 1 },
      "61-75": { "scored": 1, "conceded": 0 },
      "76-90": { "scored": 2, "conceded": 2 }
    }
  }
}
```

---

## 🎯 DONNÉES CLÉS UTILISÉES

### Pour les Prédictions:

**1. Composante Attaque (60%)**
```json
"home": {
  "goals_by_interval": {
    "61-75": {
      "scored": 1,  // ← Total buts marqués historiquement
      "conceded": 0
    }
  }
}
```
Utilisé: `scored / games_played` = moyenne buts marqués

**2. Composante Défense (40%)**
```json
"away": {
  "goals_by_interval": {
    "61-75": {
      "scored": 1,
      "conceded": 0  // ← Total buts encaissés historiquement
    }
  }
}
```
Utilisé: `conceded / games_played` = moyenne buts encaissés

**3. Boost de Forme**
```json
"home": {
  "recent_form_by_interval": {
    "61-75": {
      "scored_avg": 0.25,     // ← Forme récente (5 derniers matchs)
      "conceded_avg": 0.0,
      "matches": 4
    }
  }
}
```

---

## 🔧 COMMENT SONT GÉNÉRÉES CES DONNÉES?

### Script: `setup_profiles.py`

**Processus**:

```
1. Configuration (config.yaml)
   ↓
2. Liste des équipes à analyser
   ↓
3. Pour chaque équipe:
   a) Scrape historique (SoccerStatsHistoricalScraper)
   b) Calcule forme récente (RecentFormCompleteScraper)
   c) Agrège les données par intervalle
   d) Sauvegarde JSON
   ↓
4. Export Excel (optionnel)
```

---

## 📍 SOURCE DES DONNÉES

### Site: SoccerStats.com

**URL de scraping**:
```
https://www.soccerstats.com/timing.asp?league=LEAGUE&teamid=TEAM_ID
```

**Exemple pour Arsenal**:
```
https://www.soccerstats.com/timing.asp?league=england&teamid=arsenal
```

**Données extraites**:
- Buts marqués par intervalle
- Buts encaissés par intervalle
- Home vs Away
- Historique complet de la saison

---

## 🔄 MISE À JOUR DES DONNÉES

### Commande pour regénérer les profils:

```bash
cd football-live-prediction
python3 setup_profiles.py
```

**Durée**: ~2-5 minutes par équipe (dépend du nombre de matchs)

**Sortie**:
- Fichiers JSON mis à jour dans `data/team_profiles/`
- Fichier Excel exporté: `team_profiles_YYYYMMDD_HHMMSS.xlsx`

---

## 🗃️ CONFIGURATION DES ÉQUIPES

### Fichier: `config/config.yaml`

```yaml
teams:
  Arsenal:
    id: "arsenal"
    league: "england"
    enabled: true

  Manchester City:
    id: "manchestercity"
    league: "england"
    enabled: true

  PSG:
    id: "psg"
    league: "france"
    enabled: true

  # ... autres équipes
```

**Champs**:
- `id`: Identifiant sur SoccerStats.com
- `league`: Code de la ligue
- `enabled`: true/false (activer/désactiver)

---

## 📊 BASE DE DONNÉES SUPPLÉMENTAIRE

### Fichier: `data/production.db` (SQLite)

**Tables**:

**1. matches** - Matchs surveillés
```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY,
    home_team TEXT,
    away_team TEXT,
    league TEXT,
    final_score TEXT,
    status TEXT,
    created_at TIMESTAMP
)
```

**2. predictions** - Prédictions faites
```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    match_id INTEGER,
    minute INTEGER,
    interval TEXT,
    danger_score REAL,
    interpretation TEXT,
    confidence TEXT,
    result_correct INTEGER,
    predicted_at TIMESTAMP
)
```

**Note**: Cette BD stocke les **prédictions en temps réel**, pas l'historique des équipes.

---

## 🎯 UTILISATION DANS LES PRÉDICTIONS

### Code: `predictors/interval_predictor.py`

```python
def predict_match(self, home_team, away_team, current_minute, live_stats=None):
    # 1. Charger les profils JSON
    home_profile = self._load_profile(home_team)
    away_profile = self._load_profile(away_team)

    # 2. Extraire les données de l'intervalle
    interval = self._get_interval(current_minute)  # Ex: "61-75"

    # 3. Calculer attaque (60%)
    home_goals = home_profile['home']['goals_by_interval'][interval]['scored']
    home_games = int(home_profile['home']['gp'])
    attaque = home_goals / home_games

    # 4. Calculer défense (40%)
    away_conceded = away_profile['away']['goals_by_interval'][interval]['conceded']
    away_games = int(away_profile['away']['gp'])
    defense = away_conceded / away_games

    # 5. Boost de forme
    form_boost = self._calculate_form_boost(home_team, away_team, interval)

    # 6. Danger score
    danger_score = (attaque * 0.6 + defense * 0.4) * form_boost * saturation

    return {
        'danger_score': danger_score,
        'interpretation': self._interpret_score(danger_score),
        # ...
    }

def _load_profile(self, team_name):
    """Charge le profil JSON depuis data/team_profiles/"""
    file_path = f"data/team_profiles/{team_name.lower().replace(' ', '_')}_profile.json"
    with open(file_path, 'r') as f:
        return json.load(f)
```

---

## 🔍 EXEMPLE CONCRET

### Prédiction: Arsenal vs Man City @ 65' (intervalle 61-75)

**1. Charger les données**:
```python
# Arsenal à domicile
home_profile = load("data/team_profiles/arsenal_profile.json")
home_scored = home_profile['home']['goals_by_interval']['61-75']['scored']  # = 1
home_games = int(home_profile['home']['gp'])  # = 6
attaque = 1 / 6 = 0.17 buts/match

# Man City à l'extérieur
away_profile = load("data/team_profiles/manchester_city_profile.json")
away_conceded = away_profile['away']['goals_by_interval']['61-75']['conceded']  # = ?
away_games = int(away_profile['away']['gp'])  # = ?
defense = away_conceded / away_games
```

**2. Calculer le danger score**:
```python
base = (0.17 * 0.6) + (defense * 0.4)
danger_score = base * boost_forme * saturation
```

---

## 📈 AVANTAGES DE CE SYSTÈME

### ✅ Avantages:

1. **Données Locales**
   - Pas besoin de scraper à chaque prédiction
   - Réponse instantanée (<1s)

2. **Granularité**
   - Par intervalle de 15 min
   - Home vs Away séparé
   - Forme récente incluse

3. **Format JSON**
   - Facile à lire/modifier
   - Compatible avec tous les langages
   - Versionnable (Git)

4. **Mise à Jour Flexible**
   - Regénérer quand on veut
   - Par équipe ou toutes à la fois

### ⚠️ Limitations:

1. **Données Statiques**
   - Faut regénérer manuellement
   - Pas de mise à jour en temps réel

2. **Dépend de SoccerStats.com**
   - Si le site change de structure, faut adapter
   - Peut être bloqué par rate limiting

---

## 🔄 WORKFLOW COMPLET

```
┌─────────────────────────────────────────────────────────────┐
│ 1. GÉNÉRATION INITIALE (Une fois)                          │
│    python3 setup_profiles.py                                │
│    → Crée data/team_profiles/*.json                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PRÉDICTIONS EN TEMPS RÉEL                               │
│    Utilise les JSON existants                               │
│    Pas de scraping nécessaire                               │
│    Réponse instantanée                                      │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. MISE À JOUR PÉRIODIQUE (Hebdomadaire/Mensuelle)        │
│    python3 setup_profiles.py                                │
│    → Met à jour les JSON avec nouvelles données            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 COMMANDES UTILES

### Voir les équipes disponibles:
```bash
ls data/team_profiles/
```

### Lire un profil:
```bash
cat data/team_profiles/arsenal_profile.json | python3 -m json.tool
```

### Regénérer tous les profils:
```bash
python3 setup_profiles.py
```

### Ajouter une nouvelle équipe:
1. Modifier `config/config.yaml`
2. Ajouter l'équipe avec son ID
3. Lancer `python3 setup_profiles.py`

---

## 🎯 RÉSUMÉ

**Où sont les données?**
- ✅ `data/team_profiles/*.json` - Profils des équipes
- ✅ `data/production.db` - Prédictions en temps réel

**Format**:
- ✅ JSON (1 fichier par équipe)
- ✅ 6 intervalles de 15 min
- ✅ Home vs Away séparé
- ✅ Forme récente incluse

**Génération**:
- ✅ Script: `setup_profiles.py`
- ✅ Source: SoccerStats.com
- ✅ Durée: 2-5 min par équipe

**Utilisation**:
- ✅ Chargés par `interval_predictor.py`
- ✅ Utilisés pour calcul danger score
- ✅ Réponse instantanée

---

**Les données historiques sont dans `data/team_profiles/` au format JSON!** 📊
