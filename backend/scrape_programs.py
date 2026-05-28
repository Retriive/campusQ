import os
import re
import time
import requests
import fitz
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv

from pinecone import Pinecone
from openai import OpenAI

# =========================================================
# CONFIG
# =========================================================

START_URL = "https://calendar.carleton.ca/undergrad/undergradprograms/"
PDF_FOLDER = "pdfs"
ARCHIVE_FOLDER = "archive"

NAMESPACE = "programs"
EMBED_MODEL = "text-embedding-3-small"

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME")

if not OPENAI_API_KEY or not PINECONE_API_KEY or not PINECONE_INDEX:
    raise Exception("Missing environment variables")

# =========================================================
# CLIENTS
# =========================================================

openai_client = OpenAI(api_key=OPENAI_API_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# =========================================================
# FOLDERS
# =========================================================

os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

# =========================================================
# STAGE 1 — GET PROGRAM LINKS
# =========================================================

def get_program_links():
    print("[Stage 1] Fetching program links...")

    r = requests.get(START_URL)
    if r.status_code != 200:
        print("Failed to load start page")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    container = soup.find("div", class_="pageblock") or soup.find("main") or soup

    links = set()

    for a in container.find_all("a", href=True):
        url = urljoin(START_URL, a["href"])

        if (
            url.startswith(START_URL)
            and ".pdf" not in url
            and "#" not in url
            and url != START_URL
        ):
            links.add(url)

    links = list(links)

    print(f"Found {len(links)} programs\n")
    return links


# =========================================================
# STAGE 2 — BUILD PDF URL
# =========================================================

def build_pdf_url(program_url):
    slug = program_url.rstrip("/").split("/")[-1]
    pdf_url = f"{program_url}{slug}.pdf"
    return pdf_url, slug


# =========================================================
# STAGE 3 — DOWNLOAD PDF
# =========================================================

def download_pdf(pdf_url, slug):
    path = os.path.join(PDF_FOLDER, f"{slug}.pdf")

    if os.path.exists(path):
        return path

    r = requests.get(pdf_url, timeout=20)

    if r.status_code != 200:
        return None

    with open(path, "wb") as f:
        f.write(r.content)

    return path


# =========================================================
# STAGE 4 — EXTRACT PDF TEXT
# =========================================================

def extract_pdf_text(path):
    try:
        doc = fitz.open(path)
        text = ""

        for page in doc:
            text += page.get_text()

        doc.close()
        return text
    except:
        return ""


# =========================================================
# STAGE 5 — CLEAN TEXT
# =========================================================

def clean_text(text):
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"-\s*\d+\s*-", "", text)
    return text.strip()


# =========================================================
# STAGE 6 — CHUNK TEXT
# =========================================================

def chunk_text(text, size=1200, overlap=200):
    chunks = []
    i = 0

    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap

    return chunks


# =========================================================
# STAGE 7 — BATCH EMBEDDINGS
# =========================================================

def embed_batch(chunks):
    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=chunks
    )
    return [d.embedding for d in response.data]


# =========================================================
# ARCHIVE FUNCTION (NEW)
# =========================================================

def archive_pdf(path):
    try:
        if path and os.path.exists(path):
            filename = os.path.basename(path)
            new_path = os.path.join(ARCHIVE_FOLDER, filename)

            shutil.move(path, new_path)
            print("  Moved PDF to archive")

    except Exception as e:
        print(f"  Failed to archive PDF: {e}")


# =========================================================
# STAGE 8 — PROCESS PROGRAM
# =========================================================

def process_program(program_url):
    pdf_url, slug = build_pdf_url(program_url)

    print(f"Processing: {slug}")

    pdf_path = download_pdf(pdf_url, slug)

    if not pdf_path:
        print("  PDF missing")
        return

    try:
        raw = extract_pdf_text(pdf_path)

        if len(raw) < 200:
            print("  Not enough text")
            return

        cleaned = clean_text(raw)
        chunks = chunk_text(cleaned)

        if not chunks:
            return

        embeddings = embed_batch(chunks)

        vectors = []

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            vectors.append({
                "id": f"{slug}-{i}",
                "values": emb,
                "metadata": {
                    "text": chunk,
                    "program": slug.replace("-", " "),
                    "program_slug": slug,
                    "source_pdf": pdf_url,
                    "source_page": program_url,
                    "tenant": NAMESPACE,
                    "chunk_index": i
                }
            })

        index.upsert(vectors=vectors, namespace=NAMESPACE)

        print(f"  Uploaded {len(vectors)} chunks")

    finally:
        archive_pdf(pdf_path)


# =========================================================
# STAGE 9 — PIPELINE
# =========================================================

def run():
    start = time.time()

    links = get_program_links()

    for i, url in enumerate(links):
        print(f"[{i+1}/{len(links)}]")
        process_program(url)
        time.sleep(1)

    print("\nDONE in", round((time.time() - start)/60, 2), "min")


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":
    run()