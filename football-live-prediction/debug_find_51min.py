#!/usr/bin/env python3
"""
Cherche spécifiquement "51 min." et analyse comment c'est stylé
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
print("🔍 RECHERCHE: '51 min.' dans le HTML")
print("="*80 + "\n")

# Chercher tous les éléments contenant "51 min"
elements = soup.find_all(string=lambda text: text and '51 min' in text)

print(f"📊 Trouvé {len(elements)} éléments contenant '51 min'\n")

for i, elem in enumerate(elements, 1):
    print(f"\n{'='*80}")
    print(f"ÉLÉMENT #{i}")
    print(f"{'='*80}")

    print(f"\n1️⃣ Texte: '{elem.strip()}'")

    # Parent immédiat
    if hasattr(elem, 'parent'):
        parent = elem.parent
        print(f"\n2️⃣ Parent immédiat: <{parent.name}>")

        # Afficher tous les attributs du parent
        if hasattr(parent, 'attrs'):
            print(f"   Attributs:")
            for key, value in parent.attrs.items():
                print(f"     {key}: {value}")

        # Remonter 5 niveaux
        print(f"\n3️⃣ Structure parente (5 niveaux):")
        current = parent
        for level in range(5):
            if current:
                attrs_str = ""
                if hasattr(current, 'attrs') and current.attrs:
                    attrs_list = [f"{k}='{v}'" for k, v in list(current.attrs.items())[:3]]
                    attrs_str = " " + " ".join(attrs_list) if attrs_list else ""
                print(f"   Niveau {level+1}: <{current.name}{attrs_str}>")
                current = current.parent

        # Chercher le lien pmatch.asp dans les parents
        print(f"\n4️⃣ Recherche du lien pmatch.asp:")
        current = parent
        for level in range(15):
            if not current:
                break
            link = current.find('a', href=lambda x: x and 'pmatch.asp' in x)
            if link:
                print(f"   ✅ Trouvé au niveau {level+1}: {link.get('href')}")
                break
            current = current.parent
        else:
            print(f"   ❌ Lien non trouvé dans les 15 niveaux parents")

        # HTML brut du parent
        print(f"\n5️⃣ HTML brut du parent:")
        parent_html = str(parent)[:500]
        print(f"   {parent_html}")
        if len(str(parent)) > 500:
            print("   ... (truncated)")

print("\n" + "="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80 + "\n")
