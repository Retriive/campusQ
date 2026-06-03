"""
scrape_program_requirements.py — Parse program pages into STRUCTURED requirements.

Unlike scrape_programs.py (which stores readable text blobs in Pinecone for chat),
this produces machine-structured JSON the frontend can build an interactive,
checkable requirement tracker on:

  program -> variant -> [ requirement groups ] -> { instruction, credits, courses[] }

Each requirement group is keyed UNDER its variant heading (Honours, a Stream,
the Minor, etc.) so the tracker can show the right checklist per variant.

Output: backend/data/program_requirements.json
Run:    py scrapers/active/scrape_program_requirements.py [slug]
        (no slug = all program pages; slug e.g. "computerscience" = just one)
"""

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://calendar.carleton.ca"
PROGRAMS_ROOT = f"{BASE}/undergrad/undergradprograms/"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
OUT_FILE = os.path.join(DATA_DIR, "program_requirements.json")

DEGREE_RE = re.compile(
    r"(B\.[A-Za-z.]+\b|Bachelor of|Honours|Combined Honours|\bMajor\b|Minor in|\(Minors?\)|"
    r"Stream in|Concentration in|Specialization in|Post-Baccalaureate|Diploma in|Certificate in)",
    re.IGNORECASE,
)
SKIP_RE = re.compile(
    r"regulations|change of program|academic continuation|co-op admission|"
    r"continuation requirements|breadth requirement|^notes?$|course categories",
    re.IGNORECASE,
)


def clean(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").replace("\xa0", " ").replace("​", "")).strip()


def is_variant_heading(text: str) -> bool:
    if len(text) < 8 or len(text) > 140:
        return False
    if SKIP_RE.search(text):
        return False
    return bool(DEGREE_RE.search(text))


def parse_course_row(tr):
    """Return {code, credits, title} or None for a course row."""
    code_cell = tr.find("td", class_="codecol")
    if not code_cell:
        return None
    raw = clean(code_cell.get_text(" ", strip=True))
    if not raw:
        return None
    title_cell = tr.find("td", class_="titlecol")
    hours_cell = tr.find("td", class_="hourscol")

    credits = None
    # 1) explicit hours column
    if hours_cell:
        m = re.search(r"\d+\.?\d*", hours_cell.get_text())
        if m:
            credits = float(m.group())
    # 2) credit embedded in the code text, e.g. "COMP 1405 [0.5]"
    if credits is None:
        m = re.search(r"\[(\d+\.?\d*)\]", raw)
        if m:
            credits = float(m.group(1))

    # strip the "[0.5]" suffix from the displayed code; keep cross-listed "A / B"
    code = re.sub(r"\s*\[\d+\.?\d*\]", "", raw).strip()

    return {
        "code": code,
        "title": clean(title_cell.get_text(" ", strip=True)) if title_cell else "",
        "credits": credits,
    }


def parse_requirement_table(table) -> list[dict]:
    """
    Split a sc_courselist table into groups.
    A group begins at an area header or a comment/instruction row
    ('1.0 credit in:', '2.5 credits from the following:') and collects the
    course rows that follow until the next instruction.
    """
    groups = []
    current = None

    for tr in table.find_all("tr"):
        cls = " ".join(tr.get("class") or [])
        comment = tr.find("span", class_="courselistcomment")
        is_area = "areaheader" in cls

        if is_area or comment:
            text = clean(tr.get_text(" ", strip=True))
            # pull a credit amount if the instruction states one
            cm = re.search(r"(\d+\.?\d*)\s*credit", text, re.IGNORECASE)
            current = {
                "instruction": text,
                "credits": float(cm.group(1)) if cm else None,
                "courses": [],
            }
            groups.append(current)
            continue

        course = parse_course_row(tr)
        if course:
            if current is None:
                current = {"instruction": "", "credits": None, "courses": []}
                groups.append(current)
            current["courses"].append(course)

    # drop empty groups
    return [g for g in groups if g["courses"] or g["instruction"]]


def parse_program_page(url: str) -> dict:
    # retry transient network failures
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            break
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    else:
        raise last_err
    soup = BeautifulSoup(r.text, "html.parser")
    main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body")

    variants = {}
    current_variant = None

    # Walk the content in document order: headings define variants,
    # sc_courselist tables under them are that variant's requirements.
    for el in main.descendants:
        if getattr(el, "name", None) in ("h1", "h2", "h3", "h4"):
            name = clean(el.get_text(" ", strip=True))
            if is_variant_heading(name):
                current_variant = name
                variants.setdefault(current_variant, [])
        elif getattr(el, "name", None) == "table" and "sc_courselist" in (el.get("class") or []):
            if current_variant is None:
                continue
            groups = parse_requirement_table(el)
            if groups:
                variants[current_variant].extend(groups)

    # keep only variants that actually captured requirement groups
    return {k: v for k, v in variants.items() if v}


def get_program_urls() -> list[str]:
    r = requests.get(PROGRAMS_ROOT, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    content = soup.find("div", class_="pageblock") or soup
    urls = []
    for a in content.find_all("a", href=True):
        url = urljoin(PROGRAMS_ROOT, a["href"])
        if url.startswith(PROGRAMS_ROOT) and url.rstrip("/") != PROGRAMS_ROOT.rstrip("/") and ".pdf" not in url and "#" not in url and url not in urls:
            urls.append(url)
    return urls


def run(only_slug: str | None = None):
    os.makedirs(DATA_DIR, exist_ok=True)
    urls = get_program_urls()
    if only_slug:
        urls = [u for u in urls if u.rstrip("/").split("/")[-1] == only_slug]

    out = {}
    for i, url in enumerate(urls):
        slug = url.rstrip("/").split("/")[-1]
        try:
            variants = parse_program_page(url)
        except Exception as e:
            print(f"[{i+1}/{len(urls)}] {slug}  ERROR: {e}")
            continue
        if variants:
            out[slug] = {"source": url, "variants": variants}
            total_groups = sum(len(v) for v in variants.values())
            print(f"[{i+1}/{len(urls)}] {slug}: {len(variants)} variants, {total_groups} groups")
        time.sleep(0.3)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_FILE} ({len(out)} programs)")


if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else None)
