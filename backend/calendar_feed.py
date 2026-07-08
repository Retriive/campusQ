"""
calendar_feed.py — Academic deadlines as a subscribable calendar feed.

Students subscribe once (webcal/Google/Outlook/Apple) and every deadline lands
in the calendar they already live in — with a 2-day-before reminder. Because it
is a *subscription* (not a one-shot .ics download), the feed auto-updates in
their calendar app when Carleton publishes new dates: update DEADLINES here,
redeploy, done.

This module is the backend's single source of truth for the deadline dataset:
  - GET /api/calendar/deadlines.ics  (main.py) serves the feed built here
  - scrapers/active/scrape_dates.py embeds these entries into Pinecone

The frontend deadline-tracker.tsx keeps its own copy for instant rendering —
keep the two lists in sync when Carleton publishes a new calendar year.
"""

from datetime import date, datetime, timedelta

SCHOOL = "Carleton University"
SOURCE_URL = "https://carleton.ca/registration/academic-dates/"
CALENDAR_NAME = "Carleton Deadlines (CampusQ)"

CATEGORIES = ("registration", "withdrawal", "exams", "payment", "classes", "holiday")

# (id, term, category, title, YYYY-MM-DD) — mirrors deadline-tracker.tsx
DEADLINES = [
    # Summer 2026
    ("su26-term-begins",    "Summer 2026", "classes",      "Summer term begins", "2026-05-06"),
    ("su26-early-add",      "Summer 2026", "registration", "Last day to add/change early summer courses", "2026-05-12"),
    ("su26-full-add",       "Summer 2026", "registration", "Last day to add full summer courses", "2026-05-20"),
    ("su26-full-fee",       "Summer 2026", "withdrawal",   "Last day to drop full summer (full refund)", "2026-05-31"),
    ("su26-early-withdraw", "Summer 2026", "withdrawal",   "Last day to withdraw from early summer courses", "2026-06-01"),
    ("su26-early-lastday",  "Summer 2026", "classes",      "Last day of early summer classes", "2026-06-18"),
    ("su26-early-exams",    "Summer 2026", "exams",        "Early summer final exams begin", "2026-06-21"),
    ("su26-payment",        "Summer 2026", "payment",      "Summer final payment deadline", "2026-06-25"),
    ("su26-canada-day",     "Summer 2026", "holiday",      "Canada Day — University closed", "2026-07-01"),
    ("su26-late-begins",    "Summer 2026", "classes",      "Late summer courses begin", "2026-07-02"),
    ("su26-late-add",       "Summer 2026", "registration", "Last day to add/change late summer courses", "2026-07-08"),
    ("su26-full-withdraw",  "Summer 2026", "withdrawal",   "Last day to withdraw from full/late summer courses", "2026-08-01"),
    ("su26-civic",          "Summer 2026", "holiday",      "Civic Holiday — University closed", "2026-08-03"),
    ("su26-late-lastday",   "Summer 2026", "classes",      "Last day of late/full summer classes", "2026-08-14"),
    ("su26-final-exams",    "Summer 2026", "exams",        "Full/late summer final exams begin", "2026-08-17"),

    # Fall 2026 (registration windows open during the summer)
    ("fa26-timetickets",    "Summer 2026", "registration", "Time tickets available in Carleton Central", "2026-06-17"),
    ("fa26-reg-new",        "Summer 2026", "registration", "Registration opens — new first-year students", "2026-07-06"),
    ("fa26-reg-returning",  "Summer 2026", "registration", "Registration opens — returning students", "2026-07-10"),
    ("fa26-reg-special",    "Summer 2026", "registration", "Registration opens — special/visiting students", "2026-08-05"),
    ("fa26-payment",        "Fall 2026", "payment",      "Fall payment deadline", "2026-08-25"),
    ("fa26-labour-day",     "Fall 2026", "holiday",      "Labour Day — University closed", "2026-09-07"),
    ("fa26-term-begins",    "Fall 2026", "classes",      "Fall term begins", "2026-09-09"),
    ("fa26-early-add",      "Fall 2026", "registration", "Last day to add/change early fall courses", "2026-09-15"),
    ("fa26-full-add",       "Fall 2026", "registration", "Last day to add full fall / fall-winter courses", "2026-09-22"),
    ("fa26-full-fee",       "Fall 2026", "withdrawal",   "Last day to drop full fall courses (full refund)", "2026-09-30"),
    ("fa26-early-withdraw", "Fall 2026", "withdrawal",   "Last day to withdraw from early fall courses", "2026-10-01"),
    ("fa26-thanksgiving",   "Fall 2026", "holiday",      "Thanksgiving — University closed", "2026-10-12"),
    ("fa26-early-lastday",  "Fall 2026", "classes",      "Last day of early fall classes", "2026-10-23"),
    ("fa26-fall-break",     "Fall 2026", "holiday",      "Fall break begins (no classes)", "2026-10-26"),
    ("fa26-early-exams",    "Fall 2026", "exams",        "Early fall final exams begin", "2026-10-31"),
    ("fa26-late-begins",    "Fall 2026", "classes",      "Late fall classes begin", "2026-11-02"),
    ("fa26-full-withdraw",  "Fall 2026", "withdrawal",   "Last day to withdraw from full/late fall courses", "2026-11-15"),
    ("fa26-winter-payment", "Fall 2026", "payment",      "Winter payment deadline", "2026-11-25"),
    ("fa26-lastday",        "Fall 2026", "classes",      "Last day of full/late fall classes", "2026-12-11"),
    ("fa26-exams",          "Fall 2026", "exams",        "Fall final exams begin", "2026-12-12"),
    ("fa26-uni-closed",     "Fall 2026", "holiday",      "University closes for holidays", "2026-12-24"),

    # Winter 2027
    ("wi27-term-begins",    "Winter 2027", "classes",      "Winter term begins", "2027-01-06"),
    ("wi27-early-add",      "Winter 2027", "registration", "Last day to add/change early winter courses", "2027-01-12"),
    ("wi27-full-add",       "Winter 2027", "registration", "Last day to add full winter courses", "2027-01-19"),
    ("wi27-full-fee",       "Winter 2027", "withdrawal",   "Last day to drop full winter (full refund)", "2027-01-31"),
    ("wi27-early-withdraw", "Winter 2027", "withdrawal",   "Last day to withdraw from early winter courses", "2027-02-01"),
    ("wi27-family-day",     "Winter 2027", "holiday",      "Family Day — University closed", "2027-02-15"),
    ("wi27-reading-week",   "Winter 2027", "holiday",      "Winter break / Reading week begins", "2027-02-15"),
    ("wi27-late-begins",    "Winter 2027", "classes",      "Late winter classes begin", "2027-02-25"),
    ("wi27-full-withdraw",  "Winter 2027", "withdrawal",   "Last day to withdraw from full/late winter courses", "2027-03-15"),
    ("wi27-good-friday",    "Winter 2027", "holiday",      "Good Friday — University closed", "2027-03-26"),
    ("wi27-lastday",        "Winter 2027", "classes",      "Last day of winter classes", "2027-04-09"),
    ("wi27-exams",          "Winter 2027", "exams",        "Winter final exams begin", "2027-04-11"),
    ("wi27-takehome",       "Winter 2027", "exams",        "All take-home exams due", "2027-04-23"),
]

TERMS = tuple(dict.fromkeys(term for _, term, _, _, _ in DEADLINES))


def deadlines_as_dicts() -> list[dict]:
    return [
        {"id": i, "term": t, "category": c, "title": ti, "date": d}
        for (i, t, c, ti, d) in DEADLINES
    ]


def filter_deadlines(
    term: str | None = None,
    categories: set[str] | None = None,
    include_past: bool = False,
) -> list[dict]:
    """Filter by term ("Fall 2026"), categories ({"payment", ...}), and recency.

    include_past=False keeps events from 30 days ago onward, so a fresh
    subscriber isn't flooded with a year of stale entries but recent context
    stays visible in week view.
    """
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    out = []
    for d in deadlines_as_dicts():
        if term and d["term"].lower() != term.lower():
            continue
        if categories and d["category"] not in categories:
            continue
        if not include_past and d["date"] < cutoff:
            continue
        out.append(d)
    return sorted(out, key=lambda d: d["date"])


# ── ICS generation (RFC 5545) ─────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Escape TEXT values per RFC 5545 §3.3.11."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> list[str]:
    """Fold content lines to 75 octets (continuation lines start with a space)."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return [line]
    parts, current = [], ""
    limit = 75
    for ch in line:
        if len((current + ch).encode("utf-8")) > limit:
            parts.append(current)
            current = " " + ch  # leading space marks a continuation
            limit = 74          # continuation lines get 74 usable octets + space
        else:
            current += ch
    parts.append(current)
    return parts


def _next_day(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d").date() + timedelta(days=1)
    return d.isoformat()


def build_ics(deadlines: list[dict], calendar_name: str = CALENDAR_NAME) -> str:
    """Build a VCALENDAR of all-day events with a 2-day-before reminder each.

    UIDs are stable per deadline id, so calendar clients update events in
    place across feed refreshes instead of duplicating them.
    """
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CampusQ//Academic Deadlines//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_esc(calendar_name)}",
        f"X-WR-CALDESC:{_esc(f'{SCHOOL} academic deadlines, kept up to date by CampusQ. Verify at {SOURCE_URL}')}",
        # Hint clients to re-fetch daily (supported by Outlook/Apple; Google polls on its own)
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]
    for d in deadlines:
        start = d["date"].replace("-", "")
        end = _next_day(d["date"]).replace("-", "")
        desc = f"{d['term']} · {d['category']} deadline at {SCHOOL} (via CampusQ). Verify at {SOURCE_URL}"
        alarm = f"Reminder: {d['title']} in 2 days"
        lines += [
            "BEGIN:VEVENT",
            f"UID:campusq-{d['id']}@campusq",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            f"SUMMARY:{_esc(d['title'])}",
            f"DESCRIPTION:{_esc(desc)}",
            f"CATEGORIES:{_esc(d['category'])}",
            "BEGIN:VALARM",
            "TRIGGER:-P2D",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_esc(alarm)}",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(folded for line in lines for folded in _fold(line)) + "\r\n"
