#!/usr/bin/env python3
"""
Test du système de prédiction avec les données de Bulgarie
"""
import sys
sys.path.insert(0, '/workspaces/paris-live/football-live-prediction')

from predictors.interval_predictor import IntervalPredictor
import sqlite3

# Test avec un match bulgare
predictor = IntervalPredictor()

# Récupérer les données de Ludogorets vs Dobrudzha (4 Dec, Ludogorets gagné 2-0)
conn = sqlite3.connect('/workspaces/paris-live/football-live-prediction/data/predictions.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT team, opponent, date, goals_for, goals_against, goal_times, goal_times_conceded
    FROM soccerstats_scraped_matches 
    WHERE team='Ludogorets' AND opponent='Dobrudzha' AND date='4 Dec'
''')
match = cursor.fetchone()
print(f'\n🔎 Match: {match[0]} vs {match[1]} ({match[2]})')
print(f'   Score: {match[3]}-{match[4]}')
print(f'   Buts marqués: {match[5]}')
print(f'   Buts encaissés: {match[6]}')

# Prédire un futur match Ludogorets à domicile (minute 0 = pré-match)
print(f'\n🔮 Prédiction pour prochain match Ludogorets (domicile) vs Lokomotiv Plovdiv:')
prediction = predictor.predict_match('Ludogorets', 'Lokomotiv Plovdiv', current_minute=0)
print(f'\nInterval 0-15:   {prediction["next_goal"]["0-15"]:.2%}')
print(f'Interval 16-30:  {prediction["next_goal"]["16-30"]:.2%}')
print(f'Interval 31-45+: {prediction["next_goal"]["31-45+"]:.2%}')
print(f'Interval 46-60:  {prediction["next_goal"]["46-60"]:.2%}')
print(f'Interval 61-75:  {prediction["next_goal"]["61-75"]:.2%}')
print(f'Interval 75-90+: {prediction["next_goal"]["75-90+"]:.2%}')

# Test avec Slavia Sofia
cursor.execute('''
    SELECT team, opponent, date, goals_for, goals_against, goal_times
    FROM soccerstats_scraped_matches 
    WHERE team='Slavia Sofia' AND opponent='Levski Sofia' AND date='4 Dec'
''')
match2 = cursor.fetchone()
print(f'\n\n🔎 Match: {match2[0]} vs {match2[1]} ({match2[2]})')
print(f'   Score: {match2[3]}-{match2[4]}')
print(f'   Buts à: {match2[5]}')

print(f'\n🔮 Prédiction pour prochain match Slavia Sofia (domicile) vs CSKA 1948:')
prediction2 = predictor.predict_match('Slavia Sofia', 'CSKA 1948', current_minute=0)
for interval, prob in prediction2['next_goal'].items():
    print(f'{interval}: {prob:.2%}')

conn.close()
print('\n✅ Test complet terminé!')
