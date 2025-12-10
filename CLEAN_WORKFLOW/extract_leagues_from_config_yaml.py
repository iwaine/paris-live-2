import yaml

# Chemin du fichier YAML de config des ligues
config_path = "/workspaces/paris-live/CLEAN_WORKFLOW/config.yaml"

with open(config_path, "r") as f:
    data = yaml.safe_load(f)

# Extraire les ligues activées (enabled: true)
leagues = []
for league in data.get("leagues", []):
    if league.get("enabled", False):
        url = league.get("url", "")
        # On extrait le code de ligue depuis l'URL (après 'league=')
        if "league=" in url:
            code = url.split("league=")[1].split("&")[0]
            leagues.append(code)

# Tri et affichage
leagues = sorted(set(leagues))
print(f"{len(leagues)} ligues activées trouvées :")
for l in leagues:
    print(l)

# Génération d'une commande pour scraping sélectif
print("\nCommande à lancer :")
print(f"python3 /workspaces/paris-live/scrape_all_leagues_auto.py --leagues={','.join(leagues)}")
