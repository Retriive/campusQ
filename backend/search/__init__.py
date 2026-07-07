"""Hybrid search: a local BM25 keyword index fused with Pinecone vector results.

Embeddings are great at meaning but weak on exact tokens — course codes,
acronyms (CUSA, PMC), form names, fee line items. The lexical index catches
those; Reciprocal Rank Fusion merges both lists so neither side dominates.

Off by default. Enable with HYBRID_SEARCH=true in .env.
"""
