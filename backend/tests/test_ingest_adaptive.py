"""Tests for saturation-based adaptive crawling (ingest/adaptive.py) and its
pipeline wiring."""

from ingest import pipeline
from ingest.adaptive import SaturationTracker
from ingest.fetch import FetchedPage
from ingest.registry import Source


def _novel_page(i: int) -> str:
    # Each page introduces a fresh vocabulary → high novelty, never saturates.
    return " ".join(f"topic{i}word{j} unique{i}term{j} distinct{i}item{j}"
                    for j in range(40))


def _repetitive_page() -> str:
    # Same words every time → after warmup, novelty collapses to zero.
    return " ".join(f"sharedword{j} commonterm{j} repeated{j}" for j in range(40))


def test_never_stops_before_warmup():
    t = SaturationTracker(min_pages=5, patience=3)
    for _ in range(4):
        t.observe(_repetitive_page())
        assert not t.should_stop()


def test_stops_when_content_saturates():
    t = SaturationTracker(min_pages=5, patience=3, novelty_threshold=0.05)
    stopped_at = None
    for i in range(20):
        t.observe(_repetitive_page())
        if t.should_stop():
            stopped_at = i
            break
    assert stopped_at is not None
    # min_pages warmup + patience low-novelty pages; the very first page is all
    # "new", so saturation is reached a few pages in, well before 20.
    assert stopped_at < 10


def test_does_not_stop_on_genuinely_novel_pages():
    t = SaturationTracker(min_pages=5, patience=3)
    for i in range(15):
        t.observe(_novel_page(i))
    assert not t.should_stop()


def test_thin_pages_are_ignored():
    t = SaturationTracker(min_pages=3, patience=2, min_page_tokens=20)
    # Thin pages return novelty 1.0 and must not advance warmup or streak.
    for _ in range(5):
        assert t.observe("too short") == 1.0
    assert t.pages_seen == 0
    assert not t.should_stop()


def test_novelty_is_a_fraction():
    t = SaturationTracker()
    first = t.observe(_repetitive_page())
    assert first == 1.0                       # everything new on the first page
    second = t.observe(_repetitive_page())
    assert second == 0.0                      # nothing new the second time


# ── pipeline wiring ─────────────────────────────────────────────────────────

def test_gather_pages_stops_early_when_adaptive(monkeypatch):
    # 50 candidate links, all repetitive → adaptive should stop well short of 50.
    root_html = "".join(
        f'<a href="https://x.example.ca/p{i}">p{i}</a>' for i in range(50))
    root = FetchedPage(url="https://x.example.ca/", kind="html",
                       text="root hub page", content_hash="r", html=root_html)

    def fake_fetch(url):
        if url == root.url:
            return root
        return FetchedPage(url=url, kind="html", text=_repetitive_page(),
                           content_hash=url)

    monkeypatch.setattr(pipeline.fetch_mod, "fetch_page", fake_fetch)

    source = Source(school="test", category="services",
                    url="https://x.example.ca/", follow_links=True,
                    include_prefix="https://x.example.ca/", max_pages=50,
                    adaptive=True)
    pages = pipeline._gather_pages(source, log=lambda *_: None)
    # Far fewer than the 50 candidates were fetched.
    assert len(pages) < 20


def test_gather_pages_fetches_all_when_not_adaptive(monkeypatch):
    root_html = "".join(
        f'<a href="https://x.example.ca/p{i}">p{i}</a>' for i in range(12))
    root = FetchedPage(url="https://x.example.ca/", kind="html",
                       text="hub", content_hash="r", html=root_html)

    def fake_fetch(url):
        if url == root.url:
            return root
        return FetchedPage(url=url, kind="html", text=_repetitive_page(),
                           content_hash=url)

    monkeypatch.setattr(pipeline.fetch_mod, "fetch_page", fake_fetch)

    source = Source(school="test", category="services",
                    url="https://x.example.ca/", follow_links=True,
                    include_prefix="https://x.example.ca/", max_pages=50,
                    adaptive=False)
    pages = pipeline._gather_pages(source, log=lambda *_: None)
    # All 12 candidate pages fetched (root text too short to be inserted).
    assert len(pages) == 12
