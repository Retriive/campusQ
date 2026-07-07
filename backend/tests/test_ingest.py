"""Offline tests for the universal ingestion pipeline.

No network, no keys: fixture HTML/PDF stand in for university pages, and the
LLM / embedder / Pinecone are fakes. Covers the format matrix the pipeline
exists for (tables, collapsed accordions, lists, paragraphs, PDFs, the
calendar's course format) plus the safety rails (change detection, shrink
guard, stale-delete only on full coverage).

Run:  python -m pytest tests/test_ingest.py -q
"""

import json
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest import extract as extract_mod
from ingest import fetch as fetch_mod
from ingest import pipeline as pipeline_mod
from ingest import upsert as upsert_mod
from ingest.registry import Source, load_sources
from ingest.state import IngestState

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Fakes ─────────────────────────────────────────────────────────────────────

class FakeLLM:
    """Returns canned JSON per system-prompt type; records calls."""

    def __init__(self):
        self.calls = []

    def __call__(self, system: str, user: str) -> str:
        self.calls.append(user)
        if '"courses"' in system:
            out = {"courses": []}
            if "CSC236" in user:   # UofT-style catalog
                out["courses"].append({
                    "code": "CSC236H1", "name": "Introduction to the Theory of Computation",
                    "credits": 0.5,
                    "description": "Induction, correctness proofs, formal languages.",
                    "prerequisites": "CSC148H1, CSC165H1",
                })
            if "CS 135" in user:   # Waterloo-style catalog
                out["courses"].append({
                    "code": "CS 135", "name": "Designing Functional Programs",
                    "credits": None,   # page doesn't state units → must not be invented
                    "description": "An introduction to the fundamentals of computer science.",
                    "prerequisites": "",
                })
                out["courses"].append({"code": "not a course", "name": "junk", "credits": 1})
            return json.dumps(out)
        if "deadlines" in system:
            out = {"deadlines": []}
            if "November 15" in user:
                out["deadlines"].append({
                    "title": "Last day to withdraw from fall courses",
                    "date": "2026-11-15", "term": "Fall 2026",
                    "category": "withdrawal", "description": "No academic notation after this date.",
                })
            if "September 3" in user:
                out["deadlines"].append({
                    "title": "Fall classes begin",
                    "date": "2026-09-03", "term": "Fall 2026",
                    "category": "classes", "description": "",
                })
                # junk the extractor must reject: no parseable date
                out["deadlines"].append({"title": "Sometime later", "date": "TBD", "term": "", "category": "other"})
            return json.dumps(out)
        # generic chunks
        chunks = []
        if "defer" in user.lower():
            chunks.append({
                "title": "How to defer an exam",
                "heading": "Exam deferrals",
                "text": "Students may apply to defer a final exam within 3 working days of the exam date using the registrar's deferral form. A fee of $50 applies for late applications.",
            })
        if "audit" in user.lower():
            chunks.append({
                "title": "What-If Audit",
                "heading": "Degree audit",
                "text": "The What-If Audit in Carleton Central shows how completed credits apply to a different program before you switch majors.",
            })
        chunks.append({"title": "junk", "heading": "", "text": "too short"})
        return json.dumps({"chunks": chunks})


class FakeEmbeddings:
    def create(self, input, model):
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1] * 8) for _ in input])


class FakeOpenAI:
    def __init__(self):
        self.embeddings = FakeEmbeddings()


class FakeIndex:
    """In-memory Pinecone: enough surface for upsert/delete/list/stats."""

    def __init__(self):
        self.store: dict[str, dict[str, dict]] = {}   # ns -> id -> vector

    def upsert(self, vectors, namespace):
        ns = self.store.setdefault(namespace, {})
        for v in vectors:
            ns[v["id"]] = v

    def delete(self, ids, namespace):
        ns = self.store.setdefault(namespace, {})
        for i in ids:
            ns.pop(i, None)

    def list(self, namespace):
        yield list(self.store.get(namespace, {}).keys())

    def describe_index_stats(self):
        return {"namespaces": {ns: {"vector_count": len(v)} for ns, v in self.store.items()}}


# ── Fixture pages: the format matrix ─────────────────────────────────────────

TABLE_PAGE = """<html><body><main>
<h1>Academic dates</h1>
<table>
<tr><th>Date</th><th>Event</th></tr>
<tr><td>September 3, 2026</td><td>Fall classes begin</td></tr>
<tr><td>November 15, 2026</td><td>Last day to withdraw from fall courses</td></tr>
</table>
</main></body></html>"""

ACCORDION_PAGE = """<html><body><main>
<h1>Registrar services</h1>
<div class="accordion">
  <button>Exam deferrals</button>
  <div class="panel" style="display:none">
    <p>Students may apply to defer a final exam within 3 working days.</p>
  </div>
</div>
<ul><li>Use the What-If Audit before changing programs.</li></ul>
<p>Regular paragraph content about the audit process.</p>
<nav>Home &gt; Registrar</nav>
<script>alert('should never appear')</script>
</main></body></html>"""

COURSES_PAGE_TEXT = """COMP 2401 [0.5 credit]
Introduction to Systems Programming
Introduction to system-level programming with fundamental OS concepts.
Prerequisite(s): COMP 1405 or COMP 1406.
Lectures three hours a week.
COMP 3000 [0.5 credit]
Operating Systems
Principles and design of operating systems.
Prerequisite(s): COMP 2401 and COMP 2402.
Also listed as SYSC 3001.
"""


# ── Registry ──────────────────────────────────────────────────────────────────

def test_registry_loads_carleton_and_merges_admin_sources():
    extras = [{"url": "https://carleton.ca/new-page/", "category": "services"}]
    sources = load_sources("carleton", BACKEND_DIR, extras)
    urls = [s.url for s in sources]
    assert "https://calendar.carleton.ca/undergrad/courses/" in urls
    assert "https://carleton.ca/new-page/" in urls
    admin = [s for s in sources if s.added_by_admin]
    assert len(admin) == 1 and admin[0].resolve_extractor() == "llm_generic"


def test_registry_rejects_unknown_extractor():
    with pytest.raises(ValueError):
        Source(school="x", category="c", url="https://x", extractor="magic")


# ── Fetch / clean text ────────────────────────────────────────────────────────

def test_html_tables_become_pipe_rows():
    text = fetch_mod.html_to_text(TABLE_PAGE)
    assert "September 3, 2026 | Fall classes begin" in text
    assert "November 15, 2026 | Last day to withdraw from fall courses" in text


def test_hidden_accordion_content_is_captured_and_junk_stripped():
    text = fetch_mod.html_to_text(ACCORDION_PAGE)
    assert "defer a final exam" in text          # display:none content survives
    assert "What-If Audit" in text               # list items survive
    assert "alert(" not in text                  # scripts stripped
    assert "Home > Registrar" not in text        # nav stripped


def test_pdf_roundtrip():
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Tuition for Fall 2026 is $4,200 per term.")
    text = fetch_mod.pdf_to_text(doc.tobytes())
    assert "Tuition for Fall 2026" in text


# ── Extractors ────────────────────────────────────────────────────────────────

def test_course_regex_matches_legacy_metadata_contract():
    records = extract_mod.extract_courses(COURSES_PAGE_TEXT, "https://calendar.carleton.ca/x/")
    assert len(records) == 2
    r = records[0]
    assert r["id"] == "COMP2401"
    m = r["metadata"]
    assert m["course_code"] == "COMP 2401"
    assert m["course_name"] == "Introduction to Systems Programming"
    assert m["credits"] == "0.5"
    assert m["prerequisite_text"] == "COMP 1405 or COMP 1406"
    assert m["prerequisites"] == "COMP 1405, COMP 1406"
    assert m["department"] == "COMP"
    # the line layout main.parse_course_from_metadata depends on:
    lines = m["text"].split("\n")
    assert lines[0] == "COMP 2401" and lines[1] == "0.5" and lines[2] == "Introduction to Systems Programming"
    assert "Prerequisite" not in m["description"] and "Lectures" not in m["description"]


def test_llm_dates_rejects_unparseable_and_builds_contract():
    llm = FakeLLM()
    text = fetch_mod.html_to_text(TABLE_PAGE)
    records = extract_mod.llm_extract_dates(text, "https://carleton.ca/dates/", llm)
    titles = [r["metadata"]["title"] for r in records]
    assert any("November 15, 2026" in t for t in titles)
    assert all("TBD" not in r["metadata"]["date"] for r in records)
    for r in records:
        assert set(r["metadata"]) == {"title", "term", "category", "date", "text", "source"}


def test_llm_generic_drops_short_chunks():
    llm = FakeLLM()
    records = extract_mod.llm_extract_generic("How do I defer an exam? audit info", "https://x/", "registrar", llm)
    assert len(records) == 2                      # "junk" chunk dropped
    assert all(len(r["metadata"]["text"]) >= 40 for r in records)
    assert all(r["metadata"]["category"] == "registrar" for r in records)


def test_unknown_catalog_format_falls_back_to_structured_llm_courses():
    """A UofT-style page the Carleton regex can't parse must still yield
    full structured course records — not generic text chunks."""
    llm = FakeLLM()
    uoft_page = "CSC236H1 - Introduction to the Theory of Computation. Prereq: CSC148H1, CSC165H1"
    records = extract_mod.extract("course_regex", uoft_page, "https://artsci.calendar.utoronto.ca/x", "courses", llm)
    assert len(records) == 1
    r = records[0]
    assert r["id"] == "CSC236H1"
    m = r["metadata"]
    assert m["course_code"] == "CSC236H1"
    assert m["prerequisites"] == "CSC148H1, CSC165H1"     # prereq codes parsed for the graph
    assert m["department"] == "CSC"
    # identical contract to the regex path: line layout intact
    assert m["text"].split("\n")[0] == "CSC236H1"


def test_llm_courses_handles_waterloo_codes_and_rejects_junk():
    llm = FakeLLM()
    records = extract_mod.llm_extract_courses("CS 135 Designing Functional Programs", "https://ucalendar.uwaterloo.ca/x", llm)
    assert len(records) == 1                               # "not a course" junk rejected
    m = records[0]["metadata"]
    assert m["course_code"] == "CS 135"
    assert records[0]["id"] == "CS135"                     # stable spaceless ID for O(1) fetch
    assert m["credits"] == "0.5"                           # null credits → safe default, not invented


# ── Verify / promote safety rails ─────────────────────────────────────────────

def _recs(n, prefix="r"):
    return [{"id": f"{prefix}{i}", "embed_text": "t", "metadata": {"text": "t"}} for i in range(n)]


def test_verify_blocks_min_records_and_shrink_and_dupes():
    with pytest.raises(upsert_mod.VerificationError):
        upsert_mod.verify(_recs(3), min_records=10, previous_count=0)
    with pytest.raises(upsert_mod.VerificationError):
        upsert_mod.verify(_recs(10), min_records=1, previous_count=100)   # >50% shrink
    upsert_mod.verify(_recs(10), min_records=1, previous_count=100, force=True)  # force overrides
    dupes = _recs(2) + _recs(2)
    with pytest.raises(upsert_mod.VerificationError):
        upsert_mod.verify(dupes, min_records=1, previous_count=0)


def test_promote_upserts_then_deletes_stale_only_when_asked():
    index = FakeIndex()
    index.upsert([{"id": "old1", "values": [0], "metadata": {}},
                  {"id": "keep", "values": [0], "metadata": {}}], namespace="dates")

    records = [{"id": "keep", "embed_text": "t", "metadata": {"a": 1}},
               {"id": "new1", "embed_text": "t", "metadata": {"a": 2}}]
    vectors = [[0.1] * 8, [0.2] * 8]

    # incremental: no stale deletion — old1 survives
    upsert_mod.promote(index, "dates", records, vectors, delete_stale=False, log=lambda *_: None)
    assert set(index.store["dates"]) == {"old1", "keep", "new1"}

    # full coverage: old1 removed, live set == new set
    stats = upsert_mod.promote(index, "dates", records, vectors, delete_stale=True, log=lambda *_: None)
    assert set(index.store["dates"]) == {"keep", "new1"}
    assert stats["stale_deleted"] == 1


# ── Pipeline end-to-end (fixtures, no network) ────────────────────────────────

@pytest.fixture
def fake_env(tmp_path, monkeypatch):
    """Local school config + fixture fetches + fresh state DB."""
    school_dir = tmp_path / "schools" / "testu"
    school_dir.mkdir(parents=True)
    (school_dir / "sources.json").write_text(json.dumps({"sources": [
        {"category": "dates", "url": "https://testu.example/dates/", "extractor": "llm_dates", "min_records": 1},
        {"category": "registrar", "url": "https://testu.example/registrar/", "extractor": "llm_generic", "min_records": 1},
    ]}))

    fixtures = {
        "https://testu.example/dates/": TABLE_PAGE,
        "https://testu.example/registrar/": ACCORDION_PAGE,
    }

    def fake_fetch(url):
        html = fixtures[url]
        text = fetch_mod.html_to_text(html)
        return fetch_mod.FetchedPage(url=url, kind="html", text=text,
                                     content_hash=fetch_mod._hash(text), html=html)

    monkeypatch.setattr(pipeline_mod.fetch_mod, "fetch_page", fake_fetch)
    monkeypatch.setattr(pipeline_mod, "PREVIEW_DIR", str(tmp_path))

    state = IngestState(db_path=str(tmp_path / "state.db"))
    return SimpleNamespace(tmp=tmp_path, backend_dir=str(tmp_path), state=state,
                           fixtures=fixtures, fake_fetch=fake_fetch, monkeypatch=monkeypatch)


def test_pipeline_dry_run_writes_preview_and_skips_pinecone(fake_env):
    run = pipeline_mod.run_ingest(
        "testu", "dates", dry_run=True, backend_dir=fake_env.backend_dir,
        llm=FakeLLM(), state=fake_env.state, log=lambda *_: None)
    r = run.results[0]
    assert r.status == "dry_run" and r.records >= 2
    lines = open(r.preview_path, encoding="utf-8").read().strip().split("\n")
    assert len(lines) == r.records


def test_pipeline_full_run_then_incremental_skip(fake_env):
    index = FakeIndex()
    kwargs = dict(backend_dir=fake_env.backend_dir, llm=FakeLLM(), state=fake_env.state,
                  openai_client=FakeOpenAI(), index=index, log=lambda *_: None)

    run1 = pipeline_mod.run_ingest("testu", **kwargs)
    assert run1.ok
    assert len(index.store["dates"]) >= 2
    assert len(index.store["registrar"]) == 2

    # nothing changed → both categories skip, live data untouched
    before = {ns: dict(v) for ns, v in index.store.items()}
    run2 = pipeline_mod.run_ingest("testu", **kwargs)
    assert all(r.status == "skipped" for r in run2.results)
    assert index.store == before

    # force → full re-extract, still identical stable IDs (no churn)
    run3 = pipeline_mod.run_ingest("testu", force=True, **kwargs)
    assert run3.ok and set(index.store["dates"]) == set(before["dates"])


def test_pipeline_verification_failure_leaves_live_data_untouched(fake_env):
    index = FakeIndex()
    # existing live data that a broken crawl must not destroy
    index.upsert([{"id": f"d{i}", "values": [0], "metadata": {}} for i in range(30)], namespace="dates")

    class EmptyLLM:
        def __call__(self, system, user):
            return json.dumps({"deadlines": [{"title": "Only one", "date": "2026-01-01", "term": "", "category": "other"}]})

    run = pipeline_mod.run_ingest(
        "testu", "dates", backend_dir=fake_env.backend_dir, llm=EmptyLLM(),
        state=fake_env.state, openai_client=FakeOpenAI(), index=index, log=lambda *_: None)

    assert run.results[0].status == "failed"
    assert "VERIFICATION BLOCKED" in run.results[0].message
    assert len(index.store["dates"]) == 30       # untouched
