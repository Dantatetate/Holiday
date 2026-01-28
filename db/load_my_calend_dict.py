import json
import re
import sqlite3

DB_PATH = "db/holidays.sqlite"
SRC = "data/raw_my_calend_2025.jsonl"

def normalize_title(s: str) -> str:
    s = (s or "").lower().strip().replace("ё", "е")
    s = re.sub(r"[^a-zа-я0-9\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS descriptions_dict (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title_norm TEXT NOT NULL UNIQUE,
      title_raw TEXT NOT NULL,
      description TEXT NOT NULL,
      url TEXT NOT NULL
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_desc_title_norm ON descriptions_dict(title_norm)")
    con.commit()

    total_lines = 0
    ok = 0
    missing_desc = 0
    missing_url = 0
    missing_title = 0

    first_keys = None
    first_with_desc = None

    with open(SRC, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            obj = json.loads(line)

            if first_keys is None:
                first_keys = list(obj.keys())

            title = (obj.get("title_raw") or "").strip()
            desc = (obj.get("description") or "").strip()
            url = (obj.get("holiday_url") or obj.get("url") or "").strip()

            if not title:
                missing_title += 1
                continue
            if not desc:
                missing_desc += 1
                continue
            if not url:
                missing_url += 1
                continue

            if first_with_desc is None:
                first_with_desc = {
                    "title_raw": title,
                    "description_preview": desc[:120],
                    "url": url
                }

            tn = normalize_title(title)
            if not tn:
                continue

            cur.execute("""
              INSERT OR REPLACE INTO descriptions_dict(title_norm, title_raw, description, url)
              VALUES (?,?,?,?)
            """, (tn, title, desc, url))
            ok += 1

    con.commit()

    print("SRC lines:", total_lines)
    print("First keys:", first_keys)
    print("With description example:", first_with_desc)
    print("Inserted:", ok)
    print("Skipped missing title:", missing_title)
    print("Skipped missing desc:", missing_desc)
    print("Skipped missing url:", missing_url)

    cnt = cur.execute("select count(*) from descriptions_dict").fetchone()[0]
    print("descriptions_dict count:", cnt)

    con.close()

if __name__ == "__main__":
    main()
