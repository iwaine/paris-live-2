#!/usr/bin/env python3
"""
Scraper SoccerStats - Extraction classement avec récents matchs
Support pour parsing du format HTML fourni en exemple
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Any
import time

class SoccerStatsStandingsScraper:
    """Scrape les classements SoccerStats"""
    
    def __init__(self, timeout=15, retry=3):
        self.timeout = timeout
        self.retry = retry
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
    
    def fetch_with_retry(self, url: str) -> requests.Response:
        """Récupère l'URL avec retry automatique"""
        for attempt in range(self.retry):
            try:
                print(f"📥 Tentative {attempt+1}/{self.retry}: {url}")
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                print(f"   ⚠ Erreur: {e}")
                if attempt < self.retry - 1:
                    wait = 2 ** attempt
                    print(f"   ⏳ Attente {wait}s avant nouvelle tentative...")
                    time.sleep(wait)
        
        raise Exception(f"Impossible de récupérer {url} après {self.retry} tentatives")
    
    def extract_team_data_from_row(self, row) -> Dict[str, Any]:
        """
        Extrait les données d'une ligne du tableau des classements
        
        Structure attendue:
        | Rank | Team (link) | GP | W | D | L | GF | GA | GD | Pts | Form | PPG | Last8 | CS | SR | MPP |
        """
        tds = row.find_all('td')
        if len(tds) < 12:
            return None
        
        try:
            data = {}
            
            # Rank
            data['rank'] = int(tds[0].get_text(strip=True))
            
            # Team name & link
            team_link = tds[1].find('a')
            if not team_link:
                return None
            
            data['name'] = team_link.get_text(strip=True)
            href = team_link.get('href', '')
            
            # Extract team_id: u512-lens from "teamstats.asp?league=france&stats=u512-lens"
            match = re.search(r'stats=([^&\s"\']+)', href)
            data['team_id'] = match.group(1) if match else None
            data['stats_url'] = href
            
            # Stats: GP, W, D, L
            data['gp'] = int(tds[2].get_text(strip=True))
            
            # W, D, L (peuvent être des liens)
            for stat_idx, stat_key in [(3, 'w'), (4, 'd'), (5, 'l')]:
                link = tds[stat_idx].find('a')
                data[stat_key] = int(link.get_text(strip=True) if link else tds[stat_idx].get_text(strip=True))
            
            # GF, GA, GD, Pts
            data['gf'] = int(tds[6].get_text(strip=True))
            data['ga'] = int(tds[7].get_text(strip=True))
            data['gd'] = int(tds[8].get_text(strip=True))
            data['pts'] = int(tds[9].get_text(strip=True))
            
            # Recent matches from tooltip
            data['recent_matches'] = self.extract_recent_matches(tds[10])
            
            # PPG, Last8, CS, SR
            data['ppg'] = float(tds[11].get_text(strip=True))
            data['last8'] = float(tds[12].get_text(strip=True))
            
            cs_text = tds[13].get_text(strip=True).rstrip('%')
            data['cs_percent'] = float(cs_text) if cs_text else 0.0
            
            sr_text = tds[14].get_text(strip=True).rstrip('%')
            data['sr_percent'] = float(sr_text) if sr_text else 0.0
            
            # MPP (Maximum Possible Points)
            if len(tds) > 15:
                data['mpp'] = int(tds[15].get_text(strip=True))
            
            return data
            
        except (ValueError, AttributeError, IndexError) as e:
            print(f"  ❌ Erreur parsing ligne: {e}")
            return None
    
    def extract_recent_matches(self, form_td) -> List[Dict[str, str]]:
        """
        Extrait les matchs récents du tooltip Form
        
        Format HTML:
        <table>
          <tr>
            <td>Date</td>
            <td>Home - Away</td>
            <td>Score</td>
          </tr>
        </table>
        """
        matches = []
        
        # Find tooltip table
        tooltip_table = form_td.find('table', recursive=True)
        if not tooltip_table:
            return matches
        
        for row in tooltip_table.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) < 3:
                continue
            
            try:
                date_str = tds[0].get_text(strip=True)
                match_str = tds[1].get_text(strip=True)
                score_str = tds[2].get_text(strip=True)
                
                # Déterminer si home ou away (team en <b> = home)
                bold_team = tds[1].find('b')
                team_home = bold_team.get_text(strip=True) if bold_team else None
                
                matches.append({
                    'date': date_str,
                    'match': match_str,
                    'score': score_str,
                    'team_home': team_home
                })
            except Exception as e:
                print(f"  ⚠ Erreur extraction match: {e}")
        
        return matches
    
    def scrape_standings(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape le classement complet d'une ligue
        """
        try:
            response = self.fetch_with_retry(url)
        except Exception as e:
            print(f"❌ Impossible de récupérer {url}: {e}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find standings table
        table = soup.find('table', {'id': 'btable'})
        if not table:
            print("❌ Tableau de classement (btable) non trouvé")
            return []
        
        teams = []
        rows = table.find_all('tr', {'class': 'odd'})
        print(f"✅ Trouvé {len(rows)} équipes\n")
        
        for i, row in enumerate(rows, 1):
            data = self.extract_team_data_from_row(row)
            if data:
                teams.append(data)
                recent = f" | {len(data['recent_matches'])} matchs" if data['recent_matches'] else ""
                print(f"  {i:2d}. {data['name']:20s} | {data['gp']:2d}J {data['w']}V-{data['d']}N-{data['l']}D | {data['gf']:2d}-{data['ga']:2d} | {data['pts']:2d}pts{recent}")
        
        return teams
    
    def save_data(self, teams: List[Dict], output_file: str = 'data/standings.json'):
        """Sauvegarde les données extraites"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Données sauvegardées: {output_file}")
        print(f"   Total: {len(teams)} équipes")


def scrape_soccerstats_standings(league_url):
    """
    Scrape le tableau de classement SoccerStats
    
    Args:
        league_url: URL de la page de classement (ex: ligue française)
    
    Returns:
        list: Liste des équipes avec stats complètes
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"📥 Récupération: {league_url}")
        response = requests.get(league_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Trouver le tableau avec id="btable"
    table = soup.find('table', {'id': 'btable'})
    if not table:
        print("❌ Tableau 'btable' non trouvé")
        return []
    
    teams = []
    rows = table.find_all('tr', {'class': 'odd'})
    
    print(f"✅ Trouvé {len(rows)} équipes")
    
    for row in rows:
        try:
            team_data = extract_team_row(row)
            if team_data:
                teams.append(team_data)
                print(f"  ✓ {team_data['name']:20s} | GP:{team_data['gp']:2d} | GF:{team_data['gf']:2d} | GA:{team_data['ga']:2d} | Pts:{team_data['pts']:2d}")
        except Exception as e:
            print(f"  ⚠ Erreur extraction ligne: {e}")
            continue
    
    return teams


def extract_team_row(row):
    """
    Extrait les données d'une ligne d'équipe
    
    Format du tableau:
    | Rank | Team (link) | GP | W | D | L | GF | GA | GD | Pts | Form | PPG | Last8 | CS | SR | MPP |
    """
    tds = row.find_all('td')
    if len(tds) < 12:
        return None
    
    team_data = {}
    
    try:
        # 0: Ranking
        team_data['rank'] = int(tds[0].get_text(strip=True))
        
        # 1: Team name et link
        team_link = tds[1].find('a')
        if team_link:
            team_data['name'] = team_link.get_text(strip=True)
            href = team_link.get('href', '')
            # Extraire team_id du lien: teamstats.asp?league=france&stats=u512-lens
            match = re.search(r'stats=([^&\s]+)', href)
            team_data['team_id'] = match.group(1) if match else None
            team_data['link'] = href
        else:
            return None
        
        # 2-5: GP, W, D, L
        team_data['gp'] = int(tds[2].get_text(strip=True))
        team_data['w'] = int(tds[3].find('a').get_text(strip=True) if tds[3].find('a') else tds[3].get_text(strip=True))
        team_data['d'] = int(tds[4].find('a').get_text(strip=True) if tds[4].find('a') else tds[4].get_text(strip=True))
        team_data['l'] = int(tds[5].find('a').get_text(strip=True) if tds[5].find('a') else tds[5].get_text(strip=True))
        
        # 6-9: GF, GA, GD, Pts
        team_data['gf'] = int(tds[6].get_text(strip=True))
        team_data['ga'] = int(tds[7].get_text(strip=True))
        team_data['gd'] = int(tds[8].get_text(strip=True))
        team_data['pts'] = int(tds[9].get_text(strip=True))
        
        # 10: Form (tooltip) - extraire les matchs récents
        team_data['recent_matches'] = extract_form_tooltip(tds[10])
        
        # 11-14: PPG, Last8, CS, SR
        team_data['ppg'] = float(tds[11].get_text(strip=True))
        team_data['last8'] = float(tds[12].get_text(strip=True))
        cs_text = tds[13].get_text(strip=True).replace('%', '')
        team_data['cs'] = float(cs_text) if cs_text else 0.0
        sr_text = tds[14].get_text(strip=True).replace('%', '')
        team_data['sr'] = float(sr_text) if sr_text else 0.0
        
        # 15: MPP (Maximum Possible Points)
        if len(tds) > 15:
            team_data['mpp'] = int(tds[15].get_text(strip=True))
        
        return team_data
        
    except (ValueError, AttributeError, IndexError) as e:
        print(f"  ❌ Erreur parsing: {e}")
        return None


def extract_form_tooltip(td):
    """
    Extrait les matchs récents du tooltip (formulaire de forme)
    
    Format du tooltip:
    <table> avec lignes pour chaque match:
    | Date | Match (Team1 vs Team2) | Score |
    """
    recent_matches = []
    
    # Trouver le tableau dans le tooltip
    tooltip_table = td.find('table', recursive=True)
    if not tooltip_table:
        return recent_matches
    
    rows = tooltip_table.find_all('tr')
    
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 3:
            try:
                # Date
                date_text = tds[0].get_text(strip=True)
                
                # Match et résultat
                match_text = tds[1].get_text(strip=True)
                score_text = tds[2].get_text(strip=True)
                
                # Déterminer si home ou away
                # Format: "Team1 - Team2" ou "Team1   Team2" (avec team1 en bold = home)
                is_home = tds[1].find('b') is not None and tds[1].find('b').get_text(strip=True)
                
                recent_matches.append({
                    'date': date_text,
                    'match': match_text,
                    'score': score_text,
                    'is_home': is_home
                })
            except Exception as e:
                print(f"  ⚠ Erreur extraction match: {e}")
                continue
    
    return recent_matches


def save_standings_data(teams, output_file='data/standings.json'):
    """Sauvegarde les données en JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(teams, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Données sauvegardées: {output_file}")


if __name__ == '__main__':
    # URL exemple: page de classement Ligue 1 France
    # Remplacer par l'URL réelle si nécessaire
    league_url = "https://www.soccerstats.com/standings.asp?league=france"
    
    print("🔍 Scraping du classement SoccerStats\n")
    teams = scrape_soccerstats_standings(league_url)
    
    if teams:
        print(f"\n✅ Extraction complète: {len(teams)} équipes")
        print("\n" + "="*80)
        print("RÉSUMÉ CLASSEMENT")
        print("="*80)
        for team in teams[:5]:  # Afficher top 5
            print(f"\n{team['rank']}. {team['name'].upper()}")
            print(f"   Stats: {team['gp']}J | {team['w']}V-{team['d']}N-{team['l']}D")
            print(f"   Buts: {team['gf']}-{team['ga']} | GD: {team['gd']:+d} | Pts: {team['pts']}")
            print(f"   PPG: {team['ppg']:.2f} | CS: {team['cs']:.0f}% | SR: {team['sr']:.0f}%")
            if team['recent_matches']:
                print(f"   Derniers matchs: {len(team['recent_matches'])} trouvés")
        
        # Sauvegarder
        save_standings_data(teams)
    else:
        print("❌ Aucune donnée extraite")
