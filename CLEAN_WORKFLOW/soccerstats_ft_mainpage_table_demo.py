"""
Script d'extraction FT basé sur la structure des tableaux HTML de la page principale SoccerStats
Parcourt tous les <tr>, détecte les <td> contenant <font color="blue">FT</font>, et extrait le score et les équipes
"""

import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (FT Table Extract)"}

def extract_ft_from_table():
    r = requests.get(URL, headers=UA, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    # Parcourt tous les tableaux
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            # On cherche la cellule FT ou HT et on extrait les infos des cellules voisines
            for idx, td in enumerate(tds):
                for status in ["FT", "HT"]:
                    font = td.find("font", string=status)
                    # On ignore les cellules qui contiennent une minute (ex: 90'+2) au lieu de FT/HT
                    if font:
                        minute_cell = False
                        for cell in tds:
                            txt = cell.get_text(strip=True)
                            if re.match(r"^\d{1,3}'\+?\d*$", txt):
                                minute_cell = True
                                break
                        if minute_cell:
                            continue  # Ignore ce <tr>, ce n'est pas un match FT/HT
                        # On suppose que le score est dans la cellule précédente ou suivante
                        score = None
                        home_team = None
                        away_team = None
                        # Recherche du score dans les cellules du <tr>
                        for i, cell in enumerate(tds):
                            score_match = re.match(r"^(\d+)[:](\d+)$", cell.get_text(strip=True))
                            if score_match:
                                score = (score_match.group(1), score_match.group(2))
                                # On suppose que home_team est la cellule précédente, away_team la suivante
                                if i > 0:
                                    home_team = tds[i-1].get_text(strip=True)
                                if i < len(tds)-1:
                                    away_team = tds[i+1].get_text(strip=True)
                                break
                        if score and home_team and away_team:
                            results.append({
                                "status": status,
                                "home_team": home_team,
                                "score_home": score[0],
                                "score_away": score[1],
                                "away_team": away_team
                            })
                        else:
                            # Si le format n'est pas classique, on affiche la ligne brute
                            line = tr.get_text(" ", strip=True)
                            results.append({"status": status, "raw": line})
    return results

def main():
    matches = extract_ft_from_table()
    if not matches:
        print("Aucun match FT/HT trouvé dans les tableaux de la page principale.")
    else:
        for m in matches:
            if "raw" in m:
                line = m["raw"]
                # Extraction avancée FT
                if m["status"] == "FT":
                    m2 = re.search(r"FT\s+([A-Za-z .']+)\s+(\d+)[:](\d+)\s+.*?([A-Za-z .']+)\s+stats", line)
                    if m2:
                        home_team = m2.group(1).strip()
                        score_home = m2.group(2)
                        score_away = m2.group(3)
                        away_team = m2.group(4).strip()
                        print(f"MATCH TERMINE (FT) : {home_team} {score_home} – {score_away} {away_team}")
                    else:
                        print(f"[BRUT] {line}")
                # Extraction avancée HT
                elif m["status"] == "HT":
                    m2 = re.search(r"HT\s+([A-Za-z .']+)\s+(\d+)[:](\d+)\s+.*?([A-Za-z .']+)\s+stats", line)
                    if m2:
                        home_team = m2.group(1).strip()
                        score_home = m2.group(2)
                        score_away = m2.group(3)
                        away_team = m2.group(4).strip()
                        print(f"MI-TEMPS (HT) : {home_team} {score_home} – {score_away} {away_team}")
                    else:
                        print(f"[BRUT] {line}")
                else:
                    print(f"[BRUT] {line}")
            else:
                if m["status"] == "FT":
                    print(f"MATCH TERMINE (FT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")
                elif m["status"] == "HT":
                    print(f"MI-TEMPS (HT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")

if __name__ == "__main__":
    main()
