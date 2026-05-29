"""
scrape_programs.py — Scrapes all undergrad program requirements from calendar.carleton.ca.

Strategy:
  - Scrape HTML pages directly (NOT PDFs — PDFs lose all structure)
  - Auto-discover all program pages from the index
  - Within each program page, split by year/section heading
  - Store one Pinecone vector per year/section block
  - This means "Year 1 Required Courses" is one chunk, not split mid-list

Namespace: "programs"
"""

import os
import re
import time
import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "programs"
EMBED_MODEL = "text-embedding-3-small"
BASE = "https://calendar.carleton.ca"
PROGRAMS_ROOT = f"{BASE}/undergrad/undergradprograms/"

# Faculty mapping based on URL slug patterns
FACULTY_MAP = {
    "engineering": "Engineering & Design",
    "informationtechnology": "Information Technology",
    "computerscience": "Science",
    "science": "Science",
    "arts": "Arts & Social Sciences",
    "business": "Sprott School of Business",
    "publicaffairs": "Public Affairs",
    "health": "Health Sciences",
    "architecture": "Engineering & Design",
}

def detect_faculty(url: str, program_name: str) -> str:
    url_lower = url.lower()
    for key, faculty in FACULTY_MAP.items():
        if key in url_lower:
            return faculty
    # Fallback: engineering keywords in name
    eng_keywords = ["engineering", "network technology"]
    if any(k in program_name.lower() for k in eng_keywords):
        return "Engineering & Design"
    return "Other"

# ── Stage 1: Discover all program pages ──────────────────────────────────────

def get_program_links() -> list[str]:
    print(f"\n[1/3] Discovering program pages from {PROGRAMS_ROOT}")
    r = requests.get(PROGRAMS_ROOT, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    content = soup.find("div", class_="pageblock") or soup.find("main") or soup

    links = []
    for a in content.find_all("a", href=True):
        url = urljoin(PROGRAMS_ROOT, a["href"])
        if (
            url.startswith(PROGRAMS_ROOT)
            and url != PROGRAMS_ROOT
            and ".pdf" not in url
            and "#" not in url
            and url not in links
        ):
            links.append(url)

    print(f"  → Found {len(links)} program pages")
    return links

# ── Stage 2: Scrape and section a program page ────────────────────────────────

def scrape_program_page(url: str) -> str:
    """Trafilatura first, BeautifulSoup fallback."""
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(
            downloaded,
            include_tables=True,
            include_links=False,
            include_images=False,
            no_fallback=False,
        )
        if text and len(text) > 300:
            return text
    except Exception:
        pass

    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        main = soup.find("div", class_="pageblock") or soup.find("main") or soup
        lines = [l.strip() for l in main.get_text(separator="\n").splitlines() if l.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"  ✗ Scrape failed: {e}")
        return ""

def extract_program_name(text: str, url: str) -> str:
    """Extract the program name from the first line of text."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        if len(line) > 10 and not line.startswith("http"):
            return line
    # Fallback: derive from URL slug
    slug = url.rstrip('/').split('/')[-1]
    return slug.replace('-', ' ').title()

def split_into_sections(text: str) -> list[dict]:
    """
    Split program text into logical sections by detecting headings.

    Heading patterns:
      - "Year 1", "Year 2", "Year 3", "Year 4"
      - "First Year", "Second Year", etc.
      - "Required Courses", "Electives", "Stream", "Notes"
      - Numbered sections
    """
    HEADING_PATTERNS = [
        r'^(Year\s+[1-4]\b.*)',
        r'^(First Year|Second Year|Third Year|Fourth Year)',
        r'^(Required Courses?|Elective Courses?|Optional Courses?)',
        r'^(Stream[:\s]|Specialization[:\s])',
        r'^(Program Overview|Program Description|Introduction)',
        r'^(Graduation Requirements?|Degree Requirements?)',
        r'^(Notes?:|Important:|Notice:)',
        r'^(Honours|General Program|Combined)',
        r'^\d+\.\s+[A-Z]',  # Numbered sections
    ]
    combined = re.compile('|'.join(HEADING_PATTERNS), re.IGNORECASE | re.MULTILINE)

    lines = text.split('\n')
    sections = []
    current_heading = "Overview"
    current_lines = []

    for line in lines:
        if combined.match(line.strip()) and len(line.strip()) < 80:
            # Save previous section if it has content
            if current_lines:
                content = '\n'.join(current_lines).strip()
                if len(content) > 50:
                    sections.append({"heading": current_heading, "content": content})
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_lines:
        content = '\n'.join(current_lines).strip()
        if len(content) > 50:
            sections.append({"heading": current_heading, "content": content})

    # If no sections were detected, return the whole text as one chunk
    if not sections:
        sections = [{"heading": "Program Requirements", "content": text.strip()}]

    return sections

# ── Stage 3: Embed and upload ─────────────────────────────────────────────────

def upload_sections(program_name: str, faculty: str, url: str, sections: list[dict]):
    vectors = []
    slug = url.rstrip('/').split('/')[-1]

    texts = []
    for s in sections:
        texts.append(
            f"{program_name} — {s['heading']}\n{s['content'][:800]}"
        )

    if not texts:
        return

    response = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)

    for i, emb_data in enumerate(response.data):
        s = sections[i]
        chunk_id = f"{slug}-{re.sub(r'[^a-z0-9]', '-', s['heading'].lower())}-{i}"
        vectors.append({
            "id": chunk_id,
            "values": emb_data.embedding,
            "metadata": {
                "program": program_name,
                "faculty": faculty,
                "section": s['heading'],
                "text": f"{program_name}\n{s['heading']}\n{s['content'][:1200]}",
                "source": url,
            },
        })

    index.upsert(vectors=vectors, namespace=NAMESPACE)

# ── Main pipeline ─────────────────────────────────────────────────────────────

def run():
    program_urls = get_program_links()
    total_sections = 0
    total_programs = 0

    print(f"\n[2/3] Scraping {len(program_urls)} program pages...\n")

    for i, url in enumerate(program_urls):
        slug = url.rstrip('/').split('/')[-1]
        print(f"  [{i+1}/{len(program_urls)}] {slug}")

        text = scrape_program_page(url)
        if not text or len(text) < 200:
            print("    ✗ Not enough content")
            continue

        program_name = extract_program_name(text, url)
        faculty = detect_faculty(url, program_name)
        sections = split_into_sections(text)

        upload_sections(program_name, faculty, url, sections)
        total_sections += len(sections)
        total_programs += 1
        print(f"    ✓ '{program_name}' → {len(sections)} sections")

        time.sleep(0.8)

    print(f"\n{'='*50}")
    print(f"✓ PROGRAMS COMPLETE — {total_programs} programs, {total_sections} sections indexed")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    run()
