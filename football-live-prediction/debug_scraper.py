#!/usr/bin/env python3
"""
Script de debug pour analyser la structure HTML de la page Bulgaria
"""

import requests
from bs4 import BeautifulSoup
import re

def scrape_and_analyze(url):
    """Scrape la page et analyse la structure HTML"""

    print(f"\n🔍 Scraping: {url}\n")

    # Session sans proxy
    session = requests.Session()
    session.trust_env = False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'Connection': 'keep-alive',
    }

    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        print(f"✅ Status: {response.status_code}")
        print(f"📦 Content length: {len(response.text)} chars\n")

        # Sauvegarder le HTML complet
        with open('/tmp/bulgaria_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("💾 HTML complet sauvegardé: /tmp/bulgaria_page.html\n")

        # Parser avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')

        print("="*80)
        print("🔍 RECHERCHE DES ÉLÉMENTS AVEC COULEUR #87CEFA (LIVE)")
        print("="*80 + "\n")

        # Chercher tous les fonts avec la couleur #87CEFA
        live_fonts = soup.find_all('font', style=lambda x: x and '#87CEFA' in x.upper())

        print(f"📊 Trouvé {len(live_fonts)} éléments avec #87CEFA\n")

        # Analyser chaque élément trouvé
        for i, font in enumerate(live_fonts, 1):
            text = font.get_text(strip=True)
            style = font.get('style', '')

            # Vérifier si c'est un statut de type "XX min"
            is_minute = bool(re.search(r'\d+\s*min', text, re.IGNORECASE))
            is_ht = 'HT' in text.upper()

            if is_minute or is_ht:
                print(f"\n{'='*80}")
                print(f"🎯 MATCH LIVE #{i}: {text}")
                print(f"{'='*80}")

                print(f"\n1️⃣ Élément trouvé:")
                print(f"   Text: {text}")
                print(f"   Style: {style}")

                # Remonter pour trouver la structure parente
                print(f"\n2️⃣ Structure parente (10 niveaux):")
                current = font
                for level in range(10):
                    if current is None:
                        break
                    current = current.parent
                    if current:
                        tag_info = f"<{current.name}"
                        if current.get('class'):
                            tag_info += f" class='{' '.join(current.get('class'))}'"
                        if current.get('bgcolor'):
                            tag_info += f" bgcolor='{current.get('bgcolor')}'"
                        if current.get('width'):
                            tag_info += f" width='{current.get('width')}'"
                        if current.get('id'):
                            tag_info += f" id='{current.get('id')}'"
                        tag_info += ">"
                        print(f"   Level {level+1}: {tag_info}")

                # Chercher le lien pmatch.asp à proximité
                print(f"\n3️⃣ Recherche du lien pmatch.asp:")

                # Chercher dans les parents
                match_link = None
                current = font
                for _ in range(15):
                    if current is None:
                        break
                    link = current.find('a', href=lambda x: x and 'pmatch.asp' in x)
                    if link:
                        match_link = link.get('href')
                        print(f"   ✅ Trouvé dans parent: {match_link}")
                        break
                    current = current.parent

                if not match_link:
                    # Chercher dans les siblings
                    current = font.parent
                    if current:
                        for sibling in list(current.previous_siblings) + list(current.next_siblings):
                            if hasattr(sibling, 'find'):
                                link = sibling.find('a', href=lambda x: x and 'pmatch.asp' in x)
                                if link:
                                    match_link = link.get('href')
                                    print(f"   ✅ Trouvé dans sibling: {match_link}")
                                    break

                if not match_link:
                    print(f"   ❌ Lien pmatch.asp non trouvé!")
                    print(f"   💡 Cherchons dans toute la page autour de ce match...")

                    # Chercher "Septemvri Sofia" ou les équipes
                    parent_table = font.find_parent('table')
                    if parent_table:
                        print(f"   📋 Table parente trouvée, recherche des équipes...")
                        team_fonts = parent_table.find_all('font', style=lambda x: x and '#eeeeee' in x and '28px' in x)
                        if team_fonts:
                            for tf in team_fonts:
                                print(f"      Équipe: {tf.get_text(strip=True)}")

                # Afficher le HTML brut autour de cet élément
                print(f"\n4️⃣ HTML brut (contexte étendu):")
                parent = font.parent
                if parent and parent.parent and parent.parent.parent:
                    context = parent.parent.parent
                    html_str = str(context)
                    # Limiter à 1000 caractères
                    if len(html_str) > 1000:
                        html_str = html_str[:1000] + "\n... (truncated)"
                    print(f"{html_str}")

                print()

        # Chercher tous les liens pmatch.asp
        print("\n" + "="*80)
        print("🔗 TOUS LES LIENS pmatch.asp TROUVÉS")
        print("="*80 + "\n")

        all_links = soup.find_all('a', href=lambda x: x and 'pmatch.asp' in x)
        print(f"📊 Total: {len(all_links)} liens\n")

        for i, link in enumerate(all_links[:10], 1):  # Limiter aux 10 premiers
            href = link.get('href', '')
            text = link.get_text(strip=True)
            print(f"{i:2d}. {text[:50]:<50} → {href[:60]}")

        if len(all_links) > 10:
            print(f"\n... et {len(all_links) - 10} autres liens")

        # Chercher spécifiquement "Septemvri Sofia"
        print("\n" + "="*80)
        print("🔍 RECHERCHE SPÉCIFIQUE: Septemvri Sofia")
        print("="*80 + "\n")

        septemvri_elements = soup.find_all(string=lambda x: x and 'Septemvri Sofia' in str(x))
        print(f"📊 Trouvé {len(septemvri_elements)} occurrences de 'Septemvri Sofia'\n")

        for i, elem in enumerate(septemvri_elements[:3], 1):
            print(f"\nOccurrence #{i}:")
            print(f"   Text: {str(elem).strip()}")
            if hasattr(elem, 'parent'):
                parent = elem.parent
                for level in range(5):
                    if parent:
                        print(f"   Parent {level+1}: <{parent.name}>")
                        # Chercher lien dans ce parent
                        link = parent.find('a', href=lambda x: x and 'pmatch.asp' in x)
                        if link:
                            print(f"      → Lien trouvé: {link.get('href')}")
                        parent = parent.parent

        print("\n" + "="*80)
        print("✅ ANALYSE TERMINÉE")
        print("="*80)
        print(f"\n💡 Consulte /tmp/bulgaria_page.html pour voir le HTML complet\n")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    url = "https://www.soccerstats.com/latest.asp?league=bulgaria"
    scrape_and_analyze(url)
