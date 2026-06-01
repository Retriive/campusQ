"""
scrape_tuition.py — Scrapes all Carleton tuition, fees, and student accounts pages.

Namespace: "tuition"
Safe to re-run — content-hash IDs overwrite previous vectors.
Run: py scrape_tuition.py
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

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "tuition"
EMBED_MODEL = "text-embedding-3-small"

URLS = [
    ("Financial Rights",                    "https://carleton.ca/studentaccounts/financial-rights/"),
    ("Tuition Fee Notes",                   "https://carleton.ca/studentaccounts/tuition-fees/tuition-fee-notes/"),
    ("Fee Assessment",                      "https://carleton.ca/studentaccounts/tuition-fees/fee-assessment/"),
    ("Late Charges",                        "https://carleton.ca/studentaccounts/tuition-fees/late-charges/"),
    ("Interest Charges",                    "https://carleton.ca/studentaccounts/tuition-fees/interest-charges/"),
    ("Financial Holds",                     "https://carleton.ca/studentaccounts/tuition-fees/financial-holds/"),
    ("Administrative Charges",             "https://carleton.ca/studentaccounts/tuition-fees/admin-charges/"),
    ("Miscellaneous Fees",                  "https://carleton.ca/studentaccounts/tuition-fees/misc-fees/"),
    ("Historical Fees",                     "https://carleton.ca/studentaccounts/tuition-fees/historical-fees/"),
    ("View Student Account",               "https://carleton.ca/studentaccounts/fee-payment/view-student-account/"),
    ("Payment Schedule",                   "https://carleton.ca/studentaccounts/fee-payment/payment-schedule/"),
    ("Payment Methods",                    "https://carleton.ca/studentaccounts/fee-payment/payment-methods/"),
    ("Payment Within Canada",              "https://carleton.ca/studentaccounts/fee-payment/payment-methods/payment-within-canada/"),
    ("Payment from Outside Canada",        "https://carleton.ca/studentaccounts/fee-payment/payment-methods/payment-from-outside-canada-2/"),
    ("Payroll Deductions",                 "https://carleton.ca/studentaccounts/fee-payment/payment-methods/payroll-deductions/"),
    ("Refund Policy",                      "https://carleton.ca/studentaccounts/fee-payment/refund-policy/"),
    ("Information for New Students",       "https://carleton.ca/studentaccounts/fee-payment/information-for-new-students/"),
    ("Information for Sponsored Students", "https://carleton.ca/studentaccounts/fee-payment/information-sponsored-students/"),
    ("Fee Estimator Guide",                "https://carleton.ca/studentaccounts/fee-estimator-guide/"),
    ("Income Tax Forms for Students",      "https://carleton.ca/studentaccounts/income-tax-forms-students/"),
    ("Information for Parents / Guardians","https://carleton.ca/studentaccounts/for-parentsguardians/"),
    ("Student Accounts FAQ",               "https://carleton.ca/studentaccounts/faq/"),
    ("Third Party Billing",                "https://carleton.ca/studentaccounts/third-party/"),
    ("Student Accounts Contact",           "https://carleton.ca/studentaccounts/contact-us/"),
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
        raw_id = f"{url}-{i}"
        chunk_id = hashlib.md5(raw_id.encode()).hexdigest()[:20]
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
    print("CampusQ - Tuition & Student Accounts Scraper")
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
        time.sleep(0.5)

    print(f"\n{'='*55}")
    print(f"DONE - {total} vectors in '{NAMESPACE}' namespace")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
