from pinecone import Pinecone
from dotenv import load_dotenv
import os

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

results = index.query(vector=[0.001]*1536, top_k=5, namespace="courses", include_metadata=True)
for r in results.matches:
    print(r.id)
    print(r.metadata)
    print("---")