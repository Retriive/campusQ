"""Crawl state — SQLite, zero extra infrastructure.

Lives on the same persistent disk as the logs (/data on Render, backend/ locally).
Tracks per-page content hashes so re-runs only re-extract pages that actually
changed, plus a run history the admin dashboard can show.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    url           TEXT PRIMARY KEY,
    school        TEXT NOT NULL,
    category      TEXT NOT NULL,
    content_hash  TEXT,
    last_crawled  TEXT,
    last_changed  TEXT,
    status        TEXT,            -- ok | error | skipped
    error         TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    school        TEXT NOT NULL,
    category      TEXT NOT NULL,
    started       TEXT NOT NULL,
    finished      TEXT,
    status        TEXT NOT NULL,   -- running | ok | failed | dry_run
    pages_fetched INTEGER DEFAULT 0,
    pages_changed INTEGER DEFAULT 0,
    records       INTEGER DEFAULT 0,
    message       TEXT
);
CREATE TABLE IF NOT EXISTS extra_sources (
    url           TEXT PRIMARY KEY,
    school        TEXT NOT NULL,
    category      TEXT NOT NULL,
    extractor     TEXT DEFAULT 'auto',
    added_at      TEXT NOT NULL
);
"""

# SQLite writes from the API's background thread and CLI must not interleave.
_write_lock = threading.Lock()


def default_db_path() -> str:
    base = "/data" if os.path.isdir("/data") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "ingest_state.db")


class IngestState:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or default_db_path()
        with self._conn() as con:
            con.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    # ── Pages ──────────────────────────────────────────────────────────────
    def get_page_hash(self, url: str) -> str | None:
        with self._conn() as con:
            row = con.execute("SELECT content_hash FROM pages WHERE url = ?", (url,)).fetchone()
            return row["content_hash"] if row else None

    def record_page(self, url: str, school: str, category: str,
                    content_hash: str | None, status: str, error: str = "",
                    changed: bool = False):
        now = datetime.utcnow().isoformat()
        with _write_lock, self._conn() as con:
            existing = con.execute("SELECT last_changed FROM pages WHERE url = ?", (url,)).fetchone()
            last_changed = now if changed or not existing else existing["last_changed"]
            con.execute(
                """INSERT INTO pages (url, school, category, content_hash, last_crawled, last_changed, status, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(url) DO UPDATE SET
                     content_hash = excluded.content_hash,
                     last_crawled = excluded.last_crawled,
                     last_changed = excluded.last_changed,
                     status = excluded.status,
                     error = excluded.error""",
                (url, school, category, content_hash, now, last_changed, status, error[:500]),
            )

    def pages_for(self, school: str, category: str | None = None) -> list[dict]:
        q = "SELECT * FROM pages WHERE school = ?"
        args: list = [school]
        if category:
            q += " AND category = ?"
            args.append(category)
        with self._conn() as con:
            return [dict(r) for r in con.execute(q + " ORDER BY url", args)]

    # ── Runs ───────────────────────────────────────────────────────────────
    def start_run(self, school: str, category: str) -> int:
        with _write_lock, self._conn() as con:
            cur = con.execute(
                "INSERT INTO runs (school, category, started, status) VALUES (?, ?, ?, 'running')",
                (school, category, datetime.utcnow().isoformat()),
            )
            return cur.lastrowid

    def finish_run(self, run_id: int, status: str, pages_fetched: int,
                   pages_changed: int, records: int, message: str = ""):
        with _write_lock, self._conn() as con:
            con.execute(
                """UPDATE runs SET finished = ?, status = ?, pages_fetched = ?,
                   pages_changed = ?, records = ?, message = ? WHERE id = ?""",
                (datetime.utcnow().isoformat(), status, pages_fetched,
                 pages_changed, records, message[:1000], run_id),
            )

    def recent_runs(self, school: str | None = None, limit: int = 20) -> list[dict]:
        q = "SELECT * FROM runs"
        args: list = []
        if school:
            q += " WHERE school = ?"
            args.append(school)
        q += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        with self._conn() as con:
            return [dict(r) for r in con.execute(q, args)]

    def has_running(self) -> bool:
        with self._conn() as con:
            row = con.execute("SELECT COUNT(*) AS n FROM runs WHERE status = 'running'").fetchone()
            return row["n"] > 0

    # ── Admin-added sources ────────────────────────────────────────────────
    def add_extra_source(self, school: str, category: str, url: str, extractor: str = "auto"):
        with _write_lock, self._conn() as con:
            con.execute(
                """INSERT INTO extra_sources (url, school, category, extractor, added_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(url) DO UPDATE SET category = excluded.category, extractor = excluded.extractor""",
                (url, school, category, extractor, datetime.utcnow().isoformat()),
            )

    def remove_extra_source(self, url: str):
        with _write_lock, self._conn() as con:
            con.execute("DELETE FROM extra_sources WHERE url = ?", (url,))

    def extra_sources(self, school: str) -> list[dict]:
        with self._conn() as con:
            return [dict(r) for r in con.execute(
                "SELECT * FROM extra_sources WHERE school = ? ORDER BY added_at", (school,))]
