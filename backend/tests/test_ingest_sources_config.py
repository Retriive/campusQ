"""Tests for the Carleton sources.json cutover config + connector guard."""

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
    # Cutover scope: mechanical scrapes only. dates/facts stay curated.
    assert categories == {"courses", "library"}

    courses = [s for s in sources if s.category == "courses"]
    assert len(courses) == 1
    assert courses[0].follow_links and courses[0].max_pages >= 100
    assert courses[0].resolve_extractor() == "course_regex"
    assert courses[0].include_prefix == courses[0].url  # fan-out stays on the catalog

    library = [s for s in sources if s.category == "library"]
    assert len(library) == 19
    assert all(s.url.startswith("https://library.carleton.ca/") for s in library)
    assert all(s.resolve_extractor() == "llm_generic" for s in library)
    # verify() floor for the category comes from the max across its sources
    assert max(s.min_records for s in library) >= 10


def test_unimplemented_connector_fails_with_clear_message():
    source = Source(school="test", category="dates", url="https://x/cal.ics",
                    connector="ics")
    with pytest.raises(FetchError, match="not implemented"):
        pipeline._gather_pages(source, log=lambda *_: None)
