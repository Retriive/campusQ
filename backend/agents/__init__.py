"""Agentic answering: a planner LLM that calls specialist tools in a loop.

Where /api/chat does retrieve-once-then-answer, the agent decomposes the
question, gathers evidence across multiple targeted tool calls (knowledge
search, exact course lookups, structured degree plans, dates), and only then
synthesizes a cited answer. Complex questions — "compare these two programs
and tell me which courses I'd still need" — become several precise lookups
instead of one fuzzy retrieval.

Lives entirely beside the existing chat path: /api/agent/chat is a separate
endpoint, so nothing about today's chatbot changes until you point the
frontend at it.
"""
