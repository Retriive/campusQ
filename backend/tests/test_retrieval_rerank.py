"""Unit tests for retrieval routing and reranking."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval import (
    RankedChunk,
    detect_query_flags,
    is_program_related_query,
    is_software_eng_vs_cs_comparison,
    namespaces_for_query,
    rerank_chunks,
)


class FakeClient:
    """Minimal OpenAI client stub for LLM rerank tests."""


def test_program_comparison_detected():
    q = "How many credits do Honours programs require at Carleton?"
    assert is_program_related_query(q)
    flags = detect_query_flags(q)
    assert flags.is_program_query
    assert "tuition" not in namespaces_for_query(flags)


def test_action_query_detected():
    flags = detect_query_flags("How do I drop COMP 2402?")
    assert flags.is_action_query
    assert flags.is_deadline_query


def test_software_eng_vs_cs_comparison_detected():
    q = "What's the difference between software eng and CS at Carleton?"
    assert is_software_eng_vs_cs_comparison(q)


def test_rerank_short_circuit():
    chunks = [
        RankedChunk(id="a", metadata={"text": "a"}, score=0.9, namespace="courses"),
    ]
    assert rerank_chunks(FakeClient(), "test", chunks, top_n=10, chat_model="gpt-4o-mini") == chunks


def test_rerank_skips_when_top_scores_are_strong():
    chunks = [
        RankedChunk(id="a", metadata={"text": "a"}, score=0.95, namespace="courses"),
        RankedChunk(id="b", metadata={"text": "b"}, score=0.70, namespace="courses"),
        RankedChunk(id="c", metadata={"text": "c"}, score=0.40, namespace="courses"),
    ]
    # Pool larger than top_n, but dominant top score → no Cohere/LLM call.
    out = rerank_chunks(FakeClient(), "test", chunks, top_n=2, chat_model="gpt-4o-mini")
    assert [c.id for c in out] == ["a", "b"]
