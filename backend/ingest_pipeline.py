import os
import trafilatura
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==========================================
# 1. INITIALIZATION & AUTHENTICATION
# ==========================================
print("Loading environment variables and connecting to cloud services...")
load_dotenv()

# Initialize OpenAI and Pinecone clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = os.getenv("PINECONE_INDEX_NAME")
index = pc.Index(index_name)

# ==========================================
# 2. THE HARVESTER (TRAFILATURA)
# ==========================================
def scrape_clean_text(url):
    print(f"\n[1/4] Scraping raw data from: {url}")
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise Exception("Failed to download the webpage.")
        
    clean_text = trafilatura.extract(
        downloaded,
        include_links=False,
        include_images=False,
        include_tables=True
    )
    
    if not clean_text:
        raise Exception("No usable text found on the page.")
        
    print(f"      Success! Extracted {len(clean_text)} characters of pure text.")
    return clean_text

# ==========================================
# 3. THE SLICER (LANGCHAIN)
# ==========================================
def chunk_text(text):
    print("[2/4] Slicing text into contextually aware chunks...")
    # 800 characters per chunk, with 100 char overlap to preserve sentence context
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    print(f"      Success! Created {len(chunks)} document chunks.")
    return chunks

# ==========================================
# 4. THE BRAIN (OPENAI -> PINECONE)
# ==========================================
def vectorize_and_upload(chunks, source_url, tenant):
    print("[3/4] Generating OpenAI embeddings for all chunks...")
    
    # We embed the chunks in batches so we don't hit OpenAI API limits
    batch_size = 100
    total_vectors_uploaded = 0

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        
        # Call OpenAI to turn the text into numbers
        response = openai_client.embeddings.create(
            input=batch_chunks,
            model="text-embedding-3-small"
        )
        
        vectors_to_upsert = []
        for j, embedding_data in enumerate(response.data):
            # Create a unique ID for each chunk (e.g., carleton-url-chunk-0)
            chunk_id = f"{tenant}-chunk-{i+j}"
            
            # This is the crucial metadata payload for CampusQ citations
            metadata = {
                "text": batch_chunks[j],
                "source": source_url,
                "tenant": tenant
            }
            
            vectors_to_upsert.append({
                "id": chunk_id,
                "values": embedding_data.embedding,
                "metadata": metadata
            })

        print(f"[4/4] Uploading batch of {len(vectors_to_upsert)} vectors to Pinecone namespace: '{tenant}'...")
        # Push to Pinecone
        index.upsert(vectors=vectors_to_upsert, namespace=tenant)
        total_vectors_uploaded += len(vectors_to_upsert)

    print(f"\n✅ PIPELINE COMPLETE! Successfully uploaded {total_vectors_uploaded} vectors to Pinecone.")

# ==========================================
# 🚀 EXECUTE PIPELINE
# ==========================================
if __name__ == "__main__":
    target_url = "https://calendar.carleton.ca/undergrad/undergradprograms/engineering/"
    tenant_name = "carleton"
    
    try:
        raw_text = scrape_clean_text(target_url)
        document_chunks = chunk_text(raw_text)
        vectorize_and_upload(document_chunks, target_url, tenant_name)
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {e}")