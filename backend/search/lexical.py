"""SQLite FTS5 keyword index — the lexical half of hybrid search.

Mirrors what the ingestion pipeline writes to Pinecone: every promoted record
is also inserted here, keyed by the same stable ID and namespace, so a lexical
hit can be joined back to the exact chunk the vector side knows about.

Zero new dependencies: FTS5 ships inside Python's sqlite3. If this file is
missing or empty, hybrid search silently degrades to pure vector search —
chat never breaks because of it.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Same persistence convention as logs and ingest_state.db: /data on Render.
DEFAULT_DB = os.path.join("/data" if os.path.isdir("/data") else BACKEND_DIR,
                          "lexical_index.db")

_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-\.]*")


@dataclass
class LexicalHit:
    id: str
    namespace: str
    rank: int            # 0 = best
    metadata: dict


def _sanitize_query(query: str, max_terms: int = 12) -> str:
    """User text → safe FTS5 MATCH expression (OR of bare terms).

    FTS5 has its own query syntax (quotes, NEAR, column filters); raw user
    input can be a syntax error or worse. We keep only plain word tokens.
    """
    terms = _TOKEN_RE.findall(query)
    terms = [t for t in terms if len(t) > 1][:max_terms]
    if not terms:
        return ""
    return " OR ".join(f'"{t}"' for t in terms)


class LexicalIndex:
    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5("
            "  id UNINDEXED, namespace UNINDEXED, meta UNINDEXED,"
            "  title, body"
            ")"
        )
        self._conn.commit()

    # ── Writes (called by the ingestion pipeline after Pinecone promotion) ──

    def upsert(self, namespace: str, records: list[dict]):
        """records use the ingest shape: {'id', 'metadata': {...}, 'embed_text'}."""
        cur = self._conn.cursor()
        for r in records:
            meta = r.get("metadata", {})
            cur.execute("DELETE FROM chunks WHERE id = ? AND namespace = ?",
                        (r["id"], namespace))
            cur.execute(
                "INSERT INTO chunks (id, namespace, meta, title, body) VALUES (?,?,?,?,?)",
                (
                    r["id"],
                    namespace,
                    json.dumps(meta, ensure_ascii=False),
                    str(meta.get("title") or meta.get("course_code") or ""),
                    str(meta.get("text") or r.get("embed_text") or ""),
                ),
            )
        self._conn.commit()

    def delete_missing(self, namespace: str, keep_ids: set[str]) -> int:
        """Stale cleanup — remove ids in this namespace not in keep_ids.
        Mirrors the pipeline's delete-stale-only-on-full-coverage rule."""
        cur = self._conn.cursor()
        cur.execute("SELECT id FROM chunks WHERE namespace = ?", (namespace,))
        stale = [row[0] for row in cur.fetchall() if row[0] not in keep_ids]
        for chunk_id in stale:
            cur.execute("DELETE FROM chunks WHERE id = ? AND namespace = ?",
                        (chunk_id, namespace))
        self._conn.commit()
        return len(stale)

    def mirror_promotion(self, namespace: str, records: list[dict], delete_stale: bool):
        """One call from the pipeline: upsert everything, optionally prune."""
        self.upsert(namespace, records)
        if delete_stale:
            self.delete_missing(namespace, {r["id"] for r in records})

    # ── Reads (called by retrieval) ─────────────────────────────────────────

    def search(self, query: str, namespaces: list[str] | None = None,
               limit: int = 15) -> list[LexicalHit]:
        match_expr = _sanitize_query(query)
        if not match_expr:
            return []
        sql = "SELECT id, namespace, meta FROM chunks WHERE chunks MATCH ?"
        params: list = [match_expr]
        if namespaces:
            sql += f" AND namespace IN ({','.join('?' * len(namespaces))})"
            params.extend(namespaces)
        sql += " ORDER BY rank LIMIT ?"   # FTS5 rank = BM25, ascending = best first
        params.append(limit)
        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []
        hits = []
        for i, (chunk_id, ns, meta_json) in enumerate(rows):
            try:
                meta = json.loads(meta_json)
            except Exception:
                meta = {}
            hits.append(LexicalHit(id=chunk_id, namespace=ns, rank=i, metadata=meta))
        return hits

    def count(self) -> int:
        return self._conn.execute("SELECT count(*) FROM chunks").fetchone()[0]

    def close(self):
        self._conn.close()
