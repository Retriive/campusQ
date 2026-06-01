"""
scrape_engineering.py — HTML-aware scraper for Carleton's engineering programs page.

Structure discovered from debug_engineering.py:
  - Each program is bounded by an <h3> or <h4> heading
  - Aerospace streams use <h4> tags
  - All other programs use <h3> tags
  - Requirements are numbered items (1. First Year, 2. 0.5 credit in...) NOT year headings
  - We store ONE chunk per program/stream with ALL requirements in it

This replaces the broken plain-text approach that got confused by course names.

Run: py scrape_engineering.py
Safe to re-run — uses unique IDs, overwrites previous engineering chunks.
"""

import os
import re
import time
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
ENG_URL = "https://calendar.carleton.ca/undergrad/undergradprograms/engineering/"

# Headings that are NOT program names — skip these
SKIP_HEADINGS = [
    "courses", "regulations", "co-operative", "admissions", "participation",
    "graduation", "course load", "academic continuation", "time limit",
    "appeals", "work term", "undergraduate", "degree", "admission requirements",
    "program requirements", "course categories",
]

def is_program_heading(text: str) -> bool:
    """Returns True if this heading represents a degree program."""
    t = text.lower()
    if any(skip in t for skip in SKIP_HEADINGS):
        return False
    # Must mention engineering or a known program
    keywords = [
        "engineering", "software", "sustainable", "renewable",
        "biomedical", "mechatronics", "physics", "architectural"
    ]
    return any(k in t for k in keywords) and len(text) > 10

def clean(text: str) -> str:
    """Remove zero-width spaces, normalize whitespace."""
    text = text.replace("​", "").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_program_name(tag) -> str:
    """Get clean program name from heading tag."""
    return clean(tag.get_text(" ", strip=True))

def extract_content_until_next_heading(start_tag) -> str:
    """
    Walk forward through DOM siblings collecting all text
    until we hit the next h2, h3, or h4 heading.
    """
    parts = []
    current = start_tag.next_sibling

    while current:
        if hasattr(current, "name"):
            if current.name in ["h2", "h3", "h4"]:
                break
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
    print(f"Fetching {ENG_URL}...")
    r = requests.get(ENG_URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body")

    programs = []

    # Walk all h3 and h4 tags in document order
    for tag in main.find_all(["h3", "h4"]):
        name = extract_program_name(tag)
        if not is_program_heading(name):
            continue

        content = extract_content_until_next_heading(tag)
        if len(content) < 100:
            # Too short — likely a stub or sub-heading with no real content
            continue

        programs.append({
            "name": name,
            "content": content,
            "tag": tag.name,
        })
        print(f"  <{tag.name}> {name[:70]}  ({len(content)} chars)")

    return programs

def upload(programs: list[dict]):
    if not programs:
        print("Nothing to upload.")
        return

    print(f"\nEmbedding and uploading {len(programs)} program chunks...")

    # Build embedding texts
    embed_texts = [
        f"{p['name']}\nRequired courses and program structure:\n{p['content'][:900]}"
        for p in programs
    ]

    batch_size = 50
    total = 0

    for i in range(0, len(programs), batch_size):
        batch = programs[i:i + batch_size]
        batch_texts = embed_texts[i:i + batch_size]

        response = openai_client.embeddings.create(input=batch_texts, model=EMBED_MODEL)

        vectors = []
        for j, emb_data in enumerate(response.data):
            p = batch[j]
            slug = re.sub(r"[^a-z0-9]", "-", p["name"].lower())[:60].strip("-")
            chunk_id = f"eng-{slug}"

            vectors.append({
                "id": chunk_id,
                "values": emb_data.embedding,
                "metadata": {
                    "program": p["name"],
                    "faculty": "Engineering & Design",
                    "section": "Full Requirements",
                    # Store full content — this is what the LLM sees
                    "text": f"{p['name']}\n\n{p['content'][:2000]}",
                    "source": ENG_URL,
                },
            })

        index.upsert(vectors=vectors, namespace=NAMESPACE)
        total += len(vectors)
        print(f"  Batch {i // batch_size + 1}: {total} uploaded")

    print(f"\n✓ Done — {total} engineering program chunks in Pinecone")

def run():
    print("=" * 55)
    print("Engineering Program Scraper (HTML-aware)")
    print("=" * 55 + "\n")

    programs = scrape()
    print(f"\nFound {len(programs)} program sections\n")

    if programs:
        upload(programs)
    else:
        print("No programs found — check the HTML structure.")

if __name__ == "__main__":
    run()
