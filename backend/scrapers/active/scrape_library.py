"""
scrape_library.py — Scrapes Carleton University Library pages.

Namespace: "library"
Safe to re-run — content-hash IDs overwrite previous vectors.
Run: py scrape_library.py
"""

import os
import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "library"
EMBED_MODEL = "text-embedding-3-small"

URLS = [
    ("Library — Visit and Building Info",           "https://library.carleton.ca/visit-building"),
    ("Library — Hours",                             "https://library.carleton.ca/hours"),
    ("Library — Study Space",                       "https://library.carleton.ca/building/study-space"),
    ("Library — Study Rooms",                       "https://library.carleton.ca/services/study-rooms"),
    ("Library — Building Concerns",                 "https://library.carleton.ca/building/building-concerns-let-us-know"),
    ("Library — Book Arts Lab",                     "https://library.carleton.ca/building/book-arts-lab"),
    ("Library — Services for Undergraduate Students", "https://library.carleton.ca/services/services-undergraduate-students"),
    ("Library — Services for Graduate Students",    "https://library.carleton.ca/services/services-graduate-students"),
    ("Library — Services for Alumni",               "https://library.carleton.ca/services/services-alumni"),
    ("Library — Services for General Public",       "https://library.carleton.ca/services/services-general-public"),
    ("Library — Services for High Schools",         "https://library.carleton.ca/services/services-high-schools"),
    ("Library — Accessibility Services",            "https://library.carleton.ca/services/library-accessibility-services"),
    ("Library — Accessibility in the Building",     "https://library.carleton.ca/services/library-accessibility-services/accessibility-library-building"),
    ("Library — Adaptive Technology",               "https://library.carleton.ca/services/library-accessibility-services/adaptive-technology"),
    ("Library — Computers",                         "https://library.carleton.ca/services/computers"),
    ("Library — Borrowing",                         "https://library.carleton.ca/services/borrowing"),
    ("Library — Course Reserves",                   "https://library.carleton.ca/find/reserves"),
    ("Library — Interlibrary Loans",                "https://library.carleton.ca/services/interlibrary-loans"),
    ("Library — Research Data Centre",              "https://library.carleton.ca/services/carleton-university-research-data-centre"),
]


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ").replace("​", "")).strip()


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "CampusQ-Bot/1.0"})
        if r.status_code != 200:
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"    Fetch error: {e}")
        return None


def extract_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "form"]):
        tag.decompose()
    main = (
        soup.find("div", class_=re.compile(r"entry-content|page-content|main-content|content", re.I)) or
        soup.find("main") or
        soup.find("article") or
        soup.find("body")
    )
    if not main:
        return ""
    lines = []
    for elem in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "dt", "dd"]):
        text = clean(elem.get_text(" ", strip=True))
        if text and len(text) > 3:
            lines.append(text)
    return "\n".join(lines)


def chunk_text(title: str, text: str, max_words: int = 500) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current, word_count = [], [], 0
    for para in paragraphs:
        words = len(para.split())
        if word_count + words > max_words and current:
            chunks.append("\n".join(current))
            current, word_count = [], 0
        current.append(para)
        word_count += words
    if current:
        chunks.append("\n".join(current))
    return [c for c in chunks if len(c) > 80]


def upload(label: str, url: str, chunks: list[str]) -> int:
    if not chunks:
        return 0
    texts = [f"{label}\n{c[:900]}" for c in chunks]
    response = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)
    vectors = []
    for i, emb_data in enumerate(response.data):
        chunk_id = hashlib.md5(f"{url}-{i}".encode()).hexdigest()[:20]
        vectors.append({
            "id": chunk_id,
            "values": emb_data.embedding,
            "metadata": {
                "title": label,
                "text": f"{label}\n\n{chunks[i][:2000]}",
                "source": url,
                "chunk": i,
            },
        })
    index.upsert(vectors=vectors, namespace=NAMESPACE)
    return len(vectors)


def run():
    print("=" * 55)
    print("CampusQ - Library Scraper")
    print("=" * 55 + "\n")

    total = 0
    for i, (label, url) in enumerate(URLS):
        print(f"[{i+1}/{len(URLS)}] {label}")
        soup = fetch_page(url)
        if not soup:
            print(f"  Failed to fetch")
            time.sleep(0.5)
            continue
        text = extract_text(soup)
        if len(text) < 100:
            print(f"  No content")
            time.sleep(0.3)
            continue
        chunks = chunk_text(label, text)
        n = upload(label, url, chunks)
        total += n
        print(f"  {n} chunks")
        time.sleep(0.4)

    print(f"\n{'='*55}")
    print(f"DONE - {total} vectors in '{NAMESPACE}' namespace")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
