"""
scrape_services.py — Crawls all major Carleton student-facing service pages.

Covers: Registrar, Financial Aid & Awards, Co-op, Library, IT Services,
Student Affairs, Housing, Health Services, Admissions, Fees & Finances.

Strategy:
  - Each section has a seed URL and a URL prefix to stay within scope
  - Crawls up to depth 2 within each section
  - Extracts main content via BeautifulSoup (strips nav/footer/scripts)
  - Chunks by heading or by size (max ~800 words per chunk)
  - Uploads to "services" namespace in Pinecone

Safe to re-run — content-hash IDs overwrite previous vectors.
Run: py scrape_services.py
"""

import os
import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "services"
EMBED_MODEL = "text-embedding-3-small"

# ── Sections to crawl ─────────────────────────────────────────────────────────
# (label, seed_url, stay_within_prefix, max_depth)
SECTIONS = [
    ("Registrar",        "https://carleton.ca/registrar/",         "https://carleton.ca/registrar/",       2),
    ("Financial Aid",    "https://carleton.ca/awards/",            "https://carleton.ca/awards/",          2),
    ("Financial Aid",    "https://carleton.ca/studentaccounts/",   "https://carleton.ca/studentaccounts/", 2),
    ("Co-op",            "https://carleton.ca/coop/",              "https://carleton.ca/coop/",            2),
    ("Library",          "https://library.carleton.ca/",           "https://library.carleton.ca/",         2),
    ("IT Services",      "https://carleton.ca/its/",               "https://carleton.ca/its/",             2),
    ("Student Affairs",  "https://carleton.ca/studentaffairs/",    "https://carleton.ca/studentaffairs/",  2),
    ("Housing",          "https://housing.carleton.ca/",           "https://housing.carleton.ca/",         2),
    ("Health Services",  "https://carleton.ca/health/",            "https://carleton.ca/health/",          2),
    ("Admissions",       "https://admissions.carleton.ca/",        "https://admissions.carleton.ca/",      2),
    ("Fees & Finances",  "https://carleton.ca/studentaccounts/fees/", "https://carleton.ca/studentaccounts/fees/", 2),
    ("Graduate Studies", "https://graduate.carleton.ca/",          "https://graduate.carleton.ca/",        2),
]

SKIP_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3"}
SKIP_PATTERNS = re.compile(r"(login|logout|search|feed|wp-admin|wp-json|xmlrpc|#)", re.IGNORECASE)


# ── Crawling ──────────────────────────────────────────────────────────────────

def should_crawl(url: str, prefix: str) -> bool:
    if not url.startswith(prefix):
        return False
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext in SKIP_EXTENSIONS:
        return False
    if SKIP_PATTERNS.search(url):
        return False
    return True


def get_links(soup: BeautifulSoup, base_url: str, prefix: str) -> list[str]:
    links = []
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"]).split("#")[0].rstrip("/") + "/"
        if should_crawl(url, prefix) and url not in links:
            links.append(url)
    return links


def fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "CampusQ-Bot/1.0"})
        if r.status_code != 200:
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None


def extract_text(soup: BeautifulSoup) -> tuple[str, str]:
    """Returns (page_title, main_content_text)"""
    # Get title
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # Remove noise
    for tag in soup(["script", "style", "nav", "header", "footer",
                      "aside", "noscript", "form", "iframe",
                      ".nav", ".menu", ".sidebar", ".footer", ".header"]):
        tag.decompose()

    # Try main content containers first
    main = (
        soup.find("main") or
        soup.find("div", class_=re.compile(r"content|main|entry|post|article", re.I)) or
        soup.find("article") or
        soup.find("body")
    )

    if not main:
        return title, ""

    text = re.sub(r"\s+", " ", main.get_text(separator="\n", strip=True))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, text


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(title: str, text: str, url: str) -> list[dict]:
    """Split text into chunks of ~600 words, breaking at paragraph boundaries."""
    MAX_WORDS = 600
    chunks = []
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    current_words = 0
    current_parts = []

    for para in paragraphs:
        word_count = len(para.split())
        if current_words + word_count > MAX_WORDS and current_parts:
            chunks.append("\n".join(current_parts))
            current_parts = []
            current_words = 0
        current_parts.append(para)
        current_words += word_count

    if current_parts:
        chunks.append("\n".join(current_parts))

    return [
        {"title": title, "text": chunk, "url": url, "chunk_index": i}
        for i, chunk in enumerate(chunks)
        if len(chunk.strip()) > 100
    ]


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_chunks(chunks: list[dict], section: str) -> int:
    if not chunks:
        return 0

    texts = [
        f"{c['title']}\n{c['text'][:900]}"
        for c in chunks
    ]

    response = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)

    vectors = []
    for i, emb_data in enumerate(response.data):
        c = chunks[i]
        # Stable ID based on URL + chunk index
        raw_id = f"{c['url']}-{c['chunk_index']}"
        chunk_id = hashlib.md5(raw_id.encode()).hexdigest()[:16]
        vectors.append({
            "id": chunk_id,
            "values": emb_data.embedding,
            "metadata": {
                "section": section,
                "title": c["title"],
                "text": f"{c['title']}\n\n{c['text'][:2000]}",
                "source": c["url"],
                "chunk": c["chunk_index"],
            },
        })

    index.upsert(vectors=vectors, namespace=NAMESPACE)
    return len(vectors)


# ── Main crawler ──────────────────────────────────────────────────────────────

def crawl_section(label: str, seed: str, prefix: str, max_depth: int) -> int:
    visited = set()
    queue = [(seed, 0)]
    total_vectors = 0

    while queue:
        url, depth = queue.pop(0)
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        soup = fetch(url)
        if not soup:
            continue

        title, text = extract_text(soup)
        if len(text) < 150:
            time.sleep(0.3)
            continue

        chunks = chunk_text(title, text, url)
        n = upload_chunks(chunks, label)
        total_vectors += n

        if n > 0:
            print(f"    ✓ [{depth}] {title[:60]}  ({n} chunks)")

        # Queue child links
        if depth < max_depth:
            for link in get_links(soup, url, prefix):
                if link not in visited:
                    queue.append((link, depth + 1))

        time.sleep(0.4)

    return total_vectors


def run():
    print("=" * 55)
    print("CampusQ — Services Scraper (registrar, aid, co-op...)")
    print("=" * 55 + "\n")

    total = 0

    for label, seed, prefix, depth in SECTIONS:
        print(f"\n── {label} ──────────────────────────────────")
        print(f"   Seed: {seed}")
        try:
            n = crawl_section(label, seed, prefix, depth)
            total += n
            print(f"   → {n} vectors indexed")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

    print(f"\n{'='*55}")
    print(f"DONE — {total} total service vectors indexed")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
