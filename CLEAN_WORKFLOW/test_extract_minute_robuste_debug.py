"""
Script de test pour extraction robuste de la minute live sur SoccerStats (mode debug).

Ce script affiche toutes les lignes de la table btable, même sans minute détectée, pour diagnostic.

Usage :
    python3 CLEAN_WORKFLOW/test_extract_minute_robuste_debug.py
"""
import re
from bs4 import BeautifulSoup
import requests

URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (Test Minute Extraction)"}

def extract_all_minutes_from_row(tr):
    minutes = []
    for font in tr.find_all("font", attrs={"color": True}):
        ft = font.get_text(" ", strip=True)
        m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*('|min)", ft)
        if m:
            val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
            if 0 < val <= 130:
                minutes.append(val)
    return max(minutes) if minutes else None

def main():
    r = requests.get(URL, headers=UA, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    btable = soup.find("table", id="btable")
    if btable is None:
        print("Aucune table de matches live trouvée.")
        return
    for tr in btable.find_all("tr"):
        row_text = tr.get_text(" ", strip=True)
        minute_robuste = extract_all_minutes_from_row(tr)
        minute_classique = None
        for font in tr.find_all("font", attrs={"color": True}):
            ft = font.get_text(" ", strip=True)
            m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*('|min)", ft)
            if m:
                val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
                if 0 < val <= 130:
                    minute_classique = val
                    break
        print(f"Ligne: {row_text[:80]}...")
        print(f"  Minute robuste: {minute_robuste}")
        print(f"  Minute classique: {minute_classique}")
        print("---")

if __name__ == "__main__":
    main()
