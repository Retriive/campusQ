"""
scrape_dates.py — Structured ingestion of key academic dates.

The academic-dates page is one dense page where each date is a single line among
hundreds. Scraped as ~500-word chunks, any single deadline gets buried and embeds
poorly. This script instead creates ONE clean, synonym-rich vector PER deadline,
so "when's the payment deadline?" matches a focused chunk about exactly that.

Source of truth is shared with the frontend deadline-tracker.tsx — keep them in
sync when Carleton publishes a new calendar year.

Namespace: "dates"
Run: py scrape_dates.py
"""

import os
import re
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

# .env lives in this same backend/ dir
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "dates"
EMBED_MODEL = "text-embedding-3-small"
SOURCE_URL = "https://carleton.ca/registration/academic-dates/"

# (id, term, category, title, YYYY-MM-DD) — mirrors deadline-tracker.tsx
DEADLINES = [
    # Summer 2026
    ("su26-term-begins",    "Summer 2026", "classes",      "Summer term begins; early and full summer classes start", "2026-05-06"),
    ("su26-early-add",      "Summer 2026", "registration", "Last day to add or change early summer courses", "2026-05-12"),
    ("su26-full-add",       "Summer 2026", "registration", "Last day to add full summer courses", "2026-05-20"),
    ("su26-full-fee",       "Summer 2026", "withdrawal",   "Last day to drop full summer courses with a full fee refund", "2026-05-31"),
    ("su26-early-withdraw", "Summer 2026", "withdrawal",   "Last day for academic withdrawal from early summer courses", "2026-06-01"),
    ("su26-payment",        "Summer 2026", "payment",      "Summer term final tuition payment deadline", "2026-06-25"),
    ("su26-canada-day",     "Summer 2026", "holiday",      "Canada Day — University closed", "2026-07-01"),
    ("su26-full-withdraw",  "Summer 2026", "withdrawal",   "Last day for academic withdrawal from full and late summer courses", "2026-08-01"),

    # Fall 2026
    ("fa26-timetickets",    "Fall 2026", "registration", "Registration time tickets become available in Carleton Central", "2026-06-17"),
    ("fa26-reg-new",        "Fall 2026", "registration", "Registration opens for new first-year undergraduate students", "2026-07-06"),
    ("fa26-reg-returning",  "Fall 2026", "registration", "Registration opens for returning undergraduate and graduate students", "2026-07-10"),
    ("fa26-reg-special",    "Fall 2026", "registration", "Registration opens for special and visiting students", "2026-08-05"),
    ("fa26-payment",        "Fall 2026", "payment",      "Fall term tuition payment deadline", "2026-08-25"),
    ("fa26-labour-day",     "Fall 2026", "holiday",      "Labour Day — University closed", "2026-09-07"),
    ("fa26-term-begins",    "Fall 2026", "classes",      "Fall term begins; full fall and fall/winter classes start", "2026-09-09"),
    ("fa26-early-add",      "Fall 2026", "registration", "Last day to add or change early fall courses", "2026-09-15"),
    ("fa26-full-add",       "Fall 2026", "registration", "Last day to add full fall and fall/winter courses", "2026-09-22"),
    ("fa26-full-fee",       "Fall 2026", "withdrawal",   "Last day to drop full fall courses with a full fee refund", "2026-09-30"),
    ("fa26-early-withdraw", "Fall 2026", "withdrawal",   "Last day for academic withdrawal from early fall courses", "2026-10-01"),
    ("fa26-thanksgiving",   "Fall 2026", "holiday",      "Thanksgiving — University closed", "2026-10-12"),
    ("fa26-fall-break",     "Fall 2026", "holiday",      "Fall break begins; no classes (reading week)", "2026-10-26"),
    ("fa26-full-withdraw",  "Fall 2026", "withdrawal",   "Last day for academic withdrawal from full and late fall courses without academic penalty", "2026-11-15"),
    ("fa26-winter-payment", "Fall 2026", "payment",      "Winter term tuition payment deadline", "2026-11-25"),
    ("fa26-lastday",        "Fall 2026", "classes",      "Last day of full fall and late fall classes; fall term ends", "2026-12-11"),
    ("fa26-exams",          "Fall 2026", "exams",        "Fall term final examinations begin", "2026-12-12"),
    ("fa26-uni-closed",     "Fall 2026", "holiday",      "University closes for the December holidays", "2026-12-24"),

    # Winter 2027
    ("wi27-term-begins",    "Winter 2027", "classes",      "Winter term begins; full winter and early winter classes start", "2027-01-06"),
    ("wi27-early-add",      "Winter 2027", "registration", "Last day to add or change early winter courses", "2027-01-12"),
    ("wi27-full-add",       "Winter 2027", "registration", "Last day to add full winter courses", "2027-01-19"),
    ("wi27-full-fee",       "Winter 2027", "withdrawal",   "Last day to drop full winter courses with a full fee refund", "2027-01-31"),
    ("wi27-early-withdraw", "Winter 2027", "withdrawal",   "Last day for academic withdrawal from early winter courses", "2027-02-01"),
    ("wi27-family-day",     "Winter 2027", "holiday",      "Family Day — University closed", "2027-02-15"),
    ("wi27-reading-week",   "Winter 2027", "holiday",      "Winter break / reading week begins; no classes", "2027-02-15"),
    ("wi27-full-withdraw",  "Winter 2027", "withdrawal",   "Last day for academic withdrawal from full and late winter courses", "2027-03-15"),
    ("wi27-good-friday",    "Winter 2027", "holiday",      "Good Friday — University closed", "2027-03-26"),
    ("wi27-lastday",        "Winter 2027", "classes",      "Last day of winter classes; winter term ends", "2027-04-09"),
    ("wi27-exams",          "Winter 2027", "exams",        "Winter term final examinations begin", "2027-04-11"),
    ("wi27-takehome",       "Winter 2027", "exams",        "All winter take-home examinations due", "2027-04-23"),
]

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
