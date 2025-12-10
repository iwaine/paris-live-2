#!/usr/bin/env python3
"""
Test LIVE: Détecte matchs en direct et calcule probabilités pour équipes en DB
Filtre par équipes existantes dans data/predictions.db
"""

import sys
from pathlib import Path
import sqlite3
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from soccerstats_live_selector import get_live_matches
from scrapers.soccerstats_live import SoccerStatsLiveScraper
from utils.database_manager import DatabaseManager
from predictors.live_goal_probability_predictor import LiveGoalProbabilityPredictor


def get_teams_in_database():
    """Récupère toutes les équipes uniques dans la base historique"""
    conn = sqlite3.connect("data/predictions.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT home_team FROM matches
        UNION
        SELECT DISTINCT away_team FROM matches
    """)
    teams = {row[0].strip().lower() for row in cursor.fetchall()}
    conn.close()
    return teams


def normalize_team_name(name):
    """Normalise un nom d'équipe pour comparaison"""
    return name.strip().lower()


def test_live_detection():
    """
    Lance la détection live et filtre par équipes existantes
    """
    
    print("\n" + "=" * 100)
    print("🔍 TEST LIVE: DÉTECTION MATCHS EN DIRECT + PROBABILITÉS")
    print("=" * 100)
    
    # Charger équipes de la DB
    db_teams = get_teams_in_database()
    print(f"\n📊 Équipes dans data/predictions.db: {len(db_teams)}")
    print(f"   {', '.join(sorted(list(db_teams)[:10]))}...")
    
    # Détecter matchs live
    print("\n🔄 Détection des matchs en live...")
    try:
        live_matches = get_live_matches(
            index_url="https://www.soccerstats.com",
            timeout=30,
            debug=False
        )
    except Exception as e:
        print(f"❌ Erreur détection: {e}")
        return
    
    if not live_matches:
        print("❌ Aucun match en direct trouvé")
        return
    
    print(f"✅ {len(live_matches)} matchs en direct détectés")
    
    # Scraper et analyser
    scraper = SoccerStatsLiveScraper()
    db = DatabaseManager(db_path="data/predictions.db")
    predictor = LiveGoalProbabilityPredictor(db_manager=db)
    
    matching_count = 0
    
    print("\n" + "-" * 100)
    print("📋 FILTRAGE ET PRÉDICTIONS")
    print("-" * 100)
    
    for match_data in live_matches:
        url = match_data.get("url")
        minute_str = match_data.get("minute", "?")
        
        # Scraper le match
        try:
            live_data = scraper.scrape_match(url)
            if not live_data:
                continue
        except Exception as e:
            continue
        
        # Vérifier si équipes sont en DB
        home = normalize_team_name(live_data.get("home_team", ""))
        away = normalize_team_name(live_data.get("away_team", ""))
        
        home_in_db = home in db_teams
        away_in_db = away in db_teams
        
        if not (home_in_db or away_in_db):
            continue  # Skip si aucune équipe en DB
        
        matching_count += 1
        
        # Afficher match
        print(f"\n✅ Match {matching_count}: {live_data.get('home_team')} vs {live_data.get('away_team')}")
        print(f"   URL: {url}")
        print(f"   Score: {live_data.get('score')} | Minute: {minute_str}")
        print(f"   Équipes en DB: Home={home_in_db}, Away={away_in_db}")
        
        # Extraire stats live
        possession_home = live_data.get("possession_home", 50)
        possession_away = 100 - possession_home
        attacks_home = live_data.get("attacks_home", 0)
        attacks_away = live_data.get("attacks_away", 0)
        dangerous_home = live_data.get("dangerous_attacks_home", 0)
        dangerous_away = live_data.get("dangerous_attacks_away", 0)
        shots_home = live_data.get("shots_on_target_home", 0)
        shots_away = live_data.get("shots_on_target_away", 0)
        
        score = live_data.get("score", "0-0")
        score_parts = score.split(":")
        try:
            score_home = int(score_parts[0].strip())
            score_away = int(score_parts[1].strip())
        except:
            score_home = score_away = 0
        
        current_minute = live_data.get("minute", 0)
        if isinstance(current_minute, str):
            try:
                current_minute = int(''.join(c for c in current_minute if c.isdigit()).split('+')[0])
            except:
                current_minute = 45
        
        # Prédiction
        try:
            result = predictor.predict_goal_probability(
                home_team=live_data.get("home_team"),
                away_team=live_data.get("away_team"),
                current_minute=current_minute,
                home_possession=possession_home,
                away_possession=possession_away,
                home_attacks=attacks_home,
                away_attacks=attacks_away,
                home_dangerous_attacks=dangerous_home,
                away_dangerous_attacks=dangerous_away,
                home_shots_on_target=shots_home,
                away_shots_on_target=shots_away,
                home_red_cards=live_data.get("red_cards_home", 0),
                away_red_cards=live_data.get("red_cards_away", 0),
                score_home=score_home,
                score_away=score_away,
                last_5_min_events={"buts": 0, "tirs": 0}
            )
            
            prob = result.get("goal_probability", 0)
            level = result.get("danger_level", "?")
            
            print(f"\n   📈 Prédiction de but:")
            print(f"      Probabilité: {prob:.1f}% [{level}]")
            print(f"      Possession: H={possession_home:.0f}% vs A={possession_away:.0f}%")
            print(f"      Attaques: H={attacks_home} vs A={attacks_away}")
            print(f"      Tirs cadrés: H={shots_home} vs A={shots_away}")
            
        except Exception as e:
            print(f"   ❌ Erreur prédiction: {e}")
    
    print("\n" + "=" * 100)
    print(f"📊 RÉSUMÉ: {matching_count} matchs avec équipes en DB trouvés et analysés")
    print("=" * 100 + "\n")
    
    if matching_count == 0:
        print("⚠️  Aucun match ne correspondait aux équipes de la base historique.")
        print("    Les équipes en DB: Premier League, La Liga, Ligue 1, Bundesliga, Serie A")
        print("    Attendez des matchs de ces ligues en direct sur SoccerStats.")
    
    return matching_count > 0


if __name__ == "__main__":
    try:
        success = test_live_detection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
