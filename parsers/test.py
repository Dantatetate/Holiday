from datetime import date
from calend_ru import parse_day

items = parse_day(date(2025, 1, 1))
print("Count:", len(items))
for x in items[:20]:
    print("-", x["title_raw"])
