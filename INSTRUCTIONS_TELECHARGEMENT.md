# 📥 INSTRUCTIONS DE TÉLÉCHARGEMENT

## 🎯 DEUX OPTIONS DISPONIBLES

---

## OPTION 1 : Archive Compressée (Recommandé)

### 📦 Fichier : `paris-live-autonomous.tar.gz`
- **Taille :** 252 KB
- **Contenu :** Tous les fichiers (scripts, DB, whitelists, docs)

### Sur votre ordinateur local :

**macOS / Linux :**
```bash
# Décompresser
tar -xzf paris-live-autonomous.tar.gz

# Entrer dans le dossier
cd paris-live-autonomous

# Installer les dépendances
pip3 install -r requirements.txt

# Éditer la config Telegram
nano telegram_config.json
# Ou : open telegram_config.json (macOS)
# Ou : gedit telegram_config.json (Linux)

# Tester
python3 monitor_live.py
```

**Windows (avec WSL ou Git Bash) :**
```bash
# Extraire avec 7-Zip ou WinRAR
# Puis ouvrir PowerShell ou cmd dans le dossier

# Installer dépendances
pip install -r requirements.txt

# Éditer config
notepad telegram_config.json

# Tester
python monitor_live.py
```

---

## OPTION 2 : Dossier Complet

### 📁 Dossier : `paris-live-autonomous/`
- **Taille :** 1.3 MB
- **Avantage :** Pas besoin de décompresser

### Copier sur votre Bureau :

**Depuis le workspace :**
```bash
cp -r /workspaces/paris-live/paris-live-autonomous ~/Bureau/
```

**Ou télécharger via l'interface VSCode :**
1. Clic droit sur `paris-live-autonomous/`
2. Download...
3. Sauvegarder sur votre Bureau

---

## ✅ VÉRIFICATION POST-TÉLÉCHARGEMENT

### Fichiers essentiels à vérifier :

```bash
cd paris-live-autonomous

# Lister les fichiers
ls -la

# Vous devez voir :
# ✓ README.md
# ✓ GUIDE_AUTONOME_COMPLET.md
# ✓ PACKAGE_CONTENU.md
# ✓ monitor_live.py
# ✓ scrape_all_leagues_auto.py
# ✓ generate_top_teams_whitelist.py
# ✓ update_weekly.sh
# ✓ telegram_config.json
# ✓ requirements.txt
# ✓ football-live-prediction/
# ✓ whitelists/
```

### Vérifier la base de données :

```bash
sqlite3 football-live-prediction/data/predictions.db "SELECT COUNT(*) FROM soccerstats_scraped_matches;"
# Résultat attendu : 2288
```

### Vérifier les whitelists :

```bash
ls -la whitelists/
# Résultat attendu : 8 fichiers .json
```

---

## 🔧 CONFIGURATION TELEGRAM

### Étape 1 : Créer le bot

1. Ouvrir Telegram
2. Chercher `@BotFather`
3. Envoyer `/newbot`
4. Choisir un nom (ex: "Football Predictions Bot")
5. Choisir un username (ex: "my_football_pred_bot")
6. **Copier le token** (ex: 8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c)

### Étape 2 : Obtenir votre Chat ID

1. Chercher `@userinfobot` sur Telegram
2. Envoyer `/start`
3. **Copier votre ID** (ex: 6942358056)

### Étape 3 : Éditer le fichier de configuration

```bash
# Ouvrir telegram_config.json
nano telegram_config.json
```

**Remplacer :**
```json
{
  "bot_token": "VOTRE_TOKEN_ICI",
  "chat_id": "VOTRE_CHAT_ID_ICI"
}
```

**Par :**
```json
{
  "bot_token": "8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c",
  "chat_id": "6942358056"
}
```

**Sauvegarder et quitter :**
- Nano : `Ctrl+X` puis `Y` puis `Entrée`
- Vim : `:wq`

---

## 🚀 PREMIER TEST

### Test du monitoring :

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

**Testez avec un exemple :**
```
Ligue : portugal
Équipe domicile : Benfica
Équipe extérieure : Sporting CP
Minute actuelle : 86
Buts domicile : 1
Buts extérieur : 1
```

**Résultat attendu :**
```
✅ SIGNAL VALIDÉ (≥ 65%)
✅ Message envoyé sur Telegram !
```

**Vérifiez Telegram → Vous devez recevoir le message !**

---

## 📚 DOCUMENTATION À LIRE

### Par ordre de priorité :

1. **PACKAGE_CONTENU.md** (ce fichier)
   - Vue d'ensemble du package
   - Structure complète
   - Instructions installation

2. **README.md**
   - Guide de démarrage rapide
   - Commandes essentielles

3. **GUIDE_AUTONOME_COMPLET.md**
   - Guide détaillé (500+ lignes)
   - 8 sections avec exemples
   - Dépannage complet

---

## 🔄 MISE À JOUR HEBDOMADAIRE

**Chaque lundi (recommandé) :**

```bash
./update_weekly.sh
```

**Durée :** 20-30 minutes

**Ce qui est fait automatiquement :**
1. Scraping des 8 ligues
2. Régénération des patterns
3. Mise à jour des whitelists

---

## 🎯 UTILISATION QUOTIDIENNE

### Workflow type

**Avant le match :**
- Identifier les matchs du jour
- Noter les ligues concernées

**Pendant le match (minute ≥ 31 ou ≥ 76) :**
```bash
python3 monitor_live.py
# Entrer les infos du match
# Recevoir l'analyse
# Consulter Telegram
```

**Exemples de ligues à surveiller :**
- **Portugal** : Liga Portugal (Benfica, Porto, Sporting)
- **France** : Ligue 1 (PSG, Marseille, Monaco)
- **Germany** : Bundesliga (Bayern, Dortmund, Leipzig)
- **England** : Premier League (Arsenal, Man City, Liverpool)

---

## ⚠️ POINTS IMPORTANTS

### Fichiers sensibles
- **NE PAS partager** `telegram_config.json` (contient votre token)
- **NE PAS commit** sur GitHub public

### Dépendances Python
```bash
# Si erreur "No module named 'requests'"
pip3 install -r requirements.txt
```

### Base de données
- Contient 2288 matchs historiques
- Se met à jour avec `update_weekly.sh`
- Ne pas supprimer `predictions.db`

### Whitelists
- 8 fichiers JSON (1 par ligue)
- Se régénèrent avec `update_weekly.sh`
- Consultables directement (format JSON lisible)

---

## 🆘 DÉPANNAGE RAPIDE

### "python3: command not found"
```bash
# Sur Windows
python --version
# Utiliser 'python' au lieu de 'python3'
```

### "pip3: command not found"
```bash
# Sur Windows
pip --version
# Utiliser 'pip' au lieu de 'pip3'
```

### "Unable to open database file"
```bash
# Vérifier que vous êtes dans le bon dossier
pwd
# Résultat attendu : .../paris-live-autonomous

# Si dans un sous-dossier, remonter
cd ..
```

### "Telegram 400 Bad Request"
```bash
# Vérifier telegram_config.json
cat telegram_config.json
# Les valeurs doivent être SANS guillemets supplémentaires
# ✅ "bot_token": "1234567:ABC..."
# ❌ "bot_token": ""1234567:ABC...""
```

### Whitelist non trouvée
```bash
# Vérifier que les whitelists existent
ls whitelists/
# Si vide, les regénérer
python3 generate_top_teams_whitelist.py --all
```

---

## ✅ CHECKLIST FINALE

Avant de commencer à utiliser le système :

- [ ] Package téléchargé et décompressé
- [ ] Python 3.8+ installé
- [ ] Dépendances installées (`pip3 install -r requirements.txt`)
- [ ] Telegram bot créé
- [ ] Chat ID récupéré
- [ ] `telegram_config.json` édité
- [ ] Test `monitor_live.py` réussi
- [ ] Message Telegram reçu
- [ ] Documentation lue (au moins README.md)

**Si tout est coché : 🎉 VOUS ÊTES OPÉRATIONNEL !**

---

## 📞 RESSOURCES

### Documentation
- README.md → Guide rapide
- GUIDE_AUTONOME_COMPLET.md → Guide détaillé
- PACKAGE_CONTENU.md → Contenu du package

### Scripts
- monitor_live.py → Monitoring manuel
- update_weekly.sh → Mise à jour hebdo
- scrape_all_leagues_auto.py → Scraping
- generate_top_teams_whitelist.py → Whitelists

### Données
- football-live-prediction/data/predictions.db → 2288 matchs
- whitelists/*.json → 131 patterns validés

---

**Version :** 2.0
**Date :** 2025-12-05
**Package testé et validé ✅**

🚀 **Bon monitoring !**
