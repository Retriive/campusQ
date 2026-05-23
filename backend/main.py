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
            top_k=3,
            include_metadata=True,  # FIXED: Added the missing comma here!
            namespace="carleton"
        )
        
        context_text = ""
        sources = []
        
        # Extract matches from Pinecone response
        if results.matches:
            for match in results.matches:
                metadata = match.metadata
                doc_text = metadata.get("text", "")
                
                # FIXED: Mapped to the actual keys from our ingestion script
                doc_source = metadata.get("source", "Unknown Source")
                
                context_text += f"\n--- Source: {doc_source} ---\n{doc_text}\n"
                
                sources.append({
                    "doc": doc_source,
                    "section": "Web Policy", # Fallback since we don't use sections anymore
                    "snippet": doc_text[:150] + "..." 
                })
        
        # --- Build AI Prompt ---
        system_prompt = f"""You are CampusQ, an independent institutional knowledge assistant designed to help students navigate Carleton University policies. 
        DISCLAIMER: YOU ARE NOT OFFICIALLY AFFILIATED WITH CARLETON UNIVERSITY.
        
        You have two sources of information: 
        1. CONTEXT: Official documents extracted from the database.
        2. ATTACHMENT: A temporary file the user just uploaded.
        
        Answer the user's question using ONLY these provided texts. 
        If the answer is not in the text, explicitly say "I do not have enough information to answer this based on the provided documents." Do not guess.
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