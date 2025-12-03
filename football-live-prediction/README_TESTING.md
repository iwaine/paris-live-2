# 🧪 Guide de Test - Phase 3

## 🎯 Test Rapide (2 minutes)

```bash
cd football-live-prediction

# Lancer le test automatique
./quick_test.sh
```

Ce script va:
1. ✅ Vérifier Python et dépendances
2. ✅ Tester avec données simulées
3. ✅ Détecter matchs live réels (Bosnia + Bulgaria)
4. ✅ Optionnellement extraire les données complètes

---

## 📋 Tests Disponibles

### 1. Test Automatique (Recommandé)

```bash
./quick_test.sh
```

**Le plus simple!** Fait tout automatiquement.

---

### 2. Tests Manuels

#### Test rapide (10 secondes)
```bash
python3 test_live_detection.py --mode quick
```

#### Test avec extraction complète (30-60 secondes)
```bash
python3 test_live_detection.py --mode quick --extract
```

#### Test toutes les ligues (2-3 minutes)
```bash
python3 test_live_detection.py --mode all
```

#### Test une ligue spécifique
```bash
python3 test_live_detection.py --mode single --league Bulgaria
python3 test_live_detection.py --mode single --league France
```

---

### 3. Démo (Sans Internet)

```bash
python3 test_phase3_demo.py
```

Montre le fonctionnement avec des données simulées.

---

## 🕐 Meilleurs Moments pour Tester

**Peu/pas de matchs**:
- Lundi-Jeudi matin
- Périodes de trêve

**Beaucoup de matchs**:
- 🇫🇷 Vendredi 19h-21h (Ligue 1)
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Samedi 15h-17h (Premier League)
- 🇪🇸 Dimanche 20h-22h (La Liga)
- Week-end en général

---

## ✅ Résultats Attendus

### Journée Calme
```
🎯 RÉSULTAT: 0-2 match(es) live trouvé(s) au total
```

### Week-end Chargé
```
🎯 RÉSULTAT: 10-20 match(es) live trouvé(s) au total
```

### Avec Extraction
```
✅ DONNÉES EXTRAITES:
   Équipes : BEROE vs CHERNO MORE
   Score   : 1-1
   Minute  : 75'

📊 STATISTIQUES:
   Possession       : 55.0% - 45.0%
   Tirs totaux      : 9 - 8
   Tirs cadrés      : 4 - 5
   Attaques         : 87 - 112
   Attaques danger. : 42 - 65
   Corners          : 4 - 2
```

---

## 🐛 Problèmes Courants

### "Python 3 non trouvé"
```bash
# Installer Python 3
# Ubuntu/Debian:
sudo apt install python3 python3-pip

# macOS:
brew install python3
```

### "Dépendances manquantes"
```bash
pip install requests beautifulsoup4 pyyaml loguru lxml
```

### "Connexion refusée"
- Vérifier connexion internet
- Tester: `curl -I https://www.soccerstats.com`
- Désactiver proxy si nécessaire

---

## 📚 Documentation Complète

- **TEST_LOCAL_GUIDE.md** - Guide détaillé avec tous les scénarios
- **LIVE_SCRAPING_SYSTEM.md** - Architecture du système
- **AUTO_MONITOR_GUIDE.md** - Système automatique (Phase 4)

---

## 🚀 Après les Tests

Une fois Phase 3 validée, passer à Phase 4:

```bash
# Tester le système automatique complet
python3 auto_live_monitor.py --test

# Lancer en production
python3 auto_live_monitor.py
```

---

## ✨ Checklist

Avant de passer à Phase 4:

- [ ] `quick_test.sh` réussi
- [ ] Au moins 1 match détecté (si heures de matchs)
- [ ] Extraction complète réussie
- [ ] Toutes les stats présentes
- [ ] Pas d'erreurs

---

**Quick Start**: `./quick_test.sh` 🚀
