"""Tests for the BM25 fit-filter (ingest/fit.py) and its pipeline wiring."""

from ingest import fit, pipeline
from ingest.fetch import FetchedPage
from ingest.registry import Source


# A page with two on-topic library blocks and three boilerplate blocks.
_RELEVANT_A = ("The Macodrum Library is open 24 hours during exams. Study "
               "rooms on the fourth floor can be booked online for group work.")
_RELEVANT_B = ("Borrowing services let undergraduate students loan books for "
               "four weeks. Renew loans through the library account portal.")
_NOISE = [
    "Skip to main content. Toggle navigation menu. Search this site.",
    "Copyright 2026 Carleton University. All rights reserved. Privacy policy.",
    "Follow us on social media. Subscribe to our newsletter for updates.",
]


def _library_page() -> str:
    return "\n\n".join([_NOISE[0], _RELEVANT_A, _NOISE[1], _RELEVANT_B, _NOISE[2]])


def test_fit_keeps_topic_blocks_and_drops_boilerplate():
    result = fit.fit_text(_library_page(), fit.query_for("library"))
    assert result.reduced
    assert "Macodrum Library" in result.text
    assert "Borrowing services" in result.text
    assert "Toggle navigation" not in result.text
    assert "Copyright 2026" not in result.text
    assert result.blocks_kept < result.blocks_total


def test_fit_returns_original_when_query_has_no_signal():
    # A query whose terms appear nowhere → flat score → text untouched.
    page = _library_page()
    result = fit.fit_text(page, "quantum astrophysics thermodynamics")
    assert result.text == page
    assert not result.reduced
    assert result.blocks_kept == result.blocks_total


def test_fit_leaves_short_pages_untouched():
    page = "\n\n".join([_RELEVANT_A, _NOISE[0]])  # < min_blocks
    result = fit.fit_text(page, fit.query_for("library"))
    assert result.text == page
    assert not result.reduced


def test_fit_never_returns_empty():
    # Even at an impossible threshold the top block survives.
    result = fit.fit_text(_library_page(), fit.query_for("library"), threshold=99.0)
    assert result.text.strip()
    assert result.blocks_kept >= 1


def test_query_for_prefers_override_then_default_then_category():
    assert fit.query_for("library", "custom terms") == "custom terms"
    assert "borrowing" in fit.query_for("library")
    assert fit.query_for("unknown_ns") == "unknown_ns"


def test_pct_removed_and_reduced_are_consistent():
    result = fit.fit_text(_library_page(), fit.query_for("library"))
    assert 0 < result.pct_removed <= 100
    assert result.chars_after < result.chars_before


# ── pipeline wiring ─────────────────────────────────────────────────────────

def _capture_llm_input():
    """LLM stub that records the text it was asked to extract from."""
    seen: list[str] = []

    def llm(system: str, user: str) -> str:
        seen.append(user)
        return '{"chunks": []}'

    return llm, seen


def test_pipeline_applies_fit_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    from ingest.state import IngestState
    state = IngestState(str(tmp_path / "state.db"))

    source = Source(school="test", category="library",
                    url="https://library.example.ca/x",
                    extractor="llm_generic", fit=True)
    page = FetchedPage(url=source.url, kind="html", text=_library_page(),
                       content_hash="h1")
    monkeypatch.setattr(pipeline.fetch_mod, "fetch_page", lambda url: page)

    llm, seen = _capture_llm_input()
    pipeline.run_category("test", "library", sources=[source], state=state,
                          dry_run=True, llm=llm, log=lambda *_: None)

    assert seen, "extractor should have been called"
    joined = " ".join(seen)
    assert "Macodrum Library" in joined      # relevant content reached the LLM
    assert "Toggle navigation" not in joined  # boilerplate was pruned first


def test_pipeline_skips_fit_for_course_regex(tmp_path, monkeypatch):
    # course_regex is layout-sensitive; fit must never touch it even if flagged.
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    from ingest.state import IngestState
    state = IngestState(str(tmp_path / "state.db"))

    course_text = "\n\n".join([
        _NOISE[0],
        "COMP 2401 [0.5 credit]\nSystems Programming\nIntro to systems programming concepts.",
        _NOISE[1],
    ])
    source = Source(school="test", category="courses", url="https://x/courses",
                    extractor="course_regex", fit=True)
    page = FetchedPage(url=source.url, kind="html", text=course_text, content_hash="h1")
    monkeypatch.setattr(pipeline.fetch_mod, "fetch_page", lambda url: page)

    result = pipeline.run_category("test", "courses", sources=[source], state=state,
                                   dry_run=True, llm=lambda *a: "{}", log=lambda *_: None)
    # The regex still finds the course despite the surrounding boilerplate.
    assert result.records == 1
