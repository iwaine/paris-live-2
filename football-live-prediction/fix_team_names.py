#!/usr/bin/env python3
"""
Script de correction automatique des noms d'équipes
Détecte les vrais noms sur SoccerStats et corrige config.yaml
"""
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path.cwd()))

from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper
import yaml

print("\n" + "="*70)
print(" "*15 + "🔧 CORRECTION AUTOMATIQUE DES NOMS D'ÉQUIPES")
print("="*70 + "\n")

# 1. Scraper les noms réels
scraper = SoccerStatsHistoricalScraper()

print("📊 Étape 1: Récupération des noms réels sur SoccerStats...\n")

leagues_mapping = {
    'england': 'Premier League',
    'france': 'Ligue 1', 
    'spain': 'La Liga'
}

real_names = {}

for code, name in leagues_mapping.items():
    print(f"   🔄 {name}...", end=" ")
    df = scraper.scrape_timing_stats(code)
    if df is not None and not df.empty:
        real_names[code] = df['team'].tolist()
        print(f"✅ {len(real_names[code])} équipes")
    else:
        real_names[code] = []
        print("❌ Erreur")

scraper.cleanup()

# 2. Fonction de matching intelligent
def find_best_match(search_name, team_list):
    """Trouve la meilleure correspondance pour un nom d'équipe"""
    search_lower = search_name.lower()
    
    # Correspondances exactes d'abord
    for team in team_list:
        if team.lower() == search_lower:
            return team
    
    # Correspondances partielles
    for team in team_list:
        team_lower = team.lower()
        # Si le nom recherché est contenu dans le nom réel
        if search_lower in team_lower or team_lower in search_lower:
            return team
    
    # Correspondances par mots-clés
    search_words = set(search_lower.replace('-', ' ').split())
    best_match = None
    best_score = 0
    
    for team in team_list:
        team_words = set(team.lower().replace('-', ' ').split())
        common_words = search_words & team_words
        score = len(common_words)
        
        if score > best_score:
            best_score = score
            best_match = team
    
    return best_match if best_score > 0 else None

# 3. Trouver les correspondances pour test_teams
print("\n📋 Étape 2: Recherche des correspondances...\n")

test_teams_corrections = [
    {
        'old_name': 'Manchester United',
        'league_code': 'england',
        'real_name': find_best_match('Manchester United', real_names.get('england', []))
    },
    {
        'old_name': 'Paris Saint-Germain',
        'league_code': 'france',
        'real_name': find_best_match('Paris Saint-Germain', real_names.get('france', []))
    },
    {
        'old_name': 'Real Madrid',
        'league_code': 'spain',
        'real_name': find_best_match('Real Madrid', real_names.get('spain', []))
    }
]

print("   Correspondances trouvées:")
for correction in test_teams_corrections:
    old = correction['old_name']
    new = correction['real_name']
    league = correction['league_code']
    
    if new:
        if old == new:
            print(f"   ✅ {old} ({league}) → Nom correct !")
        else:
            print(f"   🔄 {old} ({league}) → {new}")
    else:
        print(f"   ❌ {old} ({league}) → NON TROUVÉ")

# 4. Charger config.yaml
print("\n📝 Étape 3: Modification de config.yaml...\n")

config_path = Path('config/config.yaml')

if not config_path.exists():
    print("   ❌ config.yaml non trouvé!")
    sys.exit(1)

with open(config_path, 'r', encoding='utf-8') as f:
    config_content = f.read()

# 5. Créer une sauvegarde
backup_path = Path('config/config.yaml.backup')
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(config_content)

print(f"   💾 Sauvegarde créée: {backup_path}")

# 6. Appliquer les corrections
modified_content = config_content

for correction in test_teams_corrections:
    old_name = correction['old_name']
    new_name = correction['real_name']
    
    if new_name and old_name != new_name:
        # Remplacer le nom dans la section test_teams
        pattern = f'name: "{old_name}"'
        replacement = f'name: "{new_name}"'
        
        if pattern in modified_content:
            modified_content = modified_content.replace(pattern, replacement)
            print(f"   ✅ Remplacé: {old_name} → {new_name}")
        else:
            # Essayer avec guillemets simples
            pattern = f"name: '{old_name}'"
            replacement = f"name: '{new_name}'"
            if pattern in modified_content:
                modified_content = modified_content.replace(pattern, replacement)
                print(f"   ✅ Remplacé: {old_name} → {new_name}")

# 7. Sauvegarder la config modifiée
with open(config_path, 'w', encoding='utf-8') as f:
    f.write(modified_content)

print(f"\n   💾 Config mise à jour: {config_path}")

# 8. Afficher les nouveaux noms
print("\n" + "="*70)
print(" "*20 + "📊 NOUVEAUX NOMS DANS CONFIG")
print("="*70 + "\n")

config_data = yaml.safe_load(modified_content)
test_teams = config_data.get('test_teams', [])

for team in test_teams:
    print(f"   • {team['name']} ({team['league_code']})")

print("\n" + "="*70)
print("✅ CORRECTION TERMINÉE!")
print("="*70)

print("\n💡 Prochaines étapes:")
print("   1. Vérifiez les noms ci-dessus")
print("   2. Exécutez: python setup_profiles.py")
print("   3. Si problème: cp config/config.yaml.backup config/config.yaml")
print()
