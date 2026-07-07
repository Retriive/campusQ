"""File-drop connector — ingest a local folder of documents.

The B2B reality: a registrar's office will email you a fee-schedule PDF or a
policies Word-export long before they'll fix their website. Drop those files
in a folder, point a source at it, and they flow through the same pipeline
(change detection included — re-running after a file is updated re-extracts
only that file).

source.url is a directory path. Supported: .pdf, .html/.htm, .txt, .md.
"""

from __future__ import annotations

import hashlib
import os

from ingest.fetch import FetchedPage, html_to_text, pdf_to_text

SUPPORTED = (".pdf", ".html", ".htm", ".txt", ".md")
MAX_FILES = 200
MAX_FILE_BYTES = 25 * 1024 * 1024


def _read_file(path: str) -> tuple[str, str] | None:
    """path -> (kind, text) or None if unsupported/unreadable."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED or os.path.getsize(path) > MAX_FILE_BYTES:
        return None
    if ext == ".pdf":
        with open(path, "rb") as f:
            return "pdf", pdf_to_text(f.read())
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    if ext in (".html", ".htm"):
        return "html", html_to_text(raw)
    return "text", raw.strip()


def gather_filedrop(source, log=print) -> list[FetchedPage]:
    folder = source.url
    if not os.path.isdir(folder):
        log(f"  filedrop folder not found: {folder}")
        return []

    pages: list[FetchedPage] = []
    names = sorted(os.listdir(folder))[:MAX_FILES]
    for name in names:
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        try:
            result = _read_file(path)
        except Exception as exc:
            log(f"    ✗ {name}: {exc}")
            continue
        if result is None:
            continue
        kind, text = result
        if not text:
            continue
        pages.append(FetchedPage(
            url=path, kind=kind, text=text,
            content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        ))
    log(f"  filedrop {folder} → {len(pages)} documents")
    return pages
