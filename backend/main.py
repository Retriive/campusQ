import os
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv
import fitz  # PyMuPDF

# Load API Key from .env file
load_dotenv()

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone instead of ChromaDB
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

@app.get("/")
async def health_check():
    """Keeps Render happy by returning a 200 OK status during automated health pings."""
    return {"status": "CampusQ Brain is active and listening."}

@app.get("/api/documents")
async def get_documents():
    """Reads the docs folder and sends the list of PDFs to the frontend sidebar."""
    docs_dir = "./docs"
    if not os.path.exists(docs_dir):
        return {"documents": []}
    
    files = [f for f in os.listdir(docs_dir) if f.endswith(".pdf")]
    
    documents = []
    for i, file in enumerate(files):
        documents.append({
            "id": str(i + 1),
            "name": file,
            "status": "indexed" 
        })
        
    return {"documents": documents}

# ==========================================
# 🚀 NEW: THE COURSE EXPRESS LANE
# ==========================================
@app.get("/api/course/{course_code}")
async def course_lookup(course_code: str):
    """Express lane for deterministic course lookups. Bypasses the LLM entirely."""
    clean_code = course_code.upper().strip()
    print(f"Executing deterministic lookup for: {clean_code}")
    
    try:
        # 1. THE FIX: Add "Semantic Padding" so the vector matches the vibe of a course catalog
        search_query = f"Course description, credits, and prerequisites for {clean_code}"
        
        query_embedding = openai_client.embeddings.create(
            input=search_query,
            model="text-embedding-3-small"
        ).data[0].embedding
        
        # 2. THE FIX: Widen the net to 30 chunks to ensure we catch it
        results = index.query(
            vector=query_embedding,
            top_k=30,
            include_metadata=True,
            namespace="carleton"
        )
        
        # 3. Deterministic Python Match
        if results.matches:
            for match in results.matches:
                doc_text = match.metadata.get("text", "")
                
                if clean_code in doc_text:
                    return {
                        "found": True,
                        "course_code": clean_code,
                        "description": doc_text,
                        "source": match.metadata.get("source", "Unknown")
                    }
                    
        return {"found": False, "message": f"Could not find exact course data for {clean_code}."}
        
    except Exception as e:
        print(f"Lookup Error: {e}")
        return {"found": False, "error": str(e)}

# ==========================================
# 🧠 THE RAG CHAT ENGINE
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(...),
    history: str = Form("[]"), 
    file: UploadFile = File(None) 
):
    user_query = question
    print(f"Searching database for: {user_query}")
    
    attachment_text = ""
    
    try:
        # --- Handle Attached File ---
        if file:
            print(f"Reading attached file: {file.filename}")
            content = await file.read()
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                attachment_text += page.get_text("text") + "\n"
        
        # --- Handle Pinecone RAG Search ---
        query_embedding = openai_client.embeddings.create(
            input=user_query,
            model="text-embedding-3-small"
        ).data[0].embedding
        
        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=10,  # EXPANDED: Hand the model more context to avoid missing split lists
            include_metadata=True,
            namespace="carleton"
        )
        
        context_text = ""
        sources = []
        seen_urls = set()  # TRACKER: Deduplicates messy link arrays in the UI
        
        # Extract matches from Pinecone response
        if results.matches:
            for match in results.matches:
                # FILTER: Drop low-confidence/irrelevant vector returns
                if match.score < 0.30:
                    continue
                    
                metadata = match.metadata
                doc_text = metadata.get("text", "")
                doc_source = metadata.get("source", "Unknown Source")
                
                context_text += f"\n--- Source: {doc_source} ---\n{doc_text}\n"
                
                # Deduplicate before feeding sources to frontend array
                if doc_source not in seen_urls:
                    seen_urls.add(doc_source)
                    sources.append({
                        "doc": doc_source,
                        "section": "Web Policy",
                        "snippet": doc_text[:150] + "..." 
                    })
        
        # --- Build AI Prompt ---
        system_prompt = f"""You are CampusQ, an independent institutional knowledge assistant designed to help students navigate Carleton University policies. 
        DISCLAIMER: YOU ARE NOT OFFICIALLY AFFILIATED WITH CARLETON UNIVERSITY.
        
        CRITICAL RULES FOR READING CONTEXT:
        1. NO MIXING PROGRAMS: The context contains information from MULTIPLE different engineering programs. You must strictly verify that a stream, course, or requirement actually belongs to the specific program the user is asking about. Do not list Aerospace or Biomedical streams under Software Engineering.
        2. EXACT COURSE CODES: If a user asks about a specific course code (e.g., "SYSC 4416"), scan the text for that exact number. If it is not explicitly in the text, you must say "I do not see that specific course listed in this document."
        3. NO GUESSING: If the answer is not explicitly in the text, say "I do not have enough information to answer this based on the provided documents." Do not try to extrapolate or guess.
        Keep answers clear, concise, and professional.
        
        DATABASE CONTEXT:
        {context_text}
        
        USER ATTACHMENT TEXT:
        {attachment_text if attachment_text else "None"}
        """
        
        past_messages = json.loads(history)
        api_messages = [{"role": "system", "content": system_prompt}]
        
        for msg in past_messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
            
        api_messages.append({"role": "user", "content": user_query})
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages
        )
        
        if file:
            sources.append({
                "doc": file.filename,
                "section": "User Attachment",
                "snippet": "File uploaded directly to this conversation."
            })
        
        return {
            "answer": response.choices[0].message.content,
            "sources": sources
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {"answer": "Sorry, there was an error processing your request.", "sources": []}