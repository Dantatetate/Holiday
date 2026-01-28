import sqlite3
import time
import requests
from bs4 import BeautifulSoup

DB_PATH = "db/holidays.sqlite"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def extract_description_from_calend(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # основной контент статьи
    content = soup.find("div", {"id": "article"})
    if not content:
        content = soup.find("div", class_="content")

    if not content:
        return ""

    # берём первый нормальный абзац
    for p in content.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text and len(text) > 80:
            return text

    return ""


def extract_description_from_mycalend(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    content = soup.find("div", class_="post-content") or soup.find("article")
    if not content:
        return ""

    for p in content.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text and len(text) > 80:
            return text

    return ""


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # берём все mentions без description, но с holiday_url
    rows = cur.execute("""
        SELECT m.id, m.url, s.name
        FROM mentions m
        JOIN sources s ON s.id = m.source_id
        WHERE (m.description IS NULL OR m.description = '')
          AND m.url IS NOT NULL
          AND m.url != ''
          AND s.name IN ('calend.ru', 'my-calend.ru')
    """).fetchall()

    print("Need to enrich:", len(rows))

    done = 0

    for mid, url, source in rows:
        try:
            if source == "calend.ru":
                desc = extract_description_from_calend(url)
            elif source == "my-calend.ru":
                desc = extract_description_from_mycalend(url)
            else:
                continue

            if desc:
                cur.execute(
                    "UPDATE mentions SET description=? WHERE id=?",
                    (desc, mid)
                )
                conn.commit()
                done += 1
                print(f"[OK] {source} -> {url[:60]}...")
            else:
                print(f"[EMPTY] {source} -> {url}")

        except Exception as e:
            print(f"[ERROR] {source} -> {url} :: {e}")

        time.sleep(0.5)  # чтобы не спамить сайт

    print("Enriched:", done)
    conn.close()


if __name__ == "__main__":
    main()
