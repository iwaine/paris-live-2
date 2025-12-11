# Script d’analyse des scores E. Frankfurt AWAY depuis la page SoccerStats
from bs4 import BeautifulSoup
import re

with open("/tmp/e_frankfurt_utf8.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Trouver le tableau des matches
main_table = soup.find('table', {'bgcolor': '#cccccc', 'width': '100%'})
if not main_table:
    print("Tableau principal non trouvé.")
    exit(1)

rows = main_table.find_all('tr')[1:]  # skip header
with open("/workspaces/paris-live/CLEAN_WORKFLOW/frankfurt_away_results.txt", "w", encoding="utf-8") as out:
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 9:
            continue
        # Colonne 2 = home, colonne 4 = away
        home_cell = cells[1]
        away_cell = cells[3]
        # E. Frankfurt à l'extérieur = away_cell contient <b>E. Frankfurt</b> (balise b)
        is_away = away_cell.find('b') and 'E. Frankfurt' in away_cell.get_text()
        if is_away:
            date = cells[0].get_text(strip=True)
            opponent = home_cell.get_text(strip=True)
            score_link = cells[2].find('a', class_='tooltip4')
            score = score_link.get_text(strip=True) if score_link else cells[2].get_text(strip=True)
            out.write(f"{date} | {opponent} vs E. Frankfurt | Score: {score}\n")
            # Extraire les minutes de but du tooltip
            if score_link:
                tooltip_span = score_link.find('span')
                if tooltip_span:
                    tooltip_html = str(tooltip_span)
                    out.write('  Tooltip: ' + tooltip_html + '\n')
                    soup_tt = BeautifulSoup(tooltip_html, 'html.parser')
                    for b in soup_tt.find_all('b'):
                        parent = b.parent
                        if parent:
                            parent_text = parent.get_text()
                            # Cherche (minute) ou (minute pen.) ou (minute o.g.) etc.
                            m = re.search(r'\((\d{1,3})[^)]*\)', parent_text)
                            if m:
                                minute = int(m.group(1))
                                out.write(f'    Minute détectée : {minute} (texte : {parent_text.strip()})\n')
