# 🎯 RÉCAP SIMPLE DU PROJET

## C'EST QUOI LE PROJET?

Un système qui surveille **automatiquement** les matchs de foot en direct sur 44 ligues et te dit quand parier.

---

## COMMENT ÇA MARCHE? (3 ÉTAPES)

```
1. DÉTECTION 🔍
   → Cherche les matchs en cours sur soccerstats.com
   → 44 ligues scannées toutes les 5 minutes

2. ANALYSE 📊
   → Extrait: équipes, score, minute, stats
   → Calcule le "danger score" (probabilité de but)

3. ALERTE 🔔
   → Si danger score ≥ 3.5 → Message Telegram
   → "PARIER MAINTENANT!"
```

---

## LES 3 FICHIERS IMPORTANTS

### 1. `live_match_detector.py`
**Rôle**: Trouve les matchs live sur soccerstats.com
**URL**: https://www.soccerstats.com/latest.asp?league=...

### 2. `soccerstats_live_scraper.py`
**Rôle**: Extrait les données d'un match (score, stats, etc.)
**URL**: https://www.soccerstats.com/pmatch.asp?...

### 3. `auto_live_monitor.py`
**Rôle**: Le chef d'orchestre - fait tout automatiquement
**Utilise**: Les 2 scripts ci-dessus + prédictions + Telegram + base de données

---

## COMMENT UTILISER?

### Option 1: TESTER (Recommandé)
```bash
cd football-live-prediction
./quick_test.sh
```

**Résultat**: Trouve et affiche les matchs live actuels

---

### Option 2: LANCER LE SYSTÈME COMPLET
```bash
python3 auto_live_monitor.py
```

**Ce qui se passe**:
- Toutes les 5 min: scan de 44 ligues
- Pour chaque match live trouvé:
  - Extrait les données
  - Calcule le danger score
  - Si ≥ 3.5 → Alerte Telegram
  - Stocke en base de données
- Tourne jusqu'à ce que tu l'arrêtes (Ctrl+C)

---

## OÙ SONT LES DONNÉES?

### Données Historiques (pour les prédictions)
```
📁 data/team_profiles/
   ├── arsenal_profile.json
   ├── manchester_city_profile.json
   └── ...
```

**Contenu**: Buts marqués/encaissés par intervalle de 15 min

**Génération**: `python3 setup_profiles.py`

---

### Données En Temps Réel (prédictions)
```
📁 data/
   └── production.db (SQLite)
```

**Contenu**: Matchs surveillés + prédictions faites

---

## LE DANGER SCORE (LA FORMULE MAGIQUE)

```
danger_score = (attaque × 0.6 + défense × 0.4) × forme × saturation
```

**Exemple**:
- Arsenal attaque bien à domicile 61-75 min: 1.2 buts/match
- Man City défend mal à l'extérieur 61-75 min: 0.8 buts encaissés
- Forme d'Arsenal: Bonne récemment
- Score actuel: 1-1 (saturation moyenne)

**Résultat**: danger_score = 4.2 → **ULTRA-DANGEREUX** → PARIER!

---

## LES NIVEAUX

| Danger Score | Niveau | Action |
|--------------|--------|--------|
| ≥ 4.0 | 🔴 ULTRA-DANGEREUX | PARIER MAINTENANT! |
| 3.0-4.0 | 🟠 DANGEREUX | Bon moment |
| 2.0-3.0 | 🟡 MODÉRÉ | Surveiller |
| < 2.0 | 🟢 FAIBLE | Passer |

---

## EXEMPLE CONCRET

**Tu lances**: `python3 auto_live_monitor.py`

**Le système**:
1. Scan 44 ligues → Trouve 3 matchs live
2. Match 1: Arsenal vs City @ 65'
   - Extrait: Arsenal 1-1 City (65')
   - Calcule: danger_score = 4.2
   - **Alerte Telegram**: "🔴 ULTRA-DANGEREUX - PARIER MAINTENANT!"
3. Match 2: PSG vs OM @ 38'
   - Calcule: danger_score = 1.8
   - Pas d'alerte (trop faible)
4. Match 3: Bulgarie...
   - Continue...

**Toutes les 5 min**: Re-scan pour nouveaux matchs

---

## CONFIGURATION

### Fichier: `config.yaml`

**Les 44 ligues**:
```yaml
leagues:
  - name: France – Ligue 1
    url: https://www.soccerstats.com/latest.asp?league=france
  - name: England – Premier League
    url: https://www.soccerstats.com/latest.asp?league=england
  # ... 42 autres
```

### Telegram (optionnel)
```bash
export TELEGRAM_BOT_TOKEN="ton_token"
export TELEGRAM_CHAT_ID="ton_chat_id"
```

---

## WORKFLOW SIMPLE

```
┌─────────────────────────────────────┐
│  1. SETUP (Une fois)                │
│     - Pull le repo                  │
│     - pip install requirements      │
│     - Configurer Telegram (opt.)    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  2. TEST                            │
│     ./quick_test.sh                 │
│     → Vérifie que ça marche         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  3. PRODUCTION                      │
│     python3 auto_live_monitor.py    │
│     → Surveille 24/7                │
│     → Alerte Telegram               │
└─────────────────────────────────────┘
```

---

## FAQ RAPIDE

**Q: Où trouver les matchs live?**
A: `live_match_detector.py` ou `python3 test_live_detection.py --mode quick`

**Q: Comment ça calcule le danger score?**
A: Utilise l'historique dans `data/team_profiles/*.json`

**Q: Comment ajouter des équipes?**
A: Éditer `config.yaml` + lancer `python3 setup_profiles.py`

**Q: Ça marche sans internet?**
A: Non, il faut internet pour soccerstats.com

**Q: Ça marche sans Telegram?**
A: Oui! Lance avec `--no-telegram`

---

## SCRIPTS PRINCIPAUX

| Script | Rôle | Quand l'utiliser |
|--------|------|------------------|
| `quick_test.sh` | Teste tout | Début, pour vérifier |
| `test_live_detection.py` | Teste détection | Debug détection |
| `auto_live_monitor.py` | Système complet | Production 24/7 |
| `setup_profiles.py` | Génère profils | Mise à jour équipes |

---

## EN RÉSUMÉ ULTRA-COURT

**1 commande pour tout tester**:
```bash
./quick_test.sh
```

**1 commande pour lancer en prod**:
```bash
python3 auto_live_monitor.py
```

**Ce que ça fait**:
- Surveille 44 ligues automatiquement
- Te dit quand parier (Telegram)
- Stocke tout en base de données

**C'est tout!** 🎯

---

## PROCHAINE ÉTAPE

```bash
# Sur ton PC (pas Codespaces):
git pull origin claude/continue-conversation-01CTn5GEeYZ6YMTxYVbyjtHe
cd football-live-prediction
./quick_test.sh
```

**Si OK** → Lance en prod:
```bash
python3 auto_live_monitor.py
```

---

**SIMPLE, NON?** 😊
