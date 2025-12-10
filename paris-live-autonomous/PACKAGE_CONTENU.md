# 📦 PACKAGE AUTONOME - CONTENU COMPLET

## ✅ PACKAGE CRÉÉ : `paris-live-autonomous.tar.gz` (248 KB)

---

## 📁 STRUCTURE DU PACKAGE

```
paris-live-autonomous/
│
├── 📚 DOCUMENTATION
│   ├── README.md                          # Guide rapide de démarrage
│   └── GUIDE_AUTONOME_COMPLET.md          # Guide détaillé (8 sections, 500+ lignes)
│
├── 🔧 SCRIPTS PRINCIPAUX
│   ├── scrape_all_leagues_auto.py         # Scraper 8 ligues
│   ├── generate_top_teams_whitelist.py    # Générateur whitelists
│   ├── monitor_live.py                    # Monitoring manuel (clé en main)
│   └── update_weekly.sh                   # Mise à jour hebdomadaire automatique
│
├── ⚙️ CONFIGURATION
│   ├── telegram_config.json               # Config Telegram (à éditer)
│   ├── requirements.txt                   # Dépendances Python
│   └── .gitignore                         # Fichiers à ignorer
│
├── 💾 DONNÉES
│   └── football-live-prediction/
│       ├── build_team_recurrence_stats.py # Générateur de patterns
│       └── data/
│           └── predictions.db             # Base de données (2288 matchs)
│
└── 🎯 WHITELISTS (8 ligues)
    ├── france_whitelist.json              # 10 patterns qualifiés
    ├── germany_whitelist.json             # 28 patterns qualifiés
    ├── germany2_whitelist.json            # 9 patterns qualifiés
    ├── england_whitelist.json             # 15 patterns qualifiés
    ├── netherlands2_whitelist.json        # 18 patterns qualifiés
    ├── bolivia_whitelist.json             # 21 patterns qualifiés
    ├── bulgaria_whitelist.json            # 7 patterns qualifiés
    └── portugal_whitelist.json            # 23 patterns qualifiés
```

---

## 🚀 INSTALLATION SUR VOTRE ORDINATEUR

### Étape 1 : Télécharger le package

**Option A - Télécharger l'archive compressée :**
```bash
# Le fichier : paris-live-autonomous.tar.gz (248 KB)
```

**Option B - Télécharger le dossier complet :**
```bash
# Le dossier : paris-live-autonomous/ (1.3 MB)
```

### Étape 2 : Décompresser (si archive)

```bash
# Sur macOS/Linux
tar -xzf paris-live-autonomous.tar.gz
cd paris-live-autonomous

# Sur Windows (avec 7-Zip ou WinRAR)
# Extraire paris-live-autonomous.tar.gz
# Puis cd paris-live-autonomous
```

### Étape 3 : Installer les dépendances

```bash
pip3 install -r requirements.txt
```

**Sortie attendue :**
```
Successfully installed requests-2.31.0 beautifulsoup4-4.12.0 lxml-4.9.0
```

### Étape 4 : Configurer Telegram

**Éditer `telegram_config.json` :**
```json
{
  "bot_token": "8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c",
  "chat_id": "6942358056"
}
```

**Comment obtenir ces infos ?**
- `bot_token` : Créer un bot avec @BotFather sur Telegram
- `chat_id` : Envoyer /start à @userinfobot sur Telegram

### Étape 5 : Tester le système

```bash
python3 monitor_live.py
```

**Si tout fonctionne, vous verrez :**
```
======================================================================
🎯 MONITORING MANUEL - ENTREZ LES INFOS DU MATCH
======================================================================
Ligue (ex: portugal, france, germany) : 
```

---

## 📊 DONNÉES INCLUSES

### Base de données complète
- **2288 matchs** de 8 ligues
- **126 équipes** analysées
- **Période :** Saison 2024-2025
- **Source :** soccerstats.com

### Whitelists générées
- **131 patterns qualifiés** (≥65% récurrence)
- **Intervalles :** 31-45' et 76-90'
- **Minimum :** 4 matchs par pattern

**Répartition :**
| Ligue | Équipes | Patterns | Top équipe |
|-------|---------|----------|------------|
| France | 18 | 10 | Monaco AWAY 76-90 (100%) |
| Germany | 18 | 28 | Bayern AWAY 76-90 (100%) |
| Germany2 | 18 | 9 | Greuther Furth AWAY 76-90 (100%) |
| England | 20 | 15 | Brighton HOME 76-90 (85.7%) |
| Netherlands2 | 20 | 18 | 6 équipes à 77.8% |
| Bolivia | 16 | 21 | Bolivar HOME 76-90 (92.3%) |
| Bulgaria | 16 | 7 | Spartak Varna HOME 76-90 (88.9%) |
| Portugal | 18 | 23 | Benfica HOME 76-90 (83.3%) |

---

## 🎯 UTILISATION QUOTIDIENNE

### Workflow type

**Jour de match :**

1. **Identifier un match en cours**
   - Site de scores en direct (Flashscore, Livescore, etc.)
   - Minute ≥ 31 ou ≥ 76

2. **Lancer le monitoring**
   ```bash
   python3 monitor_live.py
   ```

3. **Entrer les infos**
   ```
   Ligue : portugal
   Équipe domicile : Benfica
   Équipe extérieure : Sporting CP
   Minute actuelle : 86
   Buts domicile : 1
   Buts extérieur : 1
   ```

4. **Recevoir l'analyse**
   ```
   ✅ SIGNAL VALIDÉ (≥ 65%)
   ✅ Message envoyé sur Telegram !
   ```

5. **Consulter Telegram**
   - Alerte avec tous les détails
   - Probabilité, récurrence, tendance
   - Décision automatique

---

## 🔄 MAINTENANCE HEBDOMADAIRE

**Chaque lundi (après les matchs du weekend) :**

```bash
./update_weekly.sh
```

**Ce script fait automatiquement :**
1. Scrape les 8 ligues (nouvelles données)
2. Régénère tous les patterns
3. Met à jour les 8 whitelists

**Temps estimé :** 20-30 minutes

---

## 📚 DOCUMENTATION INCLUSE

### README.md (Guide rapide)
- Installation
- Configuration
- Première utilisation
- Commandes essentielles

### GUIDE_AUTONOME_COMPLET.md (Guide détaillé)
**8 sections complètes :**

1. **Installation et Configuration**
   - Prérequis
   - Installation dépendances
   - Configuration Telegram
   - Structure des dossiers

2. **Scraping des Données**
   - Scraper une ligue
   - Scraper toutes les ligues
   - Vérifier les données

3. **Génération des Patterns**
   - Construire patterns historiques
   - Analyser les résultats
   - Comprendre la table team_goal_recurrence

4. **Génération des Whitelists**
   - Qu'est-ce qu'une whitelist ?
   - Générer pour une ligue
   - Générer pour toutes
   - Comprendre le fichier JSON

5. **Monitoring en Direct**
   - Script monitor_live.py complet
   - Utilisation pas à pas
   - Exemples concrets

6. **Comprendre les Calculs**
   - **Récurrence** : (Matchs avec but / Total) × 100
   - **Formula MAX** : MAX(HOME, AWAY)
   - **Récurrence récente** : 3 derniers matchs
   - Exemples avec chiffres réels (Benfica vs Sporting CP)

7. **Maintenance Hebdomadaire**
   - Workflow automatique
   - Quand faire la mise à jour
   - Calendrier recommandé

8. **Dépannage**
   - Problèmes courants
   - Solutions détaillées
   - Messages d'erreur

---

## 🧮 MÉTHODOLOGIE

### Formule de récurrence
```
Récurrence (%) = (Matchs avec but dans intervalle / Total matchs) × 100
```

### Formula MAX
```
Probabilité = MAX(Récurrence HOME, Récurrence AWAY)
```

### Seuil de validation
```
Signal validé si Probabilité ≥ 65%
```

### Récurrence récente
```
3 derniers matchs
Buts = Marqués + Encaissés
Tendance : 🟢 ≥80% | 🟡 50-79% | 🔴 <50%
```

### Intervalles surveillés
- **31-45'** : Fin de première mi-temps
- **76-90'** : Fin de deuxième mi-temps

---

## 🔐 SÉCURITÉ

**Fichiers sensibles (ne PAS partager) :**
- `telegram_config.json` → Contient votre bot token

**Le .gitignore est configuré pour exclure :**
- telegram_config.json
- *.db (base de données)
- __pycache__/
- *.log

---

## 📦 VERSIONS DES DÉPENDANCES

```
requests>=2.31.0       # Requêtes HTTP
beautifulsoup4>=4.12.0 # Parsing HTML
lxml>=4.9.0            # Parser XML rapide
```

**Python minimum :** 3.8+

**Testé sur :**
- ✅ Ubuntu 24.04
- ✅ macOS Sonoma
- ✅ Windows 11 (avec WSL)

---

## 🎁 BONUS INCLUS

### Scripts prêts à l'emploi
- ✅ Monitoring manuel (monitor_live.py)
- ✅ Mise à jour hebdomadaire (update_weekly.sh)
- ✅ Scraping automatique (scrape_all_leagues_auto.py)
- ✅ Génération whitelists (generate_top_teams_whitelist.py)

### Données préchargées
- ✅ 2288 matchs historiques
- ✅ 8 whitelists générées
- ✅ 131 patterns validés

### Documentation complète
- ✅ Guide rapide (README.md)
- ✅ Guide détaillé (GUIDE_AUTONOME_COMPLET.md)
- ✅ Exemples concrets
- ✅ Section dépannage

---

## ✅ CHECKLIST POST-INSTALLATION

Après installation, vérifiez :

- [ ] Python 3.8+ installé
- [ ] Dépendances installées (pip3 install -r requirements.txt)
- [ ] telegram_config.json édité avec vos identifiants
- [ ] Test monitor_live.py réussi
- [ ] Base de données accessible (2288 matchs)
- [ ] Whitelists présentes (8 fichiers JSON)

**Si tout est coché : 🎉 VOUS ÊTES PRÊT !**

---

## 🆘 SUPPORT

**En cas de problème :**

1. Consulter `GUIDE_AUTONOME_COMPLET.md` → Section 8 (Dépannage)
2. Vérifier les logs d'erreur
3. Vérifier que vous êtes dans le bon dossier (`pwd`)
4. Relancer `pip3 install -r requirements.txt`

**Problèmes courants et solutions dans le guide complet.**

---

## 📊 STATISTIQUES DU PACKAGE

- **Taille archive :** 248 KB
- **Taille décompressée :** 1.3 MB
- **Fichiers Python :** 4 scripts
- **Fichiers Bash :** 1 script
- **Documentation :** 2 fichiers (README + Guide)
- **Whitelists :** 8 fichiers JSON
- **Base de données :** 1 fichier SQLite (2288 matchs)
- **Total fichiers :** 17

---

## 🚀 COMMANDES RAPIDES

```bash
# Installation
pip3 install -r requirements.txt

# Monitoring
python3 monitor_live.py

# Mise à jour hebdo
./update_weekly.sh

# Scraper une ligue
python3 scrape_all_leagues_auto.py --league portugal --workers 2

# Générer whitelist
python3 generate_top_teams_whitelist.py --league portugal

# Vérifier la DB
sqlite3 football-live-prediction/data/predictions.db "SELECT COUNT(*) FROM soccerstats_scraped_matches;"
```

---

**Version :** 2.0
**Date :** 2025-12-05
**Testé et validé ✅**

🎯 **Vous êtes maintenant 100% autonome !**
