"""Ad-hoc Pinecone query probe for local debugging."""

import os

from dotenv import load_dotenv
from pinecone import Pinecone


load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env",
    ),
)

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

results = index.query(
    vector=[0.001] * 1536,
    top_k=5,
    namespace="courses",
    include_metadata=True,
)
for result in results.matches:
    print(result.id)
    print(result.metadata)
    print("---")
