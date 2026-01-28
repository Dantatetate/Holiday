import sqlite3
import requests
from bs4 import BeautifulSoup
import time

DB_PATH = "db/holidays.sqlite"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract_description(url: str) -> str:
    try:
        r = requests.get(url, timeout=20, headers=HEADERS)
        r.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(r.text, "lxml")

    article = soup.find("article") or soup.find("div", class_="entry-content")
    if not article:
        return ""

    for p in article.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text and len(text) > 60:
            return text

    return ""


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT m.id, m.url
        FROM mentions m
        JOIN sources s ON s.id = m.source_id
        WHERE s.name = 'my-calend.ru'
          AND (m.description IS NULL OR m.description = '')
        """
    ).fetchall()

    print("Need to enrich:", len(rows))

    done = 0

    for mid, url in rows:
        if not url:
            continue

        print("[GET]", url)
        desc = extract_description(url)

        if desc:
            cur.execute(
                "UPDATE mentions SET description=? WHERE id=?",
                (desc, mid),
            )
            done += 1

        time.sleep(0.5)

        if done % 50 == 0 and done > 0:
            conn.commit()
            print("Saved:", done)

    conn.commit()
    conn.close()

    print("Enriched:", done)


if __name__ == "__main__":
    main()
