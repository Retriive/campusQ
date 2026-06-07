"""
dashboard.py — Aggregation layer for the CampusQ Advisor Dashboard.

Reads the append-only JSON-line logs (queries.log, feedback.log, no_context.log)
and produces anonymized, aggregated weekly insights. No student names, no raw
user IDs — only patterns.

Pure functions only; takes a log_dir so it's import-safe (no circular deps with
main.py). Self-contained intent classifier so it works on older log lines that
predate the stored `intent` field.
"""

import os
import re
import json
from collections import Counter
from datetime import datetime, timedelta


INTENT_LABELS = {
    "prerequisites":        "Prerequisites & Course Requirements",
    "course_lookup":        "Course Lookups",
    "program_requirements": "Program Requirements",
    "deadlines":            "Deadlines & Dates",
    "registration":         "Registration Procedures",
    "regulations":          "Academic Regulations & GPA",
    "services":             "Services & Campus Life",
    "general":              "General / Other",
}


# ── Self-contained classifier (mirror of main.classify_intent) ────────────────
def _classify_intent(query: str) -> str:
    q = (query or "").lower()
    if any(k in q for k in ["prerequisite", "prereq", "before taking", "without taking"]):
        return "prerequisites"
    if any(k in q for k in ["deadline", "last day", "when is", "when do", "when does", "what date"]):
        return "deadlines"
    if any(k in q for k in ["cgpa", "gpa", "good standing", "fail", "repeat", "withdraw", "ace ", "academic standing"]):
        return "regulations"
    if any(k in q for k in ["register", "registration", "add a course", "drop", "override", "waitlist", "time ticket"]):
        return "registration"
    if any(k in q for k in ["required courses", "graduate", "degree", "program", "stream", "concentration", "minor", "credits to"]):
        return "program_requirements"
    if any(k in q for k in ["co-op", "transcript", "financial aid", "bursary", "scholarship", "defer", "enrolment"]):
        return "services"
    if re.search(r'[a-zA-Z]{4}\s*\d{4}', query or ""):
        return "course_lookup"
    return "general"


# ── Log reading ───────────────────────────────────────────────────────────────
def _read_jsonl(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _parse_ts(row: dict) -> datetime | None:
    ts = row.get("ts")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", ""))
    except Exception:
        return None


def _in_window(row: dict, start: datetime, end: datetime) -> bool:
    dt = _parse_ts(row)
    return dt is not None and start <= dt < end


def _intent_of(row: dict) -> str:
    return row.get("intent") or _classify_intent(row.get("query", ""))


# ── Main aggregation ───────────────────────────────────────────────────────────
def build_dashboard_data(log_dir: str, days: int | None = 7) -> dict:
    """
    days=None means all-time. Otherwise the window is the last N days.
    The comparison window is always the same length immediately before.
    """
    now = datetime.utcnow()
    if days is None:
        # All-time: window starts at epoch
        window_start = datetime(2000, 1, 1)
        prev_start = datetime(2000, 1, 1)  # no meaningful comparison
    else:
        window_start = now - timedelta(days=days)
        prev_start = now - timedelta(days=days * 2)

    queries = _read_jsonl(os.path.join(log_dir, "queries.log"))
    feedback = _read_jsonl(os.path.join(log_dir, "feedback.log"))
    no_ctx = _read_jsonl(os.path.join(log_dir, "no_context.log"))

    this_week = [q for q in queries if _in_window(q, window_start, now)]
    last_week = [q for q in queries if _in_window(q, prev_start, window_start)]
    fb_week = [f for f in feedback if _in_window(f, window_start, now)]
    noctx_week = [n for n in no_ctx if _in_window(n, window_start, now)]

    # ── Section 1: snapshot ──
    total = len(this_week)
    answered = sum(1 for q in this_week if q.get("had_context"))
    ups = sum(1 for f in fb_week if f.get("rating") == "up")
    downs = sum(1 for f in fb_week if f.get("rating") == "down")
    accuracy = round(100 * ups / (ups + downs)) if (ups + downs) else None
    dept_counts = Counter(
        q.get("department") for q in this_week
        if q.get("department") and q.get("department") != "general"
    )
    top_department = dept_counts.most_common(1)[0][0] if dept_counts else "—"

    # ── Section 2: what students are asking (by intent) ──
    this_intents = Counter(_intent_of(q) for q in this_week)
    last_intents = Counter(_intent_of(q) for q in last_week)

    intent_rows = []
    for intent, count in this_intents.most_common(10):
        # most common verbatim question within this intent
        examples = Counter(
            q.get("query", "").strip()
            for q in this_week
            if _intent_of(q) == intent and q.get("query")
        )
        example = examples.most_common(1)[0][0] if examples else ""
        prev = last_intents.get(intent, 0)
        trend = "flat" if count == prev else ("up" if count > prev else "down")
        intent_rows.append({
            "intent": intent,
            "label": INTENT_LABELS.get(intent, intent.replace("_", " ").title()),
            "count": count,
            "example": example[:160],
            "trend": trend,
            "prev_count": prev,
        })

    # ── Section 3a: unanswered questions, grouped by theme (intent) ──
    # Prefer no_context.log; also include this-week queries with had_context False.
    unanswered_queries = [n.get("query", "") for n in noctx_week if n.get("query")]
    unanswered_queries += [q.get("query", "") for q in this_week if not q.get("had_context") and q.get("query")]
    unanswered_groups: dict[str, list[str]] = {}
    for uq in unanswered_queries:
        g = INTENT_LABELS.get(_classify_intent(uq), "General / Other")
        unanswered_groups.setdefault(g, [])
        if uq.strip() not in unanswered_groups[g]:
            unanswered_groups[g].append(uq.strip()[:160])
    unanswered = [
        {"theme": theme, "count": len(qs), "examples": qs[:5]}
        for theme, qs in sorted(unanswered_groups.items(), key=lambda kv: -len(kv[1]))
    ]

    # ── Section 3c: top 5 verbatim questions ──
    # Filter out junk (< 6 chars, no spaces for single-word gibberish)
    JUNK_RE = re.compile(r'^[a-z]{1,5}$|^[^a-zA-Z]+$', re.IGNORECASE)
    real_queries = [
        q.get("query", "").strip()
        for q in this_week
        if q.get("query") and len(q.get("query", "").strip()) >= 8
        and not JUNK_RE.match(q.get("query", "").strip())
        and q.get("had_context")
    ]
    top_questions_counter = Counter(real_queries)
    top_questions = [
        {"question": q[:200], "count": c}
        for q, c in top_questions_counter.most_common(5)
    ]

    # ── Section 3b: negative feedback ──
    negative = [
        {
            "question": (f.get("question") or "").strip()[:200],
            "answer": (f.get("answer") or "").strip()[:300],
            "department": f.get("department", "—"),
        }
        for f in fb_week if f.get("rating") == "down"
    ][:20]

    # ── Section 4: retention ──────────────────────────────────────────────────
    # Only count real users (exclude anonymous)
    all_queries_with_users = [q for q in queries if q.get("user") and q["user"] != "anonymous"]

    # Group query dates by user
    from collections import defaultdict
    user_days: dict[str, set[str]] = defaultdict(set)
    user_sessions: dict[str, set[str]] = defaultdict(set)
    for q in all_queries_with_users:
        dt = _parse_ts(q)
        if dt:
            user_days[q["user"]].add(dt.strftime("%Y-%m-%d"))
        if q.get("session"):
            user_sessions[q["user"]].add(q["session"])

    # Day-1 → Day-2 retention: users who came back on a second distinct day
    total_users = len(user_days)
    returned_users = sum(1 for days in user_days.values() if len(days) >= 2)
    day1_retention = round(100 * returned_users / total_users) if total_users else None

    # Sessions per user
    session_counts = [len(s) for s in user_sessions.values()]
    avg_sessions = round(sum(session_counts) / len(session_counts), 1) if session_counts else 0

    # Daily usage trend — use the selected window (this_week queries)
    daily_counts: dict[str, int] = Counter()
    for q in this_week:
        dt = _parse_ts(q)
        if dt:
            daily_counts[dt.strftime("%Y-%m-%d")] += 1
    daily_trend = [
        {"date": d, "queries": daily_counts.get(d, 0)}
        for d in sorted(daily_counts.keys())
    ]

    return {
        "generated_at": now.isoformat(),
        "days": days,
        "window_start": window_start.isoformat(),
        "snapshot": {
            "total_questions": total,
            "accuracy": accuracy,           # null if no feedback yet
            "thumbs_up": ups,
            "thumbs_down": downs,
            "top_department": top_department,
        },
        "daily_trend": daily_trend,
        "retention": {
            "total_users": total_users,
            "returned_day2": returned_users,
            "day1_retention_pct": day1_retention,
            "avg_sessions_per_user": avg_sessions,
        },
        "intents": intent_rows,
        "top_questions": top_questions,
        "unanswered": unanswered,
        "negative_feedback": negative,
    }


# ── Plain-text weekly digest (reused by the email script) ─────────────────────
def build_digest_text(log_dir: str) -> str:
    d = build_dashboard_data(log_dir)
    s = d["snapshot"]
    lines = []
    lines.append("CampusQ — Weekly Advisor Digest")
    lines.append("=" * 40)
    lines.append("")
    lines.append(f"Questions answered last week : {s['total_questions']}")
    acc = f"{s['accuracy']}%" if s["accuracy"] is not None else "no ratings yet"
    lines.append(f"Helpfulness (thumbs up rate) : {acc}")
    lines.append(f"Estimated advisor deflections: {s['deflections']}")
    lines.append(f"Busiest department           : {s['top_department']}")
    lines.append("")
    lines.append("Top categories:")
    for r in d["intents"][:3]:
        arrow = {"up": "^", "down": "v", "flat": "="}[r["trend"]]
        lines.append(f"  {arrow} {r['label']} — {r['count']}")
    lines.append("")
    total_unanswered = sum(g["count"] for g in d["unanswered"])
    lines.append(f"Questions CampusQ couldn't answer: {total_unanswered}")
    for g in d["unanswered"][:5]:
        lines.append(f"  [{g['theme']}] ({g['count']})")
        for ex in g["examples"][:2]:
            lines.append(f"      - {ex}")
    lines.append("")
    lines.append(f"Negative feedback responses: {len(d['negative_feedback'])}")
    lines.append("")
    lines.append("— CampusQ (anonymized, aggregate data only)")
    return "\n".join(lines)
