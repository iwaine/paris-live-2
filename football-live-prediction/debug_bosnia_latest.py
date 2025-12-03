#!/usr/bin/env python3
"""
Debug: Analyser la page latest.asp de Bosnie pour comprendre pourquoi
on ne détecte pas les matchs live
"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.soccerstats.com/latest.asp?league=bosnia"

print(f"\n🔍 Analyse de: {url}\n")

# Session sans proxy
session = requests.Session()
session.trust_env = False

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

response = session.get(url, headers=headers, timeout=30)

print(f"✅ Status: {response.status_code}")
print(f"📦 Content length: {len(response.text)} chars\n")

soup = BeautifulSoup(response.text, 'lxml')

# Sauvegarder le HTML
with open('/tmp/bosnia_latest.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("💾 Sauvegardé: /tmp/bosnia_latest.html\n")

print("="*80)
print("🔍 RECHERCHE 1: Tous les <font> avec #87CEFA")
print("="*80)

live_fonts = soup.find_all('font', style=lambda x: x and '#87CEFA' in x.upper())
print(f"\n📊 Trouvé {len(live_fonts)} éléments\n")

for i, font in enumerate(live_fonts[:10], 1):
    text = font.get_text(strip=True)
    style = font.get('style', '')
    print(f"{i}. Text: '{text}'")
    print(f"   Style: {style}")

    # Chercher "min" ou patterns live
    has_min = bool(re.search(r'\d+\s*min', text, re.IGNORECASE))
    has_ht = 'HT' in text.upper()

    if has_min or has_ht:
        print(f"   🎯 LIVE INDICATOR!")

        # Chercher le <tr> parent
        tr = font.find_parent('tr')
        if tr:
            print(f"   ✓ <tr> parent trouvé")
            link = tr.find('a', href=lambda x: x and 'pmatch.asp' in x)
            if link:
                print(f"   ✓ Lien: {link.get('href')}")
            else:
                print(f"   ✗ Pas de lien pmatch.asp dans le <tr>")
        else:
            print(f"   ✗ Pas de <tr> parent")
    print()

print("="*80)
print("🔍 RECHERCHE 2: Tous les <td> avec #87CEFA (background color)")
print("="*80)

live_tds = soup.find_all('td', bgcolor=lambda x: x and '#87CEFA' in x.upper())
print(f"\n📊 Trouvé {len(live_tds)} éléments\n")

for i, td in enumerate(live_tds[:5], 1):
    print(f"{i}. TD with bgcolor=#87CEFA")
    print(f"   Content: {td.get_text(strip=True)[:50]}")

    # Chercher le <tr> parent
    tr = td.find_parent('tr')
    if tr:
        print(f"   ✓ <tr> parent trouvé")
        link = tr.find('a', href=lambda x: x and 'pmatch.asp' in x)
        if link:
            print(f"   ✓ Lien: {link.get('href')}")
        else:
            print(f"   ✗ Pas de lien dans le <tr>")
    print()

print("="*80)
print("🔍 RECHERCHE 3: Tous les liens pmatch.asp")
print("="*80)

all_links = soup.find_all('a', href=lambda x: x and 'pmatch.asp' in x)
print(f"\n📊 Total: {len(all_links)} liens\n")

for i, link in enumerate(all_links[:10], 1):
    href = link.get('href', '')
    text = link.get_text(strip=True)
    print(f"{i:2d}. {text[:40]:<40} → {href}")

print("\n" + "="*80)
print("🔍 RECHERCHE 4: Pattern global pour 'XX min'")
print("="*80)

# Chercher tous les textes avec "XX min"
all_text = soup.get_text()
minute_matches = re.findall(r'\d+\s*min\.?', all_text, re.IGNORECASE)
print(f"\n📊 Trouvé {len(minute_matches)} occurrences de 'XX min'\n")

for match in minute_matches[:10]:
    print(f"  - {match}")

print("\n" + "="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80)
print("\n💡 Vérifie /tmp/bosnia_latest.html pour le HTML complet\n")
