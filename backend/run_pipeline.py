"""Legacy wrapper for CampusQ ingestion.

Canonical command:
  py -m ingestion.run --school carleton [--category <name>] [--force]
"""

from __future__ import annotations

import sys

from ingest.run import main as ingest_main

LEGACY_CATEGORIES = {
    "courses",
    "programs",
    "regulations",
    "registrar",
    "dates",
    "facts",
    "campus",
    "tuition",
    "library",
}


def main() -> int:
    category = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1].lower().strip()
        if candidate not in LEGACY_CATEGORIES:
            print(f"Unknown target: {candidate}")
            print(f"Valid options: {', '.join(sorted(LEGACY_CATEGORIES))}")
            return 1
        category = candidate

    print("[deprecated] run_pipeline.py is legacy. Use: py -m ingestion.run ...")

    argv = ["ingestion.run", "--school", "carleton"]
    if category:
        argv += ["--category", category]
    sys.argv = argv
    return ingest_main()


if __name__ == "__main__":
    raise SystemExit(main())
