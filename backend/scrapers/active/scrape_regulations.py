"""
scrape_regulations.py — Scrapes all academic regulations, admissions, and policies.

Covers:
  - Academic Regulations of the University (all 10 sections + sub-pages)
  - Admissions: General requirements
  - Admissions: Per-program requirements (all degree/cert/diploma pages)
  - Any other regulation pages discovered by the crawler

Strategy:
  - Start from seed URLs, auto-discover all sub-pages within /regulations/
  - Use trafilatura for clean text extraction (handles expandable accordions)
  - Split each page by section headings (numbered sections, h2/h3 patterns)
  - One Pinecone vector per section — keeps related content together

Namespace: "regulations"
"""

import os
import re
import time
import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "regulations"
EMBED_MODEL = "text-embedding-3-small"
BASE = "https://calendar.carleton.ca"

# Seed URLs — the crawler will discover all sub-pages from these
SEED_URLS = [
    # All academic regulations (10 major sections, dozens of sub-pages)
    f"{BASE}/undergrad/regulations/academicregulationsoftheuniversity/",
    # Admissions — general requirements (expandable sections)
    f"{BASE}/undergrad/regulations/admissions/general/",
    # Admissions — per-program requirements
    f"{BASE}/undergrad/regulations/admissions/programs/",
    # Fees
    f"{BASE}/undergrad/fees/",
    # Academic life (co-op, exchange, etc.)
    f"{BASE}/undergrad/academiclife/",
]

# Only crawl within these URL prefixes
ALLOWED_PREFIXES = [
    f"{BASE}/undergrad/regulations/",
    f"{BASE}/undergrad/fees/",
    f"{BASE}/undergrad/academiclife/",
]

# ── Stage 1: Crawl and discover all pages ─────────────────────────────────────

def is_allowed(url: str) -> bool:
    return any(url.startswith(prefix) for prefix in ALLOWED_PREFIXES)

def discover_pages(seed_urls: list[str]) -> list[str]:
    """BFS crawler — discovers all sub-pages reachable from seed URLs."""
    print("\n[1/3] Crawling to discover all regulation pages...")

    visited = set()
    queue = deque(seed_urls)
    found = []

    for seed in seed_urls:
        visited.add(seed)

    while queue:
        url = queue.popleft()
        found.append(url)

        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                full_url = urljoin(url, a["href"])
                # Normalize: remove fragment, trailing slash variations
                full_url = full_url.split('#')[0]
                if full_url.endswith('/') and full_url != full_url.rstrip('/') + '/':
                    pass
                if (
                    full_url not in visited
                    and is_allowed(full_url)
                    and ".pdf" not in full_url
                    and "?" not in full_url
                ):
                    visited.add(full_url)
                    queue.append(full_url)
        except Exception:
            pass

        time.sleep(0.3)

    print(f"  → Discovered {len(found)} pages to index")
    return found

# ── Stage 2: Scrape a page cleanly ───────────────────────────────────────────

def scrape_page(url: str) -> str:
    """
    Primary: trafilatura — handles expandable accordions, removes nav/footer noise.
    Fallback: BeautifulSoup.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_tables=True,
                include_links=False,
                include_images=False,
                no_fallback=False,
                favor_recall=True,  # Keep more content, less aggressive trimming
            )
            if text and len(text) > 100:
                return text
    except Exception:
        pass

    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
            tag.decompose()
        main = soup.find("div", class_="pageblock") or soup.find("main") or soup
        lines = [l.strip() for l in main.get_text(separator="\n").splitlines() if l.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"    ✗ Scrape failed: {e}")
        return ""

# ── Stage 3: Split into sections ─────────────────────────────────────────────

def infer_page_category(url: str) -> str:
    """Infer what category a URL belongs to for metadata."""
    if "academicregulationsoftheuniversity" in url:
        return "Academic Regulations"
    if "admissions/general" in url:
        return "Admissions — General"
    if "admissions/programs" in url:
        return "Admissions — Programs"
    if "fees" in url:
        return "Fees & Financial"
    if "academiclife" in url:
        return "Academic Life"
    return "Regulations"

def split_by_sections(text: str, url: str) -> list[dict]:
    """
    Split regulation text into logical sections.

    Sections are detected by:
      - Numbered headings: "1.", "1.1", "2.3.4 Title"
      - Common regulation headings
      - Blank lines preceding a short title-like line
    """
    SECTION_PATTERNS = re.compile(
        r'^(\d+\.[\d.]*\s+[A-Z].{3,}|'          # e.g. "1.1 Student Responsibility"
        r'[A-Z][A-Z\s]{5,}$)',                    # All-caps headings
        re.MULTILINE
    )

    lines = text.split('\n')
    sections = []
    current_heading = infer_page_category(url)
    current_lines = []

    for line in lines:
        stripped = line.strip()
        is_heading = False

        # Numbered section heading: "1.", "1.1", "3.2.4", etc.
        if re.match(r'^\d+\.[\d.]*\s+\S', stripped) and len(stripped) < 100:
            is_heading = True
        # Short all-caps line
        elif re.match(r'^[A-Z][A-Z\s\-&]{8,}$', stripped) and len(stripped) < 60:
            is_heading = True

        if is_heading:
            if current_lines:
                content = '\n'.join(current_lines).strip()
                if len(content) > 80:
                    sections.append({
                        "heading": current_heading,
                        "content": content,
                        "category": infer_page_category(url),
                    })
            current_heading = stripped
            current_lines = []
        else:
            if stripped:
                current_lines.append(stripped)

    # Save final section
    if current_lines:
        content = '\n'.join(current_lines).strip()
        if len(content) > 80:
            sections.append({
                "heading": current_heading,
                "content": content,
                "category": infer_page_category(url),
            })

    # No sections detected — treat whole page as one chunk
    if not sections and len(text.strip()) > 100:
        sections = [{
            "heading": infer_page_category(url),
            "content": text.strip(),
            "category": infer_page_category(url),
        }]

    return sections

# ── Stage 4: Embed and upload ─────────────────────────────────────────────────

def upload_sections(url: str, sections: list[dict], batch_size: int = 50):
    if not sections:
        return

    # Build embedding-friendly text for each section
    texts = [
        f"{s['category']} — {s['heading']}\n{s['content'][:800]}"
        for s in sections
    ]

    vectors = []
    for i in range(0, len(sections), batch_size):
        batch = sections[i:i + batch_size]
        batch_texts = texts[i:i + batch_size]

        response = openai_client.embeddings.create(input=batch_texts, model=EMBED_MODEL)

        url_slug = re.sub(r'[^a-z0-9]', '-', url.split(BASE)[-1].lower()).strip('-')

        for j, emb_data in enumerate(response.data):
            s = batch[j]
            heading_slug = re.sub(r'[^a-z0-9]', '-', s['heading'].lower())[:40]
            chunk_id = f"{url_slug}-{heading_slug}-{i+j}"

            vectors.append({
                "id": chunk_id,
                "values": emb_data.embedding,
                "metadata": {
                    "text": f"{s['category']} — {s['heading']}\n{s['content'][:1500]}",
                    "category": s['category'],
                    "heading": s['heading'],
                    "source": url,
                },
            })

    index.upsert(vectors=vectors, namespace=NAMESPACE)

# ── Main pipeline ─────────────────────────────────────────────────────────────

def run():
    pages = discover_pages(SEED_URLS)
    total_sections = 0
    total_pages = 0

    print(f"\n[2/3] Scraping and indexing {len(pages)} pages...\n")

    for i, url in enumerate(pages):
        category = infer_page_category(url)
        slug = url.rstrip('/').split('/')[-1] or url.rstrip('/').split('/')[-2]
        print(f"  [{i+1}/{len(pages)}] [{category}] {slug}")

        text = scrape_page(url)
        if not text or len(text) < 100:
            print("    ✗ No content extracted")
            continue

        sections = split_by_sections(text, url)
        if not sections:
            print("    ✗ No sections parsed")
            continue

        upload_sections(url, sections)
        total_sections += len(sections)
        total_pages += 1
        print(f"    ✓ {len(sections)} sections indexed")

        time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"✓ REGULATIONS COMPLETE — {total_pages} pages, {total_sections} sections indexed")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    run()
