#!/usr/bin/env python3
"""
Test match Portugal en live
Détection + Analyse + Message Telegram
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import json
import sqlite3
from datetime import datetime

# Config Telegram
TELEGRAM_CONFIG = "/workspaces/paris-live/telegram_config.json"

# Charger whitelist Portugal
with open("/workspaces/paris-live/football-live-prediction/whitelists/portugal_whitelist.json", "r", encoding="utf-8") as f:
    whitelist_data = json.load(f)

print(f"✓ Whitelist Portugal chargée: {len(whitelist_data['qualified_teams'])} patterns qualifiés")
print()

# 1. Détecter les matchs live Portugal
print("🔍 DÉTECTION MATCHS LIVE PORTUGAL")
print("="*70)

url = "https://www.soccerstats.com/live.asp"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Trouver les matchs Portugal
    portugal_matches = []
    
    # Chercher les sections de championnat
    championship_headers = soup.find_all(['h3', 'h2', 'div'], class_=lambda x: x and 'championship' in str(x).lower())
    
    # Approche plus large : chercher tous les liens qui contiennent "portugal"
    all_links = soup.find_all('a', href=True)
    portugal_sections = [link for link in all_links if 'portugal' in link.get('href', '').lower()]
    
    if portugal_sections:
        print(f"✓ {len(portugal_sections)} liens Portugal trouvés")
        
        # Chercher les tables de matchs à proximité
        for section in portugal_sections[:3]:  # Limiter aux 3 premiers
            parent = section.find_parent(['div', 'table'])
            if parent:
                # Chercher les lignes de match
                match_rows = parent.find_all('tr')
                for row in match_rows:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        # Format typique: Minute | Home | Score | Away | Stats
                        minute_cell = cells[0].get_text(strip=True)
                        
                        # Vérifier si c'est un match en cours (minute affichée)
                        if minute_cell and minute_cell.replace("'", "").isdigit():
                            minute = int(minute_cell.replace("'", ""))
                            home_team = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            score = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            away_team = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                            
                            if home_team and away_team and score and '-' in score:
                                portugal_matches.append({
                                    'minute': minute,
                                    'home': home_team,
                                    'away': away_team,
                                    'score': score
                                })
    
    # Affichage
    if not portugal_matches:
        print("⚠️  Aucun match Portugal détecté en live")
        print()
        print("🔄 Scraping alternatif de la page complète...")
        
        # Afficher un échantillon de la page pour debug
        text_content = soup.get_text()
        if 'portugal' in text_content.lower() or 'liga' in text_content.lower():
            print("✓ Contenu 'Portugal' trouvé dans la page")
            
            # Extraire toutes les tables
            tables = soup.find_all('table')
            print(f"✓ {len(tables)} tables trouvées sur la page")
            
            # Chercher dans toutes les tables
            for idx, table in enumerate(tables):
                rows = table.find_all('tr')
                for row in rows:
                    text = row.get_text()
                    if any(keyword in text.lower() for keyword in ['benfica', 'sporting', 'porto', 'braga', 'guimaraes']):
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            print(f"\nTable {idx} - Match potentiel trouvé:")
                            for i, cell in enumerate(cells[:6]):
                                print(f"  Cell {i}: {cell.get_text(strip=True)}")
        else:
            print("❌ Aucun contenu Portugal trouvé")
    else:
        print(f"✓ {len(portugal_matches)} match(s) Portugal en live détecté(s)")
        print()
        
        for match in portugal_matches:
            print(f"⚽ {match['home']} vs {match['away']}")
            print(f"   Minute: {match['minute']}' | Score: {match['score']}")
            print()
            
            # Analyser si équipes dans whitelist
            home_qualified = any(
                t['team_name'].lower() == match['home'].lower() 
                for t in whitelist_data['qualified_teams']
            )
            away_qualified = any(
                t['team_name'].lower() == match['away'].lower() 
                for t in whitelist_data['qualified_teams']
            )
            
            if home_qualified or away_qualified:
                print("   ✅ ÉQUIPE(S) QUALIFIÉE(S) - Analyse nécessaire")
                if home_qualified:
                    print(f"      • {match['home']} (HOME)")
                if away_qualified:
                    print(f"      • {match['away']} (AWAY)")
            else:
                print("   ⚠️  Aucune équipe qualifiée - Match ignoré")
            print()

except Exception as e:
    print(f"❌ Erreur scraping: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("✅ Test terminé")
