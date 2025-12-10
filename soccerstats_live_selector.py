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

    # Liste des ligues suivies (modifiable facilement)
    LEAGUES_TO_FOLLOW = [
        "australia", "bolivia", "bulgaria", "england", "france", "germany", "germany2", "netherlands2", "portugal"
    ]

    # 1) Priorité: table#btable (liste principale de matches)
    btable = soup.find("table", id="btable")
    if btable is not None:
        if debug:
            print("Found table#btable — scanning rows...")
        for tr in btable.find_all("tr"):
            row_text = tr.get_text(" ", strip=True)
            if not row_text:
                continue

            # attempt to find minute in the row (font color red or regex)
            minute = None
            for font in tr.find_all("font", attrs={"color": True}):
                ft = font.get_text(" ", strip=True)
                m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", ft)
                if m:
                    val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
                    if 0 <= val <= 130:
                        minute = val
                        break
            if minute is None:
                row_snippet = row_text[:150]
                m2 = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", row_snippet)
                if m2:
                    val = int(m2.group(1)) + (int(m2.group(2)) if m2.group(2) else 0)
                    if 0 <= val <= 130:
                        minute = val

            # collect all pmatch links in this row
            anchors = [a for a in tr.find_all("a", href=True) if "pmatch" in a["href"] or "pmatch.asp" in a["href"] or "pmatch" in a.get_text("")]

            # Si minute détectée mais pas d'ancre, essayer de trouver une ancre de match dans la ligne ou à proximité
            if minute is not None:
                if anchors:
                    for a in anchors:
                        href = urljoin(index_url, a["href"])
                        m_lid = re.search(r"league=([a-zA-Z0-9]+)", href)
                        league_id = m_lid.group(1) if m_lid else None
                        if league_id not in LEAGUES_TO_FOLLOW:
                            continue
                        atext = a.get_text(" ", strip=True)
                        teams_text = atext if (" vs " in atext or " - " in atext or re.search(r"\d\s*[-:]\s*\d", atext)) else row_text
                        results.append({"url": href, "minute": minute, "snippet": teams_text})
                else:
                    # Pas d'ancre directe, essayer de trouver une ancre dans les td ou tr parents
                    parent_anchor = None
                    for a in tr.find_all("a", href=True):
                        if "league=" in a["href"]:
                            parent_anchor = a
                            break
                    if parent_anchor:
                        href = urljoin(index_url, parent_anchor["href"])
                        m_lid = re.search(r"league=([a-zA-Z0-9]+)", href)
                        league_id = m_lid.group(1) if m_lid else None
                        if league_id in LEAGUES_TO_FOLLOW:
                            teams_text = row_text
                            results.append({"url": href, "minute": minute, "snippet": teams_text})
                    else:
                        # Fallback: construire l'URL de la ligue
                        m_lid = re.search(r"([a-zA-Z0-9]+)", row_text)
                        league_id = None
                        for lid in LEAGUES_TO_FOLLOW:
                            if lid in row_text.lower():
                                league_id = lid
                                break
                        if league_id:
                            href = f"https://www.soccerstats.com/latest.asp?league={league_id}"
                            teams_text = row_text
                            results.append({"url": href, "minute": minute, "snippet": teams_text})

    # 2) Fallback: scan links across page and pick the nearest compact ancestor as snippet
    if not results:
        if debug:
            print("No results from btable — using fallback scanning of fonts and links...")
        candidates: Dict[str, Dict] = {}
        for a in soup.find_all("a", href=True):
            href_raw = a["href"]
            href = urljoin(index_url, href_raw)
            # Filtrer sur les ligues suivies dans le fallback aussi
            if not ("pmatch" in href_raw or "pmatch" in a.get_text(" ")):
                continue
            m_lid = re.search(r"league=([a-zA-Z0-9]+)", href)
            league_id = m_lid.group(1) if m_lid else None
            if league_id not in LEAGUES_TO_FOLLOW:
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
"""
from __future__ import annotations

import re
import time
import csv
import os
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

    # Liste des ligues suivies (modifiable facilement)
    LEAGUES_TO_FOLLOW = [
        "australia", "bolivia", "bulgaria", "england", "france", "germany", "germany2", "netherlands2", "portugal"
    ]

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
            for font in tr.find_all("font", attrs={"color": True}):
                ft = font.get_text(" ", strip=True)
                m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*(?:'|min)", ft)
                if m:
                    val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
                    if 0 <= val <= 130:
                        minute = val
                        break
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
                m_lid = re.search(r"league=([a-zA-Z0-9]+)", href)
                league_id = m_lid.group(1) if m_lid else None
                if league_id not in LEAGUES_TO_FOLLOW:
                    continue
                atext = a.get_text(" ", strip=True)
                teams_text = atext if (" vs " in atext or " - " in atext or re.search(r"\d\s*[-:]\s*\d", atext)) else row_text
                status = "LIVE" if minute is not None else "PRE-MATCH"
                results.append({"url": href, "minute": minute, "snippet": teams_text, "status": status})

    # 2) Fallback: scan links across page and pick the nearest compact ancestor as snippet
    if not results:
        if debug:
            print("No results from btable — using fallback scanning of fonts and links...")
        candidates: Dict[str, Dict] = {}
        for a in soup.find_all("a", href=True):
            href_raw = a["href"]
            href = urljoin(index_url, href_raw)
            # Filtrer sur les ligues suivies dans le fallback aussi
            if not ("pmatch" in href_raw or "pmatch" in a.get_text(" ")):
                continue
            m_lid = re.search(r"league=([a-zA-Z0-9]+)", href)
            league_id = m_lid.group(1) if m_lid else None
            if league_id not in LEAGUES_TO_FOLLOW:
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
                home = d.get('home_team')
                away = d.get('away_team')
                teams = f"{home} vs {away}"

                # Tableau stats live
                stats_table = f"""
Statistique      | {home} | {away}
-----------------|--------|------
Possession       | {d.get('possession_home','-')}% | {d.get('possession_away','-')}%
Corners          | {d.get('corners_home','-')} | {d.get('corners_away','-')}
Total tirs       | {d.get('shots_home','-')} | {d.get('shots_away','-')}
Tirs cadrés      | {d.get('shots_on_target_home','-')} | {d.get('shots_on_target_away','-')}
Tirs surface     | {d.get('shots_inside_box_home','-')} | {d.get('shots_inside_box_away','-')}
Tirs hors surface| {d.get('shots_outside_box_home','-')} | {d.get('shots_outside_box_away','-')}
Attaques         | {d.get('attacks_home','-')} | {d.get('attacks_away','-')}
Attaques dang.   | {d.get('dangerous_attacks_home','-')} | {d.get('dangerous_attacks_away','-')}
"""

                # Détermination de l'intervalle critique
                interval_name = None
                if minute is not None:
                    if 31 <= minute <= 45:
                        interval_name = "31-45+"
                    elif 75 <= minute <= 90:
                        interval_name = "75-90+"

                # Placeholders pour patterns historiques (à remplacer par vrai appel)
                def get_team_pattern(team, league, is_home, interval):
                    # Détermination de la colonne selon l'intervalle
                    if interval == "31-45+":
                        goal_col = 'H1_Goals_Avg'
                        sem_col = 'H1_Goals_Stdev'
                    elif interval == "75-90+":
                        goal_col = 'H2_Goals_Avg'
                        sem_col = 'H2_Goals_Stdev'
                    else:
                        goal_col = 'Goals_Scored_Avg'
                        sem_col = 'Goals_Scored_Stdev'
                    path = os.path.join(os.path.dirname(__file__), 'data/recurrence_stats_export.csv')
                    with open(path, newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            if row['Team'].lower() == team.lower() and ((is_home and row['Context']=='HOME') or (not is_home and row['Context']=='AWAY')):
                                freq = float(row.get(goal_col,0))
                                sem = float(row.get(sem_col,0))
                                matches = int(row.get('Total_Matches',0))
                                avg_minute = freq # Pour la démo, à remplacer par la vraie minute
                                iqr = "-"
                                # Récurrence récente et confiance (à calculer si possible)
                                rec5 = '-' # À calculer si historique disponible
                                confidence = 'TRES_BON' if matches >= 10 else 'MOYEN'
                                return {
                                    'freq': round(freq,1),
                                    'avg_minute': avg_minute,
                                    'sem': round(sem,1),
                                    'iqr': iqr,
                                    'rec5': rec5,
                                    'confidence': confidence,
                                    'prob': round(freq,1)
                                }
                    return None
                def get_top5_patterns(league, interval):
                    # Détermination de la colonne selon l'intervalle
                    if interval == "31-45+":
                        goal_col = 'H1_Goals_Avg'
                        sem_col = 'H1_Goals_Stdev'
                    elif interval == "75-90+":
                        goal_col = 'H2_Goals_Avg'
                        sem_col = 'H2_Goals_Stdev'
                    else:
                        goal_col = 'Goals_Scored_Avg'
                        sem_col = 'Goals_Scored_Stdev'
                    # Lecture du CSV
                    path = os.path.join(os.path.dirname(__file__), 'data/recurrence_stats_export.csv')
                    top = []
                    with open(path, newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            team = row['Team']
                            # Filtrer par ligue (simple: team doit être dans la ligue, à adapter si mapping)
                            # Ici, on suppose que le nom de la ligue est dans le nom de l'équipe ou via mapping externe
                            # Pour la démo, on prend les équipes allemandes connues
                            bundesliga = ['Bayern Munich','Borussia Dortmund','RB Leipzig','Stuttgart']
                            if league == 'germany' and team not in bundesliga:
                                continue
                            if league == 'england' and team not in ['Manchester City','Liverpool','Arsenal','Chelsea','Tottenham','Manchester United']:
                                continue
                            # ...ajouter autres ligues si besoin...
                            freq = float(row.get(goal_col,0))
                            sem = float(row.get(sem_col,0))
                            matches = int(row.get('Total_Matches',0))
                            avg_minute = freq # Pour la démo, à remplacer par la vraie minute
                            iqr = "-"
                            top.append({'team': team, 'loc': row['Context'], 'freq': round(freq,1), 'matches': matches, 'avg_minute': avg_minute, 'sem': round(sem,1), 'iqr': iqr})
                    # Trier par fréquence et retourner le top 5
                    top = sorted(top, key=lambda x: x['freq'], reverse=True)[:5]
                    return top

                home_pattern = get_team_pattern(home, d.get('league','germany'), True, interval_name) if interval_name else None
                away_pattern = get_team_pattern(away, d.get('league','germany'), False, interval_name) if interval_name else None
                top5 = get_top5_patterns(d.get('league','germany'), interval_name) if interval_name else []

                # Format message Telegram enrichi
                if home_pattern and away_pattern:
                    msg = f"""
[{time.strftime('%H:%M:%S')}] {teams} | {score} | {minute} min

{stats_table}

🔎 Analyse combinée :
- Intervalle critique : {interval_name if interval_name else 'hors intervalle'}
- Pattern historique {home} (HOME) :
    Fréquence but : {home_pattern.get('freq','-')}%
    Minute moy. : {home_pattern.get('avg_minute','-')}
    SEM : {home_pattern.get('sem','-')}
    IQR : {home_pattern.get('iqr','-')}
    Récurrence 5 derniers : {home_pattern.get('rec5','-')}%
    Confiance : {home_pattern.get('confidence','-')}
- Pattern historique {away} (AWAY) :
    Fréquence but encaissé : {away_pattern.get('freq','-')}%
    Minute moy. : {away_pattern.get('avg_minute','-')}
    SEM : {away_pattern.get('sem','-')}
    IQR : {away_pattern.get('iqr','-')}
    Récurrence 5 derniers : {away_pattern.get('rec5','-')}%
    Confiance : {away_pattern.get('confidence','-')}

🏆 Top 5 patterns {d.get('league','germany')} ({interval_name if interval_name else 'interval'}):
"""
                    for i, t in enumerate(top5, 1):
                        msg += f"{i}. {t['team']} ({t['loc']}) : {t['freq']}% ({t['matches']} matchs), moy. {t['avg_minute']}, SEM {t['sem']}, IQR {t['iqr']}\n"

                    # Probabilité combinée et signal (à calculer selon logique projet)
                    msg += f"\n📊 Probabilité combinée (live + historique) : {home_pattern.get('prob','-')}%\n🟢 Signal : {'Opportunité de but' if home_pattern.get('prob',0) > 70 else 'Rien à signaler'}\n"
                else:
                    msg = f"[{time.strftime('%H:%M:%S')}] {teams} | {score} | {minute} min\n\n{stats_table}\n\n🔎 Analyse combinée :\n- Hors intervalle critique ou données historiques indisponibles."

                print(msg)
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
            print("Matches détectés (LIVE/PRE-MATCH):")
            for m in lives:
                print(f"- {m['url']} | minute: {m.get('minute')} | statut: {m.get('status','?')} | snippet: {m['snippet'][:120]}")
            # Sélection automatique du premier match LIVE, sinon du premier match tout court
            live_matches = [m for m in lives if m.get('status') == 'LIVE']
            if live_matches:
                best_match = live_matches[0]
                print(f"\nLancement du monitoring automatique sur : {best_match['url']} (minute: {best_match.get('minute')})")
                monitor_match(best_match['url'], interval=args.interval)
            else:
                print("Aucun match LIVE détecté. Monitoring non lancé.")
