# 🏆 LEAGUE IDs - Référence Complète

## 📌 Utilisation

Le `league_id` est le code utilisé dans les URLs SoccerStats pour identifier une ligue.

**Format URL:** `https://www.soccerstats.com/latest.asp?league={league_id}`

**Exemple:**
```
https://www.soccerstats.com/latest.asp?league=france
                                              ↑↑↑↑↑
                                          league_id
```

---

## 🌍 Liste Complète des League IDs

### 🇫🇷 FRANCE
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Ligue 1 | `france` | Tier 1 |
| Ligue 2 | `france2` | Tier 2 |

### 🇩🇪 GERMANY
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Bundesliga | `germany` | Tier 1 |
| 2. Bundesliga | `germany2` | Tier 2 |

### 🇮🇹 ITALY
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Serie A | `italy` | Tier 1 |

### 🇵🇹 PORTUGAL
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Liga Portugal | `portugal` | Tier 1 |
| Liga Portugal 2 | `portugal2` | Tier 2 |

### 🏴󠁧󠁢󠁳󠁣󠁴󠁿 SCOTLAND
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Premiership | `scotland` | Tier 1 |

### 🇪🇸 SPAIN
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| LaLiga | `spain` | Tier 1 |
| LaLiga 2 | `spain2` | Tier 2 |

### 🇨🇭 SWITZERLAND
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Super League | `switzerland` | Tier 1 |

### 🇦🇹 AUSTRIA
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Bundesliga | `austria` | Tier 1 |
| 2. Liga | `austria2` | Tier 2 |

### 🇧🇬 BULGARIA
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Parva liga | `bulgaria` | Tier 1 |

### 🇭🇷 CROATIA
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| HNL | `croatia` | Tier 1 |
| NL | `croatia2` | Tier 2 |

### 🇨🇿 CZECH REPUBLIC
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| 1. Liga | `czechrepublic` | Tier 1 |
| ChNL | `czechrepublic2` | Tier 2 |

### 🇩🇰 DENMARK
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Superligaen | `denmark` | Tier 1 |

### 🇳🇱 NETHERLANDS
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Eredivisie | `netherlands` | Tier 1 |

### 🇵🇱 POLAND
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Ekstraklasa | `poland` | Tier 1 |

### 🇹🇷 TURKEY
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Super Lig | `turkey` | Tier 1 |

### 🇬🇧 ENGLAND
| Ligue | League ID | Niveau |
|-------|-----------|--------|
| Premier League | `england` | Tier 1 |
| Championship | `england2` | Tier 2 |
| League One | `england3` | Tier 3 |
| League Two | `england4` | Tier 4 |

### 🌍 AUTRES LIGUES
| Pays | Ligue | League ID |
|------|-------|-----------|
| 🇸🇦 Saudi Arabia | Saudi Professional League | `saudiarabia` |
| 🇦🇺 Australia | A-League | `australia` |
| 🇬🇷 Greece | Super League | `greece` |
| 🇸🇮 Slovenia | Prva liga | `slovenia` |
| 🇯🇵 Japan | J1 League | `japan` |
| 🇮🇪 Ireland | Premier Division | `ireland` |
| 🇰🇷 South Korea | K League 1 | `southkorea` |
| 🇰🇷 South Korea | WK League Women | `southkorea4` |
| 🇦🇷 Argentina | Liga Profesional - Apertura | `argentina` |
| 🇨🇱 Chile | Primera Division | `chile` |
| 🇪🇪 Estonia | Meistriliiga | `estonia` |
| 🇫🇴 Faroe Islands | Premier League | `faroeislands` |
| 🇫🇮 Finland | Veikkausliiga | `finland` |
| 🇮🇸 Iceland | Besta deild | `iceland` |
| 🇱🇻 Latvia | Virsliga | `latvia` |
| 🇸🇪 Sweden | Allsvenskan | `sweden` |
| 🇺🇸 USA | MLS | `usa` |

---

## 🔍 Exemple d'Utilisation

### Scraper une ligue
```python
from scrapers.soccerstats_historical import SoccerStatsHistoricalScraper

scraper = SoccerStatsHistoricalScraper()

# Scraper la Ligue 1 française
url = scraper._build_url(league_code='france')
html = scraper.fetch_page(url)
soup = scraper.parse_html(html)

# Extraire les stats pour venue 'overall'
df = scraper._extract_timing_table_for_venue(soup, 'france', 'overall')
```

### Récupérer les équipes d'une ligue
```python
import yaml

config = yaml.safe_load(open('config/config.yaml'))

# Toutes les équipes de Ligue 1
france_teams = [name for name, data in config['teams'].items() 
                if data['league'] == 'france']

print(france_teams)
# ['PSG', 'Lyon', 'Marseille', 'Nice', ...]
```

---

## 📊 Statistiques

| Métrique | Valeur |
|----------|--------|
| **League IDs totaux** | 40+ |
| **Pays couverts** | 30+ |
| **Ligues principales** | 17 |
| **Divisions secondaires** | 15+ |

---

## 🚀 Comment Utiliser

### 1. Scraper les équipes d'une ligue
```bash
cd football-live-prediction
python scrapers/generate_team_ids.py
```

### 2. Récupérer les stats historiques
```bash
python scrapers/soccerstats_historical.py
```

### 3. Faire des prédictions
```bash
python main_live_predictor.py
```

---

**Dernière mise à jour:** 26 Nov 2025
**Total d'équipes:** 243
**Total de ligues:** 40+
