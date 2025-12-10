================================================================================
🎯 FONCTIONNEMENT COMPLET DU SYSTÈME - ÉTAPE PAR ÉTAPE
================================================================================

📊 OBJECTIF GLOBAL
------------------
Détecter les matchs en live qui ont une forte probabilité de but dans les 
intervalles clés (31-45' et 76-90') et envoyer des alertes Telegram.


================================================================================
ÉTAPE 1 : COLLECTE DES DONNÉES HISTORIQUES (SCRAPING)
================================================================================

📁 Fichier principal : scrape_all_leagues_auto.py
📁 Fichier secondaire : soccerstats_live_scraper.py

🎯 Ce qui se passe :
-------------------
1. Se connecte à SoccerStats.com
2. Récupère l'historique des matchs pour chaque équipe
3. Pour chaque match, extrait :
   - Date
   - Équipe domicile/extérieur
   - Adversaire
   - Ligue
   - goal_times : [6, 41, 55, 75, 90, 0, 0, 0, 0, 0] (buts MARQUÉS)
   - goal_times_conceded : [12, 34, 67, 0, 0, 0, 0, 0, 0, 0] (buts ENCAISSÉS)

📂 Stockage : 
   → Base de données SQLite : data/predictions.db
   → Table : soccerstats_scraped_matches

💡 Exemple de données :
   RKC Waalwijk vs VVV (9 Nov 2024)
   - goal_times: [90]           (RKC marque à la 90')
   - goal_times_conceded: [34, 44, 90]  (RKC encaisse à 34', 44', 90')

🔧 Commande pour lancer :
   python3 scrape_all_leagues_auto.py --league netherlands --workers 2


================================================================================
ÉTAPE 2 : CALCUL DES PATTERNS HISTORIQUES (STATISTIQUES)
================================================================================

📁 Fichier : build_team_recurrence_stats.py

🎯 Ce qui se passe :
-------------------
1. Lit TOUS les matchs de la table soccerstats_scraped_matches
2. Pour CHAQUE équipe (RKC, VVV, Monaco, etc.)
3. Pour CHAQUE contexte (HOME/AWAY)
4. Pour CHAQUE période (1ère MT / 2ème MT)

5. Combine les buts marqués ET encaissés
6. Calcule les statistiques :
   - avg_minute : Minute moyenne des buts
   - std_minute : Écart-type
   - sem_minute : Erreur standard (précision)
   - iqr_q1, iqr_q3 : Zone IQR (50% des buts)
   - goal_count : Nombre total de buts
   - total_matches : Nombre de matchs analysés

📂 Stockage :
   → Base de données SQLite : data/predictions.db
   → Table : team_goal_recurrence

💡 Exemple de résultat :
   RKC Waalwijk HOME - 2ème MT :
   - avg_minute: 75.9'
   - sem_minute: ±3.6'
   - iqr_q1: 70', iqr_q3: 89'
   - goal_count: 16 (buts marqués + encaissés)
   - total_matches: 7

⚠️ IMPORTANT : Cette table contient TOUS les buts de chaque mi-temps
   (1-45' pour 1MT, 46-90+' pour 2MT)
   PAS seulement les intervalles 31-45 et 76-90 !

🔧 Commande pour lancer :
   python3 build_team_recurrence_stats.py


================================================================================
ÉTAPE 3 : PRÉDICTION EN TEMPS RÉEL (LIVE)
================================================================================

📁 Fichier : predictors/live_goal_probability_predictor.py

🎯 Ce qui se passe :
-------------------
Quand un match est en cours (ex: minute 78, RKC vs VVV) :

1️⃣ Déterminer l'intervalle
   → Fonction : _get_interval_name()
   Minute 78 → Intervalle "76-90"
   Minute 35 → Intervalle "31-45"
   Minute 10 → "outside_key_intervals"

2️⃣ Calculer la probabilité historique (BASE RATE)
   → Fonction : _calculate_base_rate()
   
   A. Récupérer patterns RKC HOME pour intervalle 76-90
      → Fonction : _get_team_recurrence()
      → Lit soccerstats_scraped_matches
      → Compte matchs avec AU MOINS 1 but entre 76-90'
      → Résultat : 6/9 matchs = 66.7%
   
   B. Récupérer patterns VVV AWAY pour intervalle 76-90
      → Même processus
      → Résultat : 4/8 matchs = 50.0%
   
   C. Appliquer FORMULA MAX
      → base_rate = max(66.7%, 50.0%) = 66.7%

3️⃣ Ajuster avec les stats LIVE
   → Fonction : _calculate_live_adjustment()
   → Analyse :
      - Possession (62% vs 38%)
      - Tirs cadrés (6 vs 3)
      - Attaques (85 vs 55)
      - Momentum
   → Ajustement : +4.1%

4️⃣ Calculer probabilité finale
   → base_rate (66.7%) + live_adjustment (4.1%) × poids (20%)
   → Mais ajusté selon zone IQR (si mal alignée → réduction)
   → Probabilité finale : 42.1%

💡 Pourquoi 42% et pas 66.7% ?
   Le système détecte que les zones IQR ne sont pas optimales :
   - RKC : Zone [70-89'] → Pic à 75.9' (juste avant 76')
   - VVV : Zone [58-76'] → Pic à 66.3' (hors intervalle)
   → Ajustement à la baisse pour éviter les faux positifs

🔧 Utilisation dans le code :
   predictor = LiveGoalProbabilityPredictor()
   result = predictor.predict_goal_probability(
       home_team="RKC Waalwijk",
       away_team="VVV",
       league="Netherlands - Eerste Divisie",
       current_minute=78,
       home_possession=62,
       ...
   )


================================================================================
ÉTAPE 4 : DÉCISION DE SIGNAL
================================================================================

🎯 Critères pour envoyer un signal :
-------------------------------------
1. ✅ Intervalle clé : "31-45" OU "76-90"
2. ✅ Probabilité ≥ 65%
3. ❌ Si hors intervalle clé → 5% (pas de signal)

💡 Pour RKC vs VVV à 78' :
   - Intervalle : "76-90" ✅
   - Probabilité : 42.1% ❌ < 65%
   → PAS DE SIGNAL


================================================================================
ÉTAPE 5 : FORMATAGE ET ENVOI TELEGRAM
================================================================================

📁 Fichier : telegram_formatter_enriched.py

🎯 Si signal validé (probabilité ≥ 65%) :
------------------------------------------
1. Récupère tous les détails du match
2. Formate le message avec :
   - 🚨 Score et minute
   - 📊 Probabilité finale
   - 🏠 Patterns équipe domicile (timing, SEM, IQR)
   - ✈️ Patterns équipe extérieur
   - 📈 Stats live
   - 💡 Analyse momentum

3. Envoie via Telegram Bot

🔧 Utilisation :
   message = format_telegram_alert_enriched(
       match_data, 
       pred_home, 
       pred_away, 
       probability
   )


================================================================================
ÉTAPE 6 : MONITORING CONTINU
================================================================================

📁 Fichier : live_monitor_with_historical_patterns.py

🎯 Ce qui se passe :
-------------------
1. Boucle infinie
2. Toutes les 60 secondes :
   - Récupère matchs en cours
   - Pour chaque match entre minute 31-47 ou 76-95
   - Calcule probabilité
   - Si ≥ 65% → Envoie signal Telegram
   - Stocke dans cache pour éviter doublons

🔧 Commande pour lancer :
   python3 live_monitor_with_historical_patterns.py


================================================================================
📋 RÉSUMÉ DU FLUX COMPLET
================================================================================

1. SCRAPING → soccerstats_scraped_matches (goal_times + goal_times_conceded)
   ↓
2. STATISTIQUES → team_goal_recurrence (patterns par équipe/contexte/période)
   ↓
3. LIVE → Calcul probabilité (base_rate + live_adjustment)
   ↓
4. DÉCISION → Si intervalle clé ET probabilité ≥ 65%
   ↓
5. TELEGRAM → Envoi alerte formatée


================================================================================
🔍 FICHIERS PRINCIPAUX PAR FONCTION
================================================================================

COLLECTE :
  ✓ scrape_all_leagues_auto.py

CALCUL PATTERNS :
  ✓ build_team_recurrence_stats.py

PRÉDICTION :
  ✓ predictors/live_goal_probability_predictor.py

FORMATAGE :
  ✓ telegram_formatter_enriched.py

MONITORING :
  ✓ live_monitor_with_historical_patterns.py

ANALYSE/DEBUG :
  ✓ analyze_intervals_only.py (vérifie patterns sur intervalles précis)
  ✓ test_pipeline_complet_simulation.py (teste tout le système)


================================================================================
💡 POINTS CLÉS À RETENIR
================================================================================

1. Les buts MARQUÉS + ENCAISSÉS sont TOUJOURS comptés ensemble
2. La Formula MAX prend le MEILLEUR pattern des deux équipes
3. Les intervalles sont 31-45' et 76-90' (PAS 31-50 et 76-120)
4. Le seuil de signal est 65% (configurable)
5. Le système ajuste à la baisse si zones IQR mal alignées
6. Hors intervalles clés → 5% (aucun signal)

================================================================================
