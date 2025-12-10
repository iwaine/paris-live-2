#!/usr/bin/env python3
"""
Scraper des matchs live depuis l'iframe team_live.asp de SoccerStats
"""
import requests
from bs4 import BeautifulSoup
import re


IFRAME_URL = "https://www.soccerstats.com/fr/team_live.asp"
# Liste des ligues à suivre (mettre les IDs exacts, ex: 'australia', 'germany2', 'bulgaria')
LEAGUES_TO_FOLLOW = [
    "australia",     # A-League
    "bolivia",       # Division Profesional
    "bulgaria",      # Parva Liga
    "england",       # Premier League
    "france",        # Ligue 1
    "germany",       # Bundesliga
    "germany2",      # Bundesliga 2
    "netherlands2",  # Eerste Divisie
    "portugal",      # Primeira Liga
]


def parse_live_matches(html):
    soup = BeautifulSoup(html, "html.parser")
    matches = []
    for div in soup.find_all("div", class_="messagediv"):
        table = div.find("table")
        if not table:
            continue
        tr = table.find("tr")
        if not tr:
            continue
        tds = tr.find_all("td")
        # On cherche le td avec les infos du match
        info_td = None
        league_id = None
        # On cherche le td contenant le lien de la ligue
        for td in tds:
            a_tag = td.find("a", href=True)
            if a_tag and "latest.asp?league=" in a_tag["href"]:
                # Extrait l'ID de la ligue depuis l'URL
                match = re.search(r"league=([a-zA-Z0-9_]+)", a_tag["href"])
                if match:
                    league_id = match.group(1).lower()
        for td in tds:
            if td.has_attr("style") and "padding-left: 5px" in td["style"]:
                info_td = td
                break
        if not info_td or not league_id:
            continue
        if league_id not in LEAGUES_TO_FOLLOW:
            continue  # Ignore les ligues non suivies
        fonts = info_td.find_all("font")
        if len(fonts) < 5:
            continue
        home_team = fonts[0].get_text(strip=True)
        away_team = fonts[2].get_text(strip=True)
        score_text = fonts[3].get_text(strip=True)
        score_match = re.search(r"(\d+)\s*[-:]\s*(\d+)", score_text)
        if not score_match:
            continue
        score_home = int(score_match.group(1))
        score_away = int(score_match.group(2))
        minute_text = fonts[4].get_text(strip=True)
        minute_match = re.search(r"(\d+)'", minute_text)
        minute = int(minute_match.group(1)) if minute_match else None
        matches.append({
            "home_team": home_team,
            "away_team": away_team,
            "score_home": score_home,
            "score_away": score_away,
            "minute": minute,
            "league_id": league_id,
        })
    return matches


def main():
    print("Scraping iframe live matches...")
    resp = requests.get(IFRAME_URL)
    resp.encoding = "ISO-8859-1"
    matches = parse_live_matches(resp.text)
    print(f"\n=== MATCHS LIVE DÉTECTÉS ({len(matches)}) ===")
    if not matches:
        print("Aucun match live détecté dans les ligues suivies :", ', '.join(LEAGUES_TO_FOLLOW))
    for m in matches:
        print(f"[{m['league_id']}] {m['home_team']} vs {m['away_team']} | {m['score_home']}-{m['score_away']} ({m['minute']}' min)")

if __name__ == "__main__":
    main()
