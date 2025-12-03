#!/usr/bin/env python3
"""
Test Phase 3: Détection de Matchs Live
Teste uniquement la détection et l'extraction de données (sans prédictions, sans Telegram, sans BD)
"""

import sys
import yaml
from pathlib import Path

# Ajouter le répertoire au path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'scrapers'))

from scrapers.live_match_detector import LiveMatchDetector
from soccerstats_live_scraper import SoccerStatsLiveScraper


def load_leagues(config_path='config.yaml'):
    """Charge la liste des ligues depuis config.yaml"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('leagues', [])
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        return []


def test_detection_all_leagues():
    """Test 1: Détection sur TOUTES les ligues"""
    print("\n" + "="*80)
    print("🧪 TEST 1: DÉTECTION SUR TOUTES LES LIGUES (44)")
    print("="*80)

    detector = LiveMatchDetector()
    leagues = load_leagues()

    print(f"\n📊 {len(leagues)} ligues à scanner\n")

    all_matches = []

    for i, league in enumerate(leagues, 1):
        league_name = league.get('name', 'Unknown')
        league_url = league.get('url')

        if not league_url:
            continue

        print(f"[{i:2d}/{len(leagues)}] {league_name:45s} ", end='', flush=True)

        try:
            matches = detector.scrape(league_url, league_name)

            if matches:
                print(f"✅ {len(matches)} match(es) live")
                all_matches.extend(matches)
            else:
                print("⚪ Aucun match live")

        except Exception as e:
            print(f"❌ Erreur: {e}")

    detector.cleanup()

    print("\n" + "="*80)
    print(f"🎯 RÉSULTAT: {len(all_matches)} match(es) live trouvé(s) au total")
    print("="*80)

    return all_matches


def test_extraction_complete(matches):
    """Test 2: Extraction complète des données pour chaque match"""
    if not matches:
        print("\n⚠️  Aucun match à extraire (aucun match live détecté)")
        return

    print("\n" + "="*80)
    print(f"🧪 TEST 2: EXTRACTION COMPLÈTE DES DONNÉES ({len(matches)} matchs)")
    print("="*80)

    scraper = SoccerStatsLiveScraper()

    for i, match in enumerate(matches, 1):
        print(f"\n[{i}/{len(matches)}] {'='*70}")
        print(f"🏟️  Ligue: {match['league']}")
        print(f"📍 Status: {match['status']}")
        print(f"🔗 URL: {match['url']}")
        print("-"*70)

        try:
            match_data = scraper.scrape_match(match['url'])

            if match_data:
                print(f"\n✅ DONNÉES EXTRAITES:")
                print(f"   Équipes : {match_data.home_team} vs {match_data.away_team}")
                print(f"   Score   : {match_data.score_home}-{match_data.score_away}")
                print(f"   Minute  : {match_data.minute}'")
                print(f"   Time    : {match_data.timestamp}")

                print(f"\n📊 STATISTIQUES:")
                if match_data.possession_home is not None:
                    print(f"   Possession       : {match_data.possession_home}% - {match_data.possession_away}%")
                if match_data.shots_home is not None:
                    print(f"   Tirs totaux      : {match_data.shots_home} - {match_data.shots_away}")
                if match_data.shots_on_target_home is not None:
                    print(f"   Tirs cadrés      : {match_data.shots_on_target_home} - {match_data.shots_on_target_away}")
                if match_data.attacks_home is not None:
                    print(f"   Attaques         : {match_data.attacks_home} - {match_data.attacks_away}")
                if match_data.dangerous_attacks_home is not None:
                    print(f"   Attaques danger. : {match_data.dangerous_attacks_home} - {match_data.dangerous_attacks_away}")
                if match_data.corners_home is not None:
                    print(f"   Corners          : {match_data.corners_home} - {match_data.corners_away}")

                print(f"\n✅ EXTRACTION RÉUSSIE")
            else:
                print(f"\n❌ Échec de l'extraction")

        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

    scraper.session.close()

    print("\n" + "="*80)
    print("✅ TEST D'EXTRACTION TERMINÉ")
    print("="*80)


def test_single_league(league_name='Bulgaria'):
    """Test 3: Test rapide sur une seule ligue"""
    print("\n" + "="*80)
    print(f"🧪 TEST 3: DÉTECTION RAPIDE SUR UNE LIGUE ({league_name})")
    print("="*80)

    detector = LiveMatchDetector()
    leagues = load_leagues()

    # Trouver la ligue
    target_league = None
    for league in leagues:
        if league_name.lower() in league.get('name', '').lower():
            target_league = league
            break

    if not target_league:
        print(f"❌ Ligue '{league_name}' non trouvée dans config.yaml")
        detector.cleanup()
        return []

    print(f"\n📍 Ligue: {target_league['name']}")
    print(f"🔗 URL: {target_league['url']}\n")

    try:
        matches = detector.scrape(target_league['url'], target_league['name'])

        if matches:
            print(f"✅ {len(matches)} match(es) live trouvé(s):\n")
            for i, match in enumerate(matches, 1):
                print(f"{i}. Status: {match['status']}")
                print(f"   URL: {match['url']}\n")
        else:
            print("⚪ Aucun match live trouvé")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        matches = []

    detector.cleanup()

    print("="*80)

    return matches


def main():
    """Point d'entrée principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Test Phase 3: Détection de matchs live')
    parser.add_argument('--mode', choices=['all', 'single', 'quick'], default='quick',
                       help='Mode de test: all (toutes ligues), single (une ligue), quick (test rapide)')
    parser.add_argument('--league', default='Bulgaria',
                       help='Nom de la ligue pour mode single (défaut: Bulgaria)')
    parser.add_argument('--extract', action='store_true',
                       help='Extraire les données complètes (plus lent)')

    args = parser.parse_args()

    print("\n" + "="*80)
    print("🏟️  TEST PHASE 3: SYSTÈME DE DÉTECTION DE MATCHS LIVE")
    print("="*80)
    print(f"Mode: {args.mode}")
    print("="*80)

    matches = []

    if args.mode == 'all':
        # Test complet: toutes les ligues
        matches = test_detection_all_leagues()

    elif args.mode == 'single':
        # Test sur une seule ligue
        matches = test_single_league(args.league)

    elif args.mode == 'quick':
        # Test rapide: Bosnia et Bulgaria
        print("\n🚀 Mode rapide: Test sur 2 ligues (Bosnia + Bulgaria)")
        print("="*80)

        bosnia_matches = test_single_league('Bosnia')
        bulgaria_matches = test_single_league('Bulgaria')

        matches = bosnia_matches + bulgaria_matches

    # Extraction complète si demandé
    if args.extract and matches:
        test_extraction_complete(matches)

    # Résumé final
    print("\n" + "="*80)
    print("📊 RÉSUMÉ FINAL")
    print("="*80)
    print(f"Matchs live détectés : {len(matches)}")

    if matches:
        print("\nDétails des matchs:")
        for i, match in enumerate(matches, 1):
            print(f"{i}. {match['league']:40s} | Status: {match['status']:10s}")

    if args.extract:
        print("\n✅ Extraction complète effectuée")
    else:
        print("\n💡 Pour extraire les données complètes, ajoutez --extract")
        print("   Exemple: python3 test_live_detection.py --mode quick --extract")

    print("\n" + "="*80)

    if matches:
        print("✅ PHASE 3 OPÉRATIONNELLE")
    else:
        print("⚪ Aucun match live actuellement (normal si pas d'heure de match)")

    print("="*80 + "\n")


if __name__ == "__main__":
    main()
