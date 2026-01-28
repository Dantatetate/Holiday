import requests
from bs4 import BeautifulSoup

URL = "https://my-calend.ru/holidays/2025"
HEADERS = {"User-Agent": "Mozilla/5.0"}

r = requests.get(URL, timeout=30, headers=HEADERS)
r.raise_for_status()
soup = BeautifulSoup(r.text, "lxml")

span = soup.find("span", string=lambda s: s and s.strip() == "8 марта")
print("span found:", bool(span))

a = span.find_parent("a") if span else None
if not a:
    a = span.find_previous("a", href=True) if span else None

print("a:", a)
if a:
    print("href:", a.get("href"))
