"""Unit tests for citation formatting."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from citations import (
    citation_from_course,
    citation_from_match,
    citation_title_from_metadata,
    dedupe_citations,
    finalize_citations,
    should_emit_citations,
)


class FakeMatch:
    def __init__(self, metadata: dict, score: float = 0.8):
        self.metadata = metadata
        self.score = score


def test_course_citation_title():
    meta = {
        "course_code": "COMP 3000",
        "course_name": "Operating Systems",
        "department": "COMP",
        "source": "https://calendar.carleton.ca/undergrad/courses/COMP/",
    }
    assert citation_title_from_metadata(meta, "courses") == "COMP 3000 — Operating Systems"


def test_regulation_citation_title():
    meta = {
        "category": "Academic Regulations",
        "heading": "3.2.6 Minimum CGPA Requirements",
        "source": "https://calendar.carleton.ca/undergrad/regulations/academicregulationsoftheuniversity/",
    }
    title = citation_title_from_metadata(meta, "regulations")
    assert "3.2.6 Minimum CGPA Requirements" in title


def test_date_citation_title():
    meta = {
        "title": "Last day to drop full fall courses with a full fee refund — September 30, 2026",
        "term": "Fall 2026",
        "source": "https://calendar.carleton.ca/undergrad/academicdates/",
    }
    assert "Last day to drop" in citation_title_from_metadata(meta, "dates")


def test_bare_dept_code_not_used_as_citation():
    meta = {"title": "COMP", "source": "https://calendar.carleton.ca/undergrad/courses/COMP/"}
    citation = citation_from_match(FakeMatch(meta), "courses")
    assert citation is None or citation["title"] != "COMP"


def test_no_citations_on_unknown_answer():
    answer = (
        "That's outside of what I currently know. "
        "If you think this should be covered, use the Report a Problem button and we'll add it."
    )
    assert should_emit_citations(answer, chunks_used=3) is False


def test_citations_on_good_answer():
    assert should_emit_citations("A B- is worth 7 grade points.", chunks_used=2) is True


def test_no_citations_without_chunks():
    assert should_emit_citations("Some answer", chunks_used=0) is False


def test_dedupe_by_url_and_title():
    citations = [
        {"url": "https://a.com", "title": "One", "section": "A"},
        {"url": "https://a.com", "title": "One", "section": "A"},
        {"url": "https://b.com", "title": "Two", "section": "B"},
    ]
    assert len(dedupe_citations(citations)) == 2


def test_direct_course_citation():
    citation = citation_from_course(
        {"courseCode": "COMP 2401", "courseName": "Object-Oriented Programming"},
        "https://calendar.carleton.ca/undergrad/courses/COMP/",
    )
    assert citation["title"] == "COMP 2401 — Object-Oriented Programming"
    assert "calendar.carleton.ca" in citation["url"]


def test_program_citations_exclude_tuition():
    citations = [
        {"url": "https://a.com", "title": "B.Eng Software Engineering", "namespace": "programs"},
        {"url": "https://b.com", "title": "Miscellaneous Fees", "namespace": "tuition"},
        {"url": "https://c.com", "title": "Course Selection Guide", "namespace": "facts"},
        {"url": "https://d.com", "title": "B.C.S. Honours", "namespace": "programs"},
    ]
    out = finalize_citations(citations, is_program_query=True)
    titles = [c["title"] for c in out]
    assert "Miscellaneous Fees" not in titles
    assert "Course Selection Guide" not in titles
    assert titles[0] == "B.Eng Software Engineering"


def test_services_intent_drops_course_citations():
    citations = [
        {"url": "https://calendar.carleton.ca/COMP/", "title": "COMP 3000 — Operating Systems", "namespace": "courses"},
        {"url": "https://carleton.ca/awards/...", "title": "Awards — Out Of Province Aid", "namespace": "services"},
    ]
    out = finalize_citations(citations, is_program_query=False, intent="services")
    titles = [c["title"] for c in out]
    assert "COMP 3000 — Operating Systems" not in titles
    assert "Awards — Out Of Province Aid" in titles
