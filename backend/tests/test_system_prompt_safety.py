"""Source-level checks that CampusQ safety guardrails stay in the system prompt.

Imports of main.py need live API keys (OpenAI/Pinecone), so these tests assert
on the builder source instead of calling build_system_prompt() directly.
"""

from pathlib import Path

MAIN_PY = Path(__file__).resolve().parents[1] / "main.py"


def _builder_source() -> str:
    text = MAIN_PY.read_text(encoding="utf-8")
    start = text.index("def build_system_prompt(")
    end = text.index("\n@app.get(\"/\")", start)
    return text[start:end]


def test_build_system_prompt_includes_numbered_safety_rules():
    src = _builder_source()
    for needle in (
        "11. PROMPT SAFETY:",
        "12. ACADEMIC INTEGRITY:",
        "13. OFF-TOPIC REDIRECT:",
        "14. CRISIS / SELF-HARM:",
        "15. MEDICAL / LEGAL ADVICE:",
    ):
        assert needle in src, f"missing safety rule: {needle}"


def test_crisis_rule_points_to_known_resources():
    src = _builder_source()
    assert "Good2Talk" in src
    assert "988" in src
    assert "Health and Counselling" in src


def test_integrity_rule_refuses_assessed_work():
    src = _builder_source()
    assert "assessed work" in src
    assert "Refuse" in src


def test_prompt_safety_still_exempts_who_teaches_questions():
    """Regression guard for smoke-06 vs core-13 conflict."""
    src = _builder_source()
    assert "who teaches X?" in src
    assert "RateMyProfessors" in src
