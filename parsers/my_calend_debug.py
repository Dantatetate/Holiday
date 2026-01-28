import re
import requests
from bs4 import BeautifulSoup

URL = "https://my-calend.ru/holidays/2025"
HEADERS = {"User-Agent": "Mozilla/5.0"}

day_re = re.compile(
    r"^\s*(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b",
    re.I
)

r = requests.get(URL, timeout=30, headers=HEADERS)
r.raise_for_status()
soup = BeautifulSoup(r.text, "lxml")

cand = []
for tag in soup.find_all(True):
    txt = tag.get_text(" ", strip=True)
    if txt and len(txt) < 40 and day_re.match(txt):
        cand.append((tag.name, txt))
        if len(cand) >= 30:
            break

print("Found date-like tags:", len(cand))
for x in cand[:20]:
    print("-", x)
