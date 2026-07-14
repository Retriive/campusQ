"""Tests for the Carleton sources.json config + connector guard."""

from urllib.parse import urlparse

import pytest

from ingest import pipeline
from ingest.fetch import FetchError
from ingest.registry import Source, list_schools, load_sources


def test_carleton_appears_in_known_schools():
    assert "carleton" in list_schools(pipeline.BACKEND_DIR)


def test_carleton_sources_load_and_validate():
    sources = load_sources("carleton", pipeline.BACKEND_DIR)
    assert sources, "carleton sources.json must load"

    categories = {s.category for s in sources}
    assert categories == {"courses", "library", "registrar", "regulations",
                          "programs", "tuition", "services"}
    # Deliberately NOT scraped: dates/facts stay curated, schedule stays on
    # the Banner-driven legacy script.
    assert not categories & {"dates", "facts", "schedule"}

    for s in sources:
        assert s.url.startswith("https://")
        assert urlparse(s.url).netloc.endswith("carleton.ca")

    courses = [s for s in sources if s.category == "courses"]
    assert len(courses) == 1
    assert courses[0].follow_links and courses[0].max_pages >= 100
    assert courses[0].resolve_extractor() == "course_regex"
    assert courses[0].include_prefix == courses[0].url  # fan-out stays on the catalog

    library = [s for s in sources if s.category == "library"]
    assert len(library) == 19
    assert all(s.resolve_extractor() == "llm_generic" for s in library)


def test_coverage_hubs_fan_out():
    sources = load_sources("carleton", pipeline.BACKEND_DIR)
    hubs = [s for s in sources if s.category not in ("courses", "library")]
    # Hub coverage is breadth via one-hop fan-out; every hub must fan out and
    # keep its crawl inside its own prefix.
    assert all(s.follow_links for s in hubs)
    assert all(s.include_prefix.startswith("https://") for s in hubs)
    assert all(s.max_pages <= 250 for s in hubs)

    hub_urls = {s.url for s in hubs}
    # The coverage batch's key student-facing hubs
    for must_have in (
        "https://carleton.ca/registration/",
        "https://carleton.ca/registrar/",
        "https://carleton.ca/awards/",
        "https://carleton.ca/isso/",
        "https://carleton.ca/its/",
        "https://housing.carleton.ca/",
        "https://calendar.carleton.ca/undergrad/undergradprograms/",
        "https://carleton.ca/studentaccounts/",
    ):
        assert must_have in hub_urls, f"missing hub {must_have}"

    # Every category that verify() guards has a floor on at least one source
    for cat in ("registrar", "regulations", "programs", "tuition", "services"):
        assert max(s.min_records for s in sources if s.category == cat) >= 20


def test_unimplemented_connector_fails_with_clear_message():
    source = Source(school="test", category="dates", url="https://x/cal.ics",
                    connector="ics")
    with pytest.raises(FetchError, match="not implemented"):
        pipeline._gather_pages(source, log=lambda *_: None)
