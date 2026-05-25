import os
import time
import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

# Initialize API clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

BASE_URL = "https://calendar.carleton.ca"
START_URL = f"{BASE_URL}/undergrad/courses/"
NAMESPACE = "carleton"

def get_department_links():
    """Stage 1: Uses urljoin to catch every single relative and absolute department link."""
    print(f"[Stage 1] Fetching master course directory from: {START_URL}")
    response = requests.get(START_URL)
    if response.status_code != 200:
        print("Error: Could not access main course directory page.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    content_area = soup.find('div', class_='pageblock') or soup.find('main') or soup.find('body')
    
    dept_links = []
    for link in content_area.find_all('a', href=True):
        href = link['href']
        
        # FIX: Assemble the absolute URL before testing it
        full_url = urljoin(START_URL, href)
        
        # Filter: Must be a sub-page of /undergrad/courses/, and ignore PDFs/Anchors
        if full_url.startswith(START_URL) and full_url != START_URL:
            if ".pdf" not in full_url and "#" not in full_url:
                if full_url not in dept_links:
                    dept_links.append(full_url)
                
    print(f"-> Success: Identified {len(dept_links)} distinct department pages to harvest.")
    return dept_links

def scrape_clean_page(url):
    """Stage 2: Uses BeautifulSoup to extract text WITHOUT deleting hyperlink course codes."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strip structural noise
        for element in soup(["script", "style", "nav", "header", "footer", "form"]):
            element.decompose()
            
        main_content = soup.find('div', class_='pageblock') or soup.find('main') or soup.find('body')
        text = main_content.get_text(separator="\n") if main_content else soup.get_text(separator="\n")
            
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"Skipping {url} due to error: {e}")
        return None

def process_and_upload(text, source_url, dept_index):
    # Regex to capture the header (code + credits) and the remaining description
    # Group 1: Course Code, Group 2: Credits, Group 3: Description/Rest
    course_pattern = re.compile(r'([A-Z]{4}\s\d{4})\s*\[([\d\.]+\scredit)\]\n(.*?)(?=\n[A-Z]{4}\s\d{4}\s*\[|\Z)', re.DOTALL)
    
    matches = course_pattern.finditer(text)
    
    vectors_to_upsert = []
    for match in matches:
        full_header = match.group(0)
        course_code = match.group(1)
        credits = match.group(2)
        body = match.group(3).strip()
        
        # Extract metadata
        prereqs = re.findall(r'Prerequisite\(s\):\s*(.*?)(?=\n|\.)', body)
        precludes = re.findall(r'Precludes additional credit for\s*(.*?)(?=\n|\.)', body)
        
        # Prepare Metadata
        metadata = {
            "text": full_header, # Keep full text for LLM context
            "course_code": course_code,
            "credits": credits,
            "prerequisites": ", ".join(prereqs) if prereqs else "None",
            "precludes": ", ".join(precludes) if precludes else "None",
            "source": source_url,
            "tenant": NAMESPACE
        }
        
        # Generate Embedding
        embedding = openai_client.embeddings.create(
            input=f"{course_code}: {body[:500]}", 
            model="text-embedding-3-small"
        ).data[0].embedding
        
        vectors_to_upsert.append({
            "id": course_code.replace(" ", ""), # Deterministic ID
            "values": embedding,
            "metadata": metadata
        })
        
    if vectors_to_upsert:
        index.upsert(vectors=vectors_to_upsert, namespace=NAMESPACE)
        print(f"      -> Uploaded {len(vectors_to_upsert)} structured course entities.")
        
def run_pipeline():
    start_time = time.time()
    dept_urls = get_department_links()
    
    if not dept_urls:
        print("Pipeline aborted. No links harvested.")
        return

    print("\n[Stage 2] Beginning Deep Clean Harvest...")
    for idx, url in enumerate(dept_urls):
        print(f"[{idx + 1}/{len(dept_urls)}] Shredding noise and extracting from: {url}")
        
        clean_text = scrape_clean_page(url)
        if clean_text and len(clean_text) > 100:
            process_and_upload(clean_text, url, idx)
        else:
            print(f"      Warning: No meaningful context extracted from link.")
            
        time.sleep(1)

    print(f"\n✅ RECURSIVE HARVEST COMPLETE! Total execution time: {round((time.time() - start_time)/60, 2)} minutes.")

if __name__ == "__main__":
    run_pipeline()