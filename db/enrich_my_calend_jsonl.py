import json
import re
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

IN_PATH = "data/raw_my_calend_2025.jsonl"
OUT_PATH = "data/raw_my_calend_2025_enriched.jsonl"
HEADERS = {"User-Agent": "Mozilla/5.0"}

WORKERS = 10
SLEEP = 0.05 

def clean_description(desc: str, title: str = "") -> str:
    d = (desc or "").strip()
    d = re.sub(r"\s+", " ", d).strip()

    d = re.sub(r"^\d{1,2}\s+[а-яё]+\s+\d{4}\s*[-–—]\s*", "", d, flags=re.I)

    if title:
        t = re.sub(r"\s+", " ", title).strip()
        if t and d.lower().startswith(t.lower()):
            d = d[len(t):].lstrip(" .:-–—")

    bad_tail = [
        "Календарь праздников", "Календарь народных праздников",
        "Даты международных знаменательных событий",
        "Краткая история и традиции праздника",
        "Краткая история и значение события",
    ]
    for p in bad_tail:
        d = re.sub(rf"\b{re.escape(p)}\b\.?", "", d, flags=re.I).strip()

    d = re.sub(r"\s{2,}", " ", d).strip()

    if len(d) < 60:
        return ""
    return d

def extract_description(url: str, title: str) -> str:
    r = requests.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    content = (
        soup.select_one("[itemprop='articleBody']") or
        soup.select_one(".entry-content") or
        soup.select_one(".post-content") or
        soup.select_one(".content") or
        soup.find("article") or
        soup.body
    )
    if not content:
        return ""

    for bad in content.select("script, style, noscript, header, footer, nav, aside"):
        bad.decompose()

    for p in content.find_all("p"):
        txt = p.get_text(" ", strip=True)
        txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) >= 80:
            return clean_description(txt, title=title)

    raw = content.get_text("\n", strip=True)
    lines = [re.sub(r"\s+", " ", x).strip() for x in raw.split("\n") if x.strip()]
    for ln in lines:
        if len(ln) >= 80:
            return clean_description(ln, title=title)

    return ""

def worker(idx: int, obj: dict):
    url = (obj.get("holiday_url") or "").strip()
    title = (obj.get("title_raw") or "").strip()
    if not url:
        obj["description"] = ""
        return idx, obj, False

    try:
        desc = extract_description(url, title)
        obj["description"] = desc
        if SLEEP:
            time.sleep(SLEEP)
        return idx, obj, bool(desc)
    except Exception:
        obj["description"] = ""
        return idx, obj, False

def main():
    rows = []
    with open(IN_PATH, "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    total = len(rows)
    print("Loaded:", total)

    results = [None] * total
    ok = 0
    done = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(worker, i, rows[i]) for i in range(total)]
        for fut in as_completed(futures):
            idx, obj, has_desc = fut.result()
            results[idx] = obj
            done += 1
            ok += 1 if has_desc else 0
            if done % 200 == 0 or done == total:
                print(f"[{done}/{total}] ok_desc={ok}")

    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for obj in results:
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print("DONE")
    print("Saved:", OUT_PATH)
    print("Descriptions non-empty:", ok, "out of", total)

if __name__ == "__main__":
    main()
