import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URL = "https://www.tweedekamer.nl/kamerstukken/moties"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

moties = []

rows = soup.select(".views-row")

for i, row in enumerate(rows[:20]):  # limit to 20 latest
    title_el = row.select_one("h3 a")

    if not title_el:
        continue

    title = title_el.get_text(strip=True)
    link = "https://www.tweedekamer.nl" + title_el.get("href", "")

    motie = {
        "id": f"motie-{i}",
        "titel": title,
        "datum": datetime.today().strftime("%Y-%m-%d"),
        "sent": "u",
        "bron": "Tweede Kamer",
        "link": link
    }

    moties.append(motie)

with open("nieuw.json", "w", encoding="utf-8") as f:
    json.dump(moties, f, ensure_ascii=False, indent=2)

print("Moties saved:", len(moties))
