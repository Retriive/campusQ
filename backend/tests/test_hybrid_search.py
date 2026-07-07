"""Offline tests for hybrid search: the FTS5 lexical index and RRF fusion.

No network, no keys. Run:  python -m pytest tests/test_hybrid_search.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval import RankedChunk
from search.hybrid import LEXICAL_ONLY_SCORE, fuse
from search.lexical import LexicalIndex, _sanitize_query


def make_index(tmp_path) -> LexicalIndex:
    return LexicalIndex(db_path=str(tmp_path / "lex.db"))


RECORDS = [
    {"id": "COMP1005", "metadata": {
        "title": "COMP 1005", "course_code": "COMP 1005",
        "text": "COMP 1005 Introduction to Computer Science I. Programming in Python."}},
    {"id": "cusa-services", "metadata": {
        "title": "CUSA services", "text": "CUSA runs the food centre and health plan for undergrads."}},
    {"id": "withdraw-deadline", "metadata": {
        "title": "Fall withdrawal", "text": "Last day to withdraw from fall courses is November 15."}},
]


def test_upsert_and_keyword_search(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert("services", RECORDS)
    hits = idx.search("what is CUSA")
    assert hits and hits[0].id == "cusa-services"
    assert hits[0].metadata["title"] == "CUSA services"
    assert hits[0].namespace == "services"


def test_upsert_is_idempotent(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert("services", RECORDS)
    idx.upsert("services", RECORDS)   # re-run must not duplicate
    assert idx.count() == len(RECORDS)


def test_namespace_filter(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert("courses", [RECORDS[0]])
    idx.upsert("services", [RECORDS[1]])
    assert idx.search("CUSA", namespaces=["courses"]) == []
    assert idx.search("CUSA", namespaces=["services"])[0].id == "cusa-services"


def test_stale_cleanup_mirrors_promotion(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert("dates", RECORDS)
    idx.mirror_promotion("dates", [RECORDS[0]], delete_stale=True)
    assert idx.count() == 1
    assert idx.search("withdraw") == []


def test_incremental_run_keeps_everything(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert("dates", RECORDS)
    idx.mirror_promotion("dates", [RECORDS[0]], delete_stale=False)
    assert idx.count() == len(RECORDS)


def test_query_sanitizer_neutralizes_fts_syntax():
    # FTS5 operators and quotes in user input must not raise or inject syntax
    assert '"NEAR"' in _sanitize_query('NEAR("a" OR b) AND col:x')
    assert _sanitize_query("!!! ??? ***") == ""


def test_hostile_query_returns_cleanly(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert("services", RECORDS)
    assert isinstance(idx.search('"); DROP TABLE chunks; --'), list)
    assert idx.count() == len(RECORDS)


# ── RRF fusion ────────────────────────────────────────────────────────────────

def _chunk(cid, score, ns="courses"):
    return RankedChunk(id=cid, metadata={"text": cid}, score=score, namespace=ns)


def _make_chunk(cid, meta, ns, score):
    return RankedChunk(id=cid, metadata=meta, score=score, namespace=ns)


class _Hit:
    def __init__(self, cid, rank, ns="services"):
        self.id, self.rank, self.namespace = cid, rank, ns
        self.metadata = {"text": cid}


def test_fuse_promotes_items_in_both_lists():
    vector = [_chunk("a", 0.9), _chunk("b", 0.6), _chunk("c", 0.5)]
    lexical = [_Hit("c", 0), _Hit("b", 1)]
    fused = fuse(vector, lexical, _make_chunk)
    # "a" leads only one list; "b"/"c" appear in both → both outrank items
    # appearing in a single list at comparable positions
    ids = [c.id for c in fused]
    assert set(ids) == {"a", "b", "c"}
    assert ids.index("b") < ids.index("a") or ids.index("c") < ids.index("a")


def test_fuse_adds_lexical_only_hits_with_neutral_score():
    vector = [_chunk("a", 0.9)]
    lexical = [_Hit("keyword-only", 0)]
    fused = fuse(vector, lexical, _make_chunk)
    newcomer = next(c for c in fused if c.id == "keyword-only")
    assert newcomer.score == LEXICAL_ONLY_SCORE
    assert newcomer.namespace == "services"


def test_fuse_preserves_vector_scores():
    vector = [_chunk("a", 0.87)]
    fused = fuse(vector, [_Hit("a", 0, ns="courses")], _make_chunk)
    assert fused[0].score == 0.87   # existing chunk keeps its calibrated score


def test_fuse_no_lexical_hits_is_identity():
    vector = [_chunk("a", 0.9), _chunk("b", 0.6)]
    assert fuse(vector, [], _make_chunk) is vector
