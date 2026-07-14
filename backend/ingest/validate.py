"""Per-record validators + quarantine screening.

Deterministic checks that run AFTER extraction and BEFORE verify/promote.
A record that fails is quarantined (stored in SQLite with its reasons) instead
of published — and its previously-live vector keeps serving, because a failed
validation means we don't trust the NEW value, not that the old one is wrong.

The first validators target the failure modes that hurt students most:
  - deadlines outside a plausible academic window (LLM year hallucination)
  - the same deadline title+term extracted with two different dates
    (contradiction — neither value can be trusted automatically)
  - courses with implausible credit values
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

# Plausible window for an academic deadline relative to today: one year of
# history, two years of future calendar.
DATE_PAST_DAYS = 365
DATE_FUTURE_DAYS = 730

# Mirrors the category vocabulary in extract._DATES_SYSTEM.
DATE_CATEGORIES = {"registration", "withdrawal", "exams", "payment",
                   "classes", "holiday", "other"}

MAX_COURSE_CREDITS = 2.0
MIN_EMBED_CHARS = 30


def _check_dates(md: dict, today: date) -> list[str]:
    iso = str(md.get("date", ""))
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
    except ValueError:
        return [f"unparseable date '{iso}'"]

    reasons: list[str] = []
    if d < today - timedelta(days=DATE_PAST_DAYS):
        reasons.append(f"date {iso} is more than {DATE_PAST_DAYS} days in the past")
    elif d > today + timedelta(days=DATE_FUTURE_DAYS):
        reasons.append(f"date {iso} is more than {DATE_FUTURE_DAYS} days in the future")
    category = str(md.get("category", ""))
    if category not in DATE_CATEGORIES:
        reasons.append(f"unknown deadline category '{category}'")
    return reasons


def _check_courses(md: dict) -> list[str]:
    try:
        credits = float(md.get("credits", ""))
    except (TypeError, ValueError):
        return [f"non-numeric credits '{md.get('credits')}'"]
    if not 0 < credits <= MAX_COURSE_CREDITS:
        return [f"implausible credits {credits} (expected 0 < c <= {MAX_COURSE_CREDITS})"]
    return []


def validate_record(record: dict, category: str, today: date | None = None) -> list[str]:
    """Reasons this record must not be published; empty list = valid."""
    today = today or date.today()
    md = record.get("metadata", {})
    reasons: list[str] = []

    if not str(md.get("source", "")).strip():
        reasons.append("missing source URL")
    if len("".join(str(record.get("embed_text", "")).split())) < MIN_EMBED_CHARS:
        reasons.append(f"embed_text under {MIN_EMBED_CHARS} chars")

    if category == "dates":
        reasons += _check_dates(md, today)
    elif category == "courses":
        reasons += _check_courses(md)
    return reasons


def find_date_contradictions(
    records: list[dict],
) -> tuple[list[dict], list[tuple[dict, list[str]]]]:
    """Same (title, term) extracted with different dates → quarantine the whole
    group: we can't automatically know which value is true."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in records:
        md = r.get("metadata", {})
        # Stored titles are "Title — Month D, YYYY"; strip the date suffix so
        # the same deadline extracted with two dates still lands in one group.
        title = str(md.get("title", "")).split("—")[0].strip().lower()
        key = (title, str(md.get("term", "")).strip().lower())
        groups.setdefault(key, []).append(r)

    clean: list[dict] = []
    quarantined: list[tuple[dict, list[str]]] = []
    for (title, term), group in groups.items():
        dates = sorted({str(g["metadata"].get("date", "")) for g in group})
        if len(dates) > 1:
            reason = (f"contradiction: '{title}' ({term or 'no term'}) extracted with "
                      f"{len(dates)} different dates: {', '.join(dates)}")
            quarantined += [(g, [reason]) for g in group]
        else:
            clean += group
    return clean, quarantined


def screen(
    records: list[dict], category: str, today: date | None = None,
) -> tuple[list[dict], list[tuple[dict, list[str]]]]:
    """Split records into publishable and quarantined-with-reasons."""
    clean: list[dict] = []
    quarantined: list[tuple[dict, list[str]]] = []
    for r in records:
        reasons = validate_record(r, category, today)
        if reasons:
            quarantined.append((r, reasons))
        else:
            clean.append(r)
    if category == "dates":
        clean, contradicted = find_date_contradictions(clean)
        quarantined += contradicted
    return clean, quarantined
