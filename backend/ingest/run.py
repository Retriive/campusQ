"""CLI for the ingestion pipeline.

Usage (from backend/):
  py -m ingest.run --school carleton --list                 # show sources + state
  py -m ingest.run --school carleton --category dates --dry-run
  py -m ingest.run --school carleton --category dates       # incremental (changed pages only)
  py -m ingest.run --school carleton --force                # full re-crawl, all categories
  py -m ingest.run --school carleton --reextract --dry-run  # replay raw lake offline, preview

--dry-run extracts everything and writes ingest_preview_<school>_<category>.jsonl
so you can eyeball records before anything touches Pinecone.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from .pipeline import BACKEND_DIR, run_ingest          # noqa: E402
from .registry import list_schools, load_sources        # noqa: E402
from .state import IngestState                          # noqa: E402


def cmd_list(school: str):
    state = IngestState()
    sources = load_sources(school, BACKEND_DIR, state.extra_sources(school))
    if not sources:
        print(f"No sources for '{school}'. Known schools: {list_schools(BACKEND_DIR) or 'none'}")
        return 1
    print(f"\nSources for {school}:")
    for s in sources:
        origin = "admin" if s.added_by_admin else "config"
        fan = f" (+links, max {s.max_pages})" if s.follow_links else ""
        print(f"  [{s.category:12s}] {s.url}{fan}  · {s.resolve_extractor()} · {origin}")
    print("\nRecent runs:")
    for r in state.recent_runs(school, limit=10):
        print(f"  #{r['id']} {r['category']:12s} {r['status']:8s} {r['started'][:19]} "
              f"pages={r['pages_fetched']} changed={r['pages_changed']} records={r['records']}  {r['message'] or ''}")
    quarantined = state.quarantined_for(school, limit=10)
    if quarantined:
        print("\nRecent quarantine (records blocked from publishing):")
        for q in quarantined:
            print(f"  #{q['id']} [{q['category']:12s}] {q['record_id']}  {q['reasons']}  ({q['created_at'][:19]})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CampusQ ingestion pipeline")
    parser.add_argument("--school", default="carleton")
    parser.add_argument("--category", default=None, help="one category (namespace); default all")
    parser.add_argument("--force", action="store_true", help="re-extract unchanged pages / override shrink guard")
    parser.add_argument("--dry-run", action="store_true", help="extract to a preview file; no Pinecone writes")
    parser.add_argument("--reextract", action="store_true",
                        help="replay extraction from the raw lake (no crawling); combine with --dry-run to preview")
    parser.add_argument("--list", action="store_true", help="show configured sources and recent runs")
    args = parser.parse_args()

    if args.list:
        return cmd_list(args.school)

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required (extraction + embeddings).")
        return 2
    if not args.dry_run and not os.getenv("PINECONE_API_KEY"):
        print("PINECONE_API_KEY is required (or use --dry-run).")
        return 2

    run = run_ingest(args.school, args.category, force=args.force,
                     dry_run=args.dry_run, replay=args.reextract)

    print("\n" + "=" * 60)
    for r in run.results:
        mark = {"ok": "✓", "dry_run": "◦", "skipped": "-", "failed": "✗"}[r.status]
        print(f" {mark} {r.category:14s} {r.status:8s} pages={r.pages_fetched} "
              f"changed={r.pages_changed} records={r.records}  {r.message}")
        if r.preview_path:
            print(f"     preview: {r.preview_path}")
    print("=" * 60)
    return 0 if run.ok else 1


if __name__ == "__main__":
    sys.exit(main())
