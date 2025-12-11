"""
Extraction des matches FT/HT SoccerStats avec Selenium + Chromium (compatible devcontainer)
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re

URL = "https://www.soccerstats.com/"
LEAGUES_TO_FOLLOW = ["ENGLAND2", "FRANCE", "GERMANY", "SPAIN", "ITALY"]

options = Options()
options.binary_location = "/usr/bin/chromium-browser"
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service('/usr/bin/chromium-chromedriver')
browser = webdriver.Chrome(service=service, options=options)
browser.get(URL)
html = browser.page_source
browser.quit()

soup = BeautifulSoup(html, "html.parser")

results = []
btable = soup.find("table", id="btable")
if btable is not None:
    for tr in btable.find_all("tr"):
        tds = tr.find_all("td")
        league_name = None
        for td in tds:
            txt = td.get_text(strip=True)
            for lid in LEAGUES_TO_FOLLOW:
                if lid in txt.replace(" ","").upper():
                    league_name = lid
                    break
        for status in ["FT", "HT"]:
            found = False
            for td in tds:
                if status in td.get_text(strip=True):
                    found = True
                    break
            if found and len(tds) >= 4 and league_name:
                score_match = re.search(r"(\d+)[:](\d+)", tds[2].get_text(strip=True))
                if score_match:
                    results.append({
                        "status": status,
                        "league": league_name,
                        "home_team": tds[1].get_text(strip=True),
                        "score_home": score_match.group(1),
                        "score_away": score_match.group(2),
                        "away_team": tds[3].get_text(strip=True)
                    })

if results:
    print("\n=== Matches à la mi-temps (HT) et terminés (FT) des ligues suivies (Chromium/Selenium) ===")
    for m in results:
        if m["status"] == "HT":
            print(f"{m['league']} | MI-TEMPS (HT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")
        elif m["status"] == "FT":
            print(f"{m['league']} | MATCH TERMINE (FT) : {m['home_team']} {m['score_home']} – {m['score_away']} {m['away_team']}")
else:
    print("Aucun match HT ou FT détecté dans les ligues suivies.")
