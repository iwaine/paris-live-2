import yaml

# Chemin du fichier YAML
yaml_path = "/workspaces/paris-live/CLEAN_WORKFLOW/config_teams_updated.yaml"

# Extraction des ligues uniques
with open(yaml_path, "r") as f:
    data = yaml.safe_load(f)

leagues = set()
for team, info in data.get("teams", {}).items():
    league = info.get("league")
    if league:
        leagues.add(league)

# Tri pour affichage et usage
leagues = sorted(leagues)
print("LIGUES À SCRAPER (issues du YAML) :")
for l in leagues:
    print(l)

# Génération d'une commande pour scraping sélectif
print("\nCommande à lancer :")
print(f"python3 /workspaces/paris-live/scrape_all_leagues_auto.py --leagues={','.join(leagues)}")
