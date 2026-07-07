"""Offline tests for the agent orchestrator — a scripted fake LLM drives the
tool-calling loop. No network, no keys.

Run:  python -m pytest tests/test_agents.py -q
"""

import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import MAX_STEPS, AgentEvent, run_agent
from agents.tools import ToolContext, execute_tool


# ── Fakes ─────────────────────────────────────────────────────────────────────

def _tool_call(call_id, name, args):
    return SimpleNamespace(
        id=call_id, type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args)),
    )


def _turn(content=None, tool_calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=content, tool_calls=tool_calls))])


class ScriptedOpenAI:
    """Returns each queued turn in order; records every request."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        if not self.turns:
            return _turn(content="Fallback final answer.")
        return self.turns.pop(0)


def make_ctx(**overrides):
    defaults = dict(
        search_knowledge=lambda q, f: {
            "context": f"context for: {q}",
            "sources": [{"title": f"Source for {q}", "url": "https://example.edu"}],
        },
        lookup_course=lambda code: {"found": True, "courseCode": code, "credits": 0.5},
        get_degree_plan=lambda slug, variant: {"courses": [{"code": "COMP 1005"}], "edges": []},
        list_programs=lambda: [{"slug": "computer-science", "variants": ["Honours"]}],
    )
    defaults.update(overrides)
    return ToolContext(**defaults)


def events_of(gen):
    return list(gen)


# ── The loop ──────────────────────────────────────────────────────────────────

def test_direct_answer_no_tools():
    llm = ScriptedOpenAI([_turn(content="Reading week starts Feb 16.")])
    events = events_of(run_agent("when is reading week?", [], make_ctx(), llm, "gpt-4o-mini"))
    types = [e.type for e in events]
    assert types == ["token", "done"]
    assert "Feb 16" in events[0].data["content"]


def test_multi_step_decomposition_and_citations():
    """Compare-two-programs: the planner searches twice, then synthesizes."""
    llm = ScriptedOpenAI([
        _turn(tool_calls=[
            _tool_call("c1", "search_knowledge", {"query": "software engineering program", "focus": "program_requirements"}),
            _tool_call("c2", "search_knowledge", {"query": "computer science program", "focus": "program_requirements"}),
        ]),
        _turn(content="SE is a B.Eng; CS is a B.C.S."),
    ])
    events = events_of(run_agent("compare SE and CS", [], make_ctx(), llm, "gpt-4o-mini"))
    types = [e.type for e in events]
    assert types == ["step", "step", "token", "sources", "done"]
    # Sources from BOTH sub-searches are surfaced, deduped
    sources = events[3].data["data"]
    assert len(sources) == 2

    # Tool results were fed back to the model as tool messages
    final_request = llm.requests[-1]
    tool_msgs = [m for m in final_request["messages"] if m.get("role") == "tool"]
    assert len(tool_msgs) == 2
    assert "software engineering" in tool_msgs[0]["content"]


def test_duplicate_tool_calls_served_from_cache():
    calls = []

    def counting_search(q, f):
        calls.append(q)
        return {"context": "ctx", "sources": []}

    llm = ScriptedOpenAI([
        _turn(tool_calls=[_tool_call("c1", "search_knowledge", {"query": "same thing"})]),
        _turn(tool_calls=[_tool_call("c2", "search_knowledge", {"query": "same thing"})]),
        _turn(content="done"),
    ])
    events_of(run_agent("q", [], make_ctx(search_knowledge=counting_search), llm, "m"))
    assert len(calls) == 1   # second identical call never hit the executor


def test_max_steps_forces_final_answer():
    """A model that wants tools forever still terminates: after MAX_STEPS the
    loop withholds tool schemas, so the scripted turns run dry and the fake
    returns a plain answer."""
    looping = [_turn(tool_calls=[_tool_call(f"c{i}", "list_programs", {})])
               for i in range(MAX_STEPS + 3)]
    llm = ScriptedOpenAI(looping)
    events = events_of(run_agent("q", [], make_ctx(), llm, "m"))
    assert events[-1].type == "done"
    assert events[-1].data["steps"] == MAX_STEPS
    forced = llm.requests[-1]
    assert forced["tools"] is None   # tools withheld on the forced-answer turn


def test_model_error_yields_error_event():
    class ExplodingOpenAI:
        def __init__(self):
            def boom(**kwargs):
                raise RuntimeError("api down")
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=boom))

    events = events_of(run_agent("q", [], make_ctx(), ExplodingOpenAI(), "m"))
    assert [e.type for e in events] == ["error"]


# ── Tool execution ────────────────────────────────────────────────────────────

def test_unknown_tool_returns_error_payload_not_exception():
    out = json.loads(execute_tool("rm_rf_slash", {}, make_ctx()))
    assert "Unknown tool" in out["error"]


def test_tool_executor_exception_is_contained():
    def broken(code):
        raise ValueError("db offline")
    out = json.loads(execute_tool("lookup_course", {"course_code": "COMP 1005"},
                                  make_ctx(lookup_course=broken)))
    assert "failed" in out["error"]


def test_oversized_tool_result_is_truncated():
    big = make_ctx(search_knowledge=lambda q, f: {"context": "x" * 50_000, "sources": []})
    out = execute_tool("search_knowledge", {"query": "q"}, big)
    assert len(out) < 7000 and "[truncated]" in out
