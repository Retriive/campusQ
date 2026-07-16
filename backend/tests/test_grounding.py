"""Tests for hallucination grounding controls."""

from grounding import (
    classify_intent,
    is_followup_query,
    filter_matches_for_intent,
    context_is_weak,
)


class FakeMatch:
    def __init__(self, score: float, text: str = "x"):
        self.score = score
        self.metadata = {"text": text}


# ── General follow-up detection ─────────────────────────────────────────────
# The whole point: ONE detector works across every topic, so we never add a
# per-subject injector again. These cases span courses, library, and financial
# aid without any topic-specific code.

def test_followup_detected_across_unrelated_topics():
    hist = [{"role": "assistant", "content": "..."}]
    # course follow-up (anaphora)
    assert is_followup_query("what are the prereqs for it?", hist) is True
    # library follow-up (the #84 failure case — a leading follow-up phrase)
    assert is_followup_query("what if I want loud noise?", hist) is True
    # financial-aid follow-up (terse fragment) — no aid-specific code exists
    assert is_followup_query("what about part-time students?", hist) is True
    # residence follow-up (anaphora) — again, no residence-specific code
    assert is_followup_query("is that one cheaper?", hist) is True


def test_selfcontained_and_no_history_are_not_followups():
    hist = [{"role": "assistant", "content": "..."}]
    # Carries its own course code → standalone.
    assert is_followup_query("what are the prerequisites for COMP 2402?", hist) is False
    # A full, self-contained question.
    assert is_followup_query(
        "How do I apply for OSAP as an Ontario student this fall?", hist
    ) is False
    # First turn: nothing to depend on.
    assert is_followup_query("what if I want loud noise?", None) is False
    assert is_followup_query("what about it?", []) is False


def test_phone_followup_classified_as_services_from_history():
    history = [{"role": "assistant", "content": "Contact Carleton ITS Service Desk for VPN setup."}]
    assert classify_intent("What's their phone number", history) == "services"


def test_filter_drops_courses_for_services_intent():
    matches = [
        (FakeMatch(0.9), "courses"),
        (FakeMatch(0.8), "services"),
        (FakeMatch(0.7), "facts"),
    ]
    filtered = filter_matches_for_intent(matches, "services", "quebec student loan deferral")
    assert all(ns != "courses" for _, ns in filtered)
    assert {ns for _, ns in filtered} == {"services", "facts"}


def test_weak_context_when_services_only_has_courses():
    matches = [(FakeMatch(0.4), "courses")]
    assert context_is_weak(matches, "course junk", "services", threshold=0.25) is True


def test_services_filter_keeps_library():
    """Library is campus-services content; the services intent must not drop it."""
    matches = [
        (FakeMatch(0.9), "library"),
        (FakeMatch(0.8), "services"),
        (FakeMatch(0.7), "courses"),
    ]
    filtered = filter_matches_for_intent(matches, "services", "library study rooms")
    assert {ns for _, ns in filtered} == {"library", "services"}


# ── Small talk ───────────────────────────────────────────────────────────────
# Greetings retrieve nothing, so before smalltalk_answer() they hit the
# no-context refusal — "hi" answered with "that's outside of what I know".

def test_greetings_get_friendly_answer_not_refusal():
    from grounding import smalltalk_answer, NO_CONTEXT_ANSWER
    for q in ["hi", "Hello!", "hey there", "good morning", "salam", "whats up", "yo"]:
        answer = smalltalk_answer(q)
        assert answer is not None, f"{q!r} should be small talk"
        assert answer != NO_CONTEXT_ANSWER
        assert "CampusQ" in answer


def test_capability_questions_get_answer():
    from grounding import smalltalk_answer
    for q in ["what do u do", "What can you do?", "who are you", "help"]:
        assert smalltalk_answer(q) is not None, f"{q!r} should be small talk"


def test_thanks_get_answer():
    from grounding import smalltalk_answer
    assert smalltalk_answer("thanks!") is not None
    assert smalltalk_answer("thank you so much") is not None


def test_real_questions_are_not_smalltalk():
    from grounding import smalltalk_answer
    # Greeting glued to a real question must still go through retrieval.
    assert smalltalk_answer("hi, when is the last day to withdraw?") is None
    assert smalltalk_answer("what are the prereqs for COMP 2402?") is None
    assert smalltalk_answer("when do fall exams start") is None
    assert smalltalk_answer("What do you do if you fail a course?") is None
    assert smalltalk_answer("") is None
