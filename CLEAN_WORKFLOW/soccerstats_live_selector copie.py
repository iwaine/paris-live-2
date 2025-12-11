# Fonction de normalisation des noms d'équipes
def normalize_team_name(name):
    return name.strip().lower().replace('.', '').replace('-', ' ').replace("'", '').replace('  ', ' ')

# Fonction pour calculer le nombre moyen de buts par mi-temps (MT1 et MT2)
def compute_mt_goals(matchs):
    mt1_buts_list = []
    mt2_buts_list = []
    for goal_times, goal_times_conceded, is_home in matchs:
        try:
            goals = __import__('json').loads(goal_times) if goal_times else []
            conceded = __import__('json').loads(goal_times_conceded) if goal_times_conceded else []
        except Exception:
            goals, conceded = [], []
        # MT1 = 1 à 45+ (on prend tout <= 45.99)
        mt1_buts = sum(1 for m in goals + conceded if 1 <= m <= 45.99)
        # MT2 = 46 à 90+ (on prend tout >= 46)
        mt2_buts = sum(1 for m in goals + conceded if 46 <= m <= 120)
        mt1_buts_list.append(mt1_buts)
        mt2_buts_list.append(mt2_buts)
    def safe_mean(l):
        return sum(l)/len(l) if l else 0.0
    def safe_sem(l):
        n = len(l)
        if n <= 1:
            return 0.0
        m = safe_mean(l)
        return (sum((x - m) ** 2 for x in l) / (n - 1)) ** 0.5 / n ** 0.5
    def safe_iqr(l):
        if not l:
            return 0.0
        l = sorted(l)
        n = len(l)
        q1 = l[n // 4]
        q3 = l[(3 * n) // 4]
        return q3 - q1
    return {
        'mt1_moy': safe_mean(mt1_buts_list),
        'mt1_sem': safe_sem(mt1_buts_list),
        'mt1_iqr': safe_iqr(mt1_buts_list),
        'mt2_moy': safe_mean(mt2_buts_list),
        'mt2_sem': safe_sem(mt2_buts_list),
        'mt2_iqr': safe_iqr(mt2_buts_list),
        'mt1_list': mt1_buts_list,
        'mt2_list': mt2_buts_list
    }


# Fonction d'affichage patterns historiques exhaustive
def print_full_patterns(league, home_team, away_team, get_pattern_score):
    INTERVALS = [(31, 45), (75, 120)]
    INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }
    # Charger la liste des équipes normalisées de la base pour la ligue
        import os
        conn = __import__('sqlite3').connect(os.path.join(os.path.dirname(__file__), 'data', 'predictions.db'))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = ?", (league,))
    teams_in_db = [row[0] for row in cursor.fetchall()]
    norm_map = {normalize_team_name(t): t for t in teams_in_db}
    conn.close()
    import math

    def sem(data):
        n = len(data)
        if n <= 1:
            return 0.0
        m = sum(data) / n
        return (sum((x - m) ** 2 for x in data) / (n - 1)) ** 0.5 / n ** 0.5

    def iqr_interval(data):
        if not data:
            return (0.0, 0.0)
        data = sorted(data)
        n = len(data)
        q1 = data[n // 4]
        q3 = data[(3 * n) // 4]
        return (q1, q3)

    for team in [home_team, away_team]:
        team_norm = normalize_team_name(team)
        norm_team = norm_map.get(team_norm, None)
        print(f"[DEBUG] Team original: '{team}' | normalisé: '{team_norm}' | trouvé en base: '{norm_team}'")
        for side in ["HOME", "AWAY"]:
            for interval in INTERVALS:
                # Extraction détaillée
                conn = __import__('sqlite3').connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                    import os
                    conn = __import__('sqlite3').connect(os.path.join(os.path.dirname(__file__), 'data', 'predictions.db'))
                cursor = conn.cursor()
                if norm_team is not None:
                    cursor.execute("""
                        SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches
                        WHERE league = ? AND team = ?
                    """, (league, norm_team))
                else:
                    cursor.execute("""
                        SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches
                        WHERE league = ? AND team = ?
                    """, (league, team))
                matchs = cursor.fetchall()
                print(f"[DEBUG]  -> {side} {INTERVAL_LABELS[interval]} : {len(matchs)} matchs trouvés pour '{norm_team or team}'")
                conn.close()
                total = 0
                avec_but = 0
                buts_marques = 0
                buts_encaisses = 0
                minutes_buts = []
                buts_par_match_avec_but = []
                for goal_times, goal_times_conceded, is_home in matchs:
                    if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                        continue
                    try:
                        goals = __import__('json').loads(goal_times) if goal_times else []
                        conceded = __import__('json').loads(goal_times_conceded) if goal_times_conceded else []
                    except Exception:
                        goals, conceded = [], []
                    start, end = interval
                    buts_dans_intervalle = [m for m in goals if start <= m <= end] + [m for m in conceded if start <= m <= end]
                    minutes_buts += buts_dans_intervalle
                    n_marques = sum(1 for m in goals if start <= m <= end)
                    n_encaisses = sum(1 for m in conceded if start <= m <= end)
                    buts_marques += n_marques
                    buts_encaisses += n_encaisses
                    total += 1
                    if (n_marques + n_encaisses) > 0:
                        avec_but += 1
                        buts_par_match_avec_but.append(len(buts_dans_intervalle))
                if total > 0:
                    recurrence = int(round(100 * avec_but / total))
                    total_buts = buts_marques + buts_encaisses
                    label = INTERVAL_LABELS[interval]
                    def safe_mean(l):
                        return sum(l)/len(l) if l else 0.0
                    def safe_sem(l):
                        n = len(l)
                        if n <= 1:
                            return 0.0
                        m = safe_mean(l)
                        return (sum((x - m) ** 2 for x in l) / (n - 1)) ** 0.5 / n ** 0.5
                    def iqr_interval(l):
                        if not l:
                            return (0.0, 0.0)
                        l = sorted(l)
                        n = len(l)
                        q1 = l[n // 4]
                        q3 = l[(3 * n) // 4]
                        return (q1, q3)
                    moy_minute = safe_mean(minutes_buts)
                    sem_minute = safe_sem(minutes_buts)
                    q1_minute, q3_minute = iqr_interval(minutes_buts)
                    # But récurrent par match (avec but)
                    but_recurrent = safe_mean(buts_par_match_avec_but) if buts_par_match_avec_but else 0.0
                    # Diagnostic : afficher la liste brute des buts par mi-temps
                    mt_stats = compute_mt_goals(matchs)
                    print(f"    MT1 (1-45+): Nombre moyen de buts/match = {mt_stats['mt1_moy']:.2f} | SEM = {mt_stats['mt1_sem']:.2f} | IQR = [{iqr_interval(mt_stats['mt1_list'])[0]}; {iqr_interval(mt_stats['mt1_list'])[1]}] | Liste = {mt_stats['mt1_list']}")
                    print(f"    MT2 (46-90+): Nombre moyen de buts/match = {mt_stats['mt2_moy']:.2f} | SEM = {mt_stats['mt2_sem']:.2f} | IQR = [{iqr_interval(mt_stats['mt2_list'])[0]}; {iqr_interval(mt_stats['mt2_list'])[1]}] | Liste = {mt_stats['mt2_list']}")
                    # Affichage principal demandé
                    # IQR minutes de but sous la forme [min; max]
                    if minutes_buts:
                        min_minute = int(min(minutes_buts))
                        max_minute = int(max(minutes_buts))
                        iqr_str = f"[{min_minute}; {max_minute}]"
                    else:
                        iqr_str = "[N/A]"
                    print(f"{norm_team or team} {side} {label} : {recurrence}% ({total_buts} buts sur {total} matches) - {buts_marques} marqués + {buts_encaisses} encaissés | But récurrent (avec but) : {but_recurrent:.2f} | Min but: {moy_minute:.1f} SEM: {sem_minute:.2f} IQR: {iqr_str}")
                else:
                    label = INTERVAL_LABELS[interval]
                    print(f"{norm_team or team} {side} {label} : N/A (Pas de données historiques pour cet intervalle)")

#!/usr/bin/env python3
"""Detecte les matches live depuis la page principale de SoccerStats et propose un monitor simple.

Usage:
  - Lister les matches live: `python3 soccerstats_live_selector.py`
  - Monitorer un match: `python3 soccerstats_live_selector.py --monitor <match_url>`

Notes:
  - Heuristique: cherche les liens contenant "match" et un texte voisin contenant "min" ou "'" ou "live".
  - Pour un affichage exact des équipes/score, le script utilise `SoccerStatsLiveScraper.scrape_match` (import local).
"""


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
    # Synchronisation dynamique avec la base de données
    import sqlite3
    try:
        conn = sqlite3.connect("/workspaces/paris-live/football-live-prediction/data/predictions.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT league FROM soccerstats_scraped_matches ORDER BY league;")
        LEAGUES_TO_FOLLOW = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"[WARN] Impossible de charger la liste des ligues depuis la base : {e}")
        LEAGUES_TO_FOLLOW = []

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
            minute_str = None
            for font in tr.find_all("font", attrs={"color": True}):
                ft = font.get_text(" ", strip=True)
                m = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*('|min)", ft)
                if m:
                    val = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)
                    if 0 < val <= 130:
                        minute = val
                        minute_str = ft
                        break
            if minute is None:
                # Exclure les lignes qui contiennent une date ou une heure future (ex: '14 Dec', '11:30')
                if re.search(r"\b(\d{1,2}:\d{2}|\d{1,2} [A-Za-z]{3})\b", row_text):
                    continue
                row_snippet = row_text[:150]
                m2 = re.search(r"(\d{1,3})(?:\+(\d{1,3}))?\s*('|min)", row_snippet)
                if m2:
                    val = int(m2.group(1)) + (int(m2.group(2)) if m2.group(2) else 0)
                    if 0 < val <= 130:
                        minute = val
                        minute_str = m2.group(0)

            # collect all pmatch links in this row
            anchors = [a for a in tr.find_all("a", href=True) if "pmatch" in a["href"] or "pmatch.asp" in a["href"] or "pmatch" in a.get_text("")]

            # On ne garde que les vrais lives : minute détectée, >0, pas de date/heure future dans la ligne ou le snippet
            if minute is not None and minute > 0:
                # Exclure si une date (ex: 'Dec', 'Jan', 'Feb', etc.) ou une heure (ex: '11:30') est présente dans le row_text ou le snippet
                if re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", row_text, re.I):
                    continue
                if re.search(r"\b\d{1,2}:\d{2}\b", row_text):
                    continue
                if anchors:
                    for a in anchors:
                        href = urljoin(index_url, a["href"])
                        m_lid = re.search(r"league=([a-zA-Z0-9]+)", href)
                        league_id = m_lid.group(1) if m_lid else None
                        if league_id not in LEAGUES_TO_FOLLOW:
                            continue
                        atext = a.get_text(" ", strip=True)
                        # Exclure aussi si le snippet contient une date ou une heure
                        if re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", atext, re.I):
                            continue
                        if re.search(r"\b\d{1,2}:\d{2}\b", atext):
                            continue
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
    p.add_argument("--all-live-details", action='store_true', help="Affiche toutes les stats détaillées pour chaque match live détecté")
    args = p.parse_args()

    if args.monitor:
        monitor_match(args.monitor, interval=args.interval)
    elif args.all_live_details:
        if SoccerStatsLiveScraper is None:
            print("SoccerStatsLiveScraper non disponible. Placez ce fichier à la racine du projet ou installez le module.")
        else:
            lives = get_live_matches(args.url, debug=args.debug)
            if not lives:
                print("Aucun match live détecté depuis la page principale.")
            else:
                print("\nDétails complets pour tous les matches live détectés :\n")
                scraper = SoccerStatsLiveScraper()
                from scoring_detaille import scoring_detaille
                from scoring_utils import get_pattern_score, get_saturation_score, compute_momentum
                # Historique in-play pour momentum (clé: match_url)
                stats_history = {}
                for m in lives:
                    # ...existing code...
                    try:
                        data = scraper.scrape_match(m['url'])
                        if data:
                            d = data.to_dict() if hasattr(data, "to_dict") else data
                            # ...calcul patterns historiques, mt_stats_home, mt_stats_away...
                            # Calcul du score live (buts marqués dans l'intervalle en cours)
                            score_live = d['score_home'] + d['score_away']
                            # Moyenne attendue = moyenne des buts MT1 ou MT2 selon la période (moyenne des deux équipes)
                            if interval == (31, 45):
                                moyenne_attendue = (mt_stats_home['mt1_moy'] + mt_stats_away['mt1_moy']) / 2
                            else:
                                moyenne_attendue = (mt_stats_home['mt2_moy'] + mt_stats_away['mt2_moy']) / 2
                    except Exception as e:
                        print(f"  ❌ Erreur lors de l'extraction : {e}")
                    print("\n================ LIVE MATCH =================")
                    league = m['url'].split('league=')[1].split('&')[0] if 'league=' in m['url'] else 'france'
                    try:
                        data = scraper.scrape_match(m['url'])
                        if data:
                            d = data.to_dict() if hasattr(data, "to_dict") else data
                            print(f"URL : {m['url']} | minute : {d.get('minute')} | {d['home_team']} {d['score_home']} – {d['score_away']} {d['away_team']}")
                            print("--- PATTERNS HISTORIQUES ---")
                            # Affichage harmonisé patterns historiques
                            from scoring_utils import get_pattern_score
                            interval = (31, 45) if d['minute'] <= 45 else (75, 120)
                            def get_but_stats(league, team, side, interval):
                                import sqlite3, json
                                conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                                cursor = conn.cursor()
                                cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, team))
                                matchs = cursor.fetchall()
                                conn.close()
                                buts_marques, buts_encaisses, minutes_buts = 0, 0, []
                                buts_mt1, buts_mt2 = 0, 0
                                for goal_times, goal_times_conceded, is_home in matchs:
                                    if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                                        continue
                                    try:
                                        goals = json.loads(goal_times) if goal_times else []
                                        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                                    except Exception:
                                        goals, conceded = [], []
                                    start, end = interval
                                    buts_marques += sum(1 for m in goals if start <= m <= end)
                                    buts_encaisses += sum(1 for m in conceded if start <= m <= end)
                                    minutes_buts += [m for m in goals if start <= m <= end]
                                    minutes_buts += [m for m in conceded if start <= m <= end]
                                    buts_mt1 += sum(1 for m in goals if m <= 45) + sum(1 for m in conceded if m <= 45)
                                    buts_mt2 += sum(1 for m in goals if m > 45) + sum(1 for m in conceded if m > 45)
                                return buts_marques, buts_encaisses, len(matchs), minutes_buts, buts_mt1, buts_mt2
                            bm_home, be_home, total_home, min_home, bm_mt1_home, bm_mt2_home = get_but_stats(league, d['home_team'], 'HOME', interval)
                            bm_away, be_away, total_away, min_away, bm_mt1_away, bm_mt2_away = get_but_stats(league, d['away_team'], 'AWAY', interval)
                            pattern_home = get_pattern_score(league, d['home_team'], 'HOME', interval)
                            pattern_away = get_pattern_score(league, d['away_team'], 'AWAY', interval)
                            proba_but = 1 - (1 - pattern_home) * (1 - pattern_away)
                            INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }
                            label = INTERVAL_LABELS[interval]
                            # Utiliser compute_mt_goals pour stats MT1/MT2
                            # Utilisation directe de la fonction locale compute_mt_goals
                            matchs_home = []
                            matchs_away = []
                            import sqlite3
                            conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['home_team']))
                            matchs_home = [m for m in cursor.fetchall() if m[2]]
                            cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['away_team']))
                            matchs_away = [m for m in cursor.fetchall() if not m[2]]
                            conn.close()
                            mt_stats_home = compute_mt_goals(matchs_home)
                            mt_stats_away = compute_mt_goals(matchs_away)
                            # Affichage minute moyenne de but, SEM, IQR dans l'intervalle d'intérêt
                            def minute_stats(matchs, interval):
                                minutes_buts = []
                                import json
                                for goal_times, goal_times_conceded, is_home in matchs:
                                    try:
                                        goals = json.loads(goal_times) if goal_times else []
                                        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                                    except Exception:
                                        goals, conceded = [], []
                                    start, end = interval
                                    minutes_buts += [m for m in goals if start <= m <= end]
                                    minutes_buts += [m for m in conceded if start <= m <= end]
                                def safe_mean(l):
                                    return sum(l)/len(l) if l else 0.0
                                def safe_sem(l):
                                    n = len(l)
                                    if n <= 1:
                                        return 0.0
                                    m = safe_mean(l)
                                    return (sum((x - m) ** 2 for x in l) / (n - 1)) ** 0.5 / n ** 0.5
                                def safe_iqr(l):
                                    if not l:
                                        return 0.0
                                    l = sorted(l)
                                    n = len(l)
                                    q1 = l[n // 4]
                                    q3 = l[(3 * n) // 4]
                                    return q3 - q1
                                return safe_mean(minutes_buts), safe_sem(minutes_buts), safe_iqr(minutes_buts)
                            moy_min_home, sem_min_home, iqr_min_home = minute_stats(matchs_home, interval)
                            moy_min_away, sem_min_away, iqr_min_away = minute_stats(matchs_away, interval)
                            # Calculs pour affichage formaté
                            def pattern_resume(team, side, label, pattern, matchs, mt_stats, moy_min, sem_min, interval):
                                # Buts dans l'intervalle
                                buts_marques = 0
                                buts_encaisses = 0
                                minutes_buts = []
                                import json
                                start, end = interval
                                for goal_times, goal_times_conceded, is_home in matchs:
                                    try:
                                        goals = json.loads(goal_times) if goal_times else []
                                        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                                    except Exception:
                                        goals, conceded = [], []
                                    minutes_buts += [m for m in goals if start <= m <= end]
                                    minutes_buts += [m for m in conceded if start <= m <= end]
                                    buts_marques += sum(1 for m in goals if start <= m <= end)
                                    buts_encaisses += sum(1 for m in conceded if start <= m <= end)
                                total_buts = buts_marques + buts_encaisses
                                n_matchs = len(matchs)
                                recurrence = pattern * 100
                                # But récurrent par match (avec but)
                                buts_par_match_avec_but = []
                                for goal_times, goal_times_conceded, is_home in matchs:
                                    try:
                                        goals = json.loads(goal_times) if goal_times else []
                                        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                                    except Exception:
                                        goals, conceded = [], []
                                    buts_dans_intervalle = [m for m in goals if start <= m <= end] + [m for m in conceded if start <= m <= end]
                                    if len(buts_dans_intervalle) > 0:
                                        buts_par_match_avec_but.append(len(buts_dans_intervalle))
                                but_recurrent = sum(buts_par_match_avec_but)/len(buts_par_match_avec_but) if buts_par_match_avec_but else 0.0
                                # IQR minutes de but sous la forme [min; max]
                                if minutes_buts:
                                    min_minute = int(min(minutes_buts))
                                    max_minute = int(max(minutes_buts))
                                    iqr_str = f"[{min_minute}; {max_minute}]"
                                else:
                                    iqr_str = "[N/A]"
                                # Affichage MT1/MT2 avec SEM uniquement
                                mt1 = f"Moyenne buts MT1: {mt_stats['mt1_moy']:.2f} SEM: {mt_stats['mt1_sem']:.2f}"
                                mt2 = f"MT2: {mt_stats['mt2_moy']:.2f} SEM: {mt_stats['mt2_sem']:.2f}"
                                return f"{team} {side} {label} : {recurrence:.1f}% ({total_buts} buts sur {n_matchs} matches) - {buts_marques} marqués + {buts_encaisses} encaissés | But récurrent (avec but) : {but_recurrent:.2f} | Min but: {moy_min:.1f} SEM: {sem_min:.2f} IQR: {iqr_str}\n  {mt1} | {mt2}"
                            print(pattern_resume(d['home_team'], 'HOME', label, pattern_home, matchs_home, mt_stats_home, moy_min_home, sem_min_home, interval))
                            print(pattern_resume(d['away_team'], 'AWAY', label, pattern_away, matchs_away, mt_stats_away, moy_min_away, sem_min_away, interval))
                            print(f"[Proba au moins un but dans l'intervalle] : {proba_but*100:.1f}%")
                            print("--- STATISTIQUES IN-PLAY ---")
                            print(f"  Possession : {d['possession_home']}% / {d['possession_away']}%")
                            print(f"  Total tirs : {d['shots_home']} / {d['shots_away']}")
                            print(f"  Tirs cadrés : {d['shots_on_target_home']} / {d['shots_on_target_away']}")
                            print(f"  Attaques : {d['attacks_home']} / {d['attacks_away']}")
                            print(f"  Attaques dangereuses : {d['dangerous_attacks_home']} / {d['dangerous_attacks_away']}")
                            # Scoring détaillé
                            print(f"\n--- SCORING DÉTAILLÉ ---")
                            pattern_score = max(pattern_home, pattern_away)
                            if pattern_home >= pattern_away:
                                pattern_team = d['home_team']
                                pattern_side = 'HOME'
                            else:
                                pattern_team = d['away_team']
                                pattern_side = 'AWAY'
                            goals_scored = d['score_home']
                            mi_temps = 'mt1' if d['minute'] <= 45 else 'mt2'
                            saturation_score = get_saturation_score(league, d['home_team'], goals_scored, interval, mi_temps)
                            # Stats live pour chaque équipe (A = home, B = away)
                            stats_a = {
                                'possession': d['possession_home'] or 50,
                                'shots': d['shots_home'],
                                'shots_on_target': d['shots_on_target_home'],
                                'attacks': d['attacks_home'],
                                'dangerous_attacks': d['dangerous_attacks_home'],
                                'corners': d.get('corners_home', 0)
                            }
                            stats_b = {
                                'possession': d['possession_away'] or 50,
                                'shots': d['shots_away'],
                                'shots_on_target': d['shots_on_target_away'],
                                'attacks': d['attacks_away'],
                                'dangerous_attacks': d['dangerous_attacks_away'],
                                'corners': d.get('corners_away', 0)
                            }
                            # Inplay stats pour scoring_detaille (A = équipe analysée, B = adversaire)
                            def safe_ratio(a, b):
                                return a / (a + b) if (a + b) > 0 else 0.5
                            inplay_stats = {
                                'possession': safe_ratio(d['possession_home'], d['possession_away']),
                                'tirs': safe_ratio(d['shots_home'], d['shots_away']),
                                'tirs_cadres': safe_ratio(d['shots_on_target_home'], d['shots_on_target_away']),
                                'attaques': safe_ratio(d['attacks_home'], d['attacks_away']),
                                'attaques_dangereuses': safe_ratio(d['dangerous_attacks_home'], d['dangerous_attacks_away']),
                                'opponent': {
                                    'possession': d['possession_away'],
                                    'tirs': d['shots_away'],
                                    'tirs_cadres': d['shots_on_target_away'],
                                    'attaques': d['attacks_away'],
                                    'attaques_dangereuses': d['dangerous_attacks_away'],
                                },
                                'score_live': score_live,
                                'moyenne_attendue': moyenne_attendue,
                                # Valeurs brutes pour scoring_detaille
                                'raw_possession_a': d['possession_home'],
                                'raw_possession_b': d['possession_away'],
                                'raw_tirs_a': d['shots_home'],
                                'raw_tirs_b': d['shots_away'],
                                'raw_tirs_cadres_a': d['shots_on_target_home'],
                                'raw_tirs_cadres_b': d['shots_on_target_away'],
                                'raw_attaques_a': d['attacks_home'],
                                'raw_attaques_b': d['attacks_away'],
                                'raw_attaques_dangereuses_a': d['dangerous_attacks_home'],
                                'raw_attaques_dangereuses_b': d['dangerous_attacks_away'],
                            }
                            red_cards = {'home': d.get('red_cards_home', 0), 'away': d.get('red_cards_away', 0)}
                            corners = {'home': d.get('corners_home', 0), 'away': d.get('corners_away', 0)}
                            url_key = m['url']
                            if url_key not in stats_history:
                                stats_history[url_key] = []
                            stats_history[url_key].append({
                                'tirs': d['shots_home'] + d['shots_away'],
                                'attaques': d['attacks_home'] + d['attacks_away'],
                                'attaques_dangereuses': d['dangerous_attacks_home'] + d['dangerous_attacks_away'],
                                'corners': d['corners_home'] + d['corners_away']
                            })
                            momentum_5min = compute_momentum(stats_history[url_key], window=5)
                            momentum_2min = compute_momentum(stats_history[url_key], window=2)
                            print(f"[Pattern utilisé] : {pattern_team} ({pattern_side})")
                            scoring_detaille(
                                pattern_score=pattern_score,
                                saturation_score=saturation_score,
                                inplay_stats=inplay_stats,
                                red_cards=red_cards,
                                corners=corners,
                                momentum_5min=momentum_5min,
                                momentum_2min=momentum_2min,
                                debug=True
                            )
                            print("\n==========================================\n")
                        else:
                            print("  ❌ Impossible d'extraire les stats détaillées pour ce match.")
                    except Exception as e:
                        print(f"  ❌ Erreur lors de l'extraction : {e}")
    else:
        lives = get_live_matches(args.url, debug=args.debug)
        if not lives:
            print("Aucun match live détecté depuis la page principale.")
        else:
            print("Matches live détectés:")
            from scoring_utils import get_pattern_score
            for m in lives:
                # Filtrage supplémentaire : exclure tout match dont le snippet contient une date future
                snippet = m.get('snippet','')
                if re.search(r"\b(Sun|Mon|Tue|Wed|Thu|Fri|Sat|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", snippet, re.I):
                    continue
                print(f"- {m['url']} | minute: {m.get('minute')} | snippet: {snippet[:120]}")
                # Extraction des vrais noms d'équipes via scraping live si possible
                league = m['url'].split('league=')[1].split('&')[0] if 'league=' in m['url'] else 'france'
                home_team, away_team = None, None
                try:
                    if SoccerStatsLiveScraper is not None:
                        scraper = SoccerStatsLiveScraper()
                        data = scraper.scrape_match(m['url'])
                        if data:
                            d = data.to_dict() if hasattr(data, "to_dict") else data
                            home_team, away_team = d.get('home_team'), d.get('away_team')
                except Exception:
                    pass
                # Fallback parsing si scraping non disponible ou noms non extraits
                if not home_team or not away_team:
                    if ' vs ' in snippet:
                        home_team, away_team = snippet.split(' vs ')[0].strip(), snippet.split(' vs ')[1].split()[0].strip()
                    elif ' - ' in snippet:
                        home_team, away_team = snippet.split(' - ')[0].strip(), snippet.split(' - ')[1].split()[0].strip()
                    else:
                        parts = snippet.split()
                        if len(parts) >= 2:
                            home_team, away_team = parts[0], parts[-1]
                if home_team and away_team:
                    INTERVALS = [(31, 45), (75, 120)]
                    INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }
                    minute = m.get('minute')
                    interval = (31, 45) if minute and minute <= 45 else (75, 120)
                    # Patterns historiques
                    # Extraction du nombre de buts marqués/encaissés pour chaque équipe
                    import sqlite3, json
                    def get_but_stats(league, team, side, interval):
                        conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, team))
                        matchs = cursor.fetchall()
                        conn.close()
                        buts_marques, buts_encaisses = 0, 0
                        for goal_times, goal_times_conceded, is_home in matchs:
                            if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                                continue
                            try:
                                goals = json.loads(goal_times) if goal_times else []
                                conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                            except Exception:
                                goals, conceded = [], []
                            start, end = interval
                            buts_marques += sum(1 for m in goals if start <= m <= end)
                            buts_encaisses += sum(1 for m in conceded if start <= m <= end)
                        return buts_marques, buts_encaisses, buts_marques + buts_encaisses
                    def get_but_stats_and_total(league, team, side, interval):
                        conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, team))
                        matchs = cursor.fetchall()
                        conn.close()
                        buts_marques, buts_encaisses = 0, 0
                        total_matches = 0
                        for goal_times, goal_times_conceded, is_home in matchs:
                            if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                                continue
                            total_matches += 1
                            try:
                                goals = json.loads(goal_times) if goal_times else []
                                conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                            except Exception:
                                goals, conceded = [], []
                            start, end = interval
                            buts_marques += sum(1 for m in goals if start <= m <= end)
                            buts_encaisses += sum(1 for m in conceded if start <= m <= end)
                        return buts_marques, buts_encaisses, buts_marques + buts_encaisses, total_matches
                    bm_home, be_home, bt_home, tm_home = get_but_stats_and_total(league, home_team, 'HOME', interval)
                    bm_away, be_away, bt_away, tm_away = get_but_stats_and_total(league, away_team, 'AWAY', interval)
                    pattern_home = get_pattern_score(league, home_team, 'HOME', interval)
                    pattern_away = get_pattern_score(league, away_team, 'AWAY', interval)
                    proba_but = 1 - (1 - pattern_home) * (1 - pattern_away)
                    print(f"[Pattern historique] {home_team} (HOME) : {pattern_home*100:.1f}% ({bt_home}/{tm_home} buts : {bm_home} marqués, {be_home} encaissés)")
                    print(f"[Pattern historique] {away_team} (AWAY) : {pattern_away*100:.1f}% ({bt_away}/{tm_away} buts : {bm_away} marqués, {be_away} encaissés)")
                    print(f"[Proba au moins un but dans l'intervalle] : {proba_but*100:.1f}%")
                    # Extraction minute moyenne/SEM/IQR
                    # On réutilise la logique de print_full_patterns mais en résumé
                    import sqlite3, json
                    conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                    cursor = conn.cursor()
                    for team, side in [(home_team, 'HOME'), (away_team, 'AWAY')]:
                        cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, team))
                        matchs = cursor.fetchall()
                        minutes_buts = []
                        for goal_times, goal_times_conceded, is_home in matchs:
                            if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
                                continue
                            try:
                                goals = json.loads(goal_times) if goal_times else []
                                conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                            except Exception:
                                goals, conceded = [], []
                            start, end = interval
                            minutes_buts += [m for m in goals if start <= m <= end]
                            minutes_buts += [m for m in conceded if start <= m <= end]
                        def safe_mean(l):
                            return sum(l)/len(l) if l else 0.0
                        def sem(data):
                            n = len(data)
                            if n <= 1:
                                return 0.0
                            m = sum(data) / n
                            return (sum((x - m) ** 2 for x in data) / (n - 1)) ** 0.5 / n ** 0.5
                        def iqr_interval(data):
                            if not data:
                                return None, None
                            data = sorted(data)
                            n = len(data)
                            q1 = data[n // 4] if n >= 4 else None
                            q3 = data[(3 * n) // 4] if n >= 4 else None
                            return q1, q3
                        moy_minute = safe_mean(minutes_buts) if minutes_buts else None
                        sem_minute = sem(minutes_buts) if minutes_buts and len(minutes_buts) > 1 else None
                        q1, q3 = iqr_interval(minutes_buts)
                        iqr_str = f"[{q1},{q3}]" if q1 is not None and q3 is not None else "N/A"
                        sem_str = f"{sem_minute:.2f}" if sem_minute is not None else "N/A"
                        moy_str = f"{moy_minute:.1f}" if moy_minute is not None else "N/A"
                        print(f"{team} {side} {INTERVAL_LABELS[interval]} | Min moy: {moy_str} SEM: {sem_str} IQR: {iqr_str}")
                    conn.close()
