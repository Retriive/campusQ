"""Signed-in user data store — SQLite on the same persistent disk as logs.

Holds opt-in cloud chat history so students get a real reason to create an
account (cross-device sync). Guests keep device-local storage only.

Safe defaults: empty store returns empty payload; writes are size-capped.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_chats (
    user_id     TEXT PRIMARY KEY,
    payload     TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

_write_lock = threading.Lock()

# Soft caps — keep renders cheap and discourage dumping huge local histories.
MAX_SESSIONS = 20
MAX_MESSAGES_PER_SESSION = 40
MAX_CONTENT_CHARS = 4000
MAX_PAYLOAD_BYTES = 750_000


def default_db_path() -> str:
    base = "/data" if os.path.isdir("/data") else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "user_data.db")


def _empty_payload() -> dict:
    return {"sessions": [], "messagesBySession": {}, "updatedAt": 0}


def sanitize_chat_payload(raw) -> dict:
    """Normalize and bound a client payload. Raises ValueError on unusable input."""
    if not isinstance(raw, dict):
        raise ValueError("payload must be an object")

    sessions_in = raw.get("sessions") or []
    messages_in = raw.get("messagesBySession") or {}
    if not isinstance(sessions_in, list) or not isinstance(messages_in, dict):
        raise ValueError("invalid sessions shape")

    sessions: list[dict] = []
    seen_ids: set[str] = set()
    for item in sessions_in[:MAX_SESSIONS]:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("id", "")).strip()[:80]
        if not sid or sid in seen_ids:
            continue
        seen_ids.add(sid)
        title = str(item.get("title", "Chat")).strip()[:120] or "Chat"
        try:
            created = int(item.get("createdAt") or 0)
        except (TypeError, ValueError):
            created = 0
        sessions.append({"id": sid, "title": title, "createdAt": created})

    messages_by_session: dict[str, list] = {}
    for sid, msgs in messages_in.items():
        key = str(sid).strip()[:80]
        if not key or key not in seen_ids or not isinstance(msgs, list):
            continue
        cleaned = []
        for msg in msgs[-MAX_MESSAGES_PER_SESSION:]:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            if role not in ("user", "assistant"):
                continue
            content = str(msg.get("content") or "")[:MAX_CONTENT_CHARS]
            out = {
                "id": str(msg.get("id") or "")[:80] or f"{key}-{len(cleaned)}",
                "role": role,
                "content": content,
            }
            # Keep small structured fields when present; drop anything oversized later via payload cap.
            cards = msg.get("courseCards")
            if isinstance(cards, list) and cards:
                out["courseCards"] = cards[:12]
            sources = msg.get("sources")
            if isinstance(sources, list) and sources:
                out["sources"] = sources[:8]
            cleaned.append(out)
        messages_by_session[key] = cleaned

    try:
        updated_at = int(raw.get("updatedAt") or 0)
    except (TypeError, ValueError):
        updated_at = 0

    payload = {
        "sessions": sessions,
        "messagesBySession": messages_by_session,
        "updatedAt": updated_at,
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("payload too large")
    return payload


class UserStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or default_db_path()
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with self._conn() as con:
            con.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def get_chats(self, user_id: str) -> dict:
        with self._conn() as con:
            row = con.execute(
                "SELECT payload FROM user_chats WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return _empty_payload()
        try:
            data = json.loads(row["payload"])
            return sanitize_chat_payload(data)
        except Exception:
            return _empty_payload()

    def put_chats(self, user_id: str, payload: dict) -> dict:
        cleaned = sanitize_chat_payload(payload)
        if not cleaned.get("updatedAt"):
            cleaned["updatedAt"] = int(datetime.now(timezone.utc).timestamp() * 1000)
        encoded = json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
        now = datetime.now(timezone.utc).isoformat()
        with _write_lock, self._conn() as con:
            con.execute(
                """INSERT INTO user_chats (user_id, payload, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                     payload = excluded.payload,
                     updated_at = excluded.updated_at""",
                (user_id, encoded, now),
            )
        return cleaned

    def delete_chats(self, user_id: str) -> None:
        with _write_lock, self._conn() as con:
            con.execute("DELETE FROM user_chats WHERE user_id = ?", (user_id,))
