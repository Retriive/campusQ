"""Tests for per-record validation + quarantine (validate.py, pipeline wiring)."""

import json
from datetime import date
from pathlib import Path

from ingest import pipeline, validate
from ingest.extract import _stable_id
from ingest.state import IngestState

TODAY = date(2026, 7, 14)


def _date_record(title: str, iso: str, term: str = "Fall 2026",
                 category: str = "withdrawal", source: str = "https://x/dates") -> dict:
    return {
        "id": f"date-{_stable_id(source, title.lower(), iso)}",
        "embed_text": f"{title} {term} {category} deadline date {iso} details",
        "metadata": {"title": f"{title} — {iso}", "term": term, "category": category,
                     "date": iso, "text": f"{title}. {iso}.", "source": source},
    }


def _course_record(credits) -> dict:
    return {
        "id": "COMP2401",
        "embed_text": "COMP 2401 Systems Programming. Department: COMP. Intro to systems.",
        "metadata": {"course_code": "COMP 2401", "credits": str(credits),
                     "source": "https://x/courses", "text": "COMP 2401\n0.5\nSystems Programming"},
    }


# ── validate_record ─────────────────────────────────────────────────────────

def test_date_in_window_is_clean():
    assert validate.validate_record(_date_record("Withdraw", "2026-11-15"), "dates", TODAY) == []


def test_date_year_hallucination_quarantined():
    past = validate.validate_record(_date_record("Withdraw", "2016-11-15"), "dates", TODAY)
    future = validate.validate_record(_date_record("Withdraw", "2036-11-15"), "dates", TODAY)
    assert any("past" in r for r in past)
    assert any("future" in r for r in future)


def test_impossible_date_quarantined():
    reasons = validate.validate_record(_date_record("Withdraw", "2026-02-31"), "dates", TODAY)
    assert any("unparseable" in r for r in reasons)


def test_unknown_date_category_quarantined():
    rec = _date_record("Withdraw", "2026-11-15", category="vibes")
    assert any("category" in r for r in validate.validate_record(rec, "dates", TODAY))


def test_course_credits_bounds():
    assert validate.validate_record(_course_record(0.5), "courses", TODAY) == []
    assert any("credits" in r for r in validate.validate_record(_course_record(0.0), "courses", TODAY))
    assert any("credits" in r for r in validate.validate_record(_course_record(12), "courses", TODAY))
    assert any("credits" in r for r in validate.validate_record(_course_record("half"), "courses", TODAY))


def test_missing_source_and_thin_embed_quarantined():
    rec = {"id": "x", "embed_text": "tiny", "metadata": {"source": "", "text": "y"}}
    reasons = validate.validate_record(rec, "library", TODAY)
    assert any("source" in r for r in reasons)
    assert any("embed_text" in r for r in reasons)


# ── contradiction screening ────────────────────────────────────────────────

def test_same_deadline_two_dates_quarantines_both():
    a = _date_record("Last day to withdraw", "2026-11-15", source="https://x/p1")
    b = _date_record("Last day to withdraw", "2026-11-22", source="https://x/p2")
    other = _date_record("Payment deadline", "2026-09-01", category="payment")

    clean, quarantined = validate.screen([a, b, other], "dates", TODAY)

    assert clean == [other]
    assert {rec["id"] for rec, _ in quarantined} == {a["id"], b["id"]}
    assert all("contradiction" in reasons[0] for _, reasons in quarantined)


def test_same_deadline_same_date_from_two_pages_is_not_contradiction():
    a = _date_record("Last day to withdraw", "2026-11-15", source="https://x/p1")
    b = _date_record("Last day to withdraw", "2026-11-15", source="https://x/p2")
    clean, quarantined = validate.screen([a, b], "dates", TODAY)
    assert len(clean) == 2 and quarantined == []


# ── state round-trip ────────────────────────────────────────────────────────

def test_quarantine_state_roundtrip(tmp_path: Path):
    state = IngestState(str(tmp_path / "state.db"))
    rec = _date_record("Withdraw", "2016-11-15")
    state.add_quarantine("test", "dates", rec, ["date 2016-11-15 is stale"], run_id=1)

    rows = state.quarantined_for("test")
    assert len(rows) == 1
    assert rows[0]["record_id"] == rec["id"]
    assert "stale" in rows[0]["reasons"]
    assert json.loads(rows[0]["record_json"])["metadata"]["date"] == "2016-11-15"
    assert state.quarantined_for("test", "courses") == []


# ── pipeline end-to-end: quarantine blocks publish, old vector survives ─────

class _FakeEmbeddings:
    def create(self, input, model):
        class _D:
            embedding = [0.0]
        class _R:
            data = [_D() for _ in input]
        return _R()


class _FakeOpenAI:
    embeddings = _FakeEmbeddings()


class _FakeIndex:
    def __init__(self, existing_ids):
        self.existing_ids = set(existing_ids)
        self.upserted = []
        self.deleted = []

    def upsert(self, vectors, namespace):
        self.upserted.extend(vectors)

    def delete(self, ids, namespace):
        self.deleted.extend(ids)

    def describe_index_stats(self):
        class _NS:
            vector_count = len(self.existing_ids)
        class _S:
            namespaces = {"dates": _NS()}
        return _S()

    def list(self, namespace):
        yield list(self.existing_ids)


def _two_deadline_llm(system: str, user: str) -> str:
    """One good deadline, one with a hallucinated decade-old year."""
    return json.dumps({"deadlines": [
        {"title": "Last day to withdraw", "date": "2026-11-15",
         "term": "Fall 2026", "category": "withdrawal", "description": ""},
        {"title": "Payment deadline", "date": "2016-09-01",
         "term": "Fall 2026", "category": "payment", "description": ""},
    ]})


def test_pipeline_quarantines_and_keeps_old_vector(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    state = IngestState(str(tmp_path / "state.db"))

    page_text = "Fall 2026 dates. Withdraw Nov 15 2026. Pay Sep 1. " * 3
    from ingest.fetch import FetchedPage
    page = FetchedPage(url="https://x/dates", kind="html", text=page_text, content_hash="h1")
    pipeline._persist_raw(state, page, "test", "dates", "llm_dates", log=lambda *_: None)

    bad_id = f"date-{_stable_id('https://x/dates', 'payment deadline', '2016-09-01')}"
    index = _FakeIndex(existing_ids={bad_id, "date-genuinely-stale"})

    result = pipeline.run_category(
        "test", "dates", sources=[], state=state, replay=True,
        openai_client=_FakeOpenAI(), index=index, llm=_two_deadline_llm,
        log=lambda *_: None)

    assert result.status == "ok"
    assert result.quarantined == 1
    assert result.records == 1

    # Only the good deadline was published
    assert len(index.upserted) == 1
    assert index.upserted[0]["metadata"]["date"] == "2026-11-15"
    # The quarantined ID's previous vector survived; truly stale IDs were removed
    assert bad_id not in index.deleted
    assert "date-genuinely-stale" in index.deleted
    # Quarantine row persisted with the reason
    rows = state.quarantined_for("test", "dates")
    assert len(rows) == 1 and "past" in rows[0]["reasons"]
