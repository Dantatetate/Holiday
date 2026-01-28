from datetime import date
from wiki_holidays_2025 import parse_day

items = parse_day(date(2025, 1, 1))
print("Count:", len(items))
for x in items[:20]:
    print("-", x["title_raw"])
