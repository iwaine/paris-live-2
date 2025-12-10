#!/usr/bin/env python3
"""Detecte les matches live depuis la page principale de SoccerStats et propose un monitor simple.

Usage:
  - Lister les matches live: `python3 soccerstats_live_selector.py`
  - Monitorer un match: `python3 soccerstats_live_selector.py --monitor <match_url>`

Notes:
  - Heuristique: cherche les liens contenant "match" et un texte voisin contenant "min" ou "'" ou "live".
  - Pour un affichage exact des équipes/score, le script utilise `SoccerStatsLiveScraper.scrape_match` (import local).
"""
from __future__ import annotations

import re
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    from soccerstats_live_scraper import SoccerStatsLiveScraper
except Exception:
    SoccerStatsLiveScraper = None

DEFAULT_URL = "https://www.soccerstats.com/"
UA = {"User-Agent": "paris-live-bot/1.0 (Match Detection)"}


def parse_minute(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", text)
    if m:
        base = int(m.group(1))
        extra = int(m.group(2)) if m.group(2) else 0
        return base + extra
    # fallback simple digits with 'min' word
    m2 = re.search(r"(\d{1,3})\s*min", text)
    if m2:
        return int(m2.group(1))
    return None


def get_live_matches(index_url: str = DEFAULT_URL, timeout: int = 10, debug: bool = False) -> List[Dict]:
    r = requests.get(index_url, headers=UA, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    results: List[Dict] = []

    # 1) Priorité: table#btable (liste principale de matches)
    btable = soup.find("table", id="btable")
    if btable is not None:
        if debug:
            print("Found table#btable — scanning rows...")
        for tr in btable.find_all("tr"):
            row_text = tr.get_text(" ", strip=True)
            if not row_text:
                continue

            # collect all pmatch links in this row
            anchors = [a for a in tr.find_all("a", href=True) if "pmatch" in a["href"] or "pmatch.asp" in a["href"] or "pmatch" in a.get_text("")]
            if not anchors:
                continue

            # attempt to find minute in the row (font color red or regex)
            minute = None
            # search for <font color> occurrences with minute-like text
            for font in tr.find_all("font", attrs={"color": True}):
                ft = font.get_text(" ", strip=True)
                m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", ft)
                if m:
                    val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
                    # Valider que c'est une minute réaliste (pas un score ou autre stat)
                    if 0 <= val <= 130:
                        minute = val
                        break

            # Fallback: chercher dans les 150 premiers caractères du row_text (contexte proche)
            if minute is None:
                row_snippet = row_text[:150]
                m2 = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", row_snippet)
                if m2:
                    val = int(m2.group(1)) + (int(m2.group(2)) if m2.group(2) else 0)
                    if 0 <= val <= 130:
                        minute = val

            # for each anchor produce one result (some rows contain multiple matches per league listing)
            for a in anchors:
                href = urljoin(index_url, a["href"])
                # teams_text: prefer anchor text if it contains 'vs' or '-' or a score
                atext = a.get_text(" ", strip=True)
                teams_text = atext if (" vs " in atext or " - " in atext or re.search(r"\d\s*[-:]\s*\d", atext)) else row_text
                results.append({"url": href, "minute": minute, "snippet": teams_text})

    # 2) Fallback: scan links across page and pick the nearest compact ancestor as snippet
    if not results:
        if debug:
            print("No results from btable — using fallback scanning of fonts and links...")
        candidates: Dict[str, Dict] = {}
        for a in soup.find_all("a", href=True):
            href_raw = a["href"]
            href = urljoin(index_url, href_raw)
            if not ("pmatch" in href_raw or "pmatch" in a.get_text(" ")):
                continue

            # find the smallest ancestor that is a good container
            container = None
            ancestor = a
            for _ in range(4):
                ancestor = ancestor.parent
                if ancestor is None:
                    break
                if ancestor.name in ("tr", "td", "p", "li", "div"):
                    txt = ancestor.get_text(" ", strip=True)
                    if 10 < len(txt) < 400:
                        container = ancestor
                        break

            nearby_text = container.get_text(" ", strip=True) if container is not None else a.get_text(" ", strip=True)

            # try to find minute near the anchor: previous/next font or inside container
            minute = None
            # check previous font (dans un rayon de 3 fonts max)
            for font in a.find_all_previous("font", limit=3):
                m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", font.get_text(" ", strip=True))
                if m:
                    val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
                    if 0 <= val <= 130:
                        minute = val
                        break

            # check next font (dans un rayon de 3 fonts max)
            if minute is None:
                for font in a.find_all_next("font", limit=3):
                    m2 = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", font.get_text(" ", strip=True))
                    if m2:
                        val = int(m2.group(1)) + (int(m2.group(2)) if m2.group(2) else 0)
                        if 0 <= val <= 130:
                            minute = val
                            break

            # check container text regex fallback (limiter aux 200 premiers caractères)
            if minute is None:
                nearby_snippet = nearby_text[:200]
                m3 = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", nearby_snippet)
                if m3:
                    val = int(m3.group(1)) + (int(m3.group(2)) if m3.group(2) else 0)
                    if 0 <= val <= 130:
                        minute = val

            # accept if minute found or 'live' in text
            if minute is not None or re.search(r"\b(live|in-play)\b", nearby_text, re.I):
                # dedupe by href
                if href not in candidates:
                    candidates[href] = {"url": href, "minute": minute, "snippet": nearby_text}

        results = list(candidates.values())

    # sort by minute (unknown minutes last)
    results.sort(key=lambda x: x.get("minute") if x.get("minute") is not None else -1, reverse=True)
    return results


def monitor_match(url: str, interval: int = 10):
    """Boucle simple qui récupère les infos du match à intervalle régulier.

    Si `SoccerStatsLiveScraper` est disponible, on l'utilise pour des données complètes.
    """
    if SoccerStatsLiveScraper is None:
        print("SoccerStatsLiveScraper non disponible. Placez ce fichier à la racine du projet ou installez le module.")
        return

    scraper = SoccerStatsLiveScraper()
    try:
        while True:
            try:
                data = scraper.scrape_match(url)
            except Exception as e:
                print(f"Erreur scraping: {e}")
                data = None

            if data:
                d = data.to_dict() if hasattr(data, "to_dict") else data
                minute = d.get("minute")
                score = f"{d.get('home_score')}:{d.get('away_score')}" if d.get('home_score') is not None else "-"
                teams = f"{d.get('home_team')} vs {d.get('away_team')}"
                print(f"[{time.strftime('%H:%M:%S')}] {teams} | {score} | {minute} min")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Pas de données pour {url}")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("Monitor stoppé par l'utilisateur.")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Détecte les matches live sur SoccerStats et permet un monitor simple.")
    p.add_argument("--url", help="URL de la page principale (par défaut soccerstats)", default=DEFAULT_URL)
    p.add_argument("--monitor", help="URL du match à monitorer (optionnel)")
    p.add_argument("--interval", help="Intervalle de refresh en secondes", type=int, default=10)
    p.add_argument("--debug", help="Mode debug: affiche candidats bruts", action='store_true')
    args = p.parse_args()

    if args.monitor:
        monitor_match(args.monitor, interval=args.interval)
    else:
        lives = get_live_matches(args.url, debug=args.debug)
        if not lives:
            print("Aucun match live détecté depuis la page principale.")
        else:
            print("Matches live détectés:")
            for m in lives:
                print(f"- {m['url']} | minute: {m.get('minute')} | snippet: {m['snippet'][:120]}")
