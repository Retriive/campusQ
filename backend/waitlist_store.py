"""Append-only waitlist log with self-serve unsubscribe.

Emails live in waitlist.log (JSONL). Unsubscribe rewrites the file without
matching addresses so privacy requests don't require manual log surgery.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone

_write_lock = threading.Lock()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def waitlist_path(log_dir: str) -> str:
    return os.path.join(log_dir, "waitlist.log")


def append_waitlist(log_dir: str, email: str, school: str) -> None:
    path = waitlist_path(log_dir)
    now = _utcnow_iso()
    line = json.dumps(
        {
            "ts": now,
            "email": email,
            "school": school,
            "consented_at": now,
        },
        ensure_ascii=False,
    ) + "\n"
    with _write_lock, open(path, "a", encoding="utf-8") as f:
        f.write(line)


def remove_waitlist_email(log_dir: str, email: str) -> int:
    """Remove all waitlist rows for email (case-insensitive). Returns count removed."""
    path = waitlist_path(log_dir)
    target = email.strip().lower()
    if not target:
        return 0

    with _write_lock:
        if not os.path.exists(path):
            return 0

        kept: list[str] = []
        removed = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except Exception:
                    kept.append(line if line.endswith("\n") else line + "\n")
                    continue
                row_email = str(row.get("email", "")).strip().lower()
                if row_email == target:
                    removed += 1
                    continue
                kept.append(line if line.endswith("\n") else line + "\n")

        if removed:
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.writelines(kept)
            os.replace(tmp_path, path)

        return removed
