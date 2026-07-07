"""Reciprocal Rank Fusion — merge vector and keyword result lists.

RRF is the standard way to combine ranked lists from different scoring
systems without having to normalize their scores against each other:
each list contributes 1 / (k + rank) per item, and items appearing in
both lists rise to the top.

Design constraint: downstream code (threshold filter, citations, reranker)
reads chunk.score as a 0–1 relevance value, so fusion must not replace those
scores with raw RRF values. Instead, fusion reorders the pool and assigns
lexical-only newcomers a neutral score that clears the similarity threshold —
the Cohere/LLM reranker stays the final quality gate.
"""

from __future__ import annotations

RRF_K = 60                  # standard damping constant from the RRF paper
LEXICAL_ONLY_SCORE = 0.50   # above SIMILARITY_THRESHOLD, below strong vector hits


def fuse(vector_chunks: list, lexical_hits: list, make_chunk) -> list:
    """Merge vector RankedChunks with LexicalHits into one RRF-ordered pool.

    vector_chunks : RankedChunk list, already boost-adjusted, any order
    lexical_hits  : LexicalHit list, rank 0 = best
    make_chunk    : callable(id, metadata, namespace, score) -> RankedChunk
                    (injected to avoid a circular import with retrieval.py)
    """
    if not lexical_hits:
        return vector_chunks

    by_vector_score = sorted(vector_chunks, key=lambda c: c.score, reverse=True)
    fused: dict[str, float] = {}
    keep: dict[str, object] = {}

    for rank, chunk in enumerate(by_vector_score):
        fused[chunk.id] = fused.get(chunk.id, 0.0) + 1.0 / (RRF_K + rank)
        keep.setdefault(chunk.id, chunk)

    for hit in lexical_hits:
        fused[hit.id] = fused.get(hit.id, 0.0) + 1.0 / (RRF_K + hit.rank)
        if hit.id not in keep:
            keep[hit.id] = make_chunk(hit.id, hit.metadata, hit.namespace,
                                      LEXICAL_ONLY_SCORE)

    order = sorted(fused, key=fused.get, reverse=True)
    return [keep[chunk_id] for chunk_id in order]
