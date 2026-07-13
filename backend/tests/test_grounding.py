"""Tests for hallucination grounding controls."""

from grounding import (
    classify_intent,
    maybe_inject_course_from_history,
    filter_matches_for_intent,
    context_is_weak,
    prepend_its_contact_context,
    is_its_contact_query,
)


class FakeMatch:
    def __init__(self, score: float, text: str = "x"):
        self.score = score
        self.metadata = {"text": text}


def test_vpn_query_does_not_inject_course_from_history():
    history = [{"role": "assistant", "content": "COMP 3000 covers operating systems."}]
    q = "What should I do if I am a new student who needs VPN for one of my classes?"
    assert "COMP 3000" not in maybe_inject_course_from_history(q, history)


def test_course_followup_still_injects():
    history = [{"role": "user", "content": "Tell me about COMP 2402"}]
    out = maybe_inject_course_from_history("What are the prereqs?", history)
    assert "COMP 2402" in out


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


def test_its_contact_context_prefetched_for_phone_followup():
    history = [{"role": "assistant", "content": "Ask ITS about VPN access."}]
    assert is_its_contact_query("What's their phone number", history)
    out = prepend_its_contact_context("", "What's their phone number", history)
    assert "613-520-3700" in out
