"""
Script amélioré : extraction brute des matches FT et scores depuis la page principale SoccerStats
Cherche toutes les occurrences de 'FT' dans le texte et tente d'extraire le score et les équipes
"""

import re
import requests
from bs4 import BeautifulSoup

URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (FT Extract)"}

def get_ft_matches_mainpage_brut():
    r = requests.get(URL, headers=UA, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    txt = soup.get_text("\n", strip=True)
    results = []
    # Cherche toutes les lignes contenant FT
    for line in txt.splitlines():
        if "FT" in line:
            # Extraction du score et des équipes
            m = re.search(r"FT\s*([A-Za-z .']+)\s+(\d+)[:](\d+)\s+([A-Za-z .']+)", line)
            if m:
                home_team = m.group(1).strip()
                score_home = m.group(2)
                score_away = m.group(3)
                away_team = m.group(4).strip()
                results.append({
                    "status": "FT",
                    "home_team": home_team,
                    "score_home": score_home,
                    "score_away": score_away,
                    "away_team": away_team
                })
            else:
                # Format alternatif : FT Bristol City 2:2 Leicester City
                m2 = re.search(r"FT\s*([A-Za-z .']+)\s+(\d+)[:](\d+)\s+([A-Za-z .']+)", line)
                if m2:
                    home_team = m2.group(1).strip()
                    score_home = m2.group(2)
                    score_away = m2.group(3)
                    away_team = m2.group(4).strip()
                    results.append({
                        "status": "FT",
                        "home_team": home_team,
                        "score_home": score_home,
                        "score_away": score_away,
                        "away_team": away_team
                    })
                else:
                    # Affiche la ligne brute si non parsée
                    results.append({"status": "FT", "raw": line})
    return results

def main():
    matches = get_ft_matches_mainpage_brut()
    if not matches:
        print("Aucun match FT trouvé sur la page principale.")
    else:
        for m in matches:
            if "raw" in m:
                print(f"[BRUT] {m['raw']}")
            else:
                print(f"MATCH TERMINE (FT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")

if __name__ == "__main__":
    main()
