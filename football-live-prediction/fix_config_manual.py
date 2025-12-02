#!/usr/bin/env python3
"""Correction manuelle avec les bons noms"""
import yaml
from pathlib import Path

config_path = Path('config/config.yaml')

print("\n" + "="*60)
print("🔧 CORRECTION MANUELLE DES NOMS D'ÉQUIPES")
print("="*60 + "\n")

# Lire la config
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Corrections à appliquer
corrections = {
    'Manchester United': 'Manchester Utd',
    'Paris Saint-Germain': 'Paris SG',
    'Real Madrid': 'Real Madrid'  # Déjà correct
}

print("📝 Application des corrections:\n")

# Modifier test_teams
for team in config.get('test_teams', []):
    old_name = team['name']
    if old_name in corrections:
        new_name = corrections[old_name]
        if old_name != new_name:
            print(f"   🔄 {old_name} → {new_name}")
            team['name'] = new_name
        else:
            print(f"   ✅ {old_name} (déjà correct)")

# Sauvegarder
with open(config_path, 'w', encoding='utf-8') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print(f"\n💾 Config sauvegardée: {config_path}")

# Afficher résultat
print("\n" + "="*60)
print("📊 NOUVEAUX NOMS")
print("="*60 + "\n")

for team in config.get('test_teams', []):
    print(f"   • {team['name']} ({team['league_code']})")

print("\n✅ CORRECTION TERMINÉE!\n")
