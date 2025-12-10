#!/usr/bin/env python3
"""
Génère automatiquement la whitelist des meilleures équipes par ligue
À exécuter APRÈS chaque scraping pour avoir les patterns à jour

Usage:
    python3 generate_top_teams_whitelist.py --league germany
    python3 generate_top_teams_whitelist.py --all  # Toutes les ligues
"""

import sqlite3
import json
import argparse
from datetime import datetime
from collections import defaultdict


def get_interval_stats(cursor, team_name, is_home, interval_min, interval_max, min_matches=3):
    """Calcule stats d'une équipe sur un intervalle spécifique"""
    cursor.execute('''
        SELECT goal_times, goal_times_conceded, date
        FROM soccerstats_scraped_matches
        WHERE team = ? AND is_home = ?
        ORDER BY date DESC
    ''', (team_name, 1 if is_home else 0))
    
    matches = cursor.fetchall()
    total_matches = len(matches)
    
    # Minimum de matchs requis pour pattern fiable
    if total_matches < min_matches:
        return None
    
    matches_with_goal = 0
    total_goals = 0
    
    for goal_times_json, goal_conceded_json, match_date in matches:
        goals = json.loads(goal_times_json) if goal_times_json else []
        goals_conceded = json.loads(goal_conceded_json) if goal_conceded_json else []
        all_goals = goals + goals_conceded
        
        # Compter buts dans intervalle
        goals_in_interval = [g for g in all_goals if interval_min <= g <= interval_max]
        if goals_in_interval:
            matches_with_goal += 1
            total_goals += len(goals_in_interval)
    
    probability = (matches_with_goal / total_matches * 100) if total_matches > 0 else 0
    recurrence = (total_goals / total_matches * 100) if total_matches > 0 else 0
    
    return {
        'probability': probability,
        'recurrence': recurrence,
        'matches': total_matches,
        'matches_with_goal': matches_with_goal,
        'total_goals': total_goals
    }


def analyze_league_teams(db_path, league_code, threshold=65, min_matches=4):
    """
    Analyse toutes les équipes d'une ligue et identifie les meilleures
    
    Args:
        db_path: Chemin vers la DB
        league_code: Code de la ligue (ex: 'germany', 'france')
        threshold: Seuil minimal de probabilité (défaut 65%)
        min_matches: Nombre minimal de matchs requis (défaut 4)
    
    Returns:
        Dict avec équipes qualifiées et statistiques
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer toutes les équipes de la ligue
    cursor.execute('''
        SELECT DISTINCT team, league
        FROM soccerstats_scraped_matches
        WHERE league = ?
        ORDER BY team
    ''', (league_code,))
    
    teams = cursor.fetchall()
    
    print(f'\n🔍 ANALYSE DE {len(teams)} ÉQUIPES - {league_code.upper()}')
    print('=' * 70)
    
    qualified_teams = []
    team_stats = []
    
    intervals = [
        ('31-45', 31, 45),
        ('76-90', 76, 90)
    ]
    
    for team_name, league in teams:
        for location_name, is_home in [('HOME', True), ('AWAY', False)]:
            for interval_name, int_min, int_max in intervals:
                stats = get_interval_stats(cursor, team_name, is_home, int_min, int_max, min_matches)
                
                if stats and stats['probability'] >= threshold:
                    qualified_teams.append({
                        'team': team_name,
                        'location': location_name,
                        'interval': interval_name,
                        'probability': stats['probability'],
                        'recurrence': stats['recurrence'],
                        'matches': stats['matches'],
                        'matches_with_goal': stats['matches_with_goal'],
                        'total_goals': stats['total_goals']
                    })
                
                # Garder toutes les stats pour le rapport
                if stats:
                    team_stats.append({
                        'team': team_name,
                        'location': location_name,
                        'interval': interval_name,
                        'probability': stats['probability'],
                        'matches': stats['matches']
                    })
    
    conn.close()
    
    # Trier par probabilité décroissante
    qualified_teams.sort(key=lambda x: x['probability'], reverse=True)
    
    return {
        'league': league_code,
        'threshold': threshold,
        'min_matches': min_matches,
        'total_teams_analyzed': len(teams),
        'qualified_teams': qualified_teams,
        'all_stats': team_stats,
        'generated_at': datetime.now().isoformat()
    }


def save_whitelist(data, output_file):
    """Sauvegarde la whitelist au format JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'\n💾 Whitelist sauvegardée: {output_file}')


def print_report(data):
    """Affiche un rapport des équipes qualifiées"""
    print(f'\n📊 RAPPORT - {data["league"].upper()}')
    print('=' * 70)
    print(f'Seuil: {data["threshold"]}% | Min matchs: {data["min_matches"]}')
    print(f'Équipes analysées: {data["total_teams_analyzed"]}')
    print(f'Équipes qualifiées: {len(data["qualified_teams"])}')
    print(f'Généré le: {data["generated_at"]}')
    
    if data['qualified_teams']:
        print(f'\n✅ TOP ÉQUIPES (≥ {data["threshold"]}%):')
        print('=' * 70)
        for i, team in enumerate(data['qualified_teams'][:20], 1):  # Top 20
            print(f'{i:2d}. {team["team"]:25s} {team["location"]:5s} {team["interval"]:6s} '
                  f'| {team["probability"]:5.1f}% ({team["matches_with_goal"]}/{team["matches"]} matchs) '
                  f'| {team["total_goals"]} buts')
    else:
        print(f'\n⚠️  Aucune équipe ne dépasse le seuil de {data["threshold"]}%')
    
    # Stats faibles
    weak_teams = [s for s in data['all_stats'] if s['probability'] < 50]
    if weak_teams:
        print(f'\n❌ ÉQUIPES FAIBLES (< 50%) - À IGNORER:')
        print('=' * 70)
        for team in weak_teams[:10]:  # Top 10 plus faibles
            print(f'   {team["team"]:25s} {team["location"]:5s} {team["interval"]:6s} '
                  f'| {team["probability"]:5.1f}%')


def main():
    parser = argparse.ArgumentParser(description='Génère whitelist des meilleures équipes')
    parser.add_argument('--league', type=str, help='Code ligue (ex: germany, france)')
    parser.add_argument('--all', action='store_true', help='Toutes les ligues')
    parser.add_argument('--threshold', type=int, default=65, help='Seuil minimal (défaut 65%%)')
    parser.add_argument('--min-matches', type=int, default=4, help='Nb min matchs (défaut 4)')
    parser.add_argument('--output-dir', type=str, default='whitelists', help='Dossier de sortie')
    
    args = parser.parse_args()
    
    db_path = '/workspaces/paris-live/football-live-prediction/data/predictions.db'
    
    # Créer dossier de sortie
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.all:
        # Récupérer toutes les ligues
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT league FROM soccerstats_scraped_matches ORDER BY league')
        leagues = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f'\n🚀 GÉNÉRATION WHITELISTS POUR {len(leagues)} LIGUES')
        print('=' * 70)
        
        for league in leagues:
            data = analyze_league_teams(db_path, league, args.threshold, args.min_matches)
            output_file = f'{args.output_dir}/{league}_whitelist.json'
            save_whitelist(data, output_file)
            print_report(data)
            print()
    
    elif args.league:
        data = analyze_league_teams(db_path, args.league, args.threshold, args.min_matches)
        output_file = f'{args.output_dir}/{args.league}_whitelist.json'
        save_whitelist(data, output_file)
        print_report(data)
    
    else:
        parser.print_help()
        return
    
    print('\n✅ WHITELIST(S) GÉNÉRÉE(S) AVEC SUCCÈS !')
    print('=' * 70)
    print(f'📁 Dossier: {args.output_dir}/')
    print(f'🔄 À relancer après chaque scraping pour mise à jour')


if __name__ == '__main__':
    main()
