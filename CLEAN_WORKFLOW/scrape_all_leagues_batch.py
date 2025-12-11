import subprocess

# Liste complète des ligues à scrapper
leagues = [
    "france", "france2", "germany", "germany2", "italy", "portugal", "portugal2",
    "scotland", "spain", "spain2", "switzerland", "austria", "austria2", "bulgaria",
    "croatia", "croatia2", "czechrepublic", "czechrepublic2", "denmark",
    "netherlands", "poland", "turkey", "england", "england2", "england3", "england4",
    "saudiarabia", "australia", "greece", "slovenia", "japan", "ireland", "southkorea",
    "argentina", "chile", "estonia", "faroeislands", "finland", "iceland", "latvia",
    "sweden", "usa", "southkorea4", "georgia", "norway6", "iceland2", "cyprus", "bolivia"
]

for league in leagues:
    print(f"\n=== SCRAPING {league} ===")
    subprocess.run(["python3", "scrape_all_leagues_auto.py", "--league", league])
print("\nScraping batch terminé pour toutes les ligues.")
