"""Offline tests for the data connectors (sitemap, ics, filedrop).

No network: fetches are monkeypatched, files live in tmp_path.

Run:  python -m pytest tests/test_connectors.py -q
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors import get_connector
from connectors.ics import events_to_text, gather_ics, parse_ics_events
from connectors.sitemap import gather_sitemap, parse_sitemap_urls
from connectors.filedrop import gather_filedrop
from ingest.registry import Source

import connectors.ics as ics_mod
import connectors.sitemap as sitemap_mod


# ── Registry ──────────────────────────────────────────────────────────────────

def test_registry_knows_all_connectors():
    for name in ("sitemap", "ics", "filedrop"):
        assert callable(get_connector(name))


def test_unknown_connector_rejected_at_source_load():
    import pytest
    with pytest.raises(ValueError):
        Source(school="x", category="dates", url="https://x.ca", connector="carrier_pigeon")


def test_source_accepts_connector_field():
    s = Source(school="x", category="dates", url="https://x.ca/cal.ics", connector="ics")
    assert s.connector == "ics"


# ── ICS ───────────────────────────────────────────────────────────────────────

SAMPLE_ICS = "\r\n".join([
    "BEGIN:VCALENDAR",
    "BEGIN:VEVENT",
    "SUMMARY:Last day to withdraw from fall courses",
    "DTSTART;VALUE=DATE:20261115",
    "DESCRIPTION:No academic notation\\, no refund after this date.",
    "END:VEVENT",
    "BEGIN:VEVENT",
    "SUMMARY:Fall classes begin and this line is folded across",
    "  two physical lines per RFC 5545",
    "DTSTART:20260903T090000",
    "END:VEVENT",
    "BEGIN:VEVENT",
    "SUMMARY:Broken event with no date",
    "END:VEVENT",
    "END:VCALENDAR",
])


def test_ics_parsing_handles_folding_escapes_and_junk():
    events = parse_ics_events(SAMPLE_ICS)
    assert len(events) == 2   # dateless event dropped
    withdraw = next(e for e in events if "withdraw" in e["summary"])
    assert withdraw["date"] == "2026-11-15"
    assert "no refund" in withdraw["description"]
    folded = next(e for e in events if "begin" in e["summary"])
    assert folded["summary"].endswith("per RFC 5545")
    assert folded["date"] == "2026-09-03"


def test_ics_gather_produces_one_dated_page(monkeypatch):
    monkeypatch.setattr(ics_mod.fetch_mod, "_get",
                        lambda url: SimpleNamespace(text=SAMPLE_ICS))
    src = Source(school="carleton", category="dates",
                 url="https://carleton.ca/dates.ics", connector="ics")
    pages = gather_ics(src, log=lambda *a: None)
    assert len(pages) == 1
    assert pages[0].kind == "ics"
    # Sorted chronologically, pipe-delimited for the llm_dates extractor
    text = pages[0].text
    assert text.index("2026-09-03") < text.index("2026-11-15")
    assert "Last day to withdraw from fall courses | 2026-11-15" in text
    assert pages[0].content_hash   # change detection works on the rendered text


# ── Sitemap ───────────────────────────────────────────────────────────────────

SAMPLE_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://carleton.ca/registrar/deadlines/</loc></url>
  <url><loc>https://carleton.ca/registrar/forms/</loc></url>
  <url><loc>https://carleton.ca/athletics/gym-hours/</loc></url>
  <url><loc>https://carleton.ca/registrar/deadlines/</loc></url>
</urlset>"""


def test_sitemap_parse_dedupes_and_reads_namespaced_locs():
    urls = parse_sitemap_urls(SAMPLE_SITEMAP)
    assert urls == [
        "https://carleton.ca/registrar/deadlines/",
        "https://carleton.ca/registrar/forms/",
        "https://carleton.ca/athletics/gym-hours/",
    ]


def test_sitemap_gather_scopes_by_prefix_and_caps_pages(monkeypatch):
    fetched = []

    def fake_fetch(url):
        fetched.append(url)
        return SimpleNamespace(url=url, kind="html", text="page text",
                               content_hash="h", html="")

    monkeypatch.setattr(sitemap_mod.fetch_mod, "_get",
                        lambda url: SimpleNamespace(text=SAMPLE_SITEMAP))
    monkeypatch.setattr(sitemap_mod.fetch_mod, "fetch_page", fake_fetch)

    src = Source(school="carleton", category="registrar",
                 url="https://carleton.ca/sitemap.xml", connector="sitemap",
                 include_prefix="https://carleton.ca/registrar/", max_pages=10)
    pages = gather_sitemap(src, log=lambda *a: None)
    assert len(pages) == 2
    assert all(u.startswith("https://carleton.ca/registrar/") for u in fetched)


def test_sitemap_parse_garbage_returns_empty():
    assert parse_sitemap_urls("not xml at all <<<") == []


# ── Filedrop ──────────────────────────────────────────────────────────────────

def test_filedrop_reads_supported_files(tmp_path):
    (tmp_path / "fees.txt").write_text("Tuition deposit is $500 due June 1.", encoding="utf-8")
    (tmp_path / "policy.html").write_text(
        "<html><body><main><p>Deferral requests need form R-100.</p></main></body></html>",
        encoding="utf-8")
    (tmp_path / "ignore.docx").write_bytes(b"binary junk")

    src = Source(school="carleton", category="registrar",
                 url=str(tmp_path), connector="filedrop")
    pages = gather_filedrop(src, log=lambda *a: None)
    assert len(pages) == 2
    by_kind = {p.kind: p for p in pages}
    assert "Tuition deposit" in by_kind["text"].text
    assert "form R-100" in by_kind["html"].text
    # url is the file path → per-file change detection via content hash
    assert all(p.content_hash for p in pages)


def test_filedrop_missing_folder_is_safe(tmp_path):
    src = Source(school="carleton", category="registrar",
                 url=str(tmp_path / "nope"), connector="filedrop")
    assert gather_filedrop(src, log=lambda *a: None) == []
