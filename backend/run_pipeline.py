"""
run_pipeline.py — Master ingestion orchestrator for CampusQ.

Run order:
  1. wipe.py        — clears old data (run manually first)
  2. scrape_courses.py     → "courses" namespace
  3. scrape_programs.py    → "programs" namespace
  4. scrape_regulations.py → "regulations" namespace

Usage:
  py run_pipeline.py             # Run all three
  py run_pipeline.py courses     # Run only courses
  py run_pipeline.py programs    # Run only programs
  py run_pipeline.py regulations # Run only regulations
"""

import sys
import time

def run_all():
    start = time.time()

    print("\n" + "="*60)
    print("  CampusQ — Full Ingestion Pipeline")
    print("="*60)
    print("\nMake sure you ran wipe.py first to clear old data.\n")

    scrapers = []

    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        if target == "courses":
            scrapers = ["courses"]
        elif target == "programs":
            scrapers = ["programs"]
        elif target == "regulations":
            scrapers = ["regulations"]
        else:
            print(f"Unknown target: {target}")
            print("Valid options: courses, programs, regulations")
            sys.exit(1)
    else:
        scrapers = ["courses", "programs", "regulations", "services"]

    for scraper in scrapers:
        print(f"\n{'='*60}")
        print(f"  Running: {scraper}")
        print(f"{'='*60}")

        if scraper == "courses":
            import scrape_courses
            scrape_courses.run()
        elif scraper == "programs":
            import scrape_programs
            scrape_programs.run()
        elif scraper == "regulations":
            import scrape_regulations
            scrape_regulations.run()
        elif scraper == "services":
            import scrape_services
            scrape_services.run()

    elapsed = round((time.time() - start) / 60, 1)
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE in {elapsed} minutes")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_all()
