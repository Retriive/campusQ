"""Grounding helpers to reduce hallucinations in chat answers.

These controls are intentional product rules:
1. Only inject a prior course code for real course follow-ups
2. Drop off-intent namespaces (e.g. courses on ITS/aid questions)
3. Refuse when retrieved context is missing / wrong-domain / too weak
"""

from __future__ import annotations

import re

COURSE_CODE_RE = re.compile(r"([A-Za-z]{3,4})\s*(\d{4}[A-Za-z]?)")

# Never pull a leftover course code into these questions.
_COURSE_INJECT_BLOCK = (
    "vpn", "wifi", "eduroam", "password", "phone", "contact", "call them",
    "email them", "their number", "service desk", "its ", " its", "loan",
    "bursar", "scholarship", "financial aid", "osap", "quebec", "mycarleton",
    "office 365", "brightspace", "microsoft 365", "payment", "deferral",
)

# Only inject for course-shaped follow-ups.
_COURSE_FOLLOWUP = (
    "prereq", "credit", "taught", "instructor", "professor", "section",
    "offered", "semester", "term", "outline", "syllabus", "who teaches",
    "crn", "waitlist", "when is it", "when is this", "tell me more",
    "more about", "description", "can i take", "without taking",
)

# Intent → namespaces allowed into the model context + citations.
# None means "no hard filter".
INTENT_ALLOWED_NAMESPACES: dict[str, frozenset[str] | None] = {
    "services": frozenset({"services", "registrar", "facts", "tuition"}),
    "deadlines": frozenset({"dates", "registrar", "facts"}),
    "regulations": frozenset({"regulations", "facts", "registrar"}),
    "registration": frozenset({"registrar", "dates", "facts"}),
    "program_requirements": frozenset({"programs", "courses", "regulations", "registrar", "facts"}),
    "prerequisites": frozenset({"courses", "programs", "regulations", "facts"}),
    "course_lookup": frozenset({"courses", "schedule", "programs", "regulations", "facts"}),
    "general": None,
}

NO_CONTEXT_ANSWER = (
    "That's outside of what I currently know. "
    "If you think this should be covered, use the Report a Problem button and we'll add it."
)


def classify_intent(query: str, history: list[dict] | None = None) -> str:
    """Question-intent classifier used for routing, citations, and refusal."""
    q = query.lower()
    hist = " ".join((m.get("content") or "") for m in (history or [])[-6:]).lower()

    if any(k in q for k in (
        "vpn", "wifi", "eduroam", "password", "service desk", "mycarleton",
        "office 365", "microsoft 365", "brightspace login",
    )) or re.search(r"\bits\b", q):
        return "services"
    if any(k in q for k in (
        "phone number", "phone #", "call them", "contact them", "email them",
        "their number", "how can i contact", "how do i contact",
    )):
        if any(k in hist for k in (
            "its", "vpn", "service desk", "awards", "financial aid", "loan",
            "bursar", "scholarship", "osap",
        )):
            return "services"
    if any(k in q for k in ["prerequisite", "prereq", "before taking", "without taking"]):
        return "prerequisites"
    if any(k in q for k in ["deadline", "last day", "when is", "when do", "when does", "what date"]):
        return "deadlines"
    if any(k in q for k in ["cgpa", "gpa", "good standing", "fail", "repeat", "withdraw", "ace ", "academic standing"]):
        return "regulations"
    if "engineering" in q and any(k in q for k in ["how many times", "attempt", "retake", "try again"]):
        return "regulations"
    if any(k in q for k in ["register", "registration", "add a course", "drop", "override", "waitlist", "time ticket"]):
        return "registration"
    if any(k in q for k in ["required courses", "graduate", "degree", "program", "stream", "concentration", "minor", "credits to"]):
        return "program_requirements"
    if any(k in q for k in [
        "co-op", "transcript", "financial aid", "bursary", "scholarship", "defer",
        "enrolment", "loan", "osap", "quebec student", "out of province", "payment deferral",
    ]):
        return "services"
    if re.search(r"[a-zA-Z]{3,4}\s*\d{4}[a-zA-Z]?", query):
        return "course_lookup"
    return "general"


def maybe_inject_course_from_history(user_query: str, past_messages: list[dict]) -> str:
    """Attach last course code only for genuine course follow-ups."""
    if COURSE_CODE_RE.search(user_query):
        return user_query

    q = user_query.lower().strip()
    if any(k in q for k in _COURSE_INJECT_BLOCK):
        return user_query

    courseish = any(k in q for k in _COURSE_FOLLOWUP)
    short_followup = (
        len(q) < 60
        and bool(re.search(r"^(when|where|who|what|is it|does it|can i)\b", q))
        and any(k in q for k in ("it", "this", "that", "course", "class"))
    )
    if not (courseish or short_followup):
        return user_query

    for msg in reversed(past_messages):
        found = COURSE_CODE_RE.search(msg.get("content") or "")
        if found:
            code = f"{found.group(1).upper()} {found.group(2).upper()}"
            return f"{user_query} ({code})"
    return user_query


def filter_matches_for_intent(
    matches_with_ns: list[tuple],
    intent: str,
    user_query: str,
) -> list[tuple]:
    """Drop namespaces that don't belong to this intent."""
    allow = INTENT_ALLOWED_NAMESPACES.get(intent)
    if allow is None:
        # General questions that don't mention a course: prefer non-course evidence.
        if not COURSE_CODE_RE.search(user_query):
            non_course = [(m, ns) for m, ns in matches_with_ns if ns != "courses"]
            if non_course:
                return non_course
        return matches_with_ns

    filtered = [(m, ns) for m, ns in matches_with_ns if ns in allow]
    return filtered


def context_is_weak(
    matches_with_ns: list[tuple],
    context_text: str,
    intent: str,
    threshold: float,
) -> bool:
    """True when we should refuse instead of letting the model guess."""
    if not (context_text or "").strip():
        return True
    if not matches_with_ns:
        # Authoritative prepends (ITS / engineering) may still make context useful.
        return "[Authoritative" not in context_text

    top = matches_with_ns[0][0]
    top_score = getattr(top, "score", 0.0) or 0.0
    if top_score < threshold and "[Authoritative" not in context_text:
        return True

    namespaces = {ns for _, ns in matches_with_ns[:8]}
    if intent == "services" and namespaces and namespaces <= {"courses", "schedule"}:
        return "[Authoritative" not in context_text
    return False
