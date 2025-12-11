# Méthodologie complète : Du scraping de données à l’analyse live

Ce guide détaille toutes les étapes pour passer du scraping de données football (SoccerStats) à l’analyse live, avec des explications claires pour débutant.

---

## 1. Pré-requis et installation

### a. Environnement Python
- Installe Python (>=3.10) sur ta machine.
- Installe pip :
  ```bash
  sudo apt update && sudo apt install python3-pip
  ```
- Crée un environnement virtuel (optionnel mais recommandé) :
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### b. Librairies nécessaires
Installe les librairies :
```bash
pip install requests beautifulsoup4 selenium pandas numpy
```
Pour le scraping dynamique :
- Installe Chromium et ChromeDriver (Linux) :
  ```bash
  sudo apt install chromium-browser chromium-chromedriver
  ```

---

## 2. Scraping des données

### a. Scraping statique (HTML simple)
Utilise `requests` et `BeautifulSoup` pour extraire les données des pages statiques.
Exemple :
```python
import requests
from bs4 import BeautifulSoup

url = 'https://www.soccerstats.com/latest.asp?league=england2'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
# Extraction des matches, scores, équipes...
```

### b. Scraping dynamique (JavaScript)
Utilise `selenium` pour récupérer le DOM généré dynamiquement.
Exemple :
```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=options)
driver.get(url)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
```

### c. Extraction des données
- Identifie les balises HTML contenant les infos (ex : `<td>`, `<tr>`, `<table>`).
- Utilise BeautifulSoup pour parcourir et extraire :
  ```python
  for row in soup.find_all('tr'):
      # Extraction des colonnes, scores, équipes...
  ```
- Nettoie et structure les données (dictionnaire, DataFrame).

---

## 3. Stockage des données

- Sauvegarde les données dans un fichier CSV ou une base SQLite.
  ```python
  import pandas as pd
  df = pd.DataFrame(liste_de_dicts)
  df.to_csv('matches.csv', index=False)
  # ou
  df.to_sql('matches', sqlite3.connect('db.sqlite'), if_exists='replace')
  ```

---

## 4. Analyse des données historiques

- Charge les données avec pandas.
- Calcule des statistiques : moyennes, fréquences, patterns (ex : buts entre 31-45 min).
  ```python
  df = pd.read_csv('matches.csv')
  print(df['score'].value_counts())
  # Analyse par équipe, par intervalle, etc.
  ```
- Visualise avec matplotlib ou seaborn (optionnel).

---

## 5. Analyse live (monitoring en temps réel)

### a. Scraping live
- Lance un script qui scrape la page toutes les X minutes.
- Compare les nouveaux résultats avec l’historique pour détecter des patterns ou alertes.

### b. Détection d’événements
- Détecte les changements de score, FT/HT, etc.
- Envoie des alertes (console, Telegram, email).
  ```python
  # Exemple d’alerte Telegram
  import requests
  def send_telegram(msg):
      token = 'TON_TOKEN'
      chat_id = 'TON_CHAT_ID'
      url = f'https://api.telegram.org/bot{token}/sendMessage'
      requests.post(url, data={'chat_id': chat_id, 'text': msg})
  ```

### c. Automatisation
- Utilise des boucles et des timers pour automatiser le monitoring.
  ```python
  import time
  while True:
      # Scraping + analyse
      time.sleep(60)  # toutes les minutes
  ```

---

## 6. Bonnes pratiques et conseils

- Toujours vérifier le format des données (HTML peut changer).
- Gérer les exceptions (try/except) pour éviter les crashs.
- Documenter chaque étape et chaque script.
- Tester sur plusieurs ligues/pages pour valider la robustesse.

---

## 7. Ressources utiles
- [Documentation BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Documentation Selenium](https://selenium-python.readthedocs.io/)
- [Documentation pandas](https://pandas.pydata.org/docs/)
- [API Telegram](https://core.telegram.org/bots/api)

---

Ce guide te permet de partir de zéro et d’arriver à un système complet d’analyse live, avec toutes les étapes détaillées et des exemples de code pour chaque phase. Adapte chaque script à tes besoins et n’hésite pas à consulter la documentation officielle des librairies pour approfondir !