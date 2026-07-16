"""Tests for generate-once/extract-free CSS-schema extraction (ingest/css_schema.py)
and its pipeline wiring.

Testing strategy (no network, no real LLM):
  1. Deterministic engine — apply_schema / field_coverage on real HTML fixtures.
  2. Record contract — css_schema output is byte-identical in shape to the
     regex/LLM extractors (drop-in vector compatibility).
  3. Oracle equivalence — on the same set of courses, css_schema and the trusted
     course_regex parser agree on the course set.
  4. Generation + self-heal — a fake LLM returns a broken schema then a good one;
     the generator must heal and cache.
  5. Cost proof — across N pages of one template, the LLM is called exactly once.
"""

import json

from ingest import css_schema, extract, pipeline
from ingest.fetch import FetchedPage
from ingest.registry import Source
from ingest.state import IngestState


# One repeating course-block template (what a real catalog looks like).
def _course_html(courses) -> str:
    blocks = "".join(
        f'<div class="courseblock">'
        f'<span class="ccode">{c["code"]}</span>'
        f'<span class="ccr">{c["cr"]}</span>'
        f'<p class="ctitle">{c["name"]}</p>'
        f'<p class="cdesc">{c["desc"]}</p>'
        f'</div>'
        for c in courses
    )
    return f'<html><body><div class="pageblock">{blocks}</div></body></html>'


_COURSES = [
    {"code": "COMP 2401", "cr": "0.5", "name": "Systems Programming",
     "desc": "Introduction to systems programming concepts."},
    {"code": "COMP 2402", "cr": "0.5", "name": "Abstract Data Types",
     "desc": "Data structures and algorithms in depth."},
    {"code": "MATH 1007", "cr": "0.5", "name": "Elementary Calculus",
     "desc": "Limits, derivatives and integrals."},
]

_GOOD_COURSE_SCHEMA = {
    "baseSelector": "div.courseblock",
    "fields": [
        {"name": "code", "selector": "span.ccode", "type": "text"},
        {"name": "credits", "selector": "span.ccr", "type": "text"},
        {"name": "name", "selector": "p.ctitle", "type": "text"},
        {"name": "description", "selector": "p.cdesc", "type": "text"},
        {"name": "prerequisites", "selector": "span.prereq", "type": "text", "default": ""},
    ],
}


# ── 1. deterministic engine ─────────────────────────────────────────────────

def test_apply_schema_extracts_every_record():
    items = css_schema.apply_schema(_GOOD_COURSE_SCHEMA, _course_html(_COURSES))
    assert len(items) == 3
    assert items[0]["code"] == "COMP 2401"
    assert items[0]["name"] == "Systems Programming"
    assert items[0]["prerequisites"] == ""       # default applied


def test_apply_schema_bad_selector_never_raises():
    broken = {"baseSelector": "div.courseblock",
              "fields": [{"name": "code", "selector": "::::nonsense", "type": "text"}]}
    # A malformed field selector yields "" for that field, not an exception.
    items = css_schema.apply_schema(broken, _course_html(_COURSES))
    assert items == [] or all(it.get("code", "") == "" for it in items)


def test_field_coverage_reports_fill_rates():
    n, cov = css_schema.field_coverage(_GOOD_COURSE_SCHEMA, _course_html(_COURSES))
    assert n == 3
    assert cov["code"] == 1.0 and cov["name"] == 1.0
    assert cov["prerequisites"] == 0.0           # none present → 0% fill


def test_apply_schema_no_base_returns_empty():
    assert css_schema.apply_schema({"fields": []}, _course_html(_COURSES)) == []


# ── 2. record contract (drop-in compatibility) ─────────────────────────────

def test_records_match_course_record_contract():
    items = css_schema.apply_schema(_GOOD_COURSE_SCHEMA, _course_html(_COURSES))
    records = css_schema.records_from_items(items, "courses", "https://x/courses")

    assert len(records) == 3
    rec = records[0]
    # Identical shape to the canonical builder used by regex/LLM extractors.
    expected = extract._course_record(
        code="COMP 2401", name="Systems Programming", credits=0.5,
        description="Introduction to systems programming concepts.",
        prereq_text="", source_url="https://x/courses")
    assert rec["id"] == expected["id"]
    assert rec["metadata"]["course_code"] == "COMP 2401"
    assert rec["metadata"]["department"] == "COMP"
    assert set(rec["metadata"]) == set(expected["metadata"])


def test_generic_records_build_chunks():
    html = ('<div class="item"><h3 class="t">Deferring an exam</h3>'
            '<p class="b">Submit the deferral form within five business days of the exam.</p></div>'
            '<div class="item"><h3 class="t">Academic standing</h3>'
            '<p class="b">A GPA below 3.5 places a student on academic warning for the term.</p></div>')
    schema = {"baseSelector": "div.item", "fields": [
        {"name": "title", "selector": "h3.t", "type": "text"},
        {"name": "text", "selector": "p.b", "type": "text"}]}
    items = css_schema.apply_schema(schema, html)
    records = css_schema.records_from_items(items, "regulations", "https://x/reg")
    assert len(records) == 2
    assert records[0]["metadata"]["title"] == "Deferring an exam"
    assert records[0]["id"].startswith("regulations-")


# ── 3. oracle equivalence: css_schema agrees with trusted course_regex ─────

def test_css_schema_agrees_with_regex_oracle_on_course_set():
    # course_regex is the production-proven parser — treat it as ground truth.
    regex_text = "\n".join(
        f'{c["code"]} [{c["cr"]} credit]\n{c["name"]}\n{c["desc"]}' for c in _COURSES)
    regex_records = extract.extract_courses(regex_text, "https://x/courses")
    regex_codes = {r["metadata"]["course_code"] for r in regex_records}

    items = css_schema.apply_schema(_GOOD_COURSE_SCHEMA, _course_html(_COURSES))
    schema_records = css_schema.records_from_items(items, "courses", "https://x/courses")
    schema_codes = {r["metadata"]["course_code"] for r in schema_records}

    assert schema_codes == regex_codes == {"COMP 2401", "COMP 2402", "MATH 1007"}
    # And identical stable IDs → same vectors overwrite, no duplication.
    assert {r["id"] for r in schema_records} == {r["id"] for r in regex_records}


# ── 4. generation + self-heal ───────────────────────────────────────────────

class _ScriptedLLM:
    """Returns queued responses in order; counts calls."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, system, user):
        self.calls += 1
        return self.responses.pop(0) if self.responses else self.responses[-1]


def test_generate_schema_self_heals_from_broken_selectors():
    broken = json.dumps({"baseSelector": "div.nonexistent", "fields": [
        {"name": "code", "selector": "span.ccode", "type": "text"}]})
    good = json.dumps(_GOOD_COURSE_SCHEMA)
    llm = _ScriptedLLM([broken, good])

    schema = css_schema.generate_schema(_course_html(_COURSES), "courses", llm)
    n, cov = css_schema.field_coverage(schema, _course_html(_COURSES))
    assert n == 3 and cov["code"] == 1.0
    assert llm.calls == 2          # one broken round, one heal


def test_generate_schema_retries_on_unparseable():
    llm = _ScriptedLLM(["not json at all", json.dumps(_GOOD_COURSE_SCHEMA)])
    schema = css_schema.generate_schema(_course_html(_COURSES), "courses", llm)
    assert schema.get("baseSelector") == "div.courseblock"


# ── 5. schema store: cache once, reuse forever ─────────────────────────────

def test_schema_store_caches_and_persists(tmp_path):
    store = css_schema.SchemaStore(str(tmp_path))
    llm = _ScriptedLLM([json.dumps(_GOOD_COURSE_SCHEMA)])

    s1 = store.get_or_generate("carleton", "courses", _course_html(_COURSES), llm)
    s2 = store.get_or_generate("carleton", "courses", _course_html(_COURSES), llm)
    assert s1 == s2 == _GOOD_COURSE_SCHEMA
    assert llm.calls == 1                       # generated once, then cached
    # Survives a fresh store instance (persisted to disk).
    assert css_schema.SchemaStore(str(tmp_path)).get("carleton", "courses") == _GOOD_COURSE_SCHEMA


# ── pipeline wiring: one LLM call for the whole template ────────────────────

def test_pipeline_css_schema_one_llm_call_across_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setattr(pipeline, "PREVIEW_DIR", str(tmp_path))
    state = IngestState(str(tmp_path / "state.db"))

    # Three distinct catalog pages, same template, different courses each.
    pages = [
        FetchedPage(url=f"https://x/courses/p{i}", kind="html",
                    text="ignored", content_hash=f"h{i}",
                    html=_course_html([_COURSES[i]]))
        for i in range(3)
    ]
    it = iter(pages)
    monkeypatch.setattr(pipeline.fetch_mod, "fetch_page", lambda url: next(it))

    source = Source(school="carleton", category="courses",
                    url="https://x/courses/p0", extractor="css_schema")
    llm = _ScriptedLLM([json.dumps(_GOOD_COURSE_SCHEMA)])

    # Fan out over the three pages via follow_links so all three are fetched.
    monkeypatch.setattr(pipeline, "_gather_pages", lambda src, log: pages)

    result = pipeline.run_category("carleton", "courses", sources=[source], state=state,
                                   dry_run=True, llm=llm, log=lambda *_: None)

    assert result.status == "dry_run"
    assert result.records == 3                  # one course from each page
    assert llm.calls == 1                       # schema generated ONCE, not per page


def test_pipeline_css_schema_falls_back_when_schema_misses(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setattr(pipeline, "PREVIEW_DIR", str(tmp_path))
    state = IngestState(str(tmp_path / "state.db"))

    # Schema targets div.courseblock, but this page uses a different layout →
    # apply_schema matches nothing → LLM fallback (llm_courses) must fire.
    page = FetchedPage(url="https://x/courses/odd", kind="html", text="COMP 3000 course",
                       content_hash="h", html="<html><body><ul><li>COMP 3000</li></ul></body></html>")
    monkeypatch.setattr(pipeline, "_gather_pages", lambda src, log: [page])

    fallback_called = {"n": 0}

    def llm(system, user):
        if "extraction schemas" in system:            # schema-generation prompt
            return json.dumps(_GOOD_COURSE_SCHEMA)
        fallback_called["n"] += 1                      # llm_courses fallback prompt
        return json.dumps({"courses": [
            {"code": "COMP 3000", "name": "Special Topics", "credits": 0.5,
             "description": "Advanced topics.", "prerequisites": ""}]})

    source = Source(school="carleton", category="courses",
                    url="https://x/courses/odd", extractor="css_schema")
    result = pipeline.run_category("carleton", "courses", sources=[source], state=state,
                                   dry_run=True, llm=llm, log=lambda *_: None)

    assert fallback_called["n"] == 1
    assert result.records == 1
