#!/usr/bin/env python3
"""
Extract Live Match Data - Script Général
Extrait et affiche toutes les données du match (score, possession %, stats, etc.)
"""

import sys
import json
from soccerstats_live_scraper import SoccerStatsLiveScraper


def format_report(match_data):
    """Formate un rapport lisible des données du match"""
    if not match_data:
        return None

    data = match_data.to_dict() if hasattr(match_data, 'to_dict') else match_data

    report = f"""
╔════════════════════════════════════════════════════════════════╗
║                    📊 MATCH LIVE DATA REPORT                   ║
╚════════════════════════════════════════════════════════════════╝

🏟️  MATCH INFO
   Time      : {data.get('minute', 'N/A')} min
   Timestamp : {match_data.timestamp if hasattr(match_data, 'timestamp') else 'N/A'}

⚽ TEAMS & SCORE
   Home : {match_data.home_team if hasattr(match_data, 'home_team') else data.get('home_team')} {data.get('score_home', 'N/A')}
   Away : {match_data.away_team if hasattr(match_data, 'away_team') else data.get('away_team')} {data.get('score_away', 'N/A')}

📈 POSSESSION (%)
   Home : {data.get('possession_home', 'N/A')}%
   Away : {data.get('possession_away', 'N/A')}%

🎯 SHOTS
   Total Shots
      Home : {data.get('shots_home', 'N/A')}
      Away : {data.get('shots_away', 'N/A')}

   Shots on Target
      Home : {data.get('shots_on_target_home', 'N/A')}
      Away : {data.get('shots_on_target_away', 'N/A')}

🚀 ATTACKS
   Total Attacks
      Home : {data.get('attacks_home', 'N/A')}
      Away : {data.get('attacks_away', 'N/A')}

   Dangerous Attacks
      Home : {data.get('dangerous_attacks_home', 'N/A')}
      Away : {data.get('dangerous_attacks_away', 'N/A')}

🎪 OTHER STATS
   Corners
      Home : {data.get('corners_home', 'N/A')}
      Away : {data.get('corners_away', 'N/A')}

╔════════════════════════════════════════════════════════════════╗
║                        END OF REPORT                           ║
╚════════════════════════════════════════════════════════════════╝
"""
    return report


def extract_match(url: str, output_format: str = 'text', verbose: bool = True):
    """
    Extrait et affiche les données du match

    Args:
        url: URL du match SoccerStats
        output_format: 'text', 'json', ou 'dict'
        verbose: Afficher les logs d'extraction

    Returns:
        Match data (format spécifié)
    """

    if verbose:
        print(f"\n🔍 Extraction du match: {url}\n")

    scraper = SoccerStatsLiveScraper()
    match_data = scraper.scrape_match(url)

    if not match_data:
        print("❌ Impossible d'extraire les données du match.")
        return None

    if output_format == 'json':
        return json.dumps(match_data.to_dict(), indent=2, default=str)
    elif output_format == 'dict':
        return match_data.to_dict()
    else:  # text
        return format_report(match_data)


def main():
    """Lance l'extraction depuis la ligne de commande"""

    if len(sys.argv) < 2:
        print("""
Usage: python3 extract_match_data.py <URL> [--json] [--dict]

Examples:
  python3 extract_match_data.py "https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026"
  python3 extract_match_data.py "https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026" --json
  python3 extract_match_data.py "https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026" --dict
""")
        sys.exit(1)

    url = sys.argv[1]
    output_format = 'text'

    if len(sys.argv) > 2:
        if sys.argv[2] == '--json':
            output_format = 'json'
        elif sys.argv[2] == '--dict':
            output_format = 'dict'

    result = extract_match(url, output_format=output_format, verbose=True)

    if result:
        if output_format == 'text':
            print(result)
        else:
            print(result)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
