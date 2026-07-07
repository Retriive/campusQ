"""The agent loop: plan → call tools → synthesize a cited answer.

One LLM plays planner and synthesizer via OpenAI function calling. Each
iteration it either requests tool calls (we run them and feed results back)
or produces the final answer. Guards keep cost and latency bounded:

  - MAX_STEPS tool-call rounds, then the model is forced to answer
  - duplicate tool calls (same tool + args) are served from a cache
  - a wall-clock budget stops runaway loops

Yields AgentEvents so the HTTP layer can stream progress ("checking degree
plan…") the same SSE way /api/chat/stream streams tokens. The openai client
is injected, so tests drive the loop with a scripted fake — no keys.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from .tools import TOOL_SCHEMAS, ToolContext, execute_tool

MAX_STEPS = 5
TIME_BUDGET_S = 60

# Human-readable progress labels for the streaming UI
STEP_LABELS = {
    "search_knowledge": "Searching the knowledge base",
    "lookup_course": "Looking up course",
    "list_programs": "Listing programs",
    "get_degree_plan": "Loading degree plan",
}


@dataclass
class AgentEvent:
    type: str    # "step" | "token" | "sources" | "done" | "error"
    data: dict


def _agent_system_prompt(today: str) -> str:
    return f"""You are CampusQ Agent, an AI academic assistant for Carleton University students. Today's date is {today}.

You answer by CALLING TOOLS to gather evidence, then synthesizing. Rules:

1. NEVER answer from memory. Every fact (course codes, credits, dates, requirements, fees) must come from a tool result in this conversation.
2. Decompose multi-part questions: comparing two programs = one get_degree_plan or search_knowledge call PER program. Prerequisite chains = lookup_course per course.
3. Prefer exact tools over search: lookup_course for known codes, get_degree_plan for program requirements.
4. When tool results conflict or are partial, say so — never fill gaps by guessing.
5. RECOVER before giving up: if a tool returns an error, empty result, or "closest_matches"/"valid_variants" hints, fix your arguments and retry (e.g. call list_programs for exact slugs), or fall back to search_knowledge. Only after retries fail may you say information is unavailable.
6. If tools still return nothing useful, say: "That's outside of what I currently know. If you think this should be covered, use the Report a Problem button and we'll add it."
7. Be concise and student-friendly. Use short paragraphs or tight lists, not walls of text.
8. You are independent — not officially affiliated with Carleton University.
9. For questions about academic warning, repeated failure, or graduation risk, recommend the student also speak with an academic advisor.

When you have enough evidence, stop calling tools and write the final answer."""


def run_agent(question: str, history: list[dict], ctx: ToolContext,
              openai_client, model: str, today: str = ""):
    """Generator of AgentEvents. Sync on purpose — FastAPI streams it from a
    thread, and the fake-driven tests iterate it directly."""
    t0 = time.time()
    messages = [{"role": "system", "content": _agent_system_prompt(today)}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    tool_cache: dict[str, str] = {}
    steps = 0

    while True:
        force_answer = steps >= MAX_STEPS or (time.time() - t0) > TIME_BUDGET_S
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=None if force_answer else TOOL_SCHEMAS,
                temperature=0.3,
            )
        except Exception as exc:
            yield AgentEvent("error", {"message": f"Agent model call failed: {exc}"})
            return

        choice = response.choices[0].message
        tool_calls = getattr(choice, "tool_calls", None)

        # On the forced-answer turn the guard is enforced here too — even if
        # the model still asks for tools, we take whatever content it gave.
        if not tool_calls or force_answer:
            answer = choice.content or (
                "I couldn't finish researching that in time — try asking a more "
                "specific question." if force_answer else ""
            )
            yield AgentEvent("token", {"content": answer})
            if ctx.sources_seen:
                yield AgentEvent("sources", {"data": ctx.sources_seen})
            yield AgentEvent("done", {"steps": steps, "ms": int((time.time() - t0) * 1000)})
            return

        # The model asked for tools — run them and loop.
        messages.append({
            "role": "assistant",
            "content": choice.content,
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ],
        })

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {}

            label = STEP_LABELS.get(name, name)
            detail = args.get("query") or args.get("course_code") or args.get("slug") or ""
            yield AgentEvent("step", {"tool": name, "label": label, "detail": str(detail)[:120]})

            cache_key = f"{name}:{json.dumps(args, sort_keys=True)}"
            if cache_key in tool_cache:
                result = tool_cache[cache_key]
            else:
                result = execute_tool(name, args, ctx)
                tool_cache[cache_key] = result

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        steps += 1
