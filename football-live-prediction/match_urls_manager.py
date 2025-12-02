#!/usr/bin/env python3
# ============================================================================
# MATCH URLs MANAGER
# ============================================================================
# Gestionnaire d'URLs de matchs pour le monitoring continu
# ============================================================================

import json
import os
from datetime import datetime

URLS_FILE = '/workspaces/paris-live/football-live-prediction/config/match_urls.json'

# URLs de matchs populaires SoccerStats
SAMPLE_URLS = {
    "Bulgaria": "https://www.soccerstats.com/pmatch.asp?league=bulgaria&stats=141-2-5-2026",
    "France_Ligue1": "https://www.soccerstats.com/pmatch.asp?league=france&stats=141-2-5-2026",
    "Spain_LaLiga": "https://www.soccerstats.com/pmatch.asp?league=spain&stats=141-2-5-2026",
    "Germany_Bundesliga": "https://www.soccerstats.com/pmatch.asp?league=germany&stats=141-2-5-2026",
    "Italy_SerieA": "https://www.soccerstats.com/pmatch.asp?league=italy&stats=141-2-5-2026",
    "England_PremierLeague": "https://www.soccerstats.com/pmatch.asp?league=england&stats=141-2-5-2026",
    "Portugal_Primeira": "https://www.soccerstats.com/pmatch.asp?league=portugal&stats=141-2-5-2026",
}

def load_urls() -> list:
    """Charge les URLs depuis le fichier config"""
    if os.path.exists(URLS_FILE):
        with open(URLS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('urls', [])
    return []

def save_urls(urls: list):
    """Sauvegarde les URLs dans le fichier config"""
    os.makedirs(os.path.dirname(URLS_FILE), exist_ok=True)
    data = {
        'urls': urls,
        'last_updated': datetime.now().isoformat(),
        'total': len(urls)
    }
    with open(URLS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_url(url: str, name: str = None):
    """Ajoute une URL"""
    urls = load_urls()
    urls.append({'url': url, 'name': name or url, 'added': datetime.now().isoformat()})
    save_urls(urls)
    print(f"✅ URL ajoutée: {url}")

def remove_url(url: str):
    """Supprime une URL"""
    urls = load_urls()
    urls = [u for u in urls if u.get('url') != url]
    save_urls(urls)
    print(f"✅ URL supprimée: {url}")

def list_urls():
    """Liste toutes les URLs"""
    urls = load_urls()
    print("\n📋 URLs configurées:")
    for i, item in enumerate(urls, 1):
        print(f"  {i}. {item.get('name')} - {item.get('url')}")
    print(f"\nTotal: {len(urls)} URLs")

def reset_to_default():
    """Réinitialise aux URLs par défaut"""
    urls = [{'url': v, 'name': k, 'added': datetime.now().isoformat()} 
            for k, v in SAMPLE_URLS.items()]
    save_urls(urls)
    print(f"✅ {len(urls)} URLs par défaut chargées")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python match_urls_manager.py [list|add|remove|reset]")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == 'list':
        list_urls()
    elif command == 'add' and len(sys.argv) >= 3:
        url = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else None
        add_url(url, name)
    elif command == 'remove' and len(sys.argv) >= 3:
        url = sys.argv[2]
        remove_url(url)
    elif command == 'reset':
        reset_to_default()
    else:
        print("❌ Commande inconnue")
