"""Correction complète de l'export Excel pour structure Home/Away"""
from pathlib import Path

setup_path = Path('setup_profiles.py')

with open(setup_path, 'r') as f:
    content = f.read()

# Trouver et remplacer TOUTE la fonction export_profiles_to_excel
old_function_start = "def export_profiles_to_excel(profiles: List[Dict], output_file: str):"

# Chercher où commence la fonction
start_idx = content.find(old_function_start)

if start_idx == -1:
    print("❌ Fonction export_profiles_to_excel non trouvée")
    exit(1)

# Chercher la prochaine fonction
next_function = content.find("\ndef ", start_idx + 10)

if next_function == -1:
    next_function = content.find("\nif __name__", start_idx)

# Nouvelle fonction compatible Home/Away
new_function = '''def export_profiles_to_excel(profiles: List[Dict], output_file: str):
    """Export team profiles to Excel (compatible Home/Away)"""
    if not profiles:
        print("⚠️  Aucun profil à exporter")
        return
    
    summary_data = []
    
    for profile in profiles:
        team_name = profile.get('team', 'Unknown')
        league = profile.get('league', 'Unknown')
        overall = profile.get('overall', {})
        
        summary_data.append({
            "Team": team_name,
            "League": league,
            "Games Played": overall.get('games_played', 0),
            "Goals Scored": overall.get('total_scored', 0),
            "Goals Conceded": overall.get('total_conceded', 0),
            "Goal Difference": overall.get('goal_difference', 0),
            "Play Style": overall.get('play_style', {}).get('summary', 'N/A'),
            "Danger Zones": len(overall.get('danger_zones', []))
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        danger_data = []
        for profile in profiles:
            team_name = profile.get('team', 'Unknown')
            for venue in ['overall', 'home', 'away']:
                venue_data = profile.get(venue, {})
                for zone in venue_data.get('danger_zones', []):
                    danger_data.append({
                        "Team": team_name,
                        "Venue": venue.capitalize(),
                        "Interval": zone.get('interval', 'N/A'),
                        "Goals Scored": zone.get('goals_scored', 0),
                        "Goals Conceded": zone.get('goals_conceded', 0),
                        "Total Goals": zone.get('total_goals', 0),
                        "Goals Per Game": zone.get('goals_per_game', 0),
                        "Intensity": zone.get('intensity', 'N/A')
                    })
        
        if danger_data:
            df_danger = pd.DataFrame(danger_data)
            df_danger.to_excel(writer, sheet_name='Danger_Zones', index=False)
    
    print(f"✅ Fichier Excel créé: {output_file}")
'''

content = content[:start_idx] + new_function + content[next_function:]

with open(setup_path, 'w') as f:
    f.write(content)

print("✅ Fonction export_profiles_to_excel réécrite")
