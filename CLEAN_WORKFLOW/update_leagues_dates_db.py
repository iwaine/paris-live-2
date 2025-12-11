# Script pour initialiser et remplir la base leagues_dates.db avec les dates de début/fin de toutes les ligues suivies
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

LEAGUES = [
    "france", "france2", "germany", "germany2", "italy", "portugal", "portugal2",
    "scotland", "spain", "spain2", "switzerland", "austria", "austria2", "bulgaria",
    "croatia", "croatia2", "czechrepublic", "czechrepublic2", "denmark",
    "netherlands", "poland", "turkey", "england", "england2", "england3", "england4",
    "saudiarabia", "australia", "greece", "slovenia", "japan", "ireland", "southkorea",
    "argentina", "chile", "estonia", "faroeislands", "finland", "iceland", "latvia",
    "sweden", "usa", "southkorea4", "georgia", "norway6", "iceland2", "cyprus", "bolivia"
]


import os
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "leagues_dates.db")
CURRENT_YEAR = datetime.now().year
# Création du dossier data si besoin
import os
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS leagues_dates (
    league TEXT PRIMARY KEY,
    start_date TEXT,
    end_date TEXT,
    season_finished INTEGER DEFAULT 0
)
""")

for league in LEAGUES:
    url = f"https://www.soccerstats.com/latest.asp?league={league}"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        tr = soup.find('tr', bgcolor="#f8f8f8")
        start_str = end_str = None
        start_date = end_date = None
        season_finished = 0
        if tr:
            tds = tr.find_all('td')
            if len(tds) >= 3:
                start_str = tds[0].get_text(strip=True)
                end_str = tds[2].get_text(strip=True)
                if not end_str:
                    progress = tr.find('progress')
                    if progress and progress.get('value') == '100.00':
                        season_finished = 1
                    if 'finished' in tr.get_text().lower():
                        season_finished = 1
                try:
                    if start_str:
                        start_date = datetime.strptime(f"{start_str} {CURRENT_YEAR}", "%d %b %Y").strftime("%Y-%m-%d")
                    if end_str:
                        end_date = datetime.strptime(f"{end_str} {CURRENT_YEAR}", "%d %b %Y").strftime("%Y-%m-%d")
                except Exception:
                    start_date = end_date = None
        c.execute("REPLACE INTO leagues_dates (league, start_date, end_date, season_finished) VALUES (?, ?, ?, ?)",
                  (league, start_date, end_date, season_finished))
        print(f"{league}: start={start_date}, end={end_date}, finished={season_finished}")
    except Exception as e:
        print(f"Erreur pour {league}: {e}")

conn.commit()
conn.close()
print("\nBase leagues_dates.db mise à jour.")
