#!/usr/bin/env python3
"""
Script d'automatisation hebdomadaire du scraping pour toutes les ligues suivies.
A lancer via cron ou manuellement chaque semaine.
"""
import subprocess
import datetime
import os
import sqlite3
import json


# Nouvelle logique : lire la liste des ligues activées depuis CLEAN_WORKFLOW/config.yaml
import yaml
config_path = 'CLEAN_WORKFLOW/config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
leagues = [(l['url'].split('=')[-1], l['name']) for l in config['leagues'] if l.get('enabled', True)]

def run_scraper_for_league(league_code, league_name):
    print(f"\n{'='*60}\n🕒 {datetime.datetime.now()} | Scraping {league_name}\n{'='*60}")
    # Appel du workflow principal pour chaque ligue
    result = subprocess.run(["python3", "CLEAN_WORKFLOW/scrape_all_leagues_auto.py", "--league", league_code], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("[ERREUR]", result.stderr)

def run_scraper(script, label):
    print(f"\n{'='*60}\n🕒 {datetime.datetime.now()} | Scraping {label}\n{'='*60}")
    result = subprocess.run(["python3", script], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("[ERREUR]", result.stderr)

def print_global_top():
    INTERVALS = [(31, 45), (75, 120)]
    INTERVAL_LABELS = { (31, 45): "31-45+", (75, 120): "75-90+" }
    import os
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'predictions.db'))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT league FROM soccerstats_scraped_matches")
    leagues = [row[0] for row in cursor.fetchall()]
    top_patterns = []
    for league in leagues:
        cursor.execute("SELECT DISTINCT team FROM soccerstats_scraped_matches WHERE league = ?", (league,))
        teams = [row[0] for row in cursor.fetchall()]
        for team in teams:
            for side in [True, False]:
                side_label = 'HOME' if side else 'AWAY'
                for interval in INTERVALS:
                    cursor.execute("SELECT goal_times, goal_times_conceded FROM soccerstats_scraped_matches WHERE league = ? AND team = ? AND is_home = ?", (league, team, side))
                    matchs = cursor.fetchall()
                    total = len(matchs)
                    avec_but = 0
                    buts_marques = 0
                    buts_encaisses = 0
                    for goal_times, goal_times_conceded in matchs:
                        goals = json.loads(goal_times) if goal_times else []
                        conceded = json.loads(goal_times_conceded) if goal_times_conceded else []
                        start, end = interval
                        n_marques = sum(1 for m in goals if start <= m <= end)
                        n_encaisses = sum(1 for m in conceded if start <= m <= end)
                        buts_marques += n_marques
                        buts_encaisses += n_encaisses
                        if (n_marques + n_encaisses) > 0:
                            avec_but += 1
                    if total > 0:
                        recurrence = int(round(100 * avec_but / total))
                        top_patterns.append({
                            'league': league,
                            'team': team,
                            'side': side_label,
                            'interval': INTERVAL_LABELS[interval],
                            'recurrence': recurrence,
                            'buts': buts_marques + buts_encaisses,
                            'matches': total,
                            'marques': buts_marques,
                            'encaisses': buts_encaisses
                        })
    conn.close()
    top_patterns.sort(key=lambda x: x['recurrence'], reverse=True)
    print("\n=== TOP GLOBAL TOUTES LIGUES CONFONDUES ===\n")
    for p in top_patterns[:20]:
        print(f"[{p['league']}] {p['team']} {p['side']} {p['interval']} : {p['recurrence']}% ({p['buts']} buts sur {p['matches']} matches) - {p['marques']} marqués + {p['encaisses']} encaissés")
    print("\n=== FIN TOP GLOBAL ===\n")

if __name__ == "__main__":
    print("\n=== SCRAPING HEBDOMADAIRE DE TOUTES LES LIGUES (config centralisée) ===\n")
    for league_code, league_name in leagues:
        run_scraper_for_league(league_code, league_name)
    print_global_top()
    print("\n=== SCRAPING GLOBAL TERMINÉ ===\n")
