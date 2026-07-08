"""
scrape_dates.py — Structured ingestion of key academic dates.

The academic-dates page is one dense page where each date is a single line among
hundreds. Scraped as ~500-word chunks, any single deadline gets buried and embeds
poorly. This script instead creates ONE clean, synonym-rich vector PER deadline,
so "when's the payment deadline?" matches a focused chunk about exactly that.

The deadline dataset lives in backend/calendar_feed.py (shared with the
subscribable calendar feed) and is mirrored by the frontend deadline-tracker.tsx
— keep those two in sync when Carleton publishes a new calendar year.

Namespace: "dates"
Run: py scrape_dates.py
"""

import os
import re
import sys
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

# backend/ dir — .env lives here, and so does calendar_feed.py (the shared
# deadline dataset). sys.path insert lets this file run standalone too.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _BACKEND_DIR)
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

from calendar_feed import DEADLINES, SOURCE_URL  # noqa: E402

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "dates"
EMBED_MODEL = "text-embedding-3-small"

# DEADLINES and SOURCE_URL now come from backend/calendar_feed.py — the shared
# dataset that also powers the subscribable calendar feed. Old inline copy kept
# nothing this file needs; edit calendar_feed.py when Carleton publishes dates.

# Synonym hints per category — so varied phrasings all retrieve the right date
SYNONYMS = {
    "registration": "register, registration opens, sign up for courses, enrol, time ticket, course selection",
    "withdrawal":   "drop a course, withdraw, withdrawal, WDN, academic notation, last day to drop, refund deadline",
    "exams":        "final exams, examination period, exam schedule, exam season, finals",
    "payment":      "tuition, fees, payment deadline, pay tuition, fee payment, account balance",
    "classes":      "classes begin, classes start, first day of classes, last day of classes, term start, term end",
    "holiday":      "university closed, holiday, statutory holiday, break, reading week, no classes",
}

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def human_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


def build_text(term: str, category: str, title: str, iso: str) -> str:
    hd = human_date(iso)
    syn = SYNONYMS.get(category, "")
    return (
        f"{term} Academic Deadline — {title}.\n"
        f"Date: {hd} ({iso}).\n"
        f"Term: {term}. Category: {category}.\n"
        f"Related terms: {syn}.\n"
        f"Question this answers: When is {title.lower()} for {term}? "
        f"The answer is {hd}."
    )


def run():
    print("=" * 55)
    print("CampusQ - Structured Academic Dates Ingestion")
    print("=" * 55 + "\n")

    texts = [build_text(term, cat, title, iso) for (_id, term, cat, title, iso) in DEADLINES]

    print(f"Embedding {len(texts)} individual deadline vectors...")
    resp = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)

    vectors = []
    for i, emb in enumerate(resp.data):
        _id, term, cat, title, iso = DEADLINES[i]
        vectors.append({
            "id": f"date-{_id}",
            "values": emb.embedding,
            "metadata": {
                "title": f"{title} — {human_date(iso)}",
                "term": term,
                "category": cat,
                "date": iso,
                "text": texts[i],
                "source": SOURCE_URL,
            },
        })

    index.upsert(vectors=vectors, namespace=NAMESPACE)
    print(f"Done - {len(vectors)} date vectors in '{NAMESPACE}' namespace\n")
    for v in vectors:
        print(f"  - {v['metadata']['title']}")


if __name__ == "__main__":
    run()
