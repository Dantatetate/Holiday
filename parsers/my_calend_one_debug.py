import re
import requests
from bs4 import BeautifulSoup

URL = "https://my-calend.ru/holidays/novyy-god"
HEADERS = {"User-Agent": "Mozilla/5.0"}

r = requests.get(URL, headers=HEADERS, timeout=30)
print("status:", r.status_code)
soup = BeautifulSoup(r.text, "lxml")

md = soup.select_one("meta[name='description']")
og = soup.select_one("meta[property='og:description']")
print("meta description:", (md.get("content","") if md else "")[:200])
print("og description:", (og.get("content","") if og else "")[:200])

ps = soup.find_all("p")
print("p count:", len(ps))
for i, p in enumerate(ps[:10], 1):
    txt = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
    print(i, len(txt), txt[:160])
