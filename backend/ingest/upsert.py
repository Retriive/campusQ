"""Embed, verify, promote — the zero-downtime replacement for wipe.py.

Promotion strategy: records carry stable IDs (course code, content hash), so
we upsert straight over the live namespace — every ID overwrite is atomic and
the index is never empty. Only after the upsert succeeds do we delete IDs that
existed before but weren't produced by this run (removed courses, deleted
pages). A run that crashes halfway leaves the old data fully serving.

Verification runs BEFORE anything touches Pinecone: a run that extracted
suspiciously few records (broken page, changed format, network flake) aborts
instead of gutting production data.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

EMBED_MODEL = "text-embedding-3-small"
EMBED_BATCH = 100
UPSERT_BATCH = 100
DELETE_BATCH = 500

# A full re-crawl producing under this fraction of the live count aborts.
MIN_KEEP_RATIO = 0.5


class VerificationError(Exception):
    pass


def embed_records(records: list[dict], openai_client=None) -> list[list[float]]:
    if openai_client is None:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    vectors: list[list[float]] = []
    texts = [r["embed_text"][:8000] for r in records]
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i:i + EMBED_BATCH]
        response = openai_client.embeddings.create(input=batch, model=EMBED_MODEL)
        vectors.extend(d.embedding for d in response.data)
    return vectors


def live_count(index, namespace: str) -> int:
    try:
        stats = index.describe_index_stats()
        ns = getattr(stats, "namespaces", None) or stats.get("namespaces", {})
        info = ns.get(namespace)
        if info is None:
            return 0
        return getattr(info, "vector_count", None) or info.get("vector_count", 0)
    except Exception:
        return 0


def verify(records: list[dict], min_records: int, previous_count: int, force: bool = False):
    """Abort bad runs before they touch production."""
    if len(records) < min_records:
        raise VerificationError(
            f"Extracted {len(records)} records but the source requires at least "
            f"{min_records}. The page may have moved or changed format — nothing was written."
        )
    if not force and previous_count > 20 and len(records) < previous_count * MIN_KEEP_RATIO:
        raise VerificationError(
            f"Extracted {len(records)} records vs {previous_count} currently live "
            f"(>{int((1 - MIN_KEEP_RATIO) * 100)}% shrink). Looks like a broken crawl — "
            f"nothing was written. Re-run with --force if the shrink is intentional."
        )
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        raise VerificationError("Duplicate record IDs in extraction output — aborting.")


def _existing_ids(index, namespace: str) -> set[str]:
    ids: set[str] = set()
    try:
        for page in index.list(namespace=namespace):
            # pinecone client yields lists of ids (or objects with .id)
            for item in page:
                ids.add(item if isinstance(item, str) else getattr(item, "id", str(item)))
    except Exception:
        # Listing unsupported/failed → skip stale cleanup rather than fail the run
        return set()
    return ids


def promote(index, namespace: str, records: list[dict], vectors: list[list[float]],
            delete_stale: bool, log=print) -> dict:
    """Upsert over live by stable ID, then (optionally) remove stale IDs."""
    # Freshness stamp: lets "how old is this namespace's data?" be answered
    # from Pinecone metadata alone (legacy scrapers never recorded this).
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload = [
        {"id": r["id"], "values": v, "metadata": {**r["metadata"], "scraped_at": scraped_at}}
        for r, v in zip(records, vectors)
    ]

    for i in range(0, len(payload), UPSERT_BATCH):
        index.upsert(vectors=payload[i:i + UPSERT_BATCH], namespace=namespace)
    log(f"  upserted {len(payload)} vectors into '{namespace}'")

    stale_deleted = 0
    if delete_stale:
        new_ids = {r["id"] for r in records}
        stale = list(_existing_ids(index, namespace) - new_ids)
        for i in range(0, len(stale), DELETE_BATCH):
            index.delete(ids=stale[i:i + DELETE_BATCH], namespace=namespace)
        stale_deleted = len(stale)
        if stale:
            log(f"  removed {stale_deleted} stale vectors from '{namespace}'")

    return {"upserted": len(payload), "stale_deleted": stale_deleted}
