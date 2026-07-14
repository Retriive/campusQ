"""Tests for the ingestion raw lake: persist on fetch, replay without network."""

import json
from pathlib import Path

from ingest import pipeline
from ingest.fetch import FetchedPage
from ingest.state import IngestState


def _fake_llm(system: str, user: str) -> str:
    """Deterministic stand-in for OpenAILLM: one generic chunk per call."""
    return json.dumps({"chunks": [{
        "title": "Library hours",
        "heading": "Hours",
        "text": "The library is open 8am to 11pm on weekdays during the fall term.",
    }]})


def _page(url: str, text: str, chash: str) -> FetchedPage:
    return FetchedPage(url=url, kind="html", text=text, content_hash=chash)


def test_save_and_list_raw_pages(tmp_path: Path):
    state = IngestState(str(tmp_path / "state.db"))
    state.save_raw_page("https://x/a", "test", "library", "llm_generic",
                        "html", "hash-a", str(tmp_path / "a.txt"))
    # Same URL again with new content — row is replaced, not duplicated
    state.save_raw_page("https://x/a", "test", "library", "llm_generic",
                        "html", "hash-a2", str(tmp_path / "a2.txt"))
    state.save_raw_page("https://x/b", "test", "dates", "llm_dates",
                        "html", "hash-b", str(tmp_path / "b.txt"))

    rows = state.raw_pages_for("test")
    assert len(rows) == 2
    assert state.raw_pages_for("test", "library")[0]["content_hash"] == "hash-a2"
    assert state.raw_pages_for("test", "dates")[0]["extractor"] == "llm_dates"


def test_persist_raw_writes_file_and_row(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    state = IngestState(str(tmp_path / "state.db"))
    page = _page("https://x/hours", "Open 8am to 11pm weekdays. " * 5, "abc123")

    pipeline._persist_raw(state, page, "test", "library", "llm_generic", log=lambda *_: None)

    rows = state.raw_pages_for("test", "library")
    assert len(rows) == 1
    assert Path(rows[0]["path"]).read_text(encoding="utf-8") == page.text
    assert rows[0]["content_hash"] == "abc123"


def test_replay_dry_run_reextracts_from_lake(tmp_path: Path, monkeypatch):
    """Replay must produce records from disk alone — no fetching, no Pinecone."""
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setattr(pipeline, "PREVIEW_DIR", str(tmp_path))
    state = IngestState(str(tmp_path / "state.db"))

    page = _page("https://x/hours", "The library is open 8am to 11pm weekdays. " * 5, "abc123")
    pipeline._persist_raw(state, page, "test", "library", "llm_generic", log=lambda *_: None)

    result = pipeline.run_category(
        "test", "library", sources=[], state=state,
        dry_run=True, replay=True, llm=_fake_llm, log=lambda *_: None)

    assert result.status == "dry_run"
    assert result.pages_fetched == 1
    assert result.records == 1
    preview = [json.loads(line) for line in Path(result.preview_path).read_text(encoding="utf-8").splitlines()]
    assert preview[0]["metadata"]["title"] == "Library hours"
    assert preview[0]["metadata"]["source"] == "https://x/hours"


def test_replay_with_empty_lake_fails_cleanly(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    state = IngestState(str(tmp_path / "state.db"))

    result = pipeline.run_category(
        "test", "library", sources=[], state=state,
        dry_run=True, replay=True, llm=_fake_llm, log=lambda *_: None)

    assert result.status == "failed"
    assert "raw lake" in result.message


def test_promote_stamps_scraped_at():
    from ingest import upsert

    class FakeIndex:
        def __init__(self):
            self.upserted = []

        def upsert(self, vectors, namespace):
            self.upserted.extend(vectors)

    index = FakeIndex()
    records = [{"id": "r1", "embed_text": "t", "metadata": {"title": "T"}}]
    upsert.promote(index, "library", records, [[0.0]], delete_stale=False, log=lambda *_: None)

    assert index.upserted[0]["metadata"]["scraped_at"]  # stamped
    assert index.upserted[0]["metadata"]["title"] == "T"  # original metadata intact
