"""Bounded sanitization for client-controlled chat history.

Keeps system-role injection and unbounded context growth out of the model prompt.
"""

from __future__ import annotations

import json

MAX_HISTORY_MESSAGES = 20
MAX_MESSAGE_CHARS = 4_000
_ALLOWED_HISTORY_ROLES = {"user", "assistant"}


def sanitize_history(history_json: str) -> list[dict]:
    """Parse client-supplied chat history into a bounded, role-whitelisted list.

    The client controls this field entirely, so: only user/assistant roles
    survive (nothing can inject extra system messages), each message is
    length-capped, and only the most recent MAX_HISTORY_MESSAGES are kept —
    which also stops unbounded token growth on long conversations.
    """
    try:
        raw = json.loads(history_json)
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    cleaned: list[dict] = []
    for msg in raw:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role not in _ALLOWED_HISTORY_ROLES or not isinstance(content, str):
            continue
        cleaned.append({"role": role, "content": content[:MAX_MESSAGE_CHARS]})
    return cleaned[-MAX_HISTORY_MESSAGES:]
