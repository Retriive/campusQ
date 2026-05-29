"""
scrape_courses.py — Scrapes every undergrad course from calendar.carleton.ca.

Strategy:
  - Discover all department pages under /undergrad/courses/
  - Use BeautifulSoup (NOT trafilatura — course pages are structured data, not articles)
  - Parse with the regex pattern that was proven to work on Carleton's calendar format
  - Store one Pinecone vector per course, ID = course code (e.g. SYSC3110)

Namespace: "courses"
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE   = "courses"
EMBED_MODEL = "text-embedding-3-small"
COURSES_ROOT = "https://calendar.carleton.ca/undergrad/courses/"

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_description(body: str) -> str:
    """Strip calendar boilerplate from the course body."""
    cutoffs = [
        r"Precludes additional credit",
        r"Prerequisite\(s\)\s*[: ]",
        r"Includes:\s*Experiential Learning",
        r"Lectures\s+\w+\s+hours?",
        r"Also listed as",
        r"Not available for",
    ]
    desc = body
    for pattern in cutoffs:
        m = re.search(pattern, desc, re.IGNORECASE)
        if m:
            desc = desc[:m.start()].strip().rstrip(".,")
    return desc.strip()

def extract_prereq_text(body: str) -> str:
    """Extract the full prerequisite sentence."""
    m = re.search(
        r"Prerequisite\(s\)\s*[: ]\s*(.+?)(?=\s*(?:Precludes|Lectures\s+\w+|Also listed|Not available|\Z))",
        body, re.IGNORECASE | re.DOTALL
    )
    if m:
        return m.group(1).strip().rstrip(".")
    return ""

def extract_prereq_codes(prereq_text: str) -> list:
    """Pull individual course codes out of a prerequisite string."""
    raw = re.findall(r"[A-Z]{3,4}\s+\d{4}", prereq_text)
    return list(dict.fromkeys(raw))

# ── Stage 1: Discover all department pages ────────────────────────────────────

def get_department_links() -> list:
    print(f"\n[1/4] Discovering department pages from {COURSES_ROOT}")
    r = requests.get(COURSES_ROOT, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    content = soup.find("div", class_="pageblock") or soup.find("main") or soup

    links = []
    for a in content.find_all("a", href=True):
        url = urljoin(COURSES_ROOT, a["href"])
        if (
            url.startswith(COURSES_ROOT)
            and url != COURSES_ROOT
            and ".pdf" not in url
            and "#" not in url
            and url not in links
        ):
            links.append(url)

    print(f"  → Found {len(links)} department pages")
    return links

# ── Stage 2: Scrape a department page ─────────────────────────────────────────

def scrape_department(url: str) -> str:
    """
    Use BeautifulSoup — NOT trafilatura.
    Trafilatura is built for editorial articles; it discards structured
    course catalog content as 'boilerplate'. BeautifulSoup preserves it.
    """
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
            tag.decompose()
        main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body")
        raw = main.get_text(separator="\n")
        return clean_text(raw)
    except Exception as e:
        print(f"    ✗ Scrape error: {e}")
        return ""

# ── Stage 3: Parse courses from text ─────────────────────────────────────────

# Carleton calendar format:
#   SYSC 3110 [0.5 credit]
#   Software Engineering Design
#   An introduction to the design...
#
# The proven regex from the original working scraper, extended to handle
# credit format variations and non-breaking spaces.

COURSE_PATTERN = re.compile(
    r"([A-Z]{3,4}[\s\xa0]\d{4})\s*\[([\d.]+\s*credits?)\]\s*\n(.*?)(?=\n[A-Z]{3,4}[\s\xa0]\d{4}\s*\[|\Z)",
    re.DOTALL | re.IGNORECASE,
)

# Fallback for pages that list credits differently (e.g. "0.5 credit units")
COURSE_PATTERN_ALT = re.compile(
    r"([A-Z]{3,4}[\s\xa0]\d{4})\s*\n([\d.]+\s*credit[^\n]*)\n(.*?)(?=\n[A-Z]{3,4}[\s\xa0]\d{4}\s*\n|\Z)",
    re.DOTALL | re.IGNORECASE,
)

def parse_courses(text: str, source_url: str) -> list:
    courses = []
    seen = set()

    def process_match(raw_code, raw_credits, body):
        course_code = raw_code.replace("\xa0", " ").strip()
        if course_code in seen:
            return
        seen.add(course_code)

        body_lines = [l for l in body.strip().split("\n") if l.strip()]
        if not body_lines or len(body.strip()) < 30:
            return

        course_name = body_lines[0].strip()

        # Parse credits
        cred_m = re.search(r"([\d.]+)", raw_credits)
        credits = float(cred_m.group(1)) if cred_m else 0.5

        prereq_text = extract_prereq_text(body)
        prereq_codes = extract_prereq_codes(prereq_text)
        description = extract_description(body)

        dept = re.match(r"[A-Z]+", course_code)
        dept = dept.group(0) if dept else ""

        courses.append({
            "course_code": course_code,
            "course_name": course_name,
            "credits": credits,
            "description": description,
            "prerequisite_text": prereq_text,
            "prerequisites": prereq_codes,
            "department": dept,
            "source": source_url,
        })

    # Try primary pattern
    for m in COURSE_PATTERN.finditer(text):
        process_match(m.group(1), m.group(2), m.group(3))

    # If primary found nothing, try alternate format
    if not courses:
        for m in COURSE_PATTERN_ALT.finditer(text):
            process_match(m.group(1), m.group(2), m.group(3))

    return courses

# ── Stage 4: Embed and upload ─────────────────────────────────────────────────

def build_text_field(c: dict) -> str:
    """The 'text' stored in metadata — used by the backend for display."""
    lines = [c["course_code"], str(c["credits"]), c["course_name"]]
    if c["description"]:
        lines.append(c["description"])
    return "\n".join(lines)

def build_embed_text(c: dict) -> str:
    """Rich semantic text for embedding — helps RAG find the right course."""
    parts = [f"{c['course_code']}: {c['course_name']}"]
    if c["description"]:
        parts.append(c["description"][:600])
    if c["prerequisite_text"]:
        parts.append(f"Prerequisites: {c['prerequisite_text']}")
    return " | ".join(parts)

def upload_courses(courses: list, batch_size: int = 50):
    if not courses:
        return

    for i in range(0, len(courses), batch_size):
        batch = courses[i:i + batch_size]
        texts = [build_embed_text(c) for c in batch]

        response = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)

        vectors = []
        for j, emb_data in enumerate(response.data):
            c = batch[j]
            course_id = re.sub(r"[^A-Z0-9]", "", c["course_code"].upper())
            vectors.append({
                "id": course_id,
                "values": emb_data.embedding,
                "metadata": {
                    "course_code":       c["course_code"],
                    "course_name":       c["course_name"],
                    "credits":           str(c["credits"]),
                    "description":       c["description"][:800],
                    "prerequisite_text": c["prerequisite_text"],
                    "prerequisites":     ", ".join(c["prerequisites"]) if c["prerequisites"] else "None",
                    "department":        c["department"],
                    "source":            c["source"],
                    "text":              build_text_field(c),
                },
            })

        index.upsert(vectors=vectors, namespace=NAMESPACE)

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    dept_urls = get_department_links()
    total = 0

    print(f"\n[2/4] Scraping {len(dept_urls)} department pages...\n")

    for i, url in enumerate(dept_urls):
        dept = url.rstrip("/").split("/")[-1].upper()
        print(f"  [{i+1}/{len(dept_urls)}] {dept}", end="  ")

        text = scrape_department(url)
        if not text:
            print("✗ no text")
            continue

        courses = parse_courses(text, url)
        if not courses:
            # Debug: show a sample of the raw text so we can diagnose
            snippet = text[:300].replace("\n", "\\n")
            print(f"✗ 0 parsed  |  sample: {snippet[:120]}")
            continue

        upload_courses(courses)
        total += len(courses)
        print(f"✓ {len(courses)} courses")
        time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"✓ COURSES DONE — {total} total courses indexed")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    run()
