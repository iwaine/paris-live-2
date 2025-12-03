#!/usr/bin/env python3
"""
Auto Live Monitor - Scanner Automatique Multi-Ligues
Scanne 40+ ligues pour détecter automatiquement les matchs live/HT
"""

import sys
import os
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / 'football-live-prediction'))
sys.path.insert(0, str(Path(__file__).parent / 'football-live-prediction' / 'scrapers'))
sys.path.insert(0, str(Path(__file__).parent / 'football-live-prediction' / 'predictors'))
sys.path.insert(0, str(Path(__file__).parent / 'football-live-prediction' / 'utils'))

from continuous_live_monitor import ContinuousLiveMonitor
from scrapers.live_match_detector import LiveMatchDetector
from utils.config_loader import get_config
from utils.logger import get_logger

logger = get_logger()


def get_all_leagues():
    """Récupère toutes les ligues depuis la config"""
    try:
        config = get_config()
        leagues = config.get('leagues', [])

        league_list = []
        for league in leagues:
            if not league.get('enabled', True):
                continue

            url = league.get('url', '')
            if not url or 'latest.asp' not in url:
                continue

            league_list.append({
                'name': league.get('name', 'Unknown'),
                'url': url,
                'priority': league.get('priority', 50)
            })

        # Trier par priorité (haute priorité d'abord)
        league_list.sort(key=lambda x: x['priority'], reverse=True)

        return league_list
    except Exception as e:
        logger.error(f"Error loading leagues: {e}")
        return []


def scan_all_leagues():
    """Scanne toutes les ligues pour trouver les matchs live"""
    print("\n" + "="*80)
    print("🤖 AUTO LIVE MONITOR - DÉTECTION AUTOMATIQUE")
    print("="*80)

    leagues = get_all_leagues()
    print(f"\n📋 Ligues configurées: {len(leagues)}")

    if not leagues:
        print("❌ Aucune ligue trouvée dans la config!")
        return []

    print("\n" + "="*80)
    print("🔍 SCANNING POUR MATCHS LIVE/HT...")
    print("="*80)

    detector = LiveMatchDetector()
    all_live_matches = []

    for i, league in enumerate(leagues, 1):
        # Afficher la progression
        print(f"\n[{i:2d}/{len(leagues)}] {league['name']:<40}", end=" ", flush=True)

        try:
            # Détecter les matchs live
            live_matches = detector.scrape(
                league_url=league['url'],
                league_name=league['name']
            )

            if live_matches:
                print(f"✅ {len(live_matches)} match(es) live")
                all_live_matches.extend(live_matches)

                # Afficher les détails
                for match in live_matches:
                    print(f"     └─ {match['title']:<35} [{match['status']}]")
            else:
                print("⏭️  Aucun match live")

        except Exception as e:
            print(f"⚠️  Erreur: {str(e)[:40]}")
            logger.error(f"Error scanning {league['name']}: {e}")

    detector.cleanup()

    return all_live_matches


def main():
    """Main function"""
    try:
        # Scanner toutes les ligues
        live_matches = scan_all_leagues()

        if not live_matches:
            print("\n" + "="*80)
            print("❌ AUCUN MATCH LIVE TROUVÉ")
            print("="*80)
            print("\nAucun match en cours ou à la mi-temps.")
            print("Réessayez plus tard ou vérifiez la configuration.\n")
            return

        # Afficher le résumé
        print("\n" + "="*80)
        print(f"✅ TOTAL: {len(live_matches)} MATCH(ES) LIVE DÉTECTÉ(S)")
        print("="*80)

        print("\n📊 Détails des matchs:")
        print("-"*80)
        for i, match in enumerate(live_matches, 1):
            status_icon = "⚽" if "min" in match['status'].lower() else "🟡" if "HT" in match['status'] else "🔴"
            print(f"{i:2d}. {status_icon} {match['title']:<40} {match['status']:>10}")
            print(f"    League: {match['league']}")
            if match.get('score'):
                print(f"    Score:  {match['score']}")
            print()
        print("-"*80)

        # Demander confirmation
        print("\n🚀 Voulez-vous lancer le monitoring automatique?")
        print("   • Les prédictions seront faites toutes les 30 secondes")
        print("   • Alertes quand danger ≥65%")
        print()

        response = input("Lancer le monitoring? [O/n]: ").strip().lower()

        if response and response not in ['o', 'y', 'yes', 'oui']:
            print("\n✋ Monitoring annulé")
            return

        # Lancer le monitoring
        print("\n" + "="*80)
        print("🔴 MONITORING EN DIRECT LANCÉ")
        print("="*80)

        monitor = ContinuousLiveMonitor()

        # Ajouter tous les matchs
        added_count = 0
        for match in live_matches:
            try:
                monitor.add_match(
                    match_url=match['url'],
                    match_id=match['id']
                )
                print(f"   ✅ {match['id']}")
                added_count += 1
            except Exception as e:
                print(f"   ⚠️  {match['id']}: {str(e)[:50]}")
                logger.error(f"Error adding match {match['id']}: {e}")

        if added_count == 0:
            print("\n❌ Aucun match ajouté au monitoring!")
            return

        print(f"\n✅ {added_count} match(es) ajouté(s) au monitoring")
        print("\nRègles:")
        print("  • Danger ≥65%: 🎯 SIGNAL FORT")
        print("  • Danger ≥50%: ⚠️  À surveiller")
        print("  • Ctrl+C pour arrêter")
        print("\n" + "="*80 + "\n")

        # Démarrer le monitoring continu
        monitor.monitor_all_matches(interval_seconds=30)

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("✅ MONITORING ARRÊTÉ PAR L'UTILISATEUR")
        print("="*80 + "\n")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        logger.error(f"Critical error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
