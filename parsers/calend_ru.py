import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0"}

BAD_EXACT = {
    "праздники",
    "международные праздники",
    "католические праздники",
    "православные праздники",
    "религиозные",
    "по категориям",
}

STOP_TITLES = {
    "народный календарь",
    "именины",
    "хроника",
    "персоны",
}

def normalize_title(s: str) -> str:
    s = (s or "").lower().strip().replace("ё", "е")
    s = re.sub(r"\s+", " ", s)
    return s

def is_category_like(t: str) -> bool:
    tl = t.lower().strip()
    if tl in BAD_EXACT:
        return True
    if tl.startswith("праздники "):
        return True
    return False

def parse_day(d: date):
    url = f"https://www.calend.ru/day/{d.year}-{d.month:02d}-{d.day:02d}/"
    print("Parsing:", url)

    r = requests.get(url, timeout=25, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    h1 = soup.find("h1")
    if not h1:
        return []
    
    start = h1.find_next("a", string=lambda s: (s or "").strip() == "Праздники")
    if not start:
        return []

    titles = []

    for a in start.find_all_next("a", href=True, limit=1500):
        t = a.get_text(" ", strip=True)
        t = re.sub(r"\s+", " ", (t or "").strip())
        if not t:
            continue

        tl = t.lower().strip()

        if tl in STOP_TITLES:
            break

        if tl in BAD_EXACT:
            continue

        if len(t) > 80:
            continue

        if len(t) < 3:
            continue

        if is_category_like(t):
            continue

        if tl in {"россия", "беларусь", "украина", "казахстан"}:
            continue

        titles.append(t)

    seen = set()
    out = []
    for t in titles:
        tn = normalize_title(t)
        if not tn or tn in seen:
            continue
        seen.add(tn)
        out.append({
            "date": d.isoformat(),
            "title_raw": t,
            "title_norm": tn,
            "description": "",
            "source": "calend.ru",
            "url": url
        })

    return out

def main():
    start = date(2025, 1, 1)
    end = date(2025, 12, 31)

    items = []
    cur = start
    while cur <= end:
        try:
            items.extend(parse_day(cur))
        except Exception as e:
            print("Error:", cur.isoformat(), e)
        cur += timedelta(days=1)

    out_path = "data/raw_calend.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print("Saved:", len(items), "records to", out_path)

if __name__ == "__main__":
    main()
