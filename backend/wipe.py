"""
wipe.py — Clears specified Pinecone namespaces before a fresh ingestion run.
Run this FIRST before any scraper.
"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACES_TO_WIPE = ["courses", "programs", "policies", "regulations", "services", "registrar"]

def wipe():
    print("=" * 50)
    print("CampusQ — Pinecone Namespace Wipe")
    print("=" * 50)

    confirm = input(f"\nThis will DELETE ALL vectors in: {NAMESPACES_TO_WIPE}\nType 'yes' to confirm: ")
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        return

    for ns in NAMESPACES_TO_WIPE:
        print(f"\nWiping namespace: '{ns}'...")
        try:
            index.delete(delete_all=True, namespace=ns)
            print(f"  ✓ '{ns}' cleared")
        except Exception as e:
            print(f"  ✗ Failed to wipe '{ns}': {e}")

    print("\n✓ Done. All specified namespaces are empty. Ready for fresh ingestion.\n")

if __name__ == "__main__":
    wipe()
