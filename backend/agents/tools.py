"""Tool definitions and execution for the agent orchestrator.

The orchestrator never imports main.py or Pinecone directly — every
capability is injected as a plain callable on ToolContext. That keeps the
loop fully testable offline (fake callables, no keys) and avoids circular
imports with the FastAPI app.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

MAX_TOOL_RESULT_CHARS = 6000


@dataclass
class ToolContext:
    """Injected capabilities. main.py wires these to real functions;
    tests wire them to fakes."""
    search_knowledge: Callable[[str, str], dict]      # (query, focus) -> {context, sources}
    lookup_course: Callable[[str], dict]              # code -> structured course or {found: False}
    get_degree_plan: Callable[[str, str], dict]       # (slug, variant) -> {courses, edges}
    list_programs: Callable[[], list]                 # -> [{slug, variants}]
    sources_seen: list = field(default_factory=list)  # citations accumulated across calls


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "Semantic search over the university knowledge base (courses, programs, "
                "regulations, registration, dates, tuition, services). Call this multiple "
                "times with DIFFERENT focused queries for multi-part questions — e.g. one "
                "search per program when comparing two programs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A focused search query for ONE sub-question."},
                    "focus": {
                        "type": "string",
                        "enum": ["general", "prerequisites", "deadlines", "regulations",
                                 "registration", "program_requirements", "services", "course_lookup"],
                        "description": "What kind of information this sub-query is after.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_course",
            "description": (
                "Exact course lookup by code (e.g. 'COMP 1005'). Returns authoritative "
                "name, credits, prerequisites, and description. Always prefer this over "
                "search_knowledge when a specific course code is known."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "course_code": {"type": "string", "description": "Course code like 'COMP 1005'."},
                },
                "required": ["course_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_programs",
            "description": "List every program (and its variants) with structured requirement data available.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_degree_plan",
            "description": (
                "Structured degree plan for a program variant: every required course with "
                "credits, plus prerequisite edges. Use for 'what courses do I need', "
                "'am I on track', and program comparison questions. Slugs and variant "
                "names MUST be exact values from list_programs — never guess them; "
                "call list_programs first if you don't have them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Exact program slug from list_programs (e.g. 'computerscience' — no hyphens, no guessing)."},
                    "variant": {"type": "string", "description": "Exact variant name from list_programs, e.g. 'Computer Science B.C.S. Honours (20.0 credits)'."},
                },
                "required": ["slug", "variant"],
            },
        },
    },
]


def execute_tool(name: str, args: dict, ctx: ToolContext) -> str:
    """Run one tool call, return a JSON string result (truncated for token
    safety). Unknown tools and executor errors come back as error payloads
    the model can recover from, never exceptions."""
    try:
        if name == "search_knowledge":
            result = ctx.search_knowledge(args.get("query", ""), args.get("focus", "general"))
            for src in result.get("sources", []):
                if src not in ctx.sources_seen:
                    ctx.sources_seen.append(src)
        elif name == "lookup_course":
            result = ctx.lookup_course(args.get("course_code", ""))
        elif name == "list_programs":
            result = {"programs": ctx.list_programs()}
        elif name == "get_degree_plan":
            result = ctx.get_degree_plan(args.get("slug", ""), args.get("variant", ""))
        else:
            result = {"error": f"Unknown tool '{name}'."}
    except Exception as exc:
        result = {"error": f"Tool '{name}' failed: {exc}"}

    payload = json.dumps(result, ensure_ascii=False, default=str)
    if len(payload) > MAX_TOOL_RESULT_CHARS:
        payload = payload[:MAX_TOOL_RESULT_CHARS] + '... [truncated]"}'
    return payload
