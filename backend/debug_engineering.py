"""
debug_engineering.py — Prints the actual heading structure of the engineering page.
Run this to see what HTML tags and text Carleton uses for stream/year boundaries.
Output tells us exactly how to fix the parser.
"""

import sys
import requests
from bs4 import BeautifulSoup

# Force UTF-8 output so Windows cp1252 doesn't choke on special chars
sys.stdout.reconfigure(encoding="utf-8")

URL = "https://calendar.carleton.ca/undergrad/undergradprograms/engineering/"

r = requests.get(URL, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body")

print("=== ALL HEADINGS (h1-h4) and strong/b tags ===\n")
for tag in main.find_all(["h1", "h2", "h3", "h4", "strong", "b"]):
    text = tag.get_text(strip=True).replace("​", "")
    if 5 < len(text) < 150:
        print(f"<{tag.name}>: {text}")

print("\n=== FIRST 80 non-empty lines of plain text ===\n")
lines = [l.strip().replace("​", "") for l in main.get_text(separator="\n").splitlines() if l.strip()]
for line in lines[:80]:
    print(repr(line))
