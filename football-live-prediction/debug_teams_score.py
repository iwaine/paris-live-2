#!/usr/bin/env python3
"""
Cherche comment les équipes et le score sont stylés sur la page Bosnia
"""

import requests
from bs4 import BeautifulSoup

url = "https://www.soccerstats.com/latest.asp?league=bosnia"

session = requests.Session()
session.trust_env = False
headers = {'User-Agent': 'Mozilla/5.0'}

response = session.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'lxml')

print("\n" + "="*80)
print("🔍 ANALYSE: Équipes et Score")
print("="*80 + "\n")

# Chercher "51 min."
elem_51 = soup.find(string=lambda text: text and '51 min' in text)

if elem_51 and hasattr(elem_51, 'parent'):
    font_51 = elem_51.parent

    print("1️⃣ RECHERCHE DES ÉQUIPES")
    print("-" * 80)

    # Chercher dans les parents
    current = font_51
    for level in range(10):
        if not current:
            break

        # Chercher tous les <font> dans ce parent
        fonts_in_parent = current.find_all('font')

        if len(fonts_in_parent) > 1:
            print(f"\nNiveau {level+1}: <{current.name}> contient {len(fonts_in_parent)} <font>")

            # Afficher les 5 premiers
            for i, f in enumerate(fonts_in_parent[:10], 1):
                text = f.get_text(strip=True)
                color_attr = f.get('color', '')
                style_attr = f.get('style', '')

                # Ne pas afficher les vides
                if not text or len(text) < 2:
                    continue

                print(f"  {i}. '{text[:40]}'")
                if color_attr:
                    print(f"     color='{color_attr}'")
                if style_attr:
                    print(f"     style='{style_attr[:60]}'")

        current = current.parent

    print("\n2️⃣ RECHERCHE DU SCORE")
    print("-" * 80)

    # Chercher les patterns de score (X - X)
    current = font_51
    for level in range(10):
        if not current:
            break

        # Chercher tous les fonts avec des chiffres
        fonts_with_numbers = current.find_all('font')

        for f in fonts_with_numbers:
            text = f.get_text(strip=True)
            # Pattern score: "X - X" ou "X-X"
            if '-' in text and any(c.isdigit() for c in text):
                print(f"\nTrouvé score potentiel: '{text}'")
                print(f"  Niveau {level+1} dans: <{current.name}>")
                print(f"  color: {f.get('color', 'N/A')}")
                print(f"  style: {f.get('style', 'N/A')[:60]}")

        current = current.parent

    print("\n3️⃣ CHERCHER SPÉCIFIQUEMENT LES ÉQUIPES DU MATCH")
    print("-" * 80)

    # Chercher "Rudar" et "Zrinjski"
    rudar = soup.find_all(string=lambda x: x and 'Rudar' in str(x))
    zrinjski = soup.find_all(string=lambda x: x and 'Zrinjski' in str(x))

    print(f"\nTrouvé {len(rudar)} occurrences de 'Rudar'")
    for i, r in enumerate(rudar[:3], 1):
        if hasattr(r, 'parent'):
            parent = r.parent
            print(f"  {i}. Parent: <{parent.name}>")
            if hasattr(parent, 'attrs'):
                print(f"     Attributs: {dict(list(parent.attrs.items())[:3])}")

    print(f"\nTrouvé {len(zrinjski)} occurrences de 'Zrinjski'")
    for i, z in enumerate(zrinjski[:3], 1):
        if hasattr(z, 'parent'):
            parent = z.parent
            print(f"  {i}. Parent: <{parent.name}>")
            if hasattr(parent, 'attrs'):
                print(f"     Attributs: {dict(list(parent.attrs.items())[:3])}")

print("\n" + "="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80 + "\n")
