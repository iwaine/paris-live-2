"""Correction avec la bonne URL: timing.asp"""
from pathlib import Path

scraper_path = Path('scrapers/soccerstats_historical_home_away.py')

with open(scraper_path, 'r') as f:
    content = f.read()

# Corriger l'URL - remplacer h2h par timing
content = content.replace(
    "def _build_url(self, league_code: str, page_type: str = 'h2h') -> str:",
    "def _build_url(self, league_code: str, page_type: str = 'timing') -> str:"
)

content = content.replace(
    "url = self._build_url(league_code, 'h2h')",
    "url = self._build_url(league_code, 'timing')"
)

# Si c'était encore timstats, corriger aussi
content = content.replace(
    "def _build_url(self, league_code: str, page_type: str = 'timstats') -> str:",
    "def _build_url(self, league_code: str, page_type: str = 'timing') -> str:"
)

content = content.replace(
    "url = self._build_url(league_code, 'timstats')",
    "url = self._build_url(league_code, 'timing')"
)

with open(scraper_path, 'w') as f:
    f.write(content)

print("✅ URL corrigée: timing.asp")
print("🔗 URL finale: https://www.soccerstats.com/timing.asp?league=england")
