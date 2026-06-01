"""
scrape_cs.py — HTML-aware scraper for Carleton's Computer Science programs page.

CS has 13 distinct streams/programs on one page. The generic scraper lumps them
into a few coarse chunks. This scraper uses h3/h4/h2 boundaries to give each
stream its own dedicated Pinecone vector.

Run: py scrape_cs.py
Safe to re-run — uses unique IDs, overwrites previous CS chunks.
"""

import os
import re
import requests
from bs4 import BeautifulSoup, NavigableString
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "programs"
EMBED_MODEL = "text-embedding-3-small"
CS_URL = "https://calendar.carleton.ca/undergrad/undergradprograms/computerscience/"

SKIP_HEADINGS = [
    "course categories",
    "program requirements",
    "school of computer science",
    "faculty of science",
    "industrial applications internship courses",
    "prohibited courses",
    "breadth electives",
    "free electives",
    "natural science",
]

def is_program_heading(text: str) -> bool:
    t = text.lower()
    if any(s in t for s in SKIP_HEADINGS):
        return False
    keywords = [
        "computer science", "cybersecurity", "minor in computer",
        "algorithms stream", "artificial intelligence", "game development",
        "management and business", "software engineering stream",
        "user experience", "b.c.s.", "b.cyber", "b.math", "mathematics:"
    ]
    return any(k in t for k in keywords) and len(text) > 8

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("​", "").replace("\xa0", " ")).strip()

def extract_content_until_next_heading(start_tag) -> str:
    parts = []
    current = start_tag.next_sibling
    while current:
        if hasattr(current, "name") and current.name in ["h2", "h3", "h4"]:
            break
        if hasattr(current, "name"):
            text = clean(current.get_text(" ", strip=True))
            if text:
                parts.append(text)
        elif isinstance(current, NavigableString):
            text = clean(str(current))
            if text:
                parts.append(text)
        current = current.next_sibling
    return "\n".join(parts)

def scrape() -> list[dict]:
    print(f"Fetching {CS_URL}...")
    r = requests.get(CS_URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body")

    programs = []
    for tag in main.find_all(["h2", "h3", "h4"]):
        name = clean(tag.get_text(" ", strip=True))
        if not is_program_heading(name):
            continue
        content = extract_content_until_next_heading(tag)
        if len(content) < 80:
            continue
        programs.append({"name": name, "content": content})
        print(f"  <{tag.name}> {name[:70]}  ({len(content)} chars)")

    return programs

def upload(programs: list[dict]):
    if not programs:
        print("Nothing to upload.")
        return

    print(f"\nEmbedding and uploading {len(programs)} CS program chunks...")

    embed_texts = [
        f"{p['name']}\nRequired courses and program structure:\n{p['content'][:900]}"
        for p in programs
    ]

    response = openai_client.embeddings.create(input=embed_texts, model=EMBED_MODEL)

    vectors = []
    for i, emb_data in enumerate(response.data):
        p = programs[i]
        slug = re.sub(r"[^a-z0-9]", "-", p["name"].lower())[:60].strip("-")
        vectors.append({
            "id": f"cs-{slug}",
            "values": emb_data.embedding,
            "metadata": {
                "program": p["name"],
                "faculty": "Science",
                "section": "Full Requirements",
                "text": f"{p['name']}\n\n{p['content'][:2000]}",
                "source": CS_URL,
            },
        })

    index.upsert(vectors=vectors, namespace=NAMESPACE)
    print(f"✓ Done — {len(vectors)} CS program chunks in Pinecone")

def run():
    print("=" * 55)
    print("Computer Science Program Scraper (HTML-aware)")
    print("=" * 55 + "\n")
    programs = scrape()
    print(f"\nFound {len(programs)} program sections\n")
    if programs:
        upload(programs)

if __name__ == "__main__":
    run()
