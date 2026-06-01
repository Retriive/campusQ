import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# Load keys — .env lives in backend/ (one level up from tests/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

print("Connecting to CampusQ Brain...")

# The trap question
question = "What are the core SYSC courses required for Software Engineering?"
print(f"\nUser Question: '{question}'\n")

# 1. Turn the question into a vector
query_embedding = openai_client.embeddings.create(
    input=question,
    model="text-embedding-3-small"
).data[0].embedding

# 2. Search the Carleton namespace in Pinecone
results = index.query(
    vector=query_embedding,
    top_k=2, # Get the top 2 most relevant chunks
    namespace="carleton",
    include_metadata=True
)

# 3. Print the exact retrieved evidence
print("🔍 RETRIEVED EVIDENCE FROM PINECONE:\n" + "="*40)
for i, match in enumerate(results.matches):
    print(f"\nMatch {i+1} (Confidence Score: {round(match.score, 2)})")
    print(f"Source URL: {match.metadata['source']}")
    print(f"Text Snippet: {match.metadata['text'][:300]}...")