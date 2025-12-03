#!/usr/bin/env python3
"""
Debug: Analyser comment le score est stylé sur la page pmatch.asp
"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.soccerstats.com/pmatch.asp?league=bosnia&stats=82-2-7-2026"

session = requests.Session()
session.trust_env = False
headers = {'User-Agent': 'Mozilla/5.0'}

response = session.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'lxml')

print("\n" + "="*80)
print("🔍 ANALYSE: Comment le score est stylé")
print("="*80 + "\n")

# Chercher tous les patterns de score dans le texte
all_text = soup.get_text()
score_patterns = re.findall(r'\b(\d+)\s*[-:]\s*(\d+)\b', all_text)
print(f"📊 Patterns de score trouvés dans le texte: {len(score_patterns)}")
for i, (h, a) in enumerate(score_patterns[:5], 1):
    print(f"  {i}. {h} - {a}")

print("\n" + "-"*80)
print("🔍 ANALYSE DES <font> AVEC SCORE")
print("-"*80 + "\n")

# Chercher tous les <font>
all_fonts = soup.find_all('font')
print(f"Total <font> sur la page: {len(all_fonts)}\n")

fonts_with_score = []

for font in all_fonts:
    text = font.get_text(strip=True)

    # Vérifier si c'est un score (pattern X - X)
    match = re.match(r'^(\d+)\s*[-:]\s*(\d+)$', text)
    if match:
        style = font.get('style', '')
        color_attr = font.get('color', '')

        fonts_with_score.append({
            'text': text,
            'color': color_attr,
            'style': style,
            'font': font
        })

print(f"📊 Trouvé {len(fonts_with_score)} <font> contenant un score\n")

for i, data in enumerate(fonts_with_score, 1):
    print(f"\n{i}. Score: '{data['text']}'")
    print(f"   color attribute: '{data['color']}'")
    print(f"   style attribute: '{data['style']}'")

    # Afficher le HTML complet du font
    print(f"   HTML: {str(data['font'])[:200]}")

    # Chercher les parents
    parent = data['font'].parent
    if parent:
        print(f"   Parent: <{parent.name}>")
        if hasattr(parent, 'attrs'):
            print(f"   Parent attrs: {dict(list(parent.attrs.items())[:3])}")

print("\n" + "="*80)
print("🔍 CHERCHER LE SCORE SPÉCIFIQUEMENT")
print("="*80 + "\n")

# Méthode 1: Chercher avec #87CEFA
score_87cefa = []
for font in all_fonts:
    style = font.get('style', '')
    if '#87CEFA' in style.upper():
        text = font.get_text(strip=True)
        if re.match(r'^\d+\s*[-:]\s*\d+$', text):
            score_87cefa.append(text)

print(f"Scores avec #87CEFA: {score_87cefa}")

# Méthode 2: Chercher avec color="blue" et taille >= 26px
score_blue = []
for font in all_fonts:
    color_attr = font.get('color', '')
    style = font.get('style', '')

    if 'blue' in color_attr.lower() or 'blue' in style.lower():
        text = font.get_text(strip=True)
        if re.match(r'^\d+\s*[-:]\s*\d+$', text):
            has_size = any(size in style for size in ['26px', '36px', '30px', '32px'])
            score_blue.append({
                'text': text,
                'style': style,
                'color': color_attr,
                'has_large_size': has_size
            })

print(f"\nScores bleus: {len(score_blue)}")
for s in score_blue:
    print(f"  - {s['text']} (size: {s['has_large_size']}, style: {s['style'][:60]})")

print("\n" + "="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80 + "\n")
