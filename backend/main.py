import os
import json
import re
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

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

@app.get("/")
async def health_check():
    return {"status": "CampusQ Brain is active and listening."}

@app.get("/api/documents")
async def get_documents():
    docs_dir = "./docs"
    if not os.path.exists(docs_dir):
        return {"documents": []}
    files = [f for f in os.listdir(docs_dir) if f.endswith(".pdf")]
    documents = [{"id": str(i + 1), "name": file, "status": "indexed"} for i, file in enumerate(files)]
    return {"documents": documents}

# ==========================================
# ⚡ THE O(1) EXPRESS LANE (API ONLY)
# ==========================================
@app.get("/api/course/{course_code}")
async def course_lookup(course_code: str):
    """Standalone GET endpoint for pure, lightning-fast API calls."""
    clean_code = course_code.upper().strip()
    course_id = clean_code.replace(" ", "") # e.g. "ACSE3105"
    
    try:
        # O(1) Direct ID Fetch - No AI embeddings needed!
        result = index.fetch(ids=[course_id], namespace="carleton")
        
        if result and "vectors" in result and course_id in result["vectors"]:
            doc_text = result["vectors"][course_id]["metadata"].get("text", "")
            return {"found": True, "course_code": clean_code, "description": doc_text}
            
        return {"found": False, "message": f"Could not find exact course data for {clean_code}."}
    except Exception as e:
        return {"found": False, "error": str(e)}

# ==========================================
# 🧠 THE RAG CHAT ENGINE WITH SMART INTERCEPTOR
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(...),
    history: str = Form("[]"), 
    file: UploadFile = File(None) 
):
    user_query = question
    print(f"Searching database for: {user_query}")
    
    # ---------------------------------------------------------
    # 🛑 THE SMART INTERCEPTOR: Catch multiple exact courses early
    # ---------------------------------------------------------
    # re.findall returns a list of all course codes mentioned in the prompt
    course_matches = re.findall(r'([a-zA-Z]{4})\s*(\d{4})', user_query, re.IGNORECASE)
    
    if course_matches and not file: 
        responses = []
        sources = []
        seen_codes = set() # Prevent duplicate lookups if user says "SYSC 4416 and SYSC 4416"
        
        for match in course_matches:
            clean_code = f"{match[0].upper()} {match[1]}"
            if clean_code in seen_codes:
                continue
            seen_codes.add(clean_code)
            
            course_id = clean_code.replace(" ", "")
            print(f"Interceptor fetching: {course_id}")
            
            try:
                # O(1) Direct Fetch!
                result = index.fetch(ids=[course_id], namespace="carleton")
                
                if result and "vectors" in result and course_id in result["vectors"]:
                    metadata = result["vectors"][course_id]["metadata"]
                    doc_text = metadata.get("text", "")
                    source_url = metadata.get("source", f"{match[0].upper()} Calendar")
                    
                    responses.append(f"### **{clean_code}**\n{doc_text}")
                    sources.append({
                        "doc": source_url,
                        "section": "Direct Database Match",
                        "snippet": "Exact course details retrieved instantly."
                    })
            except Exception as e:
                print(f"Fetch error for {course_id}: {e}")
                
        # If we successfully fetched AT LEAST ONE course, return them all together
        if responses:
            return {
                "answer": "**Course Matches Found:**\n\n---\n" + "\n---\n".join(responses),
                "sources": sources
            }
    # ---------------------------------------------------------

    # --- Normal RAG flow for general questions ---
    attachment_text = ""
    try:
        if file:
            content = await file.read()
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                attachment_text += page.get_text("text") + "\n"
        
        query_embedding = openai_client.embeddings.create(
            input=user_query,
            model="text-embedding-3-small"
        ).data[0].embedding
        
        results = index.query(
            vector=query_embedding,
            top_k=10, 
            include_metadata=True,
            namespace="carleton"
        )
        
        context_text = ""
        sources = []
        seen_urls = set() 
        
        if results.matches:
            for match in results.matches:
                if match.score < 0.30:
                    continue
                metadata = match.metadata
                doc_text = metadata.get("text", "")
                doc_source = metadata.get("source", "Unknown Source")
                
                context_text += f"\n--- Source: {doc_source} ---\n{doc_text}\n"
                
                if doc_source not in seen_urls:
                    seen_urls.add(doc_source)
                    sources.append({
                        "doc": doc_source,
                        "section": "Web Policy",
                        "snippet": doc_text[:150] + "..." 
                    })
        
        system_prompt = f"""You are CampusQ, an independent institutional knowledge assistant designed to help students navigate Carleton University policies. 
        DISCLAIMER: YOU ARE NOT OFFICIALLY AFFILIATED WITH CARLETON UNIVERSITY.
        
        CRITICAL RULES FOR READING CONTEXT:
        1. NO MIXING PROGRAMS: The context contains information from MULTIPLE different engineering programs. You must strictly verify that a stream, course, or requirement actually belongs to the specific program the user is asking about.
        2. NO GUESSING: If the answer is not explicitly in the text, say "I do not have enough information to answer this based on the provided documents." Do not try to extrapolate or guess.
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