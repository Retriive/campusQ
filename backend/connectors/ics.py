"""ICS connector — an academic-calendar feed becomes deadline records.

Universities publish important dates as iCalendar feeds (.ics). Those are
machine-readable already, so instead of scraping a dates page and hoping the
table format holds, this connector renders each VEVENT as one clean line —
"Title | date | description" — and hands the result to the pipeline as a
single page. The existing llm_dates extractor then emits the same
{title, date, term, category} records the dates namespace already uses.

Parser is stdlib-only and deliberately minimal: SUMMARY, DTSTART, DESCRIPTION.
"""

from __future__ import annotations

import hashlib
import re

from ingest import fetch as fetch_mod
from ingest.fetch import FetchedPage

_DATE_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})")


def _unfold(ics_text: str) -> list[str]:
    """RFC 5545 line unfolding: a line starting with space/tab continues the
    previous line."""
    lines: list[str] = []
    for raw in ics_text.replace("\r\n", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _unescape(value: str) -> str:
    return (value.replace("\\n", " ").replace("\\,", ",")
                 .replace("\\;", ";").replace("\\\\", "\\").strip())


def parse_ics_events(ics_text: str) -> list[dict]:
    events: list[dict] = []
    current: dict | None = None
    for line in _unfold(ics_text):
        if line.startswith("BEGIN:VEVENT"):
            current = {}
        elif line.startswith("END:VEVENT"):
            if current and current.get("summary") and current.get("date"):
                events.append(current)
            current = None
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            key = key.split(";")[0].upper()   # DTSTART;VALUE=DATE → DTSTART
            if key == "SUMMARY":
                current["summary"] = _unescape(value)
            elif key == "DTSTART":
                m = _DATE_RE.match(value.strip())
                if m:
                    current["date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            elif key == "DESCRIPTION":
                current["description"] = _unescape(value)[:300]
    return events


def events_to_text(events: list[dict]) -> str:
    lines = ["Academic calendar events (from official iCalendar feed):", ""]
    for e in sorted(events, key=lambda x: x["date"]):
        desc = e.get("description", "")
        lines.append(f"{e['summary']} | {e['date']}" + (f" | {desc}" if desc else ""))
    return "\n".join(lines)


def gather_ics(source, log=print) -> list[FetchedPage]:
    r = fetch_mod._get(source.url)
    events = parse_ics_events(r.text)
    log(f"  ics {source.url} → {len(events)} events")
    if not events:
        return []
    text = events_to_text(events)
    return [FetchedPage(
        url=source.url, kind="ics", text=text,
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )]
