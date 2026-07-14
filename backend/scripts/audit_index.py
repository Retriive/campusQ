"""audit_index.py — what's live in Pinecone, per namespace, and how fresh.

Answers "has this already been scraped, and when?" before re-running anything.
Vector counts come from index stats; freshness comes from the `scraped_at`
metadata stamp written by ingest.upsert.promote (records written by the legacy
scrapers predate the stamp and show as "unstamped").

Usage (from backend/, with PINECONE_API_KEY in backend/.env):
  py scripts/audit_index.py
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

SAMPLE_IDS = 5  # vectors fetched per namespace to sample scraped_at


def sample_freshness(index, namespace: str) -> str:
    """Best-effort: fetch a few vectors and report their scraped_at stamps."""
    try:
        ids: list[str] = []
        for page in index.list(namespace=namespace):
            for item in page:
                ids.append(item if isinstance(item, str) else getattr(item, "id", str(item)))
                if len(ids) >= SAMPLE_IDS:
                    break
            break
        if not ids:
            return ""
        fetched = index.fetch(ids=ids, namespace=namespace)
        vectors = getattr(fetched, "vectors", None) or fetched.get("vectors", {})
        stamps = sorted({
            (getattr(v, "metadata", None) or v.get("metadata") or {}).get("scraped_at", "unstamped")
            for v in vectors.values()
        })
        return ", ".join(stamps)
    except Exception as exc:
        return f"(freshness check failed: {type(exc).__name__})"


def main() -> int:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY is not set — add it to backend/.env")
        return 2

    index = Pinecone(api_key=api_key).Index(os.getenv("PINECONE_INDEX_NAME", "knowledge-base"))
    stats = index.describe_index_stats()
    namespaces = getattr(stats, "namespaces", None) or stats.get("namespaces", {})
    if not namespaces:
        print("Index is empty — nothing has been scraped into it yet.")
        return 0

    print(f"{'namespace':16s} {'vectors':>8s}  scraped_at (sampled)")
    print("-" * 60)
    total = 0
    for ns, info in sorted(namespaces.items()):
        count = getattr(info, "vector_count", None) or info.get("vector_count", 0)
        total += count
        print(f"{ns:16s} {count:>8d}  {sample_freshness(index, ns)}")
    print("-" * 60)
    print(f"{'total':16s} {total:>8d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
