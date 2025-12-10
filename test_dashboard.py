#!/usr/bin/env python3
"""
🧪 Simulateur de Match Live
Envoie des données de test au dashboard pour tester l'interface
"""

import requests
import json
import time

DASHBOARD_URL = "http://localhost:5000"

def test_dashboard_api():
    """Teste les APIs du dashboard"""
    print("🧪 TEST DES APIs DU DASHBOARD")
    print("="*70)
    
    # Test 1: Status
    print("\n1️⃣ Test /api/status")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Monitoring actif: {data['monitoring_active']}")
            print(f"   🎯 Prédicteurs: {data['predictors_available']}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Matches
    print("\n2️⃣ Test /api/matches")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/matches")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ⚽ Matchs détectés: {data['count']}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Whitelists
    print("\n3️⃣ Test /api/whitelists")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/whitelists")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   🏆 Ligues chargées: {len(data)}")
            for league, info in list(data.items())[:3]:
                print(f"      • {info['name']}: {info['teams_count']} équipes qualifiées")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4: Page HTML
    print("\n4️⃣ Test Page HTML")
    try:
        response = requests.get(f"{DASHBOARD_URL}/")
        if response.status_code == 200:
            print(f"   ✅ Status: {response.status_code}")
            if "Paris Live" in response.text:
                print(f"   ✅ Contenu HTML valide")
            else:
                print(f"   ⚠️  Contenu inattendu")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "="*70)
    print("✅ Tests terminés !")
    print("\n💡 Ouvrez http://localhost:5000 dans votre navigateur")
    print("   puis cliquez sur '▶️ Démarrer' pour lancer le monitoring")

if __name__ == '__main__':
    test_dashboard_api()
