# 🧪 Guide de Test en Local - Phase 3

## 📋 Objectif

Tester le système de détection et extraction de matchs live avec des **données réelles** depuis SoccerStats.com.

---

## 🔧 Prérequis

### 1. Python et Dépendances

```bash
# Vérifier Python
python3 --version  # 3.8+ requis

# Installer les dépendances
cd football-live-prediction
pip install -r requirements.txt

# Ou installer manuellement
pip install requests beautifulsoup4 pyyaml loguru lxml
```

### 2. Connexion Internet

Le système nécessite un accès à `www.soccerstats.com`. Vérifier:

```bash
# Test de connexion
curl -I https://www.soccerstats.com/latest.asp?league=bulgaria

# Devrait retourner: HTTP/1.1 200 OK
# Si 403 Forbidden → problème de proxy/firewall
```

---

## 🚀 Tests Disponibles

### Test 1: Mode Rapide (Recommandé pour débuter)

Teste 2 ligues (Bosnia + Bulgaria) sans extraction complète:

```bash
python3 test_live_detection.py --mode quick
```

**Durée**: ~10-15 secondes

**Affiche**:
- Nombre de matchs live détectés
- Ligue et status de chaque match
- URLs des matchs

**Résultat attendu**:
```
================================================================================
🏟️  TEST PHASE 3: SYSTÈME DE DÉTECTION DE MATCHS LIVE
================================================================================
Mode: quick
================================================================================

🚀 Mode rapide: Test sur 2 ligues (Bosnia + Bulgaria)
================================================================================

================================================================================
🧪 TEST 3: DÉTECTION RAPIDE SUR UNE LIGUE (Bosnia)
================================================================================

📍 Ligue: Bosnia and Herzegovina – Premier League
🔗 URL: https://www.soccerstats.com/latest.asp?league=bosnia

✅ 1 match(es) live trouvé(s):

1. Status: 51 min
   URL: https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026

================================================================================
...
```

---

### Test 2: Mode Rapide avec Extraction Complète

Extrait toutes les données (équipes, score, stats):

```bash
python3 test_live_detection.py --mode quick --extract
```

**Durée**: ~30-60 secondes (selon nombre de matchs)

**Affiche** en plus:
- Noms des équipes
- Score actuel
- Minute du match
- Possession (%)
- Tirs totaux et cadrés
- Attaques et attaques dangereuses
- Corners

**Résultat attendu**:
```
================================================================================
🧪 TEST 2: EXTRACTION COMPLÈTE DES DONNÉES (2 matchs)
================================================================================

[1/2] ======================================================================
🏟️  Ligue: Bosnia and Herzegovina – Premier League
📍 Status: 51 min
🔗 URL: https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=...
----------------------------------------------------------------------

✅ DONNÉES EXTRAITES:
   Équipes : BEROE vs CHERNO MORE
   Score   : 1-1
   Minute  : 51'
   Time    : 2025-12-03T15:45:23.456789

📊 STATISTIQUES:
   Possession       : 55.0% - 45.0%
   Tirs totaux      : 9 - 8
   Tirs cadrés      : 4 - 5
   Attaques         : 87 - 112
   Attaques danger. : 42 - 65
   Corners          : 4 - 2

✅ EXTRACTION RÉUSSIE
```

---

### Test 3: Une Seule Ligue

Teste une ligue spécifique:

```bash
# Bulgaria
python3 test_live_detection.py --mode single --league Bulgaria

# France Ligue 1
python3 test_live_detection.py --mode single --league France

# Avec extraction
python3 test_live_detection.py --mode single --league Bulgaria --extract
```

**Durée**: ~5-10 secondes

**Utilité**: Debug ou test ciblé sur une ligue

---

### Test 4: Toutes les Ligues (Complet)

Scanne les **44 ligues** configurées:

```bash
python3 test_live_detection.py --mode all
```

**Durée**: ~2-3 minutes

**Affiche**:
```
[ 1/44] France – Ligue 1                               ⚪ Aucun match live
[ 2/44] France – Ligue 2                               ⚪ Aucun match live
[ 3/44] Germany – Bundesliga                           ⚪ Aucun match live
...
[29/44] Bulgaria – Parva liga                          ✅ 1 match(es) live
[30/44] Bosnia and Herzegovina – Premier League        ✅ 2 match(es) live
...
[44/44] England – Championship                         ⚪ Aucun match live

🎯 RÉSULTAT: 5 match(es) live trouvé(s) au total
```

**Avec extraction complète** (plus long):

```bash
python3 test_live_detection.py --mode all --extract
```

**Durée**: ~5-10 minutes (selon nombre de matchs)

---

## 📊 Interpréter les Résultats

### ✅ Succès Total

```
✅ PHASE 3 OPÉRATIONNELLE
Matchs live détectés : 5
```

**Signifie**:
- Le système détecte correctement les matchs live
- L'extraction fonctionne (si --extract)
- Multi-format HTML supporté (Bosnia + Bulgaria)
- Prêt pour Phase 4

---

### ⚪ Aucun Match Détecté

```
⚪ Aucun match live actuellement (normal si pas d'heure de match)
Matchs live détectés : 0
```

**Signifie**:
- Pas de matchs en cours actuellement (normal)
- **Solution**: Retester pendant les heures de matchs

**Heures propices**:
- 🕐 14h-17h (UTC): Ligues européennes
- 🕔 17h-22h (UTC): Pic d'activité
- 🕗 20h-23h (UTC): Ligues majeures (EPL, La Liga, etc.)

---

### ❌ Erreurs Possibles

#### Erreur 1: Connexion Refusée

```
❌ Error: HTTPSConnectionPool... Max retries exceeded
```

**Causes**:
- Pas de connexion internet
- Firewall bloque soccerstats.com
- Proxy mal configuré

**Solutions**:
```bash
# Test connexion
curl -I https://www.soccerstats.com

# Désactiver proxy si nécessaire
unset http_proxy
unset https_proxy

# Réessayer
python3 test_live_detection.py --mode quick
```

---

#### Erreur 2: Imports Manquants

```
ImportError: No module named 'requests'
```

**Solution**:
```bash
pip install -r requirements.txt
```

---

#### Erreur 3: Extraction Échoue

```
❌ Échec de l'extraction
```

**Causes possibles**:
- Format HTML changé sur le site
- Match terminé entre détection et extraction
- Page inaccessible temporairement

**Solutions**:
- Vérifier l'URL manuellement dans un navigateur
- Réessayer (peut être temporaire)
- Signaler le problème avec l'URL exacte

---

## 🎯 Scénarios de Test Recommandés

### Scénario 1: Validation Initiale (5 min)

**But**: Vérifier que le système fonctionne

```bash
# 1. Test rapide sans extraction
python3 test_live_detection.py --mode quick

# 2. Si matchs trouvés → extraction
python3 test_live_detection.py --mode quick --extract

# 3. Vérifier les données extraites
```

**Critères de succès**:
- ✅ Au moins 1 match détecté (si heures de matchs)
- ✅ Extraction réussie avec toutes les stats
- ✅ Pas d'erreurs Python

---

### Scénario 2: Test Complet (10 min)

**But**: Valider sur plusieurs ligues

```bash
# 1. Scan complet
python3 test_live_detection.py --mode all

# 2. Extraction sur tous les matchs
python3 test_live_detection.py --mode all --extract

# 3. Noter le nombre de matchs par ligue
```

**Critères de succès**:
- ✅ Plusieurs ligues avec matchs live
- ✅ Déduplication fonctionne (pas de doublons)
- ✅ Formats HTML multiples supportés

---

### Scénario 3: Test de Robustesse (20 min)

**But**: Tester la fiabilité

```bash
# Relancer plusieurs fois à 5 min d'intervalle
for i in {1..5}; do
    echo "=== Test $i/5 ==="
    python3 test_live_detection.py --mode all --extract
    echo "Attente 5 minutes..."
    sleep 300
done
```

**Critères de succès**:
- ✅ Détection stable dans le temps
- ✅ Gestion correcte des matchs terminés
- ✅ Pas de crashes

---

## 📈 Exemples de Résultats Réels

### Exemple 1: Journée Calme (après-midi en semaine)

```
🎯 RÉSULTAT: 2 match(es) live trouvé(s) au total

1. Bulgaria – Parva liga                   | Status: 38 min
2. Poland – Ekstraklasa                    | Status: HT
```

**Normal**: Peu de matchs en milieu de semaine

---

### Exemple 2: Week-end Chargé

```
🎯 RÉSULTAT: 15 match(es) live trouvé(s) au total

1. France – Ligue 1                        | Status: 67 min
2. England – Premier League                | Status: 23 min
3. Spain – LaLiga                          | Status: 45 min
4. Germany – Bundesliga                    | Status: 51 min
5. Italy – Serie A                         | Status: 78 min
...
```

**Excellent**: Beaucoup de matchs simultanés

---

### Exemple 3: Match Unique avec Stats

```
✅ DONNÉES EXTRAITES:
   Équipes : MANCHESTER CITY vs LIVERPOOL
   Score   : 2-1
   Minute  : 67'

📊 STATISTIQUES:
   Possession       : 58.0% - 42.0%
   Tirs totaux      : 15 - 9
   Tirs cadrés      : 8 - 4
   Attaques         : 142 - 98
   Attaques danger. : 78 - 52
   Corners          : 9 - 3

✅ EXTRACTION RÉUSSIE
```

**Parfait**: Toutes les données sont présentes

---

## 🔍 Debug et Logs

### Activer les Logs Détaillés

Modifier temporairement `test_live_detection.py`:

```python
# Au début du fichier, ajouter:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Ou** directement dans la ligne de commande:

```bash
# Logs Python
python3 -v test_live_detection.py --mode quick

# Sauvegarder les logs
python3 test_live_detection.py --mode all --extract > test_results.log 2>&1
```

---

### Analyser les Logs

Les logs montrent:
- URLs scrapées
- Temps de réponse
- HTML parsé
- Stats détectées

**Exemple de log détaillé**:
```
2025-12-03 15:45:23 | INFO  | Scanning for live matches: Bulgaria
2025-12-03 15:45:24 | DEBUG | Found 15 potential live indicators
2025-12-03 15:45:24 | DEBUG | Live status found: 51 min
2025-12-03 15:45:24 | INFO  | ✅ Live match detected: https://...
```

---

## 📝 Checklist de Validation

Avant de passer à la Phase 4, valider:

- [ ] Test rapide réussi (mode quick)
- [ ] Extraction complète réussie (--extract)
- [ ] Au moins 2 ligues testées
- [ ] Données correctes (équipes, score, stats)
- [ ] Pas d'erreurs Python
- [ ] Déduplication fonctionne
- [ ] Performance acceptable (<5s par match)

---

## 🎯 Prochaine Étape

Une fois les tests validés en local:

### Phase 4: Intégration Automatique

```bash
# Test du système automatique complet
python3 auto_live_monitor.py --test

# Surveillance continue
python3 auto_live_monitor.py
```

**Intègre**:
- ✅ Détection (Phase 3)
- ✅ Prédictions (Phase 1-2)
- ✅ Telegram (Phase 2)
- ✅ Base de données (Phase 2)

---

## 💡 Tips

### 1. Timing Optimal

**Meilleurs moments pour tester**:
- 🇫🇷 Vendredi 19h-21h: Ligue 1
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Samedi 15h-17h: Premier League
- 🇪🇸 Dimanche 20h-22h: La Liga
- 🇩🇪 Samedi 15h30-17h30: Bundesliga

### 2. Sauvegarder les Résultats

```bash
# Créer un dossier de tests
mkdir test_results

# Sauvegarder avec timestamp
python3 test_live_detection.py --mode all --extract > test_results/test_$(date +%Y%m%d_%H%M%S).log
```

### 3. Script de Test Automatique

```bash
#!/bin/bash
# test_phase3.sh

echo "🧪 Test Phase 3 - $(date)"
echo ""

# Test 1: Quick
echo "Test 1: Mode rapide"
python3 test_live_detection.py --mode quick

# Test 2: Extraction
echo ""
echo "Test 2: Avec extraction"
python3 test_live_detection.py --mode quick --extract

echo ""
echo "✅ Tests terminés"
```

Utiliser:
```bash
chmod +x test_phase3.sh
./test_phase3.sh
```

---

## 📞 Support

### En cas de problème:

1. **Vérifier les prérequis** (Python, dépendances, internet)
2. **Tester avec le mode demo** (sans internet):
   ```bash
   python3 test_phase3_demo.py
   ```
3. **Consulter la documentation**:
   - `LIVE_SCRAPING_SYSTEM.md` - Architecture
   - `AUTO_MONITOR_GUIDE.md` - Guide complet
4. **Logs détaillés** pour debug

---

## 🎉 Résumé

**Pour tester Phase 3 en local**:

```bash
# Test rapide (recommandé)
python3 test_live_detection.py --mode quick --extract

# Test complet
python3 test_live_detection.py --mode all --extract
```

**Résultat attendu**: Détection et extraction réussies de tous les matchs live actuels

**Prochaine étape**: Phase 4 (système automatique complet)

---

**Dernière mise à jour**: 3 Décembre 2025
**Status**: ✅ Prêt pour tests en local
