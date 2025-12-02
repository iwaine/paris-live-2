"""
Setup Profiles - Génération des profils d'équipes

Ce script :
1. Scrape les stats historiques pour les équipes configurées
2. Analyse les patterns
3. Génère et sauvegarde les profils
4. Exporte en JSON et Excel
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from typing import List, Dict  # ✅ AJOUT

sys.path.append(str(Path(__file__).parent))

from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
from analyzers.pattern_analyzer import PatternAnalyzer
from utils.config_loader import get_config
from utils.logger import setup_logger, get_logger


def setup_profiles_for_league(
    league_code: str,
    league_name: str,
    scraper: SoccerStatsHistoricalScraper,
    analyzer: PatternAnalyzer
) -> List[Dict]:
    """
    Génère les profils pour toutes les équipes d'une ligue
    
    Args:
        league_code: Code de la ligue
        league_name: Nom de la ligue
        scraper: Instance du scraper
        analyzer: Instance de l'analyseur
    
    Returns:
        Liste des profils générés
    """
    logger = get_logger()
    logger.info(f"Setting up profiles for {league_name}")
    
    profiles = []
    
    try:
        # Scraper les stats de timing pour la ligue
        timing_df = scraper.scrape_timing_stats(league_code)
        
        if timing_df is None or timing_df.empty:
            logger.warning(f"No data for {league_name}")
            return profiles
        
        # Extraire les noms d'équipes (première colonne)
        team_col = timing_df.columns[0]
        teams = timing_df[team_col].unique()
        
        logger.info(f"Found {len(teams)} teams in {league_name}")
        
        # Pour chaque équipe
        for i, team_name in enumerate(teams, 1):
            logger.info(f"[{i}/{len(teams)}] Processing {team_name}...")
            
            try:
                # Scraper les stats de l'équipe
                team_stats = scraper.scrape_team_stats(team_name, league_code)
                
                if team_stats is None:
                    logger.warning(f"No stats for {team_name}")
                    continue
                
                # Analyser le profil
                analysis = analyzer.analyze_team_profile(team_stats)
                
                # Sauvegarder
                analyzer.save_team_profile(analysis)
                
                profiles.append(analysis)
                logger.success(f"✅ Profile created for {team_name}")
                
            except Exception as e:
                logger.error(f"Error processing {team_name}: {e}")
                continue
        
        logger.success(f"Completed {league_name}: {len(profiles)} profiles")
        
    except Exception as e:
        logger.error(f"Error setting up {league_name}: {e}")
    
    return profiles


def export_profiles_to_excel(profiles: List[Dict], output_file: str):
    """
    Exporte les profils en Excel
    
    Args:
        profiles: Liste des profils
        output_file: Fichier de sortie
    """
    logger = get_logger()
    
    if not profiles:
        logger.warning("No profiles to export")
        return
    
    # Préparer les données pour Excel
    summary_data = []
    
    for profile in profiles:
        summary_data.append({
            "Team": profile["team"],
            "League": profile["league"],
            "Total Goals (Home)": profile["home"]["total_scored"],
            "Total Conceded (Home)": profile["home"]["total_conceded"],
            "Goal Diff (Home)": profile["home"]["goal_difference"],
            "Total Goals (Away)": profile["away"]["total_scored"],
            "Total Conceded (Away)": profile["away"]["total_conceded"],
            "Goal Diff (Away)": profile["away"]["goal_difference"],
            "Play Style": profile["play_style"]["summary"],
            "Danger Zones": len(profile["danger_zones"])
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # Sauvegarder avec plusieurs feuilles
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Feuille 1: Résumé
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Feuille 2: Zones de danger
        danger_data = []
        for profile in profiles:
            for zone in profile["danger_zones"]:
                danger_data.append({
                    "Team": profile["team"],
                    "Interval": zone["interval"],
                    "Goal Rate": zone["goal_rate"],
                    "Intensity": zone["intensity"]
                })
        
        if danger_data:
            df_danger = pd.DataFrame(danger_data)
            df_danger.to_excel(writer, sheet_name='Danger Zones', index=False)
    
    logger.success(f"Profiles exported to {output_file}")


def main():
    """Point d'entrée principal"""
    # Setup logger
    log = setup_logger(level="INFO")
    logger = get_logger()
    
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*12 + "GÉNÉRATION DES PROFILS D'ÉQUIPES" + " "*13 + "║")
    print("╚" + "="*58 + "╝\n")
    
    # Charger la config
    config = get_config()
    
    # Créer les instances
    scraper = SoccerStatsHistoricalScraper()
    analyzer = PatternAnalyzer()
    
    # Demander à l'utilisateur
    print("Options:")
    print("1. Générer profils pour équipes de test")
    print("2. Générer profils pour une ligue complète")
    print("3. Générer profils pour toutes les ligues")
    
    choice = input("\nVotre choix (1-3): ").strip()
    
    all_profiles = []
    
    if choice == "1":
        # Équipes de test
        print("\n📋 Équipes de test configurées:")
        test_teams = config.get_test_teams()
        
        for team in test_teams:
            print(f"   - {team['name']} ({team['league_code']})")
        
        print(f"\n🔄 Génération de {len(test_teams)} profils...")
        
        for team in test_teams:
            try:
                logger.info(f"Processing {team['name']}...")
                
                team_stats = scraper.scrape_team_stats(
                    team['name'],
                    team['league_code']
                )
                
                if team_stats:
                    analysis = analyzer.analyze_team_profile(team_stats)
                    analyzer.save_team_profile(analysis)
                    all_profiles.append(analysis)
                    print(f"   ✅ {team['name']}")
                else:
                    print(f"   ❌ {team['name']} - No data")
                    
            except Exception as e:
                print(f"   ❌ {team['name']} - Error: {e}")
    
    elif choice == "2":
        # Une seule ligue
        enabled_leagues = config.get_enabled_leagues()
        
        print("\n📋 Ligues disponibles:")
        for i, league in enumerate(enabled_leagues, 1):
            print(f"   {i}. {league['name']}")
        
        league_choice = input(f"\nChoisir ligue (1-{len(enabled_leagues)}): ").strip()
        
        try:
            league_idx = int(league_choice) - 1
            selected_league = enabled_leagues[league_idx]
            
            print(f"\n🔄 Génération des profils pour {selected_league['name']}...")
            
            all_profiles = setup_profiles_for_league(
                selected_league['code'],
                selected_league['name'],
                scraper,
                analyzer
            )
            
        except (ValueError, IndexError):
            print("❌ Choix invalide")
            return 1
    
    elif choice == "3":
        # Toutes les ligues
        enabled_leagues = config.get_enabled_leagues()
        
        print(f"\n🔄 Génération des profils pour {len(enabled_leagues)} ligues...")
        print("⏳ Cela peut prendre plusieurs minutes...\n")
        
        for league in enabled_leagues:
            profiles = setup_profiles_for_league(
                league['code'],
                league['name'],
                scraper,
                analyzer
            )
            all_profiles.extend(profiles)
    
    else:
        print("❌ Choix invalide")
        return 1
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    print(f"Total profils générés: {len(all_profiles)}")
    
    if all_profiles:
        # Exporter en Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = f"team_profiles_{timestamp}.xlsx"
        
        print(f"\n📤 Export en cours vers {excel_file}...")
        export_profiles_to_excel(all_profiles, excel_file)
        
        print(f"\n✅ Fichier Excel créé: {excel_file}")
        print(f"📁 Profils JSON dans: {config.get_data_directory('team_profiles')}")
    
    # Cleanup
    scraper.cleanup()
    
    print("\n🎉 GÉNÉRATION TERMINÉE!")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
