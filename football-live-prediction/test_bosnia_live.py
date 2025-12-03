#!/usr/bin/env python3
"""
Test rapide: Détecter les matchs live en Bosnie
"""

import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / 'scrapers'))
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from scrapers.live_match_detector import LiveMatchDetector

def test_bosnia():
    """Test de détection sur la Bosnie"""

    print("\n" + "="*80)
    print("🔍 TEST: Détection matchs live en Bosnie-Herzégovine")
    print("="*80 + "\n")

    detector = LiveMatchDetector()

    try:
        # Tester la Bosnie
        matches = detector.scrape(
            league_url="https://www.soccerstats.com/latest.asp?league=bosnia",
            league_name="Bosnia and Herzegovina"
        )

        if matches:
            print(f"✅ {len(matches)} match(es) live trouvé(s)!\n")

            for i, match in enumerate(matches, 1):
                print(f"Match #{i}:")
                print(f"  Titre:  {match['title']}")
                print(f"  Status: {match['status']}")
                print(f"  Score:  {match.get('score', 'N/A')}")
                print(f"  League: {match['league']}")
                print(f"  URL:    {match['url']}")
                print(f"  ID:     {match['id']}")
                print()

            print("="*80)
            print("✅ DÉTECTION RÉUSSIE!")
            print("="*80)

            return matches
        else:
            print("❌ Aucun match live trouvé")
            print("\nPossible raisons:")
            print("  1. Le match est terminé")
            print("  2. Le scraper n'a pas trouvé les éléments #87CEFA")
            print("  3. Le lien pmatch.asp n'est pas dans le <tr> parent")

            return []

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        detector.cleanup()


if __name__ == '__main__':
    matches = test_bosnia()

    if matches:
        print(f"\n🎯 Résultat: {len(matches)} match(es) détecté(s)")
    else:
        print("\n⚠️  Aucun match détecté - Vérifie que le match est encore en cours")
