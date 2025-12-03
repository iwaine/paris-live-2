#!/usr/bin/env python3
"""
Debug: Analyser le score sur une URL spécifique
"""

import sys
import requests
from bs4 import BeautifulSoup
import re

if len(sys.argv) < 2:
    print("Usage: python3 debug_score_url.py <URL>")
    sys.exit(1)

url = sys.argv[1]

session = requests.Session()
session.trust_env = False
headers = {'User-Agent': 'Mozilla/5.0'}

response = session.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'lxml')

print("\n" + "="*80)
print(f"🔍 ANALYSE: {url}")
print("="*80 + "\n")

# Chercher tous les <font> avec un score
all_fonts = soup.find_all('font')
fonts_with_score = []

for font in all_fonts:
    text = font.get_text(strip=True)
    match = re.match(r'^(\d+)\s*[-:]\s*(\d+)$', text)
    if match:
        color_attr = font.get('color', '')
        style_attr = font.get('style', '')
        parent = font.parent

        parent_info = ""
        if parent:
            parent_attrs = []
            if parent.get('width'):
                parent_attrs.append(f"width='{parent.get('width')}'")
            if parent.get('align'):
                parent_attrs.append(f"align='{parent.get('align')}'")
            if parent.get('valign'):
                parent_attrs.append(f"valign='{parent.get('valign')}'")
            parent_info = f"<{parent.name} {' '.join(parent_attrs)}>"

        fonts_with_score.append({
            'text': text,
            'color': color_attr,
            'style': style_attr,
            'parent': parent_info
        })

print(f"📊 Trouvé {len(fonts_with_score)} <font> avec un score\n")

# Afficher les 10 premiers
for i, data in enumerate(fonts_with_score[:10], 1):
    print(f"{i:2d}. Score: '{data['text']}'")
    print(f"    color: '{data['color']}'")
    print(f"    style: '{data['style'][:80] if data['style'] else ''}'")
    print(f"    parent: {data['parent']}")
    print()

print("="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80 + "\n")
