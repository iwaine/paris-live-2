"""
Script de test pour extraction robuste de la minute live sur SoccerStats.

Ce script propose une méthodologie alternative pour fiabiliser l'extraction de la minute :
- Parcourt tous les éléments <font color=...> de la ligne du match.
- Extrait toutes les valeurs de minute détectées (y compris les temps additionnels).
- Retient la valeur maximale trouvée (supposée être la minute réelle la plus avancée du match).
- Permet de comparer le résultat avec la méthode actuelle.

Usage :
    python3 CLEAN_WORKFLOW/test_extract_minute_robuste.py

Ce script n'affecte pas le code de production et sert uniquement à valider la robustesse de l'extraction.
"""
import re
from bs4 import BeautifulSoup
import requests

URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (Test Minute Extraction)"}

def extract_all_minutes_from_row(tr):
    """
    Extrait toutes les valeurs de minute trouvées dans les balises <font color=...> d'une ligne de match.
    Retourne la valeur maximale trouvée (ou None si aucune minute détectée).
    """
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
        if not row_text:
            continue
        minute_robuste = extract_all_minutes_from_row(tr)
        # Méthode classique (pour comparaison)
        minute_classique = None
        for font in tr.find_all("font", attrs={"color": True}):
            ft = font.get_text(" ", strip=True)
            m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*('|min)", ft)
            if m:
                val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
                if 0 < val <= 130:
                    minute_classique = val
                    break
        if minute_robuste or minute_classique:
            print(f"Ligne: {row_text[:80]}...")
            print(f"  Minute robuste: {minute_robuste}")
            print(f"  Minute classique: {minute_classique}")
            print("---")

if __name__ == "__main__":
    main()
