# GUIDE PRATIQUE - WORKFLOW LIVE AUSTRALIA A-LEAGUE

Ce guide liste les fichiers et scripts à utiliser pour automatiser la détection, l'analyse et l'alerte Telegram sur un match live Australia A-League.

---

## 1. Scraping des données live
- **Fichier :** `soccerstats_live_scraper.py`
- **Classe principale :** `SoccerStatsLiveScraper`guide 
- **Fonction rapide :** `scrape_live_match(url)`
- **Usage :**
    - Extrait toutes les stats live d'un match SoccerStats (minute, score, possession, tirs, corners, attaques, etc.)
    - Format de sortie : objet `LiveMatchData` (méthode `.to_dict()` pour conversion)

## 2. Analyse des patterns historiques
- **Fichier :** `analyze_all_leagues_patterns.py`
- **Usage :**
    - Scrape et analyse les patterns de buts par intervalle pour chaque équipe et chaque ligue
    - Remplit la base SQLite avec les stats avancées (moyenne, SEM, IQR, récurrence, etc.)

## 3. Prédiction live
- **Fichier :** `football-live-prediction/predictors/live_goal_probability_predictor.py`
- **Classe principale :** `LiveGoalProbabilityPredictor`
- **Usage :**
    - Combine stats live et historiques pour calculer la probabilité de but sur l'intervalle actif (31-45+ ou 76-90+)
    - Retourne toutes les valeurs nécessaires pour le formatteur Telegram

## 4. Formatage du message Telegram
- **Fichier :** `telegram_formatter_enriched.py`
- **Fonction principale :** `format_telegram_alert_enriched(match_data, prediction_home, prediction_away, combined_prob)`
- **Usage :**
    - Génère le message Telegram enrichi avec toutes les stats avancées (SEM, IQR, timing, patterns, saturation, recommandation)

## 5. Simulation et test
- **Fichier :** `test_telegram_intervals.py` ou `simulate_telegram_live_australia.py`
- **Usage :**
    - Permet de simuler le message Telegram pour différents intervalles et scénarios
    - À utiliser pour valider le format et la logique avant le test réel

## 6. Test sur un vrai match live
- **Script à lancer :**
    - Utiliser `soccerstats_live_scraper.py` pour extraire les données live du match réel
    - Passer ces données dans le pipeline de prédiction et le formatteur Telegram
    - Vérifier le message généré

---

## Exemple de workflow pour un match live

1. **Scraper le match live**
   ```python
   from soccerstats_live_scraper import scrape_live_match
   url = "https://www.soccerstats.com/pmatch.asp?league=australia&stats=41-11-2-2026"
   live_data = scrape_live_match(url)
   match_dict = live_data.to_dict()
   ```

2. **Calculer la prédiction**
   ```python
   from football_live_prediction.predictors.live_goal_probability_predictor import LiveGoalProbabilityPredictor
   predictor = LiveGoalProbabilityPredictor()
   prediction = predictor.predict_goal_probability(
       home_team=match_dict['home_team'],
       away_team=match_dict['away_team'],
       current_minute=match_dict['minute'],
       home_possession=match_dict['possession_home'],
       away_possession=match_dict['possession_away'],
       home_attacks=match_dict['attacks_home'],
       away_attacks=match_dict['attacks_away'],
       home_dangerous_attacks=match_dict['dangerous_attacks_home'],
       away_dangerous_attacks=match_dict['dangerous_attacks_away'],
       home_shots_on_target=match_dict['shots_on_target_home'],
       away_shots_on_target=match_dict['shots_on_target_away'],
       score_home=match_dict['score_home'],
       score_away=match_dict['score_away'],
       league="australia"
   )
   # Répéter pour home et away si besoin
   ```

3. **Générer le message Telegram**
   ```python
   from telegram_formatter_enriched import format_telegram_alert_enriched
   message = format_telegram_alert_enriched(match_dict, prediction_home, prediction_away, combined_prob)
   print(message)
   ```

---

**Fichiers à utiliser :**
- soccerstats_live_scraper.py
- analyze_all_leagues_patterns.py
- football-live-prediction/predictors/live_goal_probability_predictor.py
- telegram_formatter_enriched.py
- test_telegram_intervals.py (simulation)
- simulate_telegram_live_australia.py (simulation)

**Méthodologie validée :**
- Extraction → Prédiction → Formatage → Simulation → Test réel

---


**Prochaine étape :**
- Tester sur un vrai match live Australia A-League avec l’URL SoccerStats.

---


## Note sur le filtrage des ligues suivies

**Première étape du workflow :**
Le filtrage strict par la variable `LEAGUES_TO_FOLLOW` dans `soccerstats_live_selector.py` est la première étape pour détecter uniquement les matchs live des ligues que l’on suit.

Depuis décembre 2025, le script applique ce filtrage strict : seuls les matchs live des ligues explicitement listées dans la variable `LEAGUES_TO_FOLLOW` sont détectés et affichés.

**Exemple de configuration :**
```python
LEAGUES_TO_FOLLOW = [
    "australia",
    "bolivia",
    "bulgaria",
    "england",
    "france",
    "germany",
    "germany2",
    "netherlands2",
    "portugal"
]
```
Ce filtrage évite toute détection de ligues non désirées (ex : "germany7", "portugal2", etc.).
