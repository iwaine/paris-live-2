def normalize_team_name(name):
    return name.strip().lower().replace('.', '').replace('-', ' ').replace("'", '').replace('  ', ' ')
# -*- coding: utf-8 -*-
"""
Utilitaires pour extraction patterns historiques, saturation, momentum pour scoring live.
"""
import sqlite3
import json
from collections import defaultdict
from typing import Tuple

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "predictions.db")
INTERVALS = [(31, 45), (75, 120)]
INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }


def get_pattern_score(league: str, team: str, side: str, interval: Tuple[int, int]) -> float:
    """
    Retourne la récurrence stricte (0-1) pour une équipe, un intervalle, une ligue, un côté (HOME/AWAY)
    """
    # Normalisation du nom d'équipe pour correspondre à la base
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = ?", (league,))
    teams_in_db = [row[0] for row in cursor.fetchall()]
    norm_map = {normalize_team_name(t): t for t in teams_in_db}
    team_norm = normalize_team_name(team)
    norm_team = norm_map.get(team_norm, team)
    cursor.execute("""
        SELECT goal_times, goal_times_conceded, is_home FROM soccerstats_scraped_matches
        WHERE league = ? AND team = ?
    """, (league, norm_team))
    matchs = cursor.fetchall()
    conn.close()
    if not matchs:
        return 0.0
    total = 0
    avec_but = 0
    for goal_times, goal_times_conceded, is_home in matchs:
        if (side == "HOME" and not is_home) or (side == "AWAY" and is_home):
            continue
        try:
            goals = json.loads(goal_times) if goal_times else []
            conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
        except Exception:
            goals, conceded = [], []
        start, end = interval
        # Détection de la minute max du match (pour 45+X ou 90+X)
        all_minutes = goals + conceded
        minute_max = max(all_minutes) if all_minutes else end
        # Pour 31-45+, on prend jusqu'à la fin de la 1ère mi-temps (HT, typiquement 45+X)
        # Pour 75-90+, on prend jusqu'à la fin du match (FT, typiquement 90+X)
        if start == 31 and end >= 45:
            interval_end = min(minute_max, 60) if minute_max <= 60 else 45  # sécurité, rarement > 60 en 1ère MT
            buts = sum(1 for m in goals if start <= m <= interval_end) + sum(1 for m in conceded if start <= m <= interval_end)
        elif start == 75 and end >= 90:
            interval_end = minute_max if minute_max >= 90 else end
            buts = sum(1 for m in goals if start <= m <= interval_end) + sum(1 for m in conceded if start <= m <= interval_end)
        else:
            buts = sum(1 for m in goals if start <= m <= end) + sum(1 for m in conceded if start <= m <= end)
        total += 1
        if buts > 0:
            avec_but += 1
    return avec_but / total if total else 0.0


def get_saturation_score(league: str, team: str, goals_scored: int, interval: Tuple[int, int], mi_temps: str = "full") -> float:
    """
    Retourne un score de saturation (1.0 = pas saturé, <1.0 = saturation atteinte)
    """
    # Normalisation du nom d'équipe pour correspondre à la base
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = ?", (league,))
    teams_in_db = [row[0] for row in cursor.fetchall()]
    norm_map = {normalize_team_name(t): t for t in teams_in_db}
    team_norm = normalize_team_name(team)
    norm_team = norm_map.get(team_norm, team)
    cursor.execute("""
        SELECT goal_times FROM soccerstats_scraped_matches
        WHERE league = ? AND team = ?
    """, (league, norm_team))
    matchs = cursor.fetchall()
    conn.close()
    if not matchs:
        return 1.0
    total_buts = 0
    for (goal_times,) in matchs:
        try:
            goals = json.loads(goal_times) if goal_times else []
        except Exception:
            goals = []
        if mi_temps == "full":
            total_buts += len(goals)
        elif mi_temps == "mt1":
            total_buts += sum(1 for m in goals if m <= 45)
        elif mi_temps == "mt2":
            total_buts += sum(1 for m in goals if m > 45)
    moyenne = total_buts / len(matchs)
    if moyenne == 0:
        return 1.0
    return max(0.5, 1.0 - max(0, (goals_scored - moyenne) / (moyenne+1)))


def compute_momentum(stats_history: list, window: int = 5) -> float:
    """
    Calcule le momentum sur la fenêtre (en minutes) passée.
    stats_history : liste de dicts (une entrée par minute, ou par tick)
    window : nombre de minutes à regarder en arrière
    Retourne un score 0-1 (0 = pas de momentum, 1 = très fort)
    """
    if len(stats_history) < window:
        return 0.0
    # Moyenne sur la fenêtre
    recent = stats_history[-window:]
    total = 0
    for s in recent:
        total += s.get('tirs',0) + s.get('attaques',0) + s.get('attaques_dangereuses',0) + s.get('corners',0)
    # Moyenne sur tout l'historique
    all_total = 0
    for s in stats_history:
        all_total += s.get('tirs',0) + s.get('attaques',0) + s.get('attaques_dangereuses',0) + s.get('corners',0)
    moy_recent = total / window
    moy_all = all_total / len(stats_history)
    if moy_all == 0:
        return 0.0
    ratio = moy_recent / moy_all
    return min(1.0, max(0.0, (ratio-1)*0.7 + 0.5))  # 0.5 = normal, >0.7 = fort momentum
