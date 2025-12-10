#!/usr/bin/env python3
"""Inspecteur HTML léger pour la page index de SoccerStats.

Usage: python3 scrape_index_inspect.py /path/to/debug_soccerstats_index.html

Affiche des extraits utiles pour détecter les matches live (liens 'match', occurrences de "min"/"live",
et contextes parents/classes/ids).
"""
from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup


def short(x: str, n: int = 140) -> str:
    return (x.strip().replace('\n', ' ')[:n] + ('...' if len(x.strip()) > n else ''))


def inspect(path: Path):
    html = path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')

    print('PAGE TITLE:', soup.title.string if soup.title else '—')

    anchors = soup.find_all('a', href=True)
    print('\nTotal <a> tags:', len(anchors))

    match_links = [a for a in anchors if 'match' in a['href']]
    print('Links containing "match" (count):', len(match_links))
    for a in match_links[:30]:
        href = a['href']
        text = short(a.get_text(' ', strip=True), 100)
        parent = a.parent.name if a.parent else '—'
        print(f'- {href} | text="{text}" | parent=<{parent}>')

    # keywords to search in text nodes
    keywords = re.compile(r"\b(min|live|in-play)\b|\d{1,3}\s*(?:'|min)", re.I)
    found = []
    for tag in soup.find_all(text=True):
        t = tag.strip()
        if not t:
            continue
        if keywords.search(t):
            parent = tag.parent
            found.append((parent.name, short(t, 200), getattr(parent, 'attrs', {})))

    print('\nFound text nodes matching minute/live patterns (sample 60):', len(found))
    for item in found[:60]:
        tagname, txt, attrs = item
        print(f'- <{tagname}> attrs={attrs} | "{txt}"')

    # inspect tables and divs with many links (possible fixtures lists)
    candidates = []
    for div in soup.find_all(['div', 'table']):
        text = div.get_text(' ', strip=True)
        if len(re.findall(r"\d{1,3}\s*(?:'|min)", text)) >= 1 or 'live' in text.lower():
            candidates.append(div)

    print('\nCandidate containers (div/table) that contain minute/live keywords:', len(candidates))
    for i, c in enumerate(candidates[:12], 1):
        attrs = getattr(c, 'attrs', {})
        print(f"-- candidate #{i} tag=<{c.name}> attrs={attrs} sample_text=\"{short(c.get_text(' ', strip=True), 200)}\"")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 scrape_index_inspect.py /path/to/debug_soccerstats_index.html')
        raise SystemExit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print('File not found:', p)
        raise SystemExit(2)
    inspect(p)
