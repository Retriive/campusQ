"""
run_pipeline.py — Master ingestion orchestrator for CampusQ.

Run wipe.py first to clear old data, then run this.

All active scrapers live in scrapers/active/.
Superseded scrapers are in scrapers/archive/ (kept for reference only).

Usage:
  py run_pipeline.py              # Run everything
  py run_pipeline.py courses      # Run only courses
  py run_pipeline.py programs     # Run only programs
  py run_pipeline.py regulations  # Run only regulations
  py run_pipeline.py registrar    # Run only registrar
  py run_pipeline.py dates        # Run only dates
  py run_pipeline.py facts        # Run only facts
  py run_pipeline.py campus       # Run only campus services (PMC/CSAS/Awards/TLS/AI)
  py run_pipeline.py tuition      # Run only tuition
  py run_pipeline.py library      # Run only library
"""

import sys
import time
import importlib.util
import os

SCRAPERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrapers", "active")

ALL_SCRAPERS = [
    "courses",
    "programs",
    "regulations",
    "registrar",
    "dates",
    "facts",
    "campus",
    "tuition",
    "library",
]


def load_and_run(name: str):
    path = os.path.join(SCRAPERS_DIR, f"scrape_{name}.py")
    spec = importlib.util.spec_from_file_location(f"scrape_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run()


def run_all():
    start = time.time()

    print("\n" + "=" * 60)
    print("  CampusQ — Full Ingestion Pipeline")
    print("=" * 60)
    print("\nMake sure you ran wipe.py first to clear old data.\n")

    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        if target not in ALL_SCRAPERS:
            print(f"Unknown target: {target}")
            print(f"Valid options: {', '.join(ALL_SCRAPERS)}")
            sys.exit(1)
        scrapers = [target]
    else:
        scrapers = ALL_SCRAPERS

    for scraper in scrapers:
        print(f"\n{'=' * 60}")
        print(f"  Running: {scraper}")
        print(f"{'=' * 60}")
        try:
            load_and_run(scraper)
        except Exception as e:
            print(f"  ERROR running {scraper}: {e}")

    elapsed = round((time.time() - start) / 60, 1)
    print(f"\n{'=' * 60}")
    print(f"  PIPELINE COMPLETE in {elapsed} minutes")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    run_all()
