"""Build readable, trustworthy source citations from Pinecone chunk metadata."""

from __future__ import annotations

import re
from urllib.parse import urlparse

NO_ANSWER_PHRASES = (
    "that's outside of what i currently know",
    "sorry, campusq ran into an error",
)

NAMESPACE_FALLBACK_URLS = {
    "schedule": "https://carleton.ca/registration/",
    "dates": "https://calendar.carleton.ca/undergrad/academicdates/",
    "facts": "https://calendar.carleton.ca",
    "registrar": "https://carleton.ca/registration/",
    "regulations": "https://calendar.carleton.ca/undergrad/regulations/",
    "programs": "https://calendar.carleton.ca/undergrad/programs/",
    "courses": "https://calendar.carleton.ca/undergrad/courses/",
    "tuition": "https://calendar.carleton.ca/undergrad/fees/",
    "library": "https://library.carleton.ca/",
    "services": "https://carleton.ca/",
}

_BARE_DEPT_CODE = re.compile(r"^[A-Z]{3,4}$")


def _is_safe_url(url: str) -> bool:
    """Only http(s) links are safe to hand to the frontend as clickable sources.
    Chunk metadata comes from ingested pages, so a poisoned `source` field could
    otherwise smuggle a javascript:/data: URL into the citation list."""
    try:
        return urlparse(url).scheme in ("http", "https")
    except Exception:
        return False

_PROGRAM_CITATION_NS = frozenset({"programs", "courses", "regulations", "registrar"})
_PROGRAM_CITATION_ORDER = {"programs": 0, "courses": 1, "regulations": 2, "registrar": 3}


def chunk_passes_threshold(match, is_program_query: bool, threshold: float) -> bool:
    is_program_chunk = "program" in match.metadata or "section" in match.metadata
    if is_program_query and is_program_chunk:
        return True
    return match.score >= threshold


def citation_url_from_metadata(meta: dict, namespace: str = "") -> str:
    url = (meta.get("source") or "").strip()
    if url and "Unknown" not in url and _is_safe_url(url):
        return url
    return NAMESPACE_FALLBACK_URLS.get(namespace, "https://calendar.carleton.ca")


def title_from_url_path(url: str) -> str:
    try:
        parts = urlparse(url).path.strip("/").split("/")
        slug = parts[-1] if parts else ""
        if slug and slug.lower() not in ("undergrad", "courses", "carleton", "ca"):
            return slug.replace("-", " ").title()
    except Exception:
        pass
    return ""


def citation_title_from_metadata(meta: dict, namespace: str = "") -> str:
    course_code = (meta.get("course_code") or "").strip()
    course_name = (meta.get("course_name") or "").strip()
    if course_code and course_name:
        return f"{course_code} — {course_name}"
    if course_code:
        dept = (meta.get("department") or "").strip()
        suffix = f"{dept} Course Calendar" if dept else "Course Calendar"
        return f"{course_code} — {suffix}"

    term = (meta.get("term") or "").strip()
    if course_code and term:
        section_title = (meta.get("title") or "").strip()
        base = f"{course_code} — {term}"
        return f"{base} ({section_title})" if section_title else f"{base} Schedule"

    title = (meta.get("title") or "").strip()
    if title and not _BARE_DEPT_CODE.match(title):
        return title

    program = (meta.get("program") or "").strip()
    section = (meta.get("section") or "").strip()
    if program:
        if section and section.lower() not in ("full requirements",):
            return f"{program} — {section}"
        return program

    category = (meta.get("category") or "").strip()
    heading = (meta.get("heading") or "").strip()
    if category and heading:
        return f"{category} — {heading}"
    if heading:
        return heading
    if category:
        return category

    url = citation_url_from_metadata(meta, namespace)
    return title_from_url_path(url)


def citation_section_from_metadata(meta: dict, namespace: str = "") -> str:
    if meta.get("course_code"):
        return "Carleton Course Calendar"
    if meta.get("heading") and meta.get("category"):
        return meta["category"]
    if namespace == "dates":
        term = meta.get("term", "")
        return f"Academic Deadlines · {term}" if term else "Academic Deadlines"
    if namespace == "schedule":
        return "Class Schedule"
    if namespace == "regulations":
        return "Academic Regulations"
    if namespace == "programs":
        return "Program Requirements"
    if namespace == "registrar":
        return "Registration & Records"
    if namespace == "tuition":
        return "Tuition & Fees"
    if namespace == "library":
        return "MacOdrum Library"
    if namespace == "services":
        return "Campus Services"
    return "Carleton Academic Calendar"


def citation_from_match(match, namespace: str = "") -> dict | None:
    meta = match.metadata
    title = citation_title_from_metadata(meta, namespace)
    if not title or _BARE_DEPT_CODE.match(title):
        title = title_from_url_path(citation_url_from_metadata(meta, namespace))
    if not title or _BARE_DEPT_CODE.match(title):
        return None
    return {
        "url": citation_url_from_metadata(meta, namespace),
        "title": title,
        "section": citation_section_from_metadata(meta, namespace),
        "namespace": namespace,
    }


def citation_from_course(structured: dict, source_url: str = "") -> dict:
    code = structured.get("courseCode", "")
    name = structured.get("courseName", "")
    title = f"{code} — {name}" if code and name else code or name or "Course Calendar"
    safe_source = source_url if source_url and _is_safe_url(source_url) else ""
    return {
        "url": safe_source or "https://calendar.carleton.ca/undergrad/courses/",
        "title": title,
        "section": "Carleton Course Calendar",
        "namespace": "courses",
    }


def dedupe_citations(citations: list[dict], limit: int = 3) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for citation in citations:
        key = (citation.get("url", ""), citation.get("title", ""))
        if key in seen or not citation.get("title"):
            continue
        seen.add(key)
        out.append(citation)
        if len(out) >= limit:
            break
    return out


def finalize_citations(
    citations: list[dict],
    is_program_query: bool,
    limit: int = 3,
    intent: str = "general",
) -> list[dict]:
    """Drop irrelevant namespaces and rank program sources first."""
    # Lazy import avoids circular imports with grounding helpers.
    from grounding import INTENT_ALLOWED_NAMESPACES

    if is_program_query:
        citations = [c for c in citations if c.get("namespace") in _PROGRAM_CITATION_NS]
        citations.sort(key=lambda c: _PROGRAM_CITATION_ORDER.get(c.get("namespace", ""), 99))
    else:
        allow = INTENT_ALLOWED_NAMESPACES.get(intent)
        if allow is not None:
            filtered = [c for c in citations if c.get("namespace") in allow]
            # Keep filtered list even if empty — off-intent sources must not show.
            citations = filtered
    cleaned = dedupe_citations(citations, limit)
    for c in cleaned:
        c.pop("namespace", None)
    return cleaned


def should_emit_citations(answer: str, chunks_used: int) -> bool:
    if chunks_used <= 0:
        return False
    lower = answer.lower()
    return not any(phrase in lower for phrase in NO_ANSWER_PHRASES)


def build_context_and_citations(
    matches_with_ns: list[tuple],
    is_program_query: bool,
    threshold: float,
    intent: str = "general",
) -> tuple[str, list[dict], int]:
    context_text = ""
    citations: list[dict] = []
    chunks_used = 0

    for match, namespace in matches_with_ns:
        if not chunk_passes_threshold(match, is_program_query, threshold):
            continue
        meta = match.metadata
        doc_text = meta.get("text", "")
        doc_source = citation_url_from_metadata(meta, namespace)
        context_text += (
            f"\n--- Source: {doc_source} (relevance: {match.score:.2f}) ---\n{doc_text}\n"
        )
        chunks_used += 1
        citation = citation_from_match(match, namespace)
        if citation:
            citations.append(citation)

    return context_text, finalize_citations(citations, is_program_query, intent=intent), chunks_used
