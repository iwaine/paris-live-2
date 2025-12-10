import requests
from bs4 import BeautifulSoup
import re

def get_teams_by_league(league):
    url = f"https://www.soccerstats.com/latest.asp?league={league}"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        teams = set()
        # Cherche tous les liens vers les pages d'équipe
        for link in soup.find_all('a', href=re.compile(r'team\.asp\?league=' + league + r'&team=')):
            team_name = link.get_text(strip=True)
            if team_name and len(team_name) > 2:
                teams.add(team_name)
        return sorted(list(teams))
    except Exception as e:
        print(f"Erreur récupération équipes pour {league}: {e}")
        return []

if __name__ == "__main__":
    ligues = ["germany2", "england", "france", "italy", "spain", "netherlands", "portugal", "belgium"]
    for ligue in ligues:
        teams = get_teams_by_league(ligue)
        print(f"{ligue}: {teams}")
