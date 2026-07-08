"""Unit tests for deterministic retrieval scoring helpers."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval import (
    QueryFlags,
    RankedChunk,
    apply_query_aware_adjustments,
    dedupe_chunks,
    diverse_pool,
    query_course_codes,
    query_terms,
)


def test_query_terms_removes_stopwords():
    tokens = query_terms("How do I drop COMP 2402 in the fall term?")
    assert "how" not in tokens
    assert "drop" in tokens
    assert "comp" in tokens
    assert "2402" in tokens


def test_query_course_codes_normalizes_case_and_spacing():
    codes = query_course_codes("compare comp2402 and Sysc 3110 prerequisites")
    assert codes == ["COMP 2402", "SYSC 3110"]


def test_query_aware_adjustments_boost_deadline_and_code_hits():
    flags = QueryFlags(
        is_program_query=False,
        is_schedule_query=False,
        is_deadline_query=True,
        is_action_query=True,
    )
    chunk = RankedChunk(
        id="x",
        namespace="dates",
        score=0.55,
        metadata={
            "title": "Drop and withdrawal deadlines",
            "course_code": "COMP 2402",
            "text": "COMP 2402 withdrawal deadline and registration drop date are in Carleton Central.",
        },
    )
    boosted = apply_query_aware_adjustments(
        chunk,
        tokens=query_terms("How do I drop COMP 2402 and what is the deadline?"),
        course_codes=["COMP 2402"],
        flags=flags,
    )
    assert boosted > chunk.score


def test_dedupe_chunks_removes_duplicate_text_fingerprints():
    a = RankedChunk(
        id="a",
        namespace="courses",
        score=0.8,
        metadata={"source": "https://x", "title": "A", "text": "Identical snippet text"},
    )
    b = RankedChunk(
        id="b",
        namespace="courses",
        score=0.7,
        metadata={"source": "https://x", "title": "A", "text": "Identical snippet text"},
    )
    out = dedupe_chunks([a, b])
    assert [c.id for c in out] == ["a"]


def test_diverse_pool_limits_one_source_dominance():
    flags = QueryFlags(False, False, False, False)
    chunks = [
        RankedChunk(id=f"s{i}", namespace="courses", score=0.99 - i * 0.01, metadata={"source": "https://same", "text": f"same {i}"})
        for i in range(6)
    ] + [
        RankedChunk(id=f"o{i}", namespace="regulations", score=0.80 - i * 0.01, metadata={"source": f"https://other{i}", "text": f"other {i}"})
        for i in range(3)
    ]
    pool = diverse_pool(chunks, limit=5, flags=flags)
    same_source = [c for c in pool if c.metadata.get("source") == "https://same"]
    assert len(pool) == 5
    assert len(same_source) <= 2
