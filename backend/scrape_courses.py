"""
scrape_courses.py — Scrapes every undergrad course from calendar.carleton.ca.

Strategy:
  - Discover all department pages under /undergrad/courses/
  - For each department, extract every course as a structured object
  - Store one Pinecone vector per course, ID = course code (e.g. SYSC3110)
  - This enables both O(1) direct lookup AND semantic RAG search

Namespace: "courses"
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

# ── Clients ──────────────────────────────────────────────────────────────────

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "courses"
EMBED_MODEL = "text-embedding-3-small"
BASE = "https://calendar.carleton.ca"
COURSES_ROOT = f"{BASE}/undergrad/courses/"

# ── Stage 1: Discover department pages ───────────────────────────────────────

def get_department_links():
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

# ── Stage 2: Scrape a department page ────────────────────────────────────────

def scrape_department(url: str) -> str:
    """Use trafilatura for clean extraction, fall back to BeautifulSoup."""
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(
            downloaded,
            include_tables=True,
            include_links=False,
            include_images=False,
            no_fallback=False,
        )
        if text and len(text) > 200:
            return text
    except Exception:
        pass

    # BeautifulSoup fallback
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        main = soup.find("div", class_="pageblock") or soup.find("main") or soup
        lines = [l.strip() for l in main.get_text(separator="\n").splitlines() if l.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"  ✗ Failed to scrape {url}: {e}")
        return ""

# ── Stage 3: Parse courses from page text ────────────────────────────────────

def parse_courses(text: str, source_url: str) -> list[dict]:
    """
    Parses structured course data from a department page.
    Handles both formats:
      SYSC 3110 [0.5 credit] — old style with brackets
      SYSC 3110              — new style without brackets
    """
    # Pattern: course code + optional credit + everything until next course code
    pattern = re.compile(
        r'([A-Z]{3,4}[\xa0 ]\d{4})\s*(?:\[([\d.]+ credits?)\])?\s*\n(.*?)(?=\n[A-Z]{3,4}[\xa0 ]\d{4}|\Z)',
        re.DOTALL | re.IGNORECASE,
    )

    courses = []
    for match in pattern.finditer(text):
        raw_code = match.group(1).replace('\xa0', ' ').strip()
        raw_credits = match.group(2) or ""
        body = match.group(3).strip()

        # Extract course name (first non-empty line of body)
        body_lines = [l.strip() for l in body.split('\n') if l.strip()]
        course_name = body_lines[0] if body_lines else raw_code

        # Skip if body is too short (likely a stub)
        if len(body) < 20:
            continue

        # Parse credits
        cred_match = re.search(r'([\d.]+)', raw_credits)
        if not cred_match:
            # Try to find credits in the body
            cred_match = re.search(r'\[([\d.]+)\s*credit', body, re.IGNORECASE)
        credits = float(cred_match.group(1)) if cred_match else 0.5

        # Parse prerequisite text (full sentence, not just codes)
        prereq_text = ""
        prereq_match = re.search(
            r'Prerequisite\(s\)[:\s]+(.+?)(?=\s*(?:Precludes|Lectures|Also listed|$))',
            body, re.IGNORECASE | re.DOTALL
        )
        if prereq_match:
            prereq_text = prereq_match.group(1).strip().rstrip('.')

        # Extract individual course codes from prereq text
        prereq_codes = []
        if prereq_text:
            raw_codes = re.findall(r'[A-Z]{3,4}[\xa0 ]+\d{4}', prereq_text)
            prereq_codes = list(dict.fromkeys(c.replace('\xa0', ' ').strip() for c in raw_codes))

        # Clean description (strip boilerplate)
        description = body
        for cutoff in [
            r'Precludes additional credit',
            r'Prerequisite\(s\)',
            r'Includes:\s*Experiential Learning',
            r'Lectures\s+\w+\s+hours?',
            r'Also listed as',
        ]:
            m = re.search(cutoff, description, re.IGNORECASE)
            if m:
                description = description[:m.start()].strip().rstrip('.')

        # Department code (first 4 letters of course code)
        dept = re.match(r'[A-Z]+', raw_code)
        dept = dept.group(0) if dept else ""

        courses.append({
            "course_code": raw_code,
            "course_name": course_name,
            "credits": credits,
            "description": description,
            "prerequisite_text": prereq_text,
            "prerequisites": prereq_codes,
            "department": dept,
            "source": source_url,
        })

    return courses

# ── Stage 4: Embed and upload ─────────────────────────────────────────────────

def upload_courses(courses: list[dict], batch_size: int = 50):
    if not courses:
        return

    # Build embedding texts — rich semantic text for good retrieval
    texts = []
    for c in courses:
        parts = [f"{c['course_code']}: {c['course_name']}"]
        if c['description']:
            parts.append(c['description'][:600])
        if c['prerequisite_text']:
            parts.append(f"Prerequisites: {c['prerequisite_text']}")
        texts.append(" | ".join(parts))

    # Embed in batches
    vectors = []
    for i in range(0, len(courses), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_courses = courses[i:i + batch_size]

        response = openai_client.embeddings.create(
            input=batch_texts,
            model=EMBED_MODEL,
        )

        for j, emb_data in enumerate(response.data):
            c = batch_courses[j]
            course_id = c['course_code'].replace(' ', '').replace('\xa0', '')
            vectors.append({
                "id": course_id,
                "values": emb_data.embedding,
                "metadata": {
                    "course_code": c['course_code'],
                    "course_name": c['course_name'],
                    "credits": str(c['credits']),
                    "description": c['description'][:800],
                    "prerequisite_text": c['prerequisite_text'],
                    "prerequisites": ', '.join(c['prerequisites']) if c['prerequisites'] else 'None',
                    "department": c['department'],
                    "source": c['source'],
                    "text": f"{c['course_code']}\n{c['credits']}\n{c['course_name']}\n{c['description']}",
                },
            })

    index.upsert(vectors=vectors, namespace=NAMESPACE)

# ── Main pipeline ─────────────────────────────────────────────────────────────

def run():
    dept_urls = get_department_links()
    total_courses = 0

    print(f"\n[2/4] Scraping {len(dept_urls)} department pages...\n")

    for i, url in enumerate(dept_urls):
        dept = url.rstrip('/').split('/')[-1]
        print(f"  [{i+1}/{len(dept_urls)}] {dept}")

        text = scrape_department(url)
        if not text:
            print("    ✗ No text extracted")
            continue

        courses = parse_courses(text, url)
        if not courses:
            print(f"    ✗ No courses parsed")
            continue

        upload_courses(courses)
        total_courses += len(courses)
        print(f"    ✓ {len(courses)} courses uploaded")
        time.sleep(0.8)

    print(f"\n{'='*50}")
    print(f"✓ COURSES COMPLETE — {total_courses} courses indexed")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    run()
