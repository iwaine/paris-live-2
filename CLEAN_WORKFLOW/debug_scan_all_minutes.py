import requests
import re
from bs4 import BeautifulSoup

URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (Debug Minute Scan)"}

def extract_minutes_from_text(text):
    """Retourne toutes les occurrences de minutes dans un texte."""
    return re.findall(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", text)

def main():
    print(f"[INFO] Téléchargement de la page {URL} ...")
    r = requests.get(URL, headers=UA, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Scanner toutes les tables
    tables = soup.find_all("table")
    print(f"[INFO] {len(tables)} tables trouvées sur la page.")
    found = False
    for idx, table in enumerate(tables):
        print(f"\n[Table {idx+1}/{len(tables)}] id={table.get('id')} class={table.get('class')}")
        rows = table.find_all("tr")
        for tr in rows:
            row_text = tr.get_text(" ", strip=True)
            minutes = extract_minutes_from_text(row_text)
            if minutes:
                found = True
                print(f"  [Minute trouvée] Ligne: {row_text[:120]}")
                print(f"    Minutes détectées: {minutes}")

    # Scanner aussi les divs et sections
    divs = soup.find_all(["div", "section"])
    print(f"\n[INFO] {len(divs)} divs/sections trouvés sur la page.")
    for idx, div in enumerate(divs):
        div_text = div.get_text(" ", strip=True)
        minutes = extract_minutes_from_text(div_text)
        if minutes:
            found = True
            print(f"  [Minute trouvée dans div/section {idx+1}] Extrait: {div_text[:120]}")
            print(f"    Minutes détectées: {minutes}")

    if not found:
        print("\nAucune minute de match live détectée dans les tables ou sections de la page.")

if __name__ == "__main__":
    main()