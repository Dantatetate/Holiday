import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

def normalize_title(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def parse_day(d: date):
    url = f"https://en.wikipedia.org/wiki/{MONTH_NAMES[d.month]}_{d.day}"
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    target_h2 = None
    for h2 in soup.select("#mw-content-text h2"):
        txt = h2.get_text(" ", strip=True).lower()
        if "holidays and observances" in txt:
            target_h2 = h2
            break
    if not target_h2:
        return []

    items = []
    seen = set()

    for el in target_h2.next_elements:
        if getattr(el, "name", None) == "h2":
            break

        if getattr(el, "name", None) == "li":
            text = el.get_text(" ", strip=True)
            if not text:
                continue
            if not (3 <= len(text) <= 250):
                continue

            tn = normalize_title(text)
            if tn in seen:
                continue
            seen.add(tn)

            items.append({
                "date": d.isoformat(),
                "title_raw": text,
                "title_norm": tn,
                "source": "wikipedia.org",
                "url": url
            })

    return items

def main():
    start = date(2025, 1, 1)
    end = date(2025, 12, 31)

    out = "data/raw_wiki_2025.jsonl"
    all_items = []

    d = start
    while d <= end:
        print("Parsing:", d.isoformat())
        try:
            all_items.extend(parse_day(d))
        except Exception as e:
            print("Error:", d.isoformat(), e)
        d += timedelta(days=1)

    with open(out, "w", encoding="utf-8") as f:
        for it in all_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print("Saved:", len(all_items), "records to", out)

if __name__ == "__main__":
    main()
