import json
import os
import re
import sqlite3
from datetime import datetime

DB_PATH = "db/holidays.sqlite"
SCHEMA_PATH = "db/schema.sql"

FILES = [
    ("data/raw_calend.jsonl", "calend.ru"),
    ("data/raw_my_calend_2025_enriched.jsonl", "my-calend.ru"),
    ("data/raw_wiki_2025.jsonl", "wikipedia.org"),
]

def normalize_title(s: str) -> str:
    s = (s or "").lower().strip().replace("ё", "е")
    s = re.sub(r"[^a-zа-я0-9\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def detect_lang(text: str) -> str:
    return "ru" if re.search(r"[а-яё]", (text or "").lower()) else "en"

def main():
    os.makedirs("db", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    conn.commit()

    source_cache = {}
    holiday_cache = {}
    occurrence_cache = {}
    now = datetime.utcnow().isoformat(timespec="seconds")

    def get_source_id(name: str) -> int:
        if name in source_cache:
            return source_cache[name]
        cur.execute("INSERT OR IGNORE INTO sources(name) VALUES (?)", (name,))
        cur.execute("SELECT id FROM sources WHERE name=?", (name,))
        sid = cur.fetchone()[0]
        source_cache[name] = sid
        return sid

    def get_holiday_id(title_raw: str, title_norm: str, lang: str) -> int:
        key = (lang, title_norm)
        if key in holiday_cache:
            return holiday_cache[key]
        cur.execute("SELECT id FROM holidays WHERE canonical_title_norm=? AND lang=?", (title_norm, lang))
        row = cur.fetchone()
        if row:
            hid = row[0]
        else:
            cur.execute(
                "INSERT INTO holidays(canonical_title, canonical_title_norm, lang) VALUES (?,?,?)",
                (title_raw, title_norm, lang)
            )
            hid = cur.lastrowid
        holiday_cache[key] = hid
        return hid

    def get_occurrence_id(holiday_id: int, date_str: str) -> int:
        key = (holiday_id, date_str)
        if key in occurrence_cache:
            return occurrence_cache[key]
        cur.execute("INSERT OR IGNORE INTO occurrences(holiday_id, date) VALUES (?,?)", (holiday_id, date_str))
        cur.execute("SELECT id FROM occurrences WHERE holiday_id=? AND date=?", (holiday_id, date_str))
        oid = cur.fetchone()[0]
        occurrence_cache[key] = oid
        return oid

    for path, source_name in FILES:
        sid = get_source_id(source_name)
        loaded_here = 0

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)

                date_str = obj.get("date")
                title_raw = (obj.get("title_raw") or "").strip()
                if not date_str or not title_raw:
                    continue

                title_raw = re.sub(r"\[\s*\d+\s*\]", "", title_raw).strip()
                title_raw = re.sub(r"\s*\((ru|en)\)\s*$", "", title_raw, flags=re.I).strip()

                low = title_raw.lower()

                if re.fullmatch(r"\d+\s*день", low):
                    continue

                bad_starts = ("именины", "народный календарь", "хроника", "персоны", "ближайшие дни")
                if low.startswith(bad_starts):
                    continue
                if low in {"праздники", "международные праздники", "католические праздники", "православные праздники"}:
                    continue

                title_norm = obj.get("title_norm") or normalize_title(title_raw)
                if not title_norm:
                    continue

                lang = detect_lang(title_raw)

                hid = get_holiday_id(title_raw, title_norm, lang)
                oid = get_occurrence_id(hid, date_str)

                url = obj.get("holiday_url") or obj.get("url") or ""
                if not url:
                    continue

                description = (obj.get("description") or "").strip()

                cur.execute(
                    """INSERT INTO mentions(occurrence_id, source_id, title_raw, title_norm, description, url, date_parsed)
                       VALUES (?,?,?,?,?,?,?)""",
                    (oid, sid, title_raw, title_norm, description, url, now)
                )

                loaded_here += 1
                if loaded_here % 2000 == 0:
                    print(f"{source_name}: loaded {loaded_here}")

        conn.commit()
        print(f"Loaded {source_name}: {loaded_here} mentions")

    print("DONE")
    print("mentions with desc:",
          cur.execute("select count(*) from mentions where trim(coalesce(description,''))!=''").fetchone()[0])
    print("by source desc:",
          cur.execute("""select s.name, count(*) from mentions m join sources s on s.id=m.source_id
                         where trim(coalesce(m.description,''))!='' group by s.name""").fetchall())

    conn.close()

if __name__ == "__main__":
    main()
