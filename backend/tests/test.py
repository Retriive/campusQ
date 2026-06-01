from pinecone import Pinecone
from dotenv import load_dotenv
import os

# .env lives in backend/ (one level up from tests/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

results = index.query(vector=[0.001]*1536, top_k=5, namespace="courses", include_metadata=True)
for r in results.matches:
    print(r.id)
    print(r.metadata)
    print("---")