#!/usr/bin/env python3
"""
Correction du pattern_analyzer pour accepter la structure actuelle du scraper
"""
from pathlib import Path

analyzer_path = Path('analyzers/pattern_analyzer.py')

print("\n" + "="*60)
print("🔧 CORRECTION DU PATTERN ANALYZER")
print("="*60 + "\n")

# Lire le fichier
with open(analyzer_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Sauvegarder l'original
backup_path = Path('analyzers/pattern_analyzer.py.backup')
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"💾 Sauvegarde créée: {backup_path}\n")

# Trouver la méthode analyze_team_profile et la corriger
# Chercher la ligne qui cause l'erreur 'home'

if "'home'" in content or '["home"]' in content:
    print("🔍 Détection de références à 'home' dans l'analyzer")
    print("📝 Modification nécessaire pour accepter la structure plate\n")
    
    # Remplacer la logique
    old_pattern = """    def analyze_team_profile(self, team_stats: Dict) -> Dict:
        \"\"\"
        Analyse le profil d'une équipe
        
        Args:
            team_stats: Stats de l'équipe
            
        Returns:
            Profil analysé avec zones de danger
        \"\"\"
        self.logger.info(f"Analyzing profile for {team_stats.get('team', 'Unknown')}")
        
        # Extraire les stats home/away
        home_stats = team_stats['home']
        away_stats = team_stats['away']"""
    
    new_pattern = """    def analyze_team_profile(self, team_stats: Dict) -> Dict:
        \"\"\"
        Analyse le profil d'une équipe
        
        Args:
            team_stats: Stats de l'équipe
            
        Returns:
            Profil analysé avec zones de danger
        \"\"\"
        self.logger.info(f"Analyzing profile for {team_stats.get('team', 'Unknown')}")
        
        # Adapter la structure selon le format reçu
        if 'home' in team_stats and 'away' in team_stats:
            # Format Home/Away
            home_stats = team_stats['home']
            away_stats = team_stats['away']
        else:
            # Format Overall (structure plate)
            # Simuler home/away avec les mêmes données
            home_stats = {
                'gp': team_stats.get('gp', 0),
                'goals_by_interval': team_stats.get('goals_by_interval', {}),
                'first_half': team_stats.get('first_half', {}),
                'second_half': team_stats.get('second_half', {})
            }
            away_stats = home_stats.copy()"""
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ Méthode analyze_team_profile modifiée")
    else:
        print("⚠️  Pattern exact non trouvé, modification manuelle nécessaire")

# Sauvegarder
with open(analyzer_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n💾 Analyzer mis à jour: {analyzer_path}")
print("\n" + "="*60)
print("✅ CORRECTION TERMINÉE!")
print("="*60)
print("\n💡 Testez maintenant: python setup_profiles.py\n")
