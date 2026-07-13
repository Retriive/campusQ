"""Daily guest chat quota.

Guests get a small free allowance so they can try CampusQ, then we push them
to sign up. Signed-in users skip this path entirely (see chat routes).

Keyed by a client-generated guest id (localStorage UUID). Shared campus Wi‑Fi
won't burn one shared IP bucket for every student. Clearing site data resets
the guest id — soft freemium, not bank vault security.
"""

from __future__ import annotations

import os
import re
import sqlite3
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

GUEST_DAILY_LIMIT = int(os.getenv("GUEST_DAILY_LIMIT", "10"))
GUEST_QUOTA_TZ = ZoneInfo(os.getenv("GUEST_QUOTA_TZ", "America/Toronto"))

_GUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guest_usage (
    guest_id  TEXT NOT NULL,
    day       TEXT NOT NULL,
    count     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guest_id, day)
);
"""

_write_lock = threading.Lock()


def default_db_path() -> str:
    base = "/data" if os.path.isdir("/data") else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "user_data.db")


def today_key() -> str:
    return datetime.now(GUEST_QUOTA_TZ).date().isoformat()


def normalize_guest_id(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if not _GUEST_ID_RE.match(value):
        return None
    return value


class GuestQuotaExceeded(Exception):
    def __init__(self, used: int, limit: int, day: str):
        self.used = used
        self.limit = limit
        self.day = day
        super().__init__("guest daily limit reached")


class GuestQuotaStore:
    def __init__(self, db_path: str | None = None, limit: int | None = None):
        self.db_path = db_path or default_db_path()
        self.limit = GUEST_DAILY_LIMIT if limit is None else limit
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with self._conn() as con:
            con.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def status(self, guest_id: str, day: str | None = None) -> dict:
        day = day or today_key()
        with self._conn() as con:
            row = con.execute(
                "SELECT count FROM guest_usage WHERE guest_id = ? AND day = ?",
                (guest_id, day),
            ).fetchone()
        used = int(row["count"]) if row else 0
        remaining = max(0, self.limit - used)
        return {
            "guest_id": guest_id,
            "day": day,
            "used": used,
            "limit": self.limit,
            "remaining": remaining,
            "timezone": str(GUEST_QUOTA_TZ),
        }

    def consume(self, guest_id: str, day: str | None = None) -> dict:
        """Increment today's count. Raises GuestQuotaExceeded if already at limit."""
        day = day or today_key()
        with _write_lock, self._conn() as con:
            row = con.execute(
                "SELECT count FROM guest_usage WHERE guest_id = ? AND day = ?",
                (guest_id, day),
            ).fetchone()
            used = int(row["count"]) if row else 0
            if used >= self.limit:
                raise GuestQuotaExceeded(used=used, limit=self.limit, day=day)
            if row:
                con.execute(
                    "UPDATE guest_usage SET count = count + 1 WHERE guest_id = ? AND day = ?",
                    (guest_id, day),
                )
            else:
                con.execute(
                    "INSERT INTO guest_usage (guest_id, day, count) VALUES (?, ?, 1)",
                    (guest_id, day),
                )
            used += 1
        return {
            "guest_id": guest_id,
            "day": day,
            "used": used,
            "limit": self.limit,
            "remaining": max(0, self.limit - used),
            "timezone": str(GUEST_QUOTA_TZ),
        }
