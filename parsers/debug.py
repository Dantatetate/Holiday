import requests
from bs4 import BeautifulSoup

url = "https://www.calend.ru/day/2025-1-1/"
r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
r.raise_for_status()
soup = BeautifulSoup(r.text, "lxml")

h1 = soup.find("h1")
print("H1:", h1.get_text(" ", strip=True) if h1 else "NO H1")

all_holidays_links = soup.select("a[href*='/holidays/']")
print("Total /holidays/ links on page:", len(all_holidays_links))
print("First 10 titles:")
for a in all_holidays_links[:10]:
    print("-", a.get_text(" ", strip=True))

if h1:
    after_h1 = []
    for a in h1.find_all_next("a", href=True, limit=3000):
        if "/holidays/" in a["href"]:
            after_h1.append(a)
    print("Links /holidays/ after H1:", len(after_h1))
    print("First 10 after H1:")
    for a in after_h1[:10]:
        print("-", a.get_text(" ", strip=True))
