"""
scrape_engineering.py — Specialized scraper for Carleton's engineering programs page.

The generic scraper got 21 sections for a page covering 20+ programs × 4 years.
This scraper understands the specific structure:

  [Stream heading] Aerospace Engineering - Stream A: Aerodynamics...
    [Year heading] First Year / Second Year / Third Year / Fourth Year
      [Course list] AERO 2001 [0.5]...

Each (stream, year) pair becomes one Pinecone vector.
Result: ~80+ focused chunks instead of 21 coarse ones.

Run: py scrape_engineering.py
     (no need to wipe — uses unique IDs so safe to re-run)
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
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

# ── Patterns ──────────────────────────────────────────────────────────────────

# Stream-level headings — these mark the start of a new program/stream
STREAM_PATTERN = re.compile(
    r'^('
    r'Aerospace Engineering[^$]*|'
    r'Architectural Conservation[^$]*|'
    r'Biomedical and (Electrical|Mechanical) Engineering[^$]*|'
    r'Civil Engineering[^$]*|'
    r'Communications Engineering[^$]*|'
    r'Computer Systems Engineering[^$]*|'
    r'Electrical Engineering[^$]*|'
    r'Engineering Physics[^$]*|'
    r'Environmental Engineering[^$]*|'
    r'Mechanical Engineering[^$]*|'
    r'Mechatronics Engineering[^$]*|'
    r'Network Technology[^$]*|'
    r'Software Engineering[^$]*|'
    r'Sustainable and Renewable Energy[^$]*'
    r')$',
    re.IGNORECASE,
)

# Year-level headings within a stream
YEAR_PATTERN = re.compile(
    r'^(First Year|Second Year|Third Year|Fourth Year|'
    r'Year\s+1\b|Year\s+2\b|Year\s+3\b|Year\s+4\b|'
    r'Year One|Year Two|Year Three|Year Four)(.*)$',
    re.IGNORECASE,
)

YEAR_LABELS = {
    "first": 1, "year 1": 1, "year one": 1,
    "second": 2, "year 2": 2, "year two": 2,
    "third": 3, "year 3": 3, "year three": 3,
    "fourth": 4, "year 4": 4, "year four": 4,
}

def normalize_year(heading: str) -> int:
    h = heading.lower()
    for key, val in YEAR_LABELS.items():
        if key in h:
            return val
    return 0

# ── Scrape ────────────────────────────────────────────────────────────────────

def scrape_engineering_page() -> str:
    print(f"Fetching {ENG_URL}")
    r = requests.get(ENG_URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
        tag.decompose()
    main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body")
    raw = main.get_text(separator="\n")
    raw = raw.replace("\xa0", " ")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()

# ── Parse into (stream, year, content) triples ────────────────────────────────

def parse_stream_years(text: str) -> list[dict]:
    """
    Walk through the text line by line.
    State machine:
      - When we hit a stream heading → new stream
      - When we hit a year heading → new year within current stream
      - Everything else → content for current (stream, year)
    """
    results = []
    current_stream = None
    current_year = None
    current_year_num = 0
    current_lines = []

    def flush():
        if current_stream and current_year and current_lines:
            content = "\n".join(current_lines).strip()
            if len(content) > 40:
                results.append({
                    "stream": current_stream,
                    "year": current_year,
                    "year_num": current_year_num,
                    "content": content,
                })

    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines:
                current_lines.append("")
            continue

        # Check if this is a stream heading
        if STREAM_PATTERN.match(stripped) and len(stripped) < 120:
            flush()
            current_stream = stripped
            current_year = "Overview"
            current_year_num = 0
            current_lines = []
            continue

        # Check if this is a year heading
        if current_stream:
            ym = YEAR_PATTERN.match(stripped)
            if ym and len(stripped) < 60:
                flush()
                current_year = stripped
                current_year_num = normalize_year(stripped)
                current_lines = []
                continue

        # Regular content line
        if current_stream:
            current_lines.append(stripped)

    flush()
    return results

# ── Also scrape individual stream pages if they exist ─────────────────────────

STREAM_SLUGS = {
    "Aerospace Engineering Stream A": "aerospaceengineeringa",
    "Aerospace Engineering Stream B": "aerospaceengineeringb",
    "Aerospace Engineering Stream C": "aerospaceengineeringc",
    "Aerospace Engineering Stream D": "aerospaceengineeringd",
    "Software Engineering": "softwareengineering",
    "Software Engineering Stream A": "softwareengineeringai",
    "Sustainable and Renewable Energy Stream A": "sreea",
    "Sustainable and Renewable Energy Stream B": "sreeb",
}

# ── Upload ─────────────────────────────────────────────────────────────────────

def upload_chunks(chunks: list[dict]):
    if not chunks:
        return

    print(f"\nUploading {len(chunks)} stream-year chunks...")

    embed_texts = []
    for c in chunks:
        embed_texts.append(
            f"{c['stream']} — {c['year']}\n{c['content'][:800]}"
        )

    batch_size = 50
    total = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_texts = embed_texts[i:i + batch_size]

        response = openai_client.embeddings.create(input=batch_texts, model=EMBED_MODEL)

        vectors = []
        for j, emb_data in enumerate(response.data):
            c = batch[j]
            stream_slug = re.sub(r"[^a-z0-9]", "-", c["stream"].lower())[:50]
            year_slug = re.sub(r"[^a-z0-9]", "-", c["year"].lower())[:20]
            chunk_id = f"eng-{stream_slug}-{year_slug}-{i+j}"

            vectors.append({
                "id": chunk_id,
                "values": emb_data.embedding,
                "metadata": {
                    "program": c["stream"],
                    "section": c["year"],
                    "year_num": c["year_num"],
                    "faculty": "Engineering & Design",
                    "text": f"{c['stream']}\n{c['year']}\n{c['content'][:1500]}",
                    "source": ENG_URL,
                },
            })

        index.upsert(vectors=vectors, namespace=NAMESPACE)
        total += len(vectors)
        print(f"  Uploaded batch {i // batch_size + 1} ({total} total)")

    print(f"✓ Done — {total} engineering chunks indexed")

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 50)
    print("Engineering Program Scraper")
    print("=" * 50)

    text = scrape_engineering_page()
    print(f"Extracted {len(text)} characters\n")

    chunks = parse_stream_years(text)
    print(f"Parsed {len(chunks)} stream-year sections:\n")

    # Print summary
    by_stream = {}
    for c in chunks:
        by_stream.setdefault(c["stream"], []).append(c["year"])
    for stream, years in sorted(by_stream.items()):
        print(f"  {stream}: {len(years)} sections ({', '.join(years)})")

    print()
    upload_chunks(chunks)

if __name__ == "__main__":
    run()
