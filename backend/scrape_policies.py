import os
import requests
from bs4 import BeautifulSoup
import re
import time
import hashlib
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# CONFIG & CLIENTS
# =========================================================
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "knowledge-base"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

NAMESPACE = "policies"
EMBED_MODEL = "text-embedding-3-small"

POLICY_URLS = [
    "https://carleton.ca/co-op/apply/undergraduate-students/",
    "https://carleton.ca/co-op/program-cost/",
    "https://carleton.ca/co-op/work-study-sequences/undergraduate/",
    "https://carleton.ca/co-op/rules-regulations/co-op-participation-agreement/",
    "https://carleton.ca/co-op/co-op-work-study-patterns/faculty-of-arts-and-social-sciences/",
    "https://carleton.ca/co-op/co-op-work-study-patterns/faculty-of-public-and-global-affairs/",
    "https://carleton.ca/co-op/co-op-work-study-patterns/sprott-school-of-business/",
    "https://carleton.ca/co-op/faqs/prospective-co-op-students-faqs/",
    "https://carleton.ca/co-op/co-op-work-study-patterns/faculty-of-engineering-and-design/",
    "https://carleton.ca/co-op/co-op-work-study-patterns/faculty-of-science/",
    "https://carleton.ca/co-op/co-op-work-study-patterns/school-of-computer-science/",
    "https://carleton.ca/engineering-design/current-students/undergrad-academic-support/prerequisites/"
]

def extract_semantic_chunks(soup: BeautifulSoup) -> list[dict]:
    chunks = []
    content_area = soup.find('div', class_='entry-content') or soup.find('main')
    if not content_area: return []

    page_title_elem = soup.find('h1')
    page_title = page_title_elem.get_text(strip=True) if page_title_elem else "General Policy"
    
    current_header = page_title
    current_content = []

    for element in content_area.children:
        if not element.name:
            continue

        text_content = element.get_text(strip=True)
        
        # 1. Standard HTML Headers
        is_standard_header = element.name in ['h1', 'h2', 'h3', 'h4']
        
        # 2. Faux Headers (Short paragraphs entirely in bold)
        is_faux_header = False
        if element.name == 'p':
            strong_tag = element.find('strong')
            if strong_tag and text_content and len(text_content) < 80:
                if text_content == strong_tag.get_text(strip=True):
                    is_faux_header = True

        # 3. ALL CAPS Headers (Carleton specific formatting fix)
        is_caps_header = (
            element.name in ['p', 'div'] and 
            text_content.isupper() and 
            len(text_content) > 3 and 
            len(text_content) < 80
        )

        if is_standard_header or is_faux_header or is_caps_header:
            if current_content:
                text_body = "\n".join(current_content)
                if len(text_body.strip()) > 20:
                    chunks.append({"section_header": current_header, "text": text_body})
                current_content = []
            
            section_title = text_content
            if section_title.lower() not in page_title.lower():
                current_header = f"{page_title} - {section_title}"
            else:
                current_header = section_title
                
        else:
            # Normal content
            element_text = element.get_text(separator="\n", strip=True)
            if element_text:
                current_content.append(element_text)

    # Catch the final chunk
    if current_content:
        text_body = "\n".join(current_content)
        if len(text_body.strip()) > 20:
            chunks.append({"section_header": current_header, "text": text_body})

    return chunks

def process_policy_page(url: str):
    print(f"Scraping: {url}")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"  ✗ Failed to fetch (Status {response.status_code})")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
            
        semantic_chunks = extract_semantic_chunks(soup)
        
        if not semantic_chunks:
            print("  ✗ No content extracted.")
            return
            
        texts_to_embed = [f"Section: {c['section_header']}\n{c['text']}" for c in semantic_chunks]
        print(f"  Extracted {len(texts_to_embed)} semantic sections. Generating embeddings...")
        
        # Embed
        embeddings = [d.embedding for d in openai_client.embeddings.create(model=EMBED_MODEL, input=texts_to_embed).data]
        
        vectors = []
        slug = url.rstrip('/').split('/')[-1]
        
        for i, (chunk_data, emb) in enumerate(zip(semantic_chunks, embeddings)):
            vector_id = hashlib.md5(f"{slug}_{i}".encode()).hexdigest()
            vectors.append({
                "id": vector_id,
                "values": emb,
                "metadata": {
                    "section_header": chunk_data['section_header'],
                    "text": chunk_data['text'],
                    "source_url": url,
                    "doc_type": "policy",
                    "category": "co-op" if "co-op" in url else "engineering_support"
                }
            })
            
        # Upsert
        for i in range(0, len(vectors), 100):
            index.upsert(vectors=vectors[i:i+100], namespace=NAMESPACE)
            
        print(f"  ✓ Upserted {len(vectors)} semantic policy blocks")
        
    except Exception as e:
        print(f"  ✗ Error processing {url}: {e}")

if __name__ == "__main__":
    print("Starting Semantic Policy Scraper...")
    for url in POLICY_URLS:
        process_policy_page(url)
        time.sleep(1)
    print("\n✓ Policy Data Ingestion Complete!")