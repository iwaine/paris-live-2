
DEFAULT_URL = "https://www.soccerstats.com/"

try:
    from soccerstats_live_scraper import SoccerStatsLiveScraper
except Exception:
    SoccerStatsLiveScraper = None

import requests
UA = {"User-Agent": "paris-live-bot/1.0 (Match Detection)"}
from bs4 import BeautifulSoup
import re

def parse_minute(text: str) -> int:
    if not text:
        return None
    # Détecte les formats : 90'+2, 90'+2min, 90+2', 90+2min, etc.
    m = re.search(r"(\d{1,3})[' ]*\+(\d{1,3})\s*(?:'|min)?", text)
    if m:
        base = int(m.group(1))
        extra = int(m.group(2)) if m.group(2) else 0
        return base + extra
    # Ancien format : 90' ou 90min
    m2 = re.search(r"(\d{1,3})\s*(?:'|min)", text)
    if m2:
        return int(m2.group(1))
    return None
UA = {"User-Agent": "paris-live-bot/1.0 (Match Detection)"}
def compute_mt_goals(matchs):
    mt1_buts_list = []
    mt2_buts_list = []
    for goal_times, goal_times_conceded, is_home in matchs:
        try:
            goals = json.loads(goal_times) if goal_times else []
            conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
        except Exception:
            goals, conceded = [], []
        mt1_buts = sum(1 for m in goals if 1 <= m <= 45) + sum(1 for m in conceded if 1 <= m <= 45)
        mt2_buts = sum(1 for m in goals if 46 <= m <= 90) + sum(1 for m in conceded if 46 <= m <= 90)
        mt1_buts_list.append(mt1_buts)
        mt2_buts_list.append(mt2_buts)
    mt1_moy = sum(mt1_buts_list) / len(mt1_buts_list) if mt1_buts_list else 0.0
    mt2_moy = sum(mt2_buts_list) / len(mt2_buts_list) if mt2_buts_list else 0.0
    return {'mt1_moy': mt1_moy, 'mt2_moy': mt2_moy}

def get_live_matches(index_url: str = DEFAULT_URL, timeout: int = 10, debug: bool = False) -> list:
    r = requests.get(index_url, headers=UA, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    btable = soup.find("table", id="btable")
    if btable is not None:
        for tr in btable.find_all("tr"):
            row_text = tr.get_text(" ", strip=True)
            if not row_text:
                continue
            minute = None
            nearby_text = row_text
            for font in tr.find_all("font", attrs={"color": True}):
                if font.get("color") in ["red", "#FF0000"]:
                    minute = parse_minute(font.text)
                    break
            if minute is None:
                minute = parse_minute(row_text)
            if minute is not None or re.search(r"\b(live|in-play)\b", nearby_text, re.I):
                href = None
                for a in tr.find_all("a", href=True):
                    href = urljoin(index_url, a["href"])
                    break
                if href:
                    results.append({"url": href, "minute": minute, "snippet": nearby_text})
    results.sort(key=lambda x: x.get("minute") if x.get("minute") is not None else -1, reverse=True)
    return results

def monitor_match(url: str, interval: int = 10):
    pass

"""
METHODOLOGIE D'EXTRACTION ET D'AFFICHAGE DES MATCHES LIVE
=========================================================

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

Ce script est le workflow principal pour la détection et l'analyse des matches live SoccerStats.

Principes méthodologiques :
- Extraction robuste de la minute :
	- Recherche la minute dans les balises <font color=...> de chaque ligne de match.
	- Utilise la première valeur trouvée (améliorable, voir script de test dédié).
	- Exclut les lignes contenant des dates/heures futures.
- Affichage enrichi :
	- Utilisation de codes couleurs ANSI pour la lisibilité terminal.
	- Affichage détaillé des patterns historiques, stats MT1/MT2, récurrence récente, etc.
	- Calcul de probabilités combinées (historique, domination live, saturation).
- Modularité :
	- Les fonctions critiques (extraction, scoring, patterns) sont isolées pour faciliter la maintenance.
	- Un script de test séparé permet de valider/améliorer la robustesse de l'extraction de la minute (voir test_extract_minute_robuste.py).

Pour toute modification de la logique d'extraction, valider d'abord dans le script de test avant d'intégrer ici.
"""


# --- Ajout de la logique d'affichage unique ---
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
			matches_exploitables = []
			scraper = SoccerStatsLiveScraper()
			from scoring_detaille import scoring_detaille
			from scoring_utils import get_pattern_score, get_saturation_score, compute_momentum
			stats_history = {}
			for m in lives:
				try:
					data = scraper.scrape_match(m['url'])
					if data:
						d = data.to_dict() if hasattr(data, "to_dict") else data
						minute_num = d.get('minute', 0)
						minute_raw = d.get('minute_raw', str(minute_num)) if 'minute_raw' in d else str(minute_num)
						if not is_in_interval(minute_raw, minute_num):
							continue
						matches_exploitables.append((m, d, minute_raw, minute_num))
				except Exception:
					continue
			if not matches_exploitables:
				print("Aucun match live détecté pour le moment.")
			else:
				print("\nDétails complets pour tous les matches live détectés :\n")
				for m, d, minute_raw, minute_num in matches_exploitables:
					# ...affichage détaillé comme avant...
					interval = (31, 45) if minute_raw.strip().upper() == "HT" or (is_in_interval(minute_raw, minute_num) and ("45'" in minute_raw or "45+" in minute_raw or (31 <= minute_num <= 45))) else (75, 90)
					league = m['url'].split('league=')[1].split('&')[0] if 'league=' in m['url'] else 'france'
					import sqlite3
                    import os
                    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'predictions.db'))
					cursor = conn.cursor()
					cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['home_team']))
					matchs_home = [mm for mm in cursor.fetchall() if mm[2]]
					cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['away_team']))
					matchs_away = [mm for mm in cursor.fetchall() if not mm[2]]
					conn.close()
					mt_stats_home = compute_mt_goals(matchs_home)
					mt_stats_away = compute_mt_goals(matchs_away)
					if interval == (31, 45):
						moyenne_attendue = (mt_stats_home['mt1_moy'] + mt_stats_away['mt1_moy']) / 2
					else:
						moyenne_attendue = (mt_stats_home['mt2_moy'] + mt_stats_away['mt2_moy']) / 2
					print("\n================ LIVE MATCH =================")
					if minute_raw.strip().upper() == "HT":
						print(f"URL : {m['url']} | minute : HT (mi-temps) | {d['home_team']} {d['score_home']} – {d['score_away']} {d['away_team']}")
					else:
						print(f"URL : {m['url']} | minute : {minute_raw} | {d['home_team']} {d['score_home']} – {d['score_away']} {d['away_team']}")
					print("--- PATTERNS HISTORIQUES ---")
					# ...suite de l'affichage détaillé...
def is_in_interval(minute_raw, minute_num):
	"""
	Détermine si la minute (brute et formatée) est dans l'intervalle d'intérêt.
	minute_raw : chaîne telle que 'HT', 'FT', '45'+1', '90'+2', '48', etc.
	minute_num : entier (ex : 48)
	"""
	if isinstance(minute_raw, str):
		if minute_raw.strip().upper() == "FT":
			return False  # Exclure FT
		if minute_raw.strip().upper() == "HT":
			return True  # Inclure HT dans 31-45+
		if "45'" in minute_raw or "45+" in minute_raw:
			return True  # temps additionnel MT1
		if "90'" in minute_raw or "90+" in minute_raw:
			return True  # temps additionnel MT2
	if 31 <= minute_num <= 45:
		return True
	if 75 <= minute_num <= 90:
		return True
	return False
# Imports globaux
import sqlite3, json

# Fonction pour calculer la récurrence récente (n derniers matchs)
def get_recent_pattern_score(league, team, side, interval, n_last=5):
    conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, team))
    matchs = cursor.fetchall()
    conn.close()
    # Filtrer selon le côté
    if side == "HOME":
        matchs = [m for m in matchs if m[2]]
    else:
        matchs = [m for m in matchs if not m[2]]
    matchs = matchs[-n_last:] if len(matchs) >= n_last else matchs
    total = len(matchs)
    avec_but = 0
    for goal_times, goal_times_conceded, is_home in matchs:
        try:
            goals = json.loads(goal_times) if goal_times else []
            conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
        except Exception:
            goals, conceded = [], []
        start, end = interval
        buts = sum(1 for m in goals if start <= m <= end) + sum(1 for m in conceded if start <= m <= end)
        if buts > 0:
            avec_but += 1
    return (avec_but / total) if total else 0.0
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
    conn = __import__('sqlite3').connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
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

            # On ne garde que les vrais lives : minute détectée, >0, pas de date/heure future, pas FT/HT
            if minute is not None and minute > 0:
                # Exclure FT et HT (matches terminés ou à la mi-temps)
                if minute_str and minute_str.strip().upper() in ["FT", "HT"]:
                    continue
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
                        # Exclure FT et HT dans le texte associé
                        if atext.strip().upper() in ["FT", "HT"]:
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
                            # Exclure FT et HT dans le texte associé
                            if teams_text.strip().upper() in ["FT", "HT"]:
                                continue
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
                            # Exclure FT et HT dans le texte associé
                            if teams_text.strip().upper() in ["FT", "HT"]:
                                continue
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
                # Intervalles d'intérêt ajustés pour inclure les arrêts de jeu
                for m in lives:
                    try:
                        data = scraper.scrape_match(m['url'])
                        if data:
                            d = data.to_dict() if hasattr(data, "to_dict") else data
                            minute_num = d.get('minute', 0)
                            minute_raw = d.get('minute_raw', str(minute_num)) if 'minute_raw' in d else str(minute_num)
                            # Filtrage intelligent sur les intervalles d'intérêt
                            if not is_in_interval(minute_raw, minute_num):
                                continue  # On saute ce match
                            # Détermination de l'intervalle avant usage
                            if minute_raw.strip().upper() == "HT" or (is_in_interval(minute_raw, minute_num) and ("45'" in minute_raw or "45+" in minute_raw or (31 <= minute_num <= 45))):
                                interval = (31, 45)
                            else:
                                interval = (75, 90)
                            league = m['url'].split('league=')[1].split('&')[0] if 'league=' in m['url'] else 'france'
                            import sqlite3
                            conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['home_team']))
                            matchs_home = [mm for mm in cursor.fetchall() if mm[2]]
                            cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['away_team']))
                            matchs_away = [mm for mm in cursor.fetchall() if not mm[2]]
                            conn.close()
                            mt_stats_home = compute_mt_goals(matchs_home)
                            mt_stats_away = compute_mt_goals(matchs_away)
                            if interval == (31, 45):
                                moyenne_attendue = (mt_stats_home['mt1_moy'] + mt_stats_away['mt1_moy']) / 2
                            else:
                                moyenne_attendue = (mt_stats_home['mt2_moy'] + mt_stats_away['mt2_moy']) / 2
                            print("\n================ LIVE MATCH =================")
                            if minute_raw.strip().upper() == "HT":
                                print(f"URL : {m['url']} | minute : HT (mi-temps) | {d['home_team']} {d['score_home']} – {d['score_away']} {d['away_team']}")
                            else:
                                print(f"URL : {m['url']} | minute : {minute_raw} | {d['home_team']} {d['score_home']} – {d['score_away']} {d['away_team']}")
                            print("--- PATTERNS HISTORIQUES ---")
                            # ...suite de l'affichage détaillé...
                    except Exception as e:
                        print(f"  ❌ Erreur lors de l'extraction : {e}")
                    import argparse
                    import sys

                    def main():
                        parser = argparse.ArgumentParser(description="SoccerStats Live Selector")
                        parser.add_argument('--all-live-details', action='store_true', help='Afficher tous les détails des matchs en direct')
                        # Ajoutez ici d'autres options si besoin
                        args = parser.parse_args()

                        if args.all_live_details:
                            # Exemple d'utilisation d'une fonction utilitaire (à adapter selon la logique métier)
                            print("[INFO] Option --all-live-details activée.")
                            # Ici, vous pouvez appeler une fonction utilitaire, par exemple :
                            # result = get_all_live_details()  # À implémenter selon vos besoins
                            # print(result)
                            print("(Simulation) Détails des matchs en direct affichés.")
                        else:
                            print("Aucune option reconnue. Utilisez --help pour voir les options disponibles.")

                    if __name__ == "__main__":
                        main()
                    try:
                        data = scraper.scrape_match(m['url'])
                        if data:
                            d = data.to_dict() if hasattr(data, "to_dict") else data
                            # Détermination de l'intervalle avant usage
                            interval = (31, 45) if d.get('minute', 0) <= 45 else (75, 120)
                            # ...calcul patterns historiques, mt_stats_home, mt_stats_away...
                            # Calcul du score live (buts marqués dans l'intervalle en cours)
                            score_live = d['score_home'] + d['score_away']
                            # Utilisation des stats MT1/MT2 pour la moyenne attendue
                            # On récupère les matchs home/away pour chaque équipe
                            league = m['url'].split('league=')[1].split('&')[0] if 'league=' in m['url'] else 'france'
                            import sqlite3
                            conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['home_team']))
                            matchs_home = [mm for mm in cursor.fetchall() if mm[2]]
                            cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, d['away_team']))
                            matchs_away = [mm for mm in cursor.fetchall() if not mm[2]]
                            conn.close()
                            mt_stats_home = compute_mt_goals(matchs_home)
                            mt_stats_away = compute_mt_goals(matchs_away)
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
                            # Calcul récurrence récente avant affichage
                            recent_home = get_recent_pattern_score(league, d['home_team'], 'HOME', interval)
                            recent_away = get_recent_pattern_score(league, d['away_team'], 'AWAY', interval)
                            def pattern_details(team, side, label, pattern, matchs, mt_stats, moy_min, sem_min, interval, recent_score):
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
                                recent = recent_score * 100
                                score_combine = (recurrence + recent) / 2
                                return (
                                    f"→ Récurrence globale : {recurrence:.1f}% ({total_buts} buts sur {n_matchs} matches)- {buts_marques} marqués + {buts_encaisses} encaissés\n"
                                    f"    → Meilleure récurrence récente : {recent:.0f}% ({buts_marques} buts sur {n_matchs if n_matchs < 5 else 5} derniers matches)- {buts_marques} marqués + {buts_encaisses} encaissés\n"
                                    f"    → Score combiné (moyenne) : {score_combine:.0f}\n"
                                )
                            def pattern_full_block(team, side, label, pattern, matchs, mt_stats, moy_min, sem_min, interval, recent_score):
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
                                mt1 = f"Moyenne buts MT1: {mt_stats['mt1_moy']:.2f} SEM: {mt_stats['mt1_sem']:.2f}"
                                mt2 = f"MT2: {mt_stats['mt2_moy']:.2f} SEM: {mt_stats['mt2_sem']:.2f}"
                                recent = recent_score * 100
                                score_combine = (recurrence + recent) / 2
                                # Calcul détails récurrence récente
                                # On prend les n derniers matchs
                                n_last = 5
                                matchs_recent = matchs[-n_last:] if len(matchs) >= n_last else matchs
                                buts_marques_recent = 0
                                buts_encaisses_recent = 0
                                total_buts_recent = 0
                                for goal_times, goal_times_conceded, is_home in matchs_recent:
                                    try:
                                        goals = json.loads(goal_times) if goal_times else []
                                        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                                    except Exception:
                                        goals, conceded = [], []
                                    start, end = interval
                                    buts_marques_recent += sum(1 for m in goals if start <= m <= end)
                                    buts_encaisses_recent += sum(1 for m in conceded if start <= m <= end)
                                total_buts_recent = buts_marques_recent + buts_encaisses_recent
                                n_matchs_recent = len(matchs_recent)
                                # Codes couleurs ANSI
                                YELLOW = '\033[33m'
                                CYAN = '\033[36m'
                                GREEN = '\033[32m'
                                BLUE = '\033[34m'
                                MAGENTA = '\033[35m'
                                RESET = '\033[0m'

                                return (
                                    f"{YELLOW}{team} {side} {label}{RESET} : {BLUE}{recurrence:.1f}%{RESET} ({MAGENTA}{total_buts} buts sur {n_matchs} matches{RESET}) - {GREEN}{buts_marques} marqués{RESET} + {MAGENTA}{buts_encaisses} encaissés{RESET} | But récurrent (avec but) : {BLUE}{but_recurrent:.2f}{RESET} | Min but: {MAGENTA}{moy_min:.1f}{RESET} SEM: {MAGENTA}{sem_min:.2f}{RESET} IQR: {CYAN}{iqr_str}{RESET}\n  {CYAN}{mt1}{RESET} | {CYAN}{mt2}{RESET}\n   {YELLOW}Récurrence globale{RESET} : {BLUE}{recurrence:.1f}%{RESET} ({MAGENTA}{total_buts} buts sur {n_matchs} matches{RESET}) - {GREEN}{buts_marques} marqués{RESET} + {MAGENTA}{buts_encaisses} encaissés{RESET}\n   {YELLOW}Meilleure récurrence récente{RESET}: {BLUE}{recent:.1f}%{RESET} ({MAGENTA}{total_buts_recent} buts sur {n_matchs_recent} derniers matches{RESET}) - {GREEN}{buts_marques_recent} marqués{RESET} + {MAGENTA}{buts_encaisses_recent} encaissés{RESET}\n   {YELLOW}Score combiné{RESET}: {BLUE}{score_combine:.1f}{RESET}\n"
                                )
                            print(pattern_full_block(d['home_team'], 'HOME', label, pattern_home, matchs_home, mt_stats_home, moy_min_home, sem_min_home, interval, recent_home))
                            print(pattern_full_block(d['away_team'], 'AWAY', label, pattern_away, matchs_away, mt_stats_away, moy_min_away, sem_min_away, interval, recent_away))
                            # Calcul du score de domination live (total_a, total_b)
                            # On récupère la variable total_a et total_b calculée juste après ce bloc
                            # Pour la proba combinée, on prend le score de domination de l'équipe la plus dominante
                            # (si total_a > total_b, on prend total_a, sinon total_b)
                            # On normalise le score domination entre 0.5 et 1.0 (pour éviter d'impacter trop fort)
                            domination_score = max(total_a, total_b) if 'total_a' in locals() and 'total_b' in locals() else 0.5
                            domination_score_norm = 0.5 + 0.5 * domination_score  # 0.5 à 1.0
                            # Récupération des scores de saturation calculés plus haut
                            saturation_home = locals().get('saturation_home', 1.0)
                            saturation_away = locals().get('saturation_away', 1.0)
                            saturation_moy = (saturation_home + saturation_away) / 2
                            proba_combinee = (0.8 * proba_but + 0.2 * domination_score_norm) * saturation_moy
                            print(f"[Proba au moins un but dans l'intervalle] : {proba_but*100:.1f}% (historique)")
                            print(f"[Proba combinée (80% historique + 20% domination live, pondéré par saturation moyenne)] : {proba_combinee*100:.1f}%")
                            print("[DOMINATION LIVE - DÉTAILS]")
                            # Nouveau système pondéré de domination avec gestion des valeurs manquantes
                            domination_params = [
                                ("Possession", d.get('possession_home'), d.get('possession_away'), 0.15),
                                ("Shots", d.get('shots_home'), d.get('shots_away'), 0.15),
                                ("Shots on target", d.get('shots_on_target_home'), d.get('shots_on_target_away'), 0.25),
                                ("Shots inside box", d.get('shots_inside_box_home'), d.get('shots_inside_box_away'), 0.15),
                                ("Shots outside box", d.get('shots_outside_box_home'), d.get('shots_outside_box_away'), 0.05),
                                ("Attacks", d.get('attacks_home'), d.get('attacks_away'), 0.10),
                                ("Dangerous attacks", d.get('dangerous_attacks_home'), d.get('dangerous_attacks_away'), 0.15),
                            ]
                            total_a = 0.0
                            total_b = 0.0
                            total_poids = 0.0
                            for label, a, b, poids in domination_params:
                                if a is None or b is None:
                                    print(f"{label} : N/D")
                                    continue
                                if (a + b) > 0:
                                    ratio = a / (a + b)
                                else:
                                    print(f"{label} : N/D")
                                    continue
                                contribution = ratio * poids
                                contribution_b = (1 - ratio) * poids
                                total_a += contribution
                                total_b += contribution_b
                                total_poids += poids
                                print(f"{label} : A={a} / B={b} | ratio={ratio:.3f} | poids={poids:.2f} | contribution={contribution:.3f}")
                            if total_poids > 0:
                                print(f"Total domination A : {int(round(total_a/total_poids*100))}%, domination B : {int(round(total_b/total_poids*100))}%")
                            else:
                                print("Total domination : N/D")

                            # Ajout saturation mi-temps basée sur data historiques et score live
                            from scoring_utils import get_saturation_score
                            mi_temps = 'mt1' if d['minute'] <= 45 else 'mt2'
                            # Moyenne attendue individuelle par équipe
                            if mi_temps == 'mt1':
                                moyenne_home = mt_stats_home['mt1_moy']
                                moyenne_away = mt_stats_away['mt1_moy']
                            else:
                                moyenne_home = mt_stats_home['mt2_moy']
                                moyenne_away = mt_stats_away['mt2_moy']
                            saturation_home = get_saturation_score(league, d['home_team'], d['score_home'], interval, mi_temps)
                            saturation_away = get_saturation_score(league, d['away_team'], d['score_away'], interval, mi_temps)
                            # Affichage interprétatif saturation mi-temps pour chaque équipe
                            def saturation_message(team, score_live, moyenne_attendue, saturation):
                                if score_live >= moyenne_attendue:
                                    return f"[Potentiel restant faible (score live {score_live} / attendu {moyenne_attendue:.2f}) — le nombre de buts attendus est déjà atteint, peu de potentiel pour nouveaux buts.] (saturation={saturation:.2f})"
                                else:
                                    return f"[Potentiel restant élevé (score live {score_live} / attendu {moyenne_attendue:.2f}) — il reste du potentiel pour de nouveaux buts.] (saturation={saturation:.2f})"
                            print(saturation_message(d['home_team'], d['score_home'], moyenne_home, saturation_home))
                            print(saturation_message(d['away_team'], d['score_away'], moyenne_away, saturation_away))
                            # Scoring détaillé
                            # Ajout de la récurrence récente (5 derniers matchs) dans les patterns historiques
                            # Fonction pour calculer la récurrence récente (n derniers matchs)
                            # Fonction pour calculer la récurrence récente (n derniers matchs)
                            # Fonction pour calculer la récurrence récente (n derniers matchs)
                            def get_recent_pattern_score(league, team, side, interval, n_last=5):
                                import sqlite3, json
                                conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
                                cursor = conn.cursor()
                                cursor.execute("SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches WHERE league = ? AND team = ?", (league, team))
                                matchs = cursor.fetchall()
                                conn.close()
                                # Filtrer selon le côté
                                if side == "HOME":
                                    matchs = [m for m in matchs if m[2]]
                                else:
                                    matchs = [m for m in matchs if not m[2]]
                                matchs = matchs[-n_last:] if len(matchs) >= n_last else matchs
                                total = len(matchs)
                                avec_but = 0
                                for goal_times, goal_times_conceded, is_home in matchs:
                                    try:
                                        goals = json.loads(goal_times) if goal_times else []
                                        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                                    except Exception:
                                        goals, conceded = [], []
                                    start, end = interval
                                    buts = sum(1 for m in goals if start <= m <= end) + sum(1 for m in conceded if start <= m <= end)
                                    if buts > 0:
                                        avec_but += 1
                                return (avec_but / total) if total else 0.0

                            recent_home = get_recent_pattern_score(league, d['home_team'], 'HOME', interval)
                            recent_away = get_recent_pattern_score(league, d['away_team'], 'AWAY', interval)
                            print(f"Indice dynamique récente (5 derniers matchs) : {d['home_team']} = {recent_home*100:.1f}% | {d['away_team']} = {recent_away*100:.1f}%")
                            # stats_history[url_key] = []
                            # stats_history[url_key].append({
                            #     'tirs': d['shots_home'] + d['shots_away'],
                            #     'attaques': d['attacks_home'] + d['attacks_away'],
                            #     'attaques_dangereuses': d['dangerous_attacks_home'] + d['dangerous_attacks_away'],
                            #     'corners': d['corners_home'] + d['corners_away']
                            # })
                            # momentum_5min = compute_momentum(stats_history[url_key], window=5)
                            # momentum_2min = compute_momentum(stats_history[url_key], window=2)
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

