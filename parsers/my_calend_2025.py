import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import date

URL = "https://my-calend.ru/holidays/2025"
HEADERS = {"User-Agent": "Mozilla/5.0"}

MONTH_MAP = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
    "мая": "05", "июня": "06", "июля": "07", "августа": "08",
    "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
}

DATE_RE = re.compile(
    r"^\s*(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b",
    re.IGNORECASE
)

def normalize_title(s: str) -> str:
    s = (s or "").lower().strip().replace("ё", "е")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def is_date_tag(tag) -> str | None:
    """
    Возвращает YYYY-MM-DD если tag выглядит как '1 января Ср'
    """
    txt = tag.get_text(" ", strip=True)
    m = DATE_RE.match(txt.lower())
    if not m:
        return None
    day = int(m.group(1))
    mm = MONTH_MAP[m.group(2)]
    return f"2025-{mm}-{day:02d}"

def main():
    r = requests.get(URL, timeout=30, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    body = soup.body or soup
    items = []
    current_date = None

    for tag in body.find_all(True):

        ds = is_date_tag(tag)
        if ds:
            current_date = ds
            continue

        if not current_date:
            continue

        if tag.name == "a" and tag.get("href"):
            title = tag.get_text(" ", strip=True)
            href = tag.get("href", "").strip()

            if not title or len(title) < 3 or len(title) > 140:
                continue

            if "/holidays/" not in href:
                continue

            if href.startswith("http"):
                holiday_url = href
            else:
                holiday_url = "https://my-calend.ru" + href

            if holiday_url.rstrip("/") == URL.rstrip("/"):
                continue

            items.append({
                "date": current_date,
                "title_raw": title,
                "title_norm": normalize_title(title),
                "source": "my-calend.ru",
                "url": URL,
                "holiday_url": holiday_url
            })

    seen = set()
    uniq = []
    for it in items:
        key = (it["date"], it["title_norm"], it["holiday_url"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)

    out = "data/raw_my_calend_2025.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for it in uniq:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print("Saved:", len(uniq), "records to", out)
    if uniq:
        print("Example:", uniq[0])

if __name__ == "__main__":
    main()
