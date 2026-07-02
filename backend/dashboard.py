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

# Synthetic test traffic (eval harness) — excluded from the internal team brief
EVAL_SESSIONS = frozenset({"quality-gate"})


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


def _is_excluded(row: dict, exclude: frozenset[str] | None) -> bool:
    """True if a log row is synthetic test traffic (eval harness) we should drop."""
    return bool(exclude) and (row.get("session") in exclude or row.get("user") in exclude)


# ── Main aggregation ───────────────────────────────────────────────────────────
def build_dashboard_data(log_dir: str, days: int | None = 7,
                         exclude_sessions: frozenset[str] | None = None) -> dict:
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

    if exclude_sessions:
        queries = [q for q in queries if not _is_excluded(q, exclude_sessions)]
        feedback = [f for f in feedback if not _is_excluded(f, exclude_sessions)]
        no_ctx = [n for n in no_ctx if not _is_excluded(n, exclude_sessions)]

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
    response_times = [q["ms"] for q in this_week if isinstance(q.get("ms"), (int, float))]
    avg_response_ms = round(sum(response_times) / len(response_times)) if response_times else None
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

    # Hourly usage — what hour of day do students ask questions?
    hourly_counts: dict[int, int] = Counter()
    for q in this_week:
        dt = _parse_ts(q)
        if dt:
            hourly_counts[dt.hour] += 1
    hourly_trend = [
        {"hour": h, "queries": hourly_counts.get(h, 0)}
        for h in range(24)
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
            "avg_response_ms": avg_response_ms,   # null if no queries yet
        },
        "hourly_trend": hourly_trend,
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


# ── Waitlist signups (multi-university landing pages) ─────────────────────────
def build_waitlist_data(log_dir: str, days: int | None = 30) -> dict:
    """days=None means all-time."""
    now = datetime.utcnow()
    window_start = datetime(2000, 1, 1) if days is None else now - timedelta(days=days)

    rows = _read_jsonl(os.path.join(log_dir, "waitlist.log"))
    in_window = [r for r in rows if _in_window(r, window_start, now)]

    by_school = Counter(r.get("school", "unknown") for r in in_window)
    school_rows = [
        {"school": school, "count": count}
        for school, count in by_school.most_common()
    ]

    recent = sorted(in_window, key=lambda r: r.get("ts", ""), reverse=True)[:50]
    recent_rows = [
        {"email": r.get("email", ""), "school": r.get("school", ""), "ts": r.get("ts", "")}
        for r in recent
    ]

    return {
        "generated_at": now.isoformat(),
        "total": len(in_window),
        "by_school": school_rows,
        "recent": recent_rows,
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
    resp = f"{s['avg_response_ms']} ms" if s["avg_response_ms"] is not None else "no data yet"
    lines.append(f"Average response time        : {resp}")
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


# ── Internal weekly team brief (the founder pulse) ────────────────────────────
def build_team_brief(log_dir: str) -> str:
    """
    Internal weekly brief emailed to the team (Monday morning).

    Unlike build_digest_text (the external, anonymized ADVISOR digest), this is
    for running the company: usage, growth, retention, quality, and what needs
    attention. 7-day window, compared to the week before. Plain-text email body.
    """
    d = build_dashboard_data(log_dir, days=7, exclude_sessions=EVAL_SESSIONS)
    s = d["snapshot"]
    r = d["retention"]

    # Week-over-week question volume
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)
    queries = [q for q in _read_jsonl(os.path.join(log_dir, "queries.log"))
               if not _is_excluded(q, EVAL_SESSIONS)]
    this_week = sum(1 for q in queries if _in_window(q, week_start, now))
    last_week = sum(1 for q in queries if _in_window(q, prev_start, week_start))
    if last_week:
        delta = round(100 * (this_week - last_week) / last_week)
        trend = f"({'+' if delta >= 0 else ''}{delta}% vs prior week)"
    else:
        trend = "(first week of data)"

    # Waitlist: all-time total + new in the last 7 days
    wl_all = build_waitlist_data(log_dir, days=None)
    wl_week = build_waitlist_data(log_dir, days=7)

    L = []
    L.append("CampusQ - Weekly Team Brief")
    L.append(now.strftime("Week of %A, %B %d, %Y"))
    L.append("=" * 44)
    L.append("")

    L.append("USAGE (last 7 days)")
    L.append(f"  Questions asked   : {this_week} {trend}")
    acc = f"{s['accuracy']}% helpful" if s["accuracy"] is not None else "no ratings yet"
    L.append(f"  Helpfulness       : {acc}  ({s['thumbs_up']} up / {s['thumbs_down']} down)")
    resp = f"{s['avg_response_ms']} ms" if s["avg_response_ms"] is not None else "no data yet"
    L.append(f"  Avg response time : {resp}")
    L.append(f"  Busiest area      : {s['top_department']}")
    L.append("")

    L.append("USERS (all-time)")
    ret = f"{r['day1_retention_pct']}% returned" if r["day1_retention_pct"] is not None else "n/a"
    L.append(f"  Total users       : {r['total_users']}")
    L.append(f"  Came back (2nd day): {r['returned_day2']}  ({ret})")
    L.append(f"  Avg sessions/user : {r['avg_sessions_per_user']}")
    L.append("")

    L.append("GROWTH - Waitlist")
    L.append(f"  Total signups     : {wl_all['total']}  (+{wl_week['total']} this week)")
    for row in wl_all["by_school"][:6]:
        L.append(f"     {row['school']}: {row['count']}")
    if not wl_all["by_school"]:
        L.append("     (no signups logged yet)")
    L.append("")

    L.append("WHAT STUDENTS ASKED")
    if d["top_questions"]:
        for row in d["top_questions"][:3]:
            L.append(f"  - \"{row['question']}\" (x{row['count']})")
    else:
        L.append("  (no answered questions this week)")
    L.append("")

    L.append("NEEDS ATTENTION")
    total_unanswered = sum(g["count"] for g in d["unanswered"])
    L.append(f"  Couldn't answer   : {total_unanswered}  -> roadmap candidates")
    for g in d["unanswered"][:3]:
        L.append(f"     [{g['theme']}] ({g['count']})")
    L.append(f"  Thumbs-down       : {len(d['negative_feedback'])}")
    L.append("")

    L.append("-- CampusQ internal brief - tell me what to add or cut")
    return "\n".join(L)


# ── HTML version of the team brief (purple + black dashboard email) ────────────
def build_team_brief_html(log_dir: str) -> str:
    """
    Rich HTML email version of build_team_brief — a dashboard-style digest with
    big headline stats and a plain-English explanation under each section.
    Inline styles only (email clients strip <style>/<head> CSS). 600px, dark theme.
    """
    C = {
        "bg": "#08080b", "card": "#15121d", "border": "#2c2540",
        "purple": "#b072f5", "purple2": "#7c3aed",
        "text": "#f2eef9", "muted": "#9b93ac",
        "good": "#4ade80", "bad": "#fb7185", "amber": "#fbbf24",
    }
    FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

    d = build_dashboard_data(log_dir, days=7, exclude_sessions=EVAL_SESSIONS)
    s = d["snapshot"]
    r = d["retention"]

    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)
    queries = [q for q in _read_jsonl(os.path.join(log_dir, "queries.log"))
               if not _is_excluded(q, EVAL_SESSIONS)]
    this_week_q = [q for q in queries if _in_window(q, week_start, now)]
    this_week = len(this_week_q)
    last_week = sum(1 for q in queries if _in_window(q, prev_start, week_start))
    active = len({q.get("user") for q in this_week_q
                  if q.get("user") and q.get("user") != "anonymous"})

    wl_all = build_waitlist_data(log_dir, days=None)
    wl_week = build_waitlist_data(log_dir, days=7)

    # Week-over-week trend pill
    if last_week:
        delta = round(100 * (this_week - last_week) / last_week)
        if delta > 0:
            trend = f'<span style="color:{C["good"]};">&#9650; {delta}%</span> vs last week'
        elif delta < 0:
            trend = f'<span style="color:{C["bad"]};">&#9660; {abs(delta)}%</span> vs last week'
        else:
            trend = "flat vs last week"
    else:
        trend = "first week of data"

    def hero(value, label):
        return (
            f'<td align="center" width="33%" style="padding:4px 4px;font-family:{FONT};">'
            f'<div style="font-size:36px;line-height:1;font-weight:800;color:{C["text"]};">{value}</div>'
            f'<div style="margin-top:7px;font-size:11px;font-weight:600;letter-spacing:.8px;'
            f'text-transform:uppercase;color:{C["muted"]};">{label}</div></td>'
        )

    def section(title, inner, note):
        return (
            f'<tr><td style="padding:7px 24px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" role="presentation" '
            f'style="background:{C["card"]};border:1px solid {C["border"]};border-radius:14px;">'
            f'<tr><td style="padding:18px 20px 15px;font-family:{FONT};">'
            f'<div style="font-size:12px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;'
            f'color:{C["purple"]};margin-bottom:12px;">{title}</div>{inner}'
            f'<div style="margin-top:14px;padding-top:11px;border-top:1px solid {C["border"]};'
            f'font-size:12px;line-height:1.55;color:{C["muted"]};">{note}</div>'
            f'</td></tr></table></td></tr>'
        )

    def kv(label, value):
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" role="presentation"><tr>'
            f'<td style="font-size:14px;color:{C["muted"]};padding:5px 0;font-family:{FONT};">{label}</td>'
            f'<td align="right" style="font-size:15px;color:{C["text"]};font-weight:600;'
            f'padding:5px 0;font-family:{FONT};">{value}</td></tr></table>'
        )

    # ── Usage ──
    acc = f'{s["accuracy"]}% helpful' if s["accuracy"] is not None else "no ratings yet"
    resp = f'{s["avg_response_ms"]} ms' if s["avg_response_ms"] is not None else "no data yet"
    usage = (
        kv("Questions asked (7d)", f'{this_week} &nbsp;<span style="font-size:12px;color:{C["muted"]};font-weight:400;">{trend}</span>')
        + kv("Helpfulness", f'{acc} <span style="color:{C["muted"]};font-weight:400;">({s["thumbs_up"]}&#128077; / {s["thumbs_down"]}&#128078;)</span>')
        + kv("Avg response time", resp)
        + kv("Busiest area", s["top_department"] if s["top_department"] != "—" else "not enough data yet")
    )

    # ── Users / retention ──
    ret = f'{r["day1_retention_pct"]}% came back' if r["day1_retention_pct"] is not None else "n/a"
    users = (
        kv("Total users (all-time)", r["total_users"])
        + kv("Returned a 2nd day", f'{r["returned_day2"]} <span style="color:{C["muted"]};font-weight:400;">({ret})</span>')
        + kv("Avg sessions / user", r["avg_sessions_per_user"])
    )

    # ── Waitlist (with mini bars) ──
    if wl_all["by_school"]:
        top = max(row["count"] for row in wl_all["by_school"]) or 1
        bars = ""
        for row in wl_all["by_school"][:6]:
            pct = int(100 * row["count"] / top)
            bars += (
                f'<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin:6px 0;"><tr>'
                f'<td width="90" style="font-size:13px;color:{C["text"]};font-family:{FONT};">{row["school"]}</td>'
                f'<td><div style="background:{C["border"]};border-radius:6px;height:9px;">'
                f'<div style="background:{C["purple"]};width:{pct}%;height:9px;border-radius:6px;"></div></div></td>'
                f'<td width="34" align="right" style="font-size:13px;color:{C["text"]};font-weight:600;font-family:{FONT};">{row["count"]}</td>'
                f'</tr></table>'
            )
    else:
        bars = f'<div style="font-size:14px;color:{C["muted"]};font-family:{FONT};">No signups logged yet.</div>'
    growth = (
        kv("Total signups", f'{wl_all["total"]} <span style="color:{C["good"]};font-weight:600;">+{wl_week["total"]} this week</span>')
        + f'<div style="margin-top:8px;">{bars}</div>'
    )

    # ── What students asked ──
    if d["top_questions"]:
        asked = ""
        for row in d["top_questions"][:5]:
            asked += (
                f'<div style="font-size:14px;color:{C["text"]};line-height:1.5;padding:6px 0;'
                f'border-bottom:1px solid {C["border"]};font-family:{FONT};">'
                f'&ldquo;{row["question"]}&rdquo; '
                f'<span style="color:{C["purple"]};font-weight:600;">&times;{row["count"]}</span></div>'
            )
    else:
        asked = f'<div style="font-size:14px;color:{C["muted"]};font-family:{FONT};">No answered questions yet this week.</div>'

    # ── Needs attention ──
    total_unanswered = sum(g["count"] for g in d["unanswered"])
    chips = ""
    for g in d["unanswered"][:4]:
        chips += (
            f'<span style="display:inline-block;background:{C["bg"]};border:1px solid {C["border"]};'
            f'border-radius:20px;padding:4px 11px;margin:3px 4px 3px 0;font-size:12px;'
            f'color:{C["text"]};font-family:{FONT};">{g["theme"]} &middot; {g["count"]}</span>'
        )
    attention = (
        kv("Couldn&#39;t answer", f'<span style="color:{C["amber"]};">{total_unanswered}</span> &rarr; roadmap candidates')
        + kv("Thumbs-down", f'<span style="color:{C["bad"] if d["negative_feedback"] else C["text"]};">{len(d["negative_feedback"])}</span>')
        + (f'<div style="margin-top:8px;">{chips}</div>' if chips else "")
    )

    dash_url = os.getenv("DASHBOARD_URL", "").strip()
    cta = ""
    if dash_url:
        cta = (
            f'<tr><td align="center" style="padding:10px 24px 4px;">'
            f'<a href="{dash_url}" style="display:inline-block;background:{C["purple2"]};color:#fff;'
            f'text-decoration:none;font-weight:600;font-size:14px;padding:11px 22px;border-radius:10px;'
            f'font-family:{FONT};">Open the full dashboard &rarr;</a></td></tr>'
        )

    week_label = now.strftime("Week of %A, %B %d, %Y")

    return f"""\
<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{C['bg']};">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:{C['bg']};padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" role="presentation" style="max-width:600px;width:100%;">

  <tr><td style="padding:8px 24px 0;font-family:{FONT};">
    <table width="100%" cellpadding="0" cellspacing="0" role="presentation"><tr>
      <td style="font-size:19px;font-weight:800;color:{C['text']};letter-spacing:-.3px;">
        <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{C['purple']};margin-right:8px;"></span>CampusQ</td>
      <td align="right" style="font-size:12px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:{C['muted']};">Weekly Team Brief</td>
    </tr></table>
    <div style="margin-top:16px;font-size:24px;font-weight:800;color:{C['text']};">{week_label}</div>
    <div style="margin-top:4px;font-size:13px;color:{C['muted']};">Real student activity &middot; test traffic excluded</div>
    <div style="margin-top:16px;height:3px;border-radius:3px;background:linear-gradient(90deg,{C['purple']},{C['purple2']});"></div>
  </td></tr>

  <tr><td style="padding:16px 24px 4px;">
    <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:{C['card']};border:1px solid {C['border']};border-radius:14px;">
      <tr style="padding:18px 0;">{hero(this_week, "Questions (7d)")}{hero(active, "Active students")}{hero(wl_all['total'], "Waitlist")}</tr>
    </table>
  </td></tr>

  {section("Usage", usage, "How much CampusQ is used and whether answers land. Helpfulness is the thumbs up/down rate students give in the chat.")}
  {section("Users &amp; retention", users, "Whether students come back &mdash; the truest signal of value. &ldquo;Returned a 2nd day&rdquo; is our core retention metric.")}
  {section("Growth &mdash; waitlist", growth, "Demand for schools we haven&#39;t launched yet. This ranks our expansion order &mdash; we should open the school with the most pull next.")}
  {section("What students asked", asked, "The most common real questions this week. Patterns here tell us what to make faster and more accurate.")}
  {section("Needs attention", attention, "Gaps to close. Unanswered questions become scraping/roadmap targets; thumbs-down are answers to review.")}
  {cta}

  <tr><td style="padding:18px 24px 8px;font-family:{FONT};text-align:center;">
    <div style="font-size:12px;color:{C['muted']};line-height:1.6;">
      CampusQ internal brief &middot; sent every Monday<br>
      Reply to this email to change what&#39;s in it.</div>
  </td></tr>

</table></td></tr></table></body></html>"""
