"""
scrape_campus.py — Scrapes AI tools, TLS, PMC, CSAS, and Awards/Financial Aid pages.

Namespace: "services" (shared with scrape_services.py and scrape_registrar.py)
Safe to re-run — content-hash IDs overwrite previous vectors.
Run: py scrape_campus.py
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

NAMESPACE = "services"
EMBED_MODEL = "text-embedding-3-small"

URLS = [
    # ── AI at Carleton ───────────────────────────────────────────────────────
    ("AI Tools — Get Help",                     "https://carleton.ca/ai/get-help/"),
    ("AI Tools — Students",                     "https://carleton.ca/ai/students/"),
    ("AI Tools — Microsoft Copilot",            "https://carleton.ca/ai/microsoft-copilot/"),
    ("AI Tools — Policies and Guidelines",      "https://carleton.ca/ai/policies-and-guidelines/"),
    ("AI Tools — Generative AI Copyright",      "https://library.carleton.ca/copyright/generative-ai-tools-copyright-considerations"),
    ("AI Tools — Generative AI and Citations",  "https://library.carleton.ca/guides/help/generative-ai-chatgpt-and-citations"),

    # ── Teaching and Learning Services (TLS) ────────────────────────────────
    ("TLS — About",                             "https://carleton.ca/tls/about/"),
    ("TLS — Who We Are",                        "https://carleton.ca/tls/about/who-we-are/"),
    ("TLS — Events and Programs",               "https://carleton.ca/tls/events-and-programs/"),
    ("TLS — Teaching Resources",               "https://carleton.ca/teachingresources/"),
    ("TLS — Brightspace LMS",                   "https://carleton.ca/brightspace/"),
    ("TLS — Supported Educational Technology",  "https://carleton.ca/tls/educational-technology/supported-educational-technology/"),
    ("TLS — Scantron",                          "https://carleton.ca/tls/teaching-learning-and-pedagogy/scantron/"),
    ("TLS — Future Learning Lab",               "https://carleton.ca/tls/future-learning-lab/"),
    ("TLS — iCureus",                           "https://carleton.ca/tls/future-learning-lab/i-cureus/"),
    ("TLS — Pathy Foundation Fellowship",       "https://carleton.ca/tls/future-learning-lab/pathy-foundation-fellowship/"),
    ("TLS — CityStudio Ottawa",                 "https://carleton.ca/tls/future-learning-lab/citystudio-ottawa/"),
    ("TLS — Fusion",                            "https://carleton.ca/tls/future-learning-lab/fusion/"),
    ("TLS — SAPP",                              "https://carleton.ca/tls/future-learning-lab/sapp/"),
    ("TLS — Experiential Learning Hub",         "https://carleton.ca/tls/experiential-learning-hub/exlh-services-and-programming/"),
    ("TLS — Experience Studios",                "https://carleton.ca/tls/experiential-learning-hub/experience-studios/"),
    ("TLS — XR Projects and Use Cases",         "https://carleton.ca/tls/experiential-learning-hub/xr-projects-and-use-cases/"),
    ("TLS — Immersive Technologies (XR/VR/AR)", "https://carleton.ca/tls/experiential-learning-hub/immersive-technologies-xr-vr-ar/"),

    # ── Paul Menton Centre (PMC) — Accessibility ────────────────────────────
    ("PMC — About",                             "https://carleton.ca/pmc/about-pmc/"),
    ("PMC — Legal Policies and Responsibilities","https://carleton.ca/pmc/about-pmc/legal-policies-and-responsibilities/"),
    ("PMC — Our Team",                          "https://carleton.ca/pmc/about-pmc/our-team/"),
    ("PMC — Registering with PMC",              "https://carleton.ca/pmc/registering-with-pmc/"),
    ("PMC — Documentation Requirements",       "https://carleton.ca/pmc/registering-with-pmc/documentation-requirements-and-forms/"),
    ("PMC — FAQ: Registering",                  "https://carleton.ca/pmc/registering-with-pmc/faq-registering-with-pmc/"),
    ("PMC — Orientation",                       "https://carleton.ca/pmc/registering-with-pmc/pmc-orientation/"),
    ("PMC — Transition Tips for Parents",       "https://carleton.ca/pmc/registering-with-pmc/transition-tips-for-parents/"),
    ("PMC — Transition Tips for Students",      "https://carleton.ca/pmc/registering-with-pmc/transition-tips-for-students/"),
    ("PMC — Current Students",                  "https://carleton.ca/pmc/current-students/"),
    ("PMC — Academic Accommodations",           "https://carleton.ca/pmc/current-students/academic-accommodations/"),
    ("PMC — New Term Checklist",                "https://carleton.ca/pmc/current-students/new-term-checklist/"),
    ("PMC — Exam Accommodations",               "https://carleton.ca/pmc/current-students/academic-accommodations/exam-accommodations/"),
    ("PMC — Learning Strategies",               "https://carleton.ca/pmc/current-students/learning-strategies/"),
    ("PMC — Assistive Technology",              "https://carleton.ca/pmc/current-students/assistive-technology-support/"),
    ("PMC — Support and Study Groups",          "https://carleton.ca/pmc/current-students/support-social-and-study-groups/"),
    ("PMC — Mentor Volunteer Program",          "https://carleton.ca/pmc/current-students/pmc-mentor-volunteer-program-mvp/"),
    ("PMC — Wellness Support",                  "https://carleton.ca/pmc/current-students/pmc-wellness-support/"),
    ("PMC — Notetaking Opportunities",          "https://carleton.ca/pmc/opportunities-at-pmc/notetaking/"),
    ("PMC — Volunteer Proofreading",            "https://carleton.ca/pmc/opportunities-at-pmc/volunteer-proofreading/"),
    ("PMC — Practicum and Internships",         "https://carleton.ca/pmc/opportunities-at-pmc/practicum-and-internships/"),
    ("PMC — Opportunities",                     "https://carleton.ca/pmc/opportunities-at-pmc/"),

    # ── Centre for Student Academic Support (CSAS) ──────────────────────────
    ("CSAS — Home",                             "https://carleton.ca/csas/"),
    ("CSAS — How To Get Support",               "https://carleton.ca/csas/support/how-to/"),
    ("CSAS — One-on-One Appointments",          "https://carleton.ca/csas/support/one-on-one-appointments/"),
    ("CSAS — Learning Support Sessions",        "https://carleton.ca/csas/support/one-on-one-appointments/learning-support-sessions/"),
    ("CSAS — Writing Consultation Sessions",    "https://carleton.ca/csas/support/one-on-one-appointments/writing-consultation-sessions/"),
    ("CSAS — Appointments FAQ",                 "https://carleton.ca/csas/support/one-on-one-appointments/faqs/"),
    ("CSAS — Online Support",                   "https://carleton.ca/csas/online-support/"),
    ("CSAS — Learning and Writing Series",      "https://carleton.ca/csas/online-support/csas-learning-and-writing-development-series/"),
    ("CSAS — Grammar Foundations",              "https://carleton.ca/csas/online-support/grammar-foundations/"),
    ("CSAS — Academic Orientation Day",         "https://carleton.ca/csas/academic-orientation-day/"),
    ("CSAS — Our Team",                         "https://carleton.ca/csas/our-team/"),

    # ── Awards, Scholarships and Financial Aid ───────────────────────────────
    ("Awards — Important Dates",                "https://carleton.ca/awards/dates/"),
    ("Awards — Summer Dates",                   "https://carleton.ca/awards/dates_summer/"),
    ("Awards — Scholarships Overview",          "https://carleton.ca/awards/awards/scholarships/"),
    ("Awards — Entrance Scholarships",          "https://carleton.ca/awards/awards/scholarships/entrance-scholarships/"),
    ("Awards — Prestige Awards",                "https://carleton.ca/awards/awards/scholarships/prestige/"),
    ("Awards — Current Student Scholarships",   "https://carleton.ca/awards/awards/scholarships/current-students/"),
    ("Awards — Scholarship Rules",              "https://carleton.ca/awards/awards/scholarships/rules/"),
    ("Awards — Awards Database",                "https://carleton.ca/awards/awards/scholarships/awards-db/"),
    ("Awards — Scholarship FAQ",                "https://carleton.ca/awards/awards/scholarships/faq/"),
    ("Awards — OSAP Overview",                  "https://carleton.ca/awards/government-financial-aid/osap/"),
    ("Awards — OSAP Application",               "https://carleton.ca/awards/government-financial-aid/osap/application/"),
    ("Awards — After Submitting OSAP",          "https://carleton.ca/awards/government-financial-aid/osap/after-submitting-your-osap-application/"),
    ("Awards — Receiving OSAP Funding",         "https://carleton.ca/awards/government-financial-aid/osap/receiving-funding/"),
    ("Awards — OSAP Academic Progress",         "https://carleton.ca/awards/government-financial-aid/osap/academic-progress/"),
    ("Awards — OSAP Interest-Free Status",      "https://carleton.ca/awards/government-financial-aid/osap/interest-free-status/"),
    ("Awards — OSAP Repayment",                 "https://carleton.ca/awards/government-financial-aid/osap/repayment/"),
    ("Awards — Online MBA OSAP",                "https://carleton.ca/awards/government-financial-aid/osap/online-mba-osap/"),
    ("Awards — Ontario Learn and Stay Grant",   "https://carleton.ca/awards/government-financial-aid/ontario-learn-and-stay-grant-for-nursing-students/"),
    ("Awards — Out of Province Aid",            "https://carleton.ca/awards/government-financial-aid/out-of-province/"),
    ("Awards — US Student Loans",               "https://carleton.ca/awards/government-financial-aid/us-student-loans/"),
    ("Awards — Work Study Program",             "https://carleton.ca/awards/other-resources/work-study/"),
    ("Awards — Other Resources FAQ",            "https://carleton.ca/awards/other-resources/faqs/"),
    ("Awards — Glossary",                       "https://carleton.ca/awards/other-resources/glossary/"),
    ("Awards — Budgeting FLM",                  "https://carleton.ca/awards/budgeting/flm/"),
    ("Awards — Online Budgeting Resources",     "https://carleton.ca/awards/budgeting/online-budgeting-resources/"),
    ("Awards — Budget Calculator",              "https://carleton.ca/awards/budgeting/budget-calculator/"),
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
        soup.find("div", class_=re.compile(r"entry-content|page-content|main-content", re.I)) or
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
    print("CampusQ - Campus Services Scraper")
    print("(AI, TLS, PMC, CSAS, Awards)")
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
