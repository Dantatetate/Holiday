import json
import re

def is_probably_menu(text: str) -> bool:
    t = text.lower()
    bad_fragments = [
        "журнал", "подпишитесь", "введите корректный email", "политикой конфиденциальности",
        "получить код", "информер", "праздники именины", "производственные календари",
        "смотреть другие информеры", "главная страница / календарь"
    ]
    return any(b in t for b in bad_fragments)

def split_title_description(text: str):

    text = re.sub(r"\s+", " ", text).strip()

    if " — " in text:
        left, right = text.split(" — ", 1)
        if 3 <= len(left) <= 120 and len(right) >= 20:
            return left.strip(), right.strip()

    if len(text) <= 120:
        return text, ""

    words = text.split()
    title = " ".join(words[:10]).strip()
    desc = text
    return title, desc

def normalize_title(s: str) -> str:
    s = s.lower().strip().replace("ё", "е")
    s = re.sub(r"[^a-zа-я0-9\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    inp = "data/raw_calend.jsonl"
    out = "data/clean_calend.jsonl"

    cleaned = 0
    with open(inp, "r", encoding="utf-8") as f_in, open(out, "w", encoding="utf-8") as f_out:
        for line in f_in:
            item = json.loads(line)
            raw = item.get("title_raw", "").strip()
            if not raw:
                continue

            if is_probably_menu(raw):
                continue

            title, desc = split_title_description(raw)
            title_norm = normalize_title(title)

            if len(title_norm) < 3:
                continue

            cleaned_item = {
                "date": item["date"],
                "source": item["source"],
                "day_url": item["url"],
                "title": title,
                "title_norm": title_norm,
                "description": desc
            }
            f_out.write(json.dumps(cleaned_item, ensure_ascii=False) + "\n")
            cleaned += 1

    print("Saved cleaned:", cleaned, "to", out)

if __name__ == "__main__":
    main()
