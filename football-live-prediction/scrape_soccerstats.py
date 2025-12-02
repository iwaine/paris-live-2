import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.soccerstats.com/team.asp?league=england&teamid=10"
print("⏳ Chargement de la page…")
response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(response.text, "html.parser")
print("📄 Page récupérée, extraction match par match...\n")

rows = soup.select("table[width='100%'] tbody tr")
for row in rows:
    cols = row.find_all("td")
    if len(cols) < 4:
        continue
    home_team = cols[1].get_text(strip=True)
    away_team = cols[3].get_text(strip=True)
    score_cell = cols[2]
    score_link = score_cell.find("a", class_="tooltip4")
    if not score_link:
        continue
    tooltip_div = score_link.select_one("span div")
    if not tooltip_div:
        continue
    tooltip_text = tooltip_div.get_text("\n", strip=True)
    
    # Extraction de toutes les minutes (parenthèses)
    goals = re.findall(r"\((\d+)\)", tooltip_text)
    if not goals:
        continue

    print(f"{home_team} vs {away_team}")
    for g in goals:
        minute = int(g)
        # On regarde si le texte avant la minute correspond à home ou away
        pattern = r"(\d+-\d+)\s+.*?\((\d+)\)"
        matches = re.findall(pattern, tooltip_text)
        team = "?"  # par défaut
        for score, m in matches:
            if int(m) == minute:
                home_goals, away_goals = map(int, score.split("-"))
                if home_goals > away_goals:  # simplification : le but est pour home
                    team_name = home_team
                    venue = "Domicile"
                else:
                    team_name = away_team
                    venue = "Extérieur"
                team = f"{team_name} ({venue})"
        print(f"  ⚽ {minute} min - {team}")
    print()
