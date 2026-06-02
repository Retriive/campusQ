import os
import fitz  # PyMuPDF
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()

# Initialize OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base") # Matches your dashboard exactly!

def get_embedding(text):
    """Converts text into an AI vector array using OpenAI."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small" # Fast, cheap, and highly accurate
    )
    return response.data[0].embedding

def process_pdf(file_path):
    """Extracts text from a PDF page by page."""
    doc_name = os.path.basename(file_path)
    print(f"Reading {doc_name}...")
    
    doc = fitz.open(file_path)
    chunks = []
    
    # MVP approach: Chunk by page
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        
        # Only save pages that actually have text
        if text:
            chunks.append({
                "text": text,
                "metadata": {"doc": doc_name, "section": f"Page {page_num + 1}"}
            })
            
    return chunks

def build_database():
    """Reads all PDFs in the docs folder and saves them to Pinecone."""
    docs_dir = "./docs"
    
    if not os.path.exists(docs_dir) or not os.listdir(docs_dir):
        print(f"Error: Put some PDFs in the '{docs_dir}' folder first!")
        return

    print("Starting Pinecone ingestion pipeline...")
    
    for filename in os.listdir(docs_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(docs_dir, filename)
            chunks = process_pdf(file_path)
            
            vectors_to_upsert = []
            
            for i, chunk in enumerate(chunks):
                print(f"Embedding {filename} (Chunk {i+1}/{len(chunks)})...")
                embedding = get_embedding(chunk["text"])
                
                # Package the data for Pinecone (id, values, metadata)
                vectors_to_upsert.append({
                    "id": f"{filename}_chunk_{i}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk["text"],
                        "doc": chunk["metadata"]["doc"],
                        "section": chunk["metadata"]["section"]
                    }
                })
                
            # Send the batch over the internet to Pinecone
            if vectors_to_upsert:
                index.upsert(vectors=vectors_to_upsert)
                
    print("✅ Knowledge base built successfully! Vectors stored in Pinecone.")

if __name__ == "__main__":
    build_database()