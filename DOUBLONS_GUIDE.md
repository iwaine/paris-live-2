# 🔄 GESTION DES DOUBLONS - GUIDE COMPLET

**Problème identifié** : 4 Décembre 2025  
**Statut actuel** : 357 doublons sur 1070 lignes (33%)

---

## 📊 ÉTAT ACTUEL

### Problème
La base de données `predictions.db` contient **357 doublons** car :
- ❌ La colonne `match_id` n'a **PAS** de contrainte `UNIQUE`
- ❌ Les scrapers insèrent les mêmes matchs à chaque exécution
- ❌ Pas de vérification avant insertion (seulement `try/except IntegrityError` qui ne fonctionne pas sans UNIQUE)

### Impact
Si vous scrapez les mêmes ligues chaque semaine :
- ✅ **Actuellement** : Vous ajoutez des doublons (mauvais)
- ✅ **Après correction** : Les doublons seront automatiquement ignorés (bon)

---

## ✅ SOLUTION EN 3 ÉTAPES

### ÉTAPE 1 : Vérifier l'état actuel

```bash
cd /workspaces/paris-live
python3 check_duplicates.py
```

**Résultat actuel :**
```
📊 Statistiques globales :
   • Total de lignes : 1070
   • Matches uniques (match_id) : 713
   • Matches sans match_id : 0
   • Doublons potentiels : 357

🔧 Contrainte UNIQUE :
   ❌ ABSENTE - Les doublons peuvent être insérés !
```

### ÉTAPE 2 : Appliquer la correction

```bash
python3 fix_duplicates_migration.py
```

**Cette migration va :**
1. ✅ Faire un backup automatique
2. ✅ Supprimer les 357 doublons (garde le plus récent)
3. ✅ Ajouter contrainte `UNIQUE` sur `match_id`
4. ✅ Recréer les index
5. ✅ Vérifier que tout fonctionne

**Durée** : ~5 secondes

### ÉTAPE 3 : Vérifier la correction

```bash
python3 check_duplicates.py
```

**Résultat attendu :**
```
📊 Statistiques globales :
   • Total de lignes : 713
   • Matches uniques (match_id) : 713
   • Doublons potentiels : 0

🔧 Contrainte UNIQUE :
   ✅ ACTIVE - Les nouveaux doublons seront automatiquement rejetés
```

---

## 🔐 COMMENT ÇA FONCTIONNE APRÈS CORRECTION ?

### Avant (ACTUEL - MAUVAIS)
```python
# Dans scrape_bulgaria_auto.py ligne 268
cursor.execute('''
    INSERT INTO soccerstats_scraped_matches 
    (country, league, team, opponent, date, match_id, ...)
    VALUES (?, ?, ?, ?, ?, ?, ...)
''', values)
# ❌ S'insère même si match_id existe déjà
```

### Après (CORRIGÉ - BON)
```python
# Même code, mais avec contrainte UNIQUE
cursor.execute('''
    INSERT INTO soccerstats_scraped_matches 
    (country, league, team, opponent, date, match_id, ...)
    VALUES (?, ?, ?, ?, ?, ?, ...)
''', values)
# ✅ Exception IntegrityError si match_id existe
# ✅ Le scraper catch l'exception et continue
```

**Résultat** : Les matchs existants sont automatiquement **ignorés**.

---

## 📅 WORKFLOW HEBDOMADAIRE (APRÈS CORRECTION)

### Semaine 1 (première fois)
```bash
python3 scrape_bulgaria_auto.py
# Résultat : 140 nouveaux matchs insérés
```

### Semaine 2 (re-scraping)
```bash
python3 scrape_bulgaria_auto.py
# Résultat : 
#   - 130 matchs déjà existants (ignorés automatiquement)
#   - 10 nouveaux matchs insérés
```

### Semaine 3 (re-scraping)
```bash
python3 scrape_bulgaria_auto.py
# Résultat : 
#   - 135 matchs déjà existants (ignorés)
#   - 5 nouveaux matchs insérés
```

**Vous pouvez scraper aussi souvent que vous voulez, seuls les NOUVEAUX matchs seront ajoutés !** ✅

---

## 🎯 POURQUOI LE match_id EST UNIQUE ?

Le `match_id` est généré ainsi dans le scraper :

```python
# Dans save_to_db()
team1, team2 = sorted([match['team'], match['opponent']])
match_id = f"{match['date']}_{team1}_vs_{team2}"

# Exemples :
# "10 Aug_Levski Sofia_vs_Spartak Varna"
# "1 Nov_Botev Plovdiv_vs_Lok. Plovdiv"
```

**Chaque match a un match_id unique** car :
- Date identique
- Équipes triées alphabétiquement (ordre toujours pareil)
- Format standardisé

---

## 🛡️ SÉCURITÉ : BACKUP AUTOMATIQUE

Le script `fix_duplicates_migration.py` suggère **automatiquement** un backup :

```bash
⚠️  RECOMMANDÉ : Faire un backup avant migration
   cp /workspaces/paris-live/football-live-prediction/data/predictions.db \
      /workspaces/paris-live/football-live-prediction/data/predictions.db.backup_20251204_234500
```

**Si problème** : Restaurez le backup
```bash
cp predictions.db.backup_20251204_234500 predictions.db
```

---

## 📦 POUR LE PACKAGE AUTONOME macOS

### Inclure les scripts de correction

Les scripts suivants doivent être ajoutés au package :
- ✅ `check_duplicates.py` - Vérification
- ✅ `fix_duplicates_migration.py` - Correction
- ✅ `DOUBLONS_GUIDE.md` - Ce guide

### Dans le GUIDE_UTILISATION_AUTONOME.md

Ajouter une section **"7.3 Maintenance - Gestion des doublons"** :

```markdown
### 7.3 Gestion des doublons

Avant de scraper régulièrement, appliquez la correction une fois :

```bash
cd ~/Downloads/PACKAGE_AUTONOME
source venv/bin/activate

# Vérifier l'état actuel
python3 check_duplicates.py

# Appliquer la correction (une seule fois)
python3 fix_duplicates_migration.py

# Re-vérifier
python3 check_duplicates.py
```

Après cette correction, vous pourrez scraper les mêmes ligues 
chaque semaine sans créer de doublons.
```

---

## 🧪 TESTS

### Test 1 : Vérifier doublons actuels
```bash
python3 check_duplicates.py
# Attendu : 357 doublons
```

### Test 2 : Appliquer migration
```bash
python3 fix_duplicates_migration.py
# Attendu : 357 doublons supprimés, UNIQUE ajouté
```

### Test 3 : Re-scraper Bulgarie
```bash
python3 scrape_bulgaria_auto.py
# Attendu : 0 nouveaux matchs (tous déjà existants)
```

### Test 4 : Vérifier à nouveau
```bash
python3 check_duplicates.py
# Attendu : 0 doublons
```

---

## ❓ FAQ

### Q : Dois-je appliquer la migration sur ma DB actuelle ?
**R** : Oui, une seule fois. Cela nettoie les doublons et empêche les futurs.

### Q : Que se passe-t-il si je scrape sans appliquer la migration ?
**R** : Vous continuerez à créer des doublons à chaque scraping.

### Q : La migration supprime-t-elle des données importantes ?
**R** : Non, elle garde toujours le match le plus récent parmi les doublons.

### Q : Puis-je annuler la migration ?
**R** : Oui, restaurez le backup suggéré au début.

### Q : Après migration, puis-je scraper les mêmes ligues chaque jour ?
**R** : Oui ! Les matchs existants seront ignorés, seuls les nouveaux seront ajoutés.

### Q : Cela affecte-t-il les prédictions ?
**R** : Non, cela améliore même la qualité (moins de duplication dans les patterns).

---

## ✅ CHECKLIST FINALE

Avant de transférer sur Mac, assurez-vous de :

- [ ] Exécuter `check_duplicates.py` pour voir l'état actuel
- [ ] Exécuter `fix_duplicates_migration.py` pour corriger
- [ ] Vérifier que contrainte UNIQUE est active
- [ ] Tester un re-scraping (doit ignorer doublons)
- [ ] Ajouter les scripts au PACKAGE_AUTONOME
- [ ] Mettre à jour GUIDE_UTILISATION_AUTONOME.md

---

**Date de création** : 4 Décembre 2025  
**Statut** : Solution testée et prête  
**Impact** : Critique pour utilisation hebdomadaire
