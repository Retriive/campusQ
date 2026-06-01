"""
scrape_programs.py — Scrapes all Carleton undergrad program pages.

Each real degree variant (Honours, Major, Minor, Stream, Concentration,
Specialization, Certificate, Diploma) becomes its own Pinecone vector.
Boilerplate sections (Regulations, Co-op, Transfer, Change of Program, etc.)
are filtered out.

Safe to re-run — stable IDs overwrite previous vectors.
Run: py scrape_programs.py
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "programs"
EMBED_MODEL = "text-embedding-3-small"
BASE = "https://calendar.carleton.ca"
PROGRAMS_ROOT = f"{BASE}/undergrad/undergradprograms/"

FACULTY_MAP = {
    "engineering":              "Engineering & Design",
    "architecture":             "Engineering & Design",
    "architecturalstudies":     "Engineering & Design",
    "historyandtheoryofarchitecture": "Engineering & Design",
    "industrialdesign":         "Engineering & Design",
    "informationtechnology":    "Information Technology",
    "computerscience":          "Science",
    "mathematics":              "Science",
    "mathematicsandstatistics": "Science",
    "physics":                  "Science",
    "chemistry":                "Science",
    "biology":                  "Science",
    "biochemistry":             "Science",
    "biotechnology":            "Science",
    "earthsciences":            "Science",
    "environmentalscience":     "Science",
    "neuroscience":             "Science",
    "psychology":               "Science",
    "statistics":               "Science",
    "datascience":              "Science",
    "nanoscience":              "Science",
    "foodscience":              "Science",
    "bioinformatics":           "Science",
    "integratedscience":        "Science",
    "linguistics-bsc":          "Science",
    "business":                 "Sprott School of Business",
    "publicaffairsandpolicymanagement": "Public Affairs",
    "publicadministration":     "Public Affairs",
    "humanrights":              "Public Affairs",
    "socialwork":               "Public Affairs",
    "healthsciences":           "Health Sciences",
    "nursing":                  "Health Sciences",
}

# ── Heading filters ───────────────────────────────────────────────────────────

# Hard reject: boilerplate sections that are never degree entries
BLOCKLIST = re.compile(
    r"regulations|change of program|academic continuation|co-op admission|"
    r"continuation requirements|transfer (into|from|in )|advanced standing|"
    r"transferring|breadth requirement|approved electives|first-year course "
    r"selection|graduation \(|concentrations (in|for) |"
    r"^post-baccalaureate diploma$|"           # generic, no subject
    r"^bachelor of \w+ combined honours$|"     # no discipline named (section header)
    r"^bachelor of \w+ and bachelor of|"       # dual-degree admin heading
    r"^b\.[a-z.]+\s+hons\.$|"                  # e.g. "B.A.S. Hons."
    r"^b\.[a-z.]+\s+with minor$|"              # e.g. "B.Hum. with Minor"
    r"^b\.[a-z.]+\s+combined honours$|"        # co-op section headers like "B.Sc. Combined Honours Neuroscience"
    r"school of|faculty of|department of|"
    r"program overview|calendar updates|disclaimer|accreditation|glossary|"
    r"print and pdf|industrial applications|year abroad",
    re.IGNORECASE,
)

def is_degree_heading(text: str) -> bool:
    if len(text) < 8 or len(text) > 140:
        return False
    if BLOCKLIST.search(text):
        return False

    # Strong positive signal 1: has a credit count "(X.X credits)"
    # Almost every real degree entry has this; almost no boilerplate does.
    if re.search(r'\(\d+\.?\d*\s+credits?\)', text, re.IGNORECASE):
        return True

    # Strong positive signal 2: named sub-program types
    if re.search(
        r'\b(Minor|Concentration|Stream|Specialization|Certificate|'
        r'Post-Baccalaureate Diploma)\s+in\s+\S',
        text, re.IGNORECASE,
    ):
        return True

    # Strong positive signal 3: explicit degree designation (B.C.S., B.Sc., B.A., B.Math., etc.)
    # followed by Honours, Major, or Combined
    if re.search(r'\bB\.[A-Z][a-zA-Z.]*\.?\s+(Honours|Major|Combined)', text):
        return True

    # Strong positive signal 4: "Bachelor of [discipline]" headings
    if re.search(r'\bBachelor of\b', text, re.IGNORECASE):
        return True

    return False


# ── Scraping helpers ──────────────────────────────────────────────────────────

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("​", "").replace("\xa0", " ")).strip()


def extract_until_next_heading(start_tag) -> str:
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


def detect_faculty(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1].lower()
    for key, faculty in FACULTY_MAP.items():
        if slug == key or key in slug:
            return faculty
    return "Arts & Social Sciences"


def get_program_urls() -> list[str]:
    print("Discovering program pages...")
    r = requests.get(PROGRAMS_ROOT, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    content = soup.find("div", class_="pageblock") or soup.find("main") or soup

    urls = []
    for a in content.find_all("a", href=True):
        url = urljoin(PROGRAMS_ROOT, a["href"])
        if (
            url.startswith(PROGRAMS_ROOT)
            and url.rstrip("/") != PROGRAMS_ROOT.rstrip("/")
            and ".pdf" not in url
            and "#" not in url
            and url not in urls
        ):
            urls.append(url)

    print(f"  Found {len(urls)} program pages\n")
    return urls


def scrape_page(url: str) -> list[dict]:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body")

    chunks = []
    for tag in main.find_all(["h2", "h3", "h4"]):
        name = clean(tag.get_text(" ", strip=True))
        if not is_degree_heading(name):
            continue
        content = extract_until_next_heading(tag)
        if len(content) < 80:
            continue
        chunks.append({"name": name, "content": content})

    return chunks


def upload(url: str, chunks: list[dict], faculty: str) -> int:
    slug = url.rstrip("/").split("/")[-1]

    texts = [
        f"{c['name']}\nRequired courses and program structure:\n{c['content'][:900]}"
        for c in chunks
    ]

    response = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)

    vectors = []
    for i, emb_data in enumerate(response.data):
        c = chunks[i]
        name_slug = re.sub(r"[^a-z0-9]", "-", c["name"].lower())[:60].strip("-")
        vectors.append({
            "id": f"{slug}-{name_slug}",
            "values": emb_data.embedding,
            "metadata": {
                "program": c["name"],
                "faculty": faculty,
                "section": "Full Requirements",
                "text": f"{c['name']}\n\n{c['content'][:2000]}",
                "source": url,
            },
        })

    index.upsert(vectors=vectors, namespace=NAMESPACE)
    return len(vectors)


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 55)
    print("CampusQ — Program Scraper (heading-aware, all depts)")
    print("=" * 55 + "\n")

    urls = get_program_urls()
    total_chunks = 0
    total_pages = 0

    for i, url in enumerate(urls):
        slug = url.rstrip("/").split("/")[-1]
        print(f"[{i+1}/{len(urls)}] {slug}")

        try:
            chunks = scrape_page(url)
        except Exception as e:
            print(f"  ✗ Fetch failed: {e}")
            continue

        if not chunks:
            print(f"  — no degree headings found")
            continue

        faculty = detect_faculty(url)

        try:
            n = upload(url, chunks, faculty)
            total_chunks += n
            total_pages += 1
            print(f"  ✓ {n} variants  [{faculty}]")
            for c in chunks:
                print(f"      · {c['name'][:75]}")
        except Exception as e:
            print(f"  ✗ Upload failed: {e}")

        time.sleep(0.5)

    print(f"\n{'='*55}")
    print(f"DONE — {total_pages} pages, {total_chunks} variants indexed")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
