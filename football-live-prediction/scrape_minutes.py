from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

URL = "https://www.soccerstats.com/teamstats.asp?league=england&stats=u324-arsenal#m9"   # ← Remplace par l’URL du match Arsenal

def scrape_minutes_js(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("⏳ Chargement de la page...")
        page.goto(url, timeout=60000)

        page.wait_for_load_state("networkidle")
        time.sleep(2)

        html = page.content()
        browser.close()

    return html


def extract_goals_minutes(html):
    soup = BeautifulSoup(html, "html.parser")
    goals = []

    for tag in soup.find_all(text=True):
        text = tag.strip()
        if "'" in text and any(c.isdigit() for c in text):
            goals.append(text)

    for el in soup.find_all(["span", "div"]):
        if el.text and "'" in el.text:
            goals.append(el.text.strip())

    goals = list(set(goals))
    return goals


if __name__ == "__main__":
    html = scrape_minutes_js(URL)
    print("📄 HTML récupéré ! Extraction des minutes...")

    minutes = extract_goals_minutes(html)
    print("\n🎯 Minutes détectées:")
    for m in minutes:
        print("➡️", m)
