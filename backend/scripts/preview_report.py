#!/usr/bin/env python3
"""Quality report for a dry-run preview — read this BEFORE publishing.

Turns ingest_preview_<school>_<category>.jsonl into the numbers and samples a
human needs to judge extraction quality, instead of scrolling raw JSONL.

Usage (from backend/):
  py -m ingestion.run --school carleton --category library --dry-run
  py scripts/preview_report.py carleton library
  py scripts/preview_report.py carleton courses --samples 5
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import Counter
from statistics import median

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW_DIR = "/data" if os.path.isdir("/data") else BACKEND_DIR

SHORT_WORDS = 20          # records under this many words get listed for review
KNOWN_COURSE_CODES = ("COMP 1005", "COMP 2401", "SYSC 3110")  # spot-check anchors


def load_jsonl(path: str) -> list[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def words(text: str) -> int:
    return len(text.split())


def report(school: str, category: str, samples: int) -> int:
    path = os.path.join(PREVIEW_DIR, f"ingest_preview_{school}_{category}.jsonl")
    records = load_jsonl(path)
    if not records:
        print(f"No preview at {path} — run the dry-run first:\n"
              f"  py -m ingestion.run --school {school} --category {category} --dry-run")
        return 1

    quarantined = load_jsonl(path.replace(".jsonl", ".quarantine.jsonl"))
    metas = [r.get("metadata", {}) for r in records]
    bodies = [str(m.get("text", "")) for m in metas]
    sources = [str(m.get("source", "")) for m in metas]
    warnings: list[str] = []

    print("=" * 70)
    print(f"PREVIEW QUALITY REPORT — {school} / {category}")
    print("=" * 70)

    # ── Coverage ────────────────────────────────────────────────────────────
    pages = Counter(sources)
    print(f"\nRecords: {len(records)}   Pages: {len(pages)}   "
          f"Avg records/page: {len(records) / max(len(pages), 1):.1f}")
    print(f"Quarantined in this run: {len(quarantined)}")
    thin_pages = [u for u, n in pages.items() if n == 1]
    if len(thin_pages) > len(pages) / 2:
        warnings.append(f"{len(thin_pages)}/{len(pages)} pages produced only 1 record "
                        f"— extraction may be missing content (JS-rendered pages?)")

    # ── Completeness ────────────────────────────────────────────────────────
    no_source = sum(1 for s in sources if not s.startswith("http"))
    no_title = sum(1 for m in metas if not str(m.get("title", "")).strip())
    print(f"\nMissing source URL: {no_source}   Missing title: {no_title}")
    if no_source:
        warnings.append(f"{no_source} records have no source URL (uncitable)")

    # ── Body length ─────────────────────────────────────────────────────────
    lengths = sorted(words(b) for b in bodies)
    short = [(words(b), m) for b, m in zip(bodies, metas) if words(b) < SHORT_WORDS]
    print(f"\nBody length (words): min={lengths[0]}  median={median(lengths):.0f}  "
          f"max={lengths[-1]}   under {SHORT_WORDS} words: {len(short)}")
    for n, m in sorted(short)[:10]:
        print(f"  [{n:>3}w] {str(m.get('title', ''))[:50]!r}  ← {m.get('source', '')}")

    # ── Duplicates ──────────────────────────────────────────────────────────
    norm = Counter(" ".join(b.lower().split()) for b in bodies)
    dupes = {b: n for b, n in norm.items() if n > 1}
    print(f"\nDuplicate bodies (same text, multiple records): {sum(dupes.values()) - len(dupes)}")
    if sum(dupes.values()) - len(dupes) > len(records) * 0.1:
        warnings.append("over 10% duplicate bodies — boilerplate is leaking through")

    # ── Category-specific ───────────────────────────────────────────────────
    if category == "courses":
        credits = Counter(str(m.get("credits", "?")) for m in metas)
        with_prereq = sum(1 for m in metas if m.get("prerequisites") not in (None, "", "None"))
        print(f"\nCredits distribution: {dict(credits.most_common(6))}")
        print(f"With prerequisites: {with_prereq}/{len(records)}")
        codes = {str(m.get("course_code", "")) for m in metas}
        for anchor in KNOWN_COURSE_CODES:
            mark = "✓" if anchor in codes else "✗ MISSING"
            print(f"  spot-check {anchor}: {mark}")
            if anchor not in codes:
                warnings.append(f"known course {anchor} not extracted")
        if with_prereq == 0:
            warnings.append("zero courses have prerequisites — parser likely broken")

    if category == "dates":
        isos = sorted(str(m.get("date", "")) for m in metas)
        cats = Counter(str(m.get("category", "")) for m in metas)
        print(f"\nDate range: {isos[0]} → {isos[-1]}")
        print(f"By category: {dict(cats)}")

    # ── Human samples ───────────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print(f"RANDOM SAMPLES ({samples}) — read these against the live page:")
    print("-" * 70)
    rng = random.Random(0)  # reproducible so a re-run shows the same samples
    for r in rng.sample(records, min(samples, len(records))):
        m = r.get("metadata", {})
        print(f"\n■ {m.get('title', '(no title)')}")
        print(f"  source: {m.get('source', '')}")
        body = str(m.get("text", ""))
        print("  " + re.sub(r"\s+", " ", body)[:400])

    if quarantined:
        print("\n" + "-" * 70)
        print("QUARANTINE REASONS (what was blocked):")
        reason_counts = Counter(r for q in quarantined for r in q.get("reasons", []))
        for reason, n in reason_counts.most_common(10):
            print(f"  {n:>3}× {reason[:90]}")

    # ── Verdict ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    if warnings:
        print("⚠ WARNINGS — investigate before publishing:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("No automated warnings. Now do the human check on the samples above:")
        print("  1. Open each sample's source URL — is every number/date/name in the")
        print("     record actually on that page? (ctrl-F a number)")
        print("  2. Does each record make sense read alone, out of context?")
        print("  3. Is anything important on the page MISSING from the preview?")
    print("=" * 70)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Quality report for a dry-run preview")
    p.add_argument("school")
    p.add_argument("category")
    p.add_argument("--samples", type=int, default=8)
    args = p.parse_args()
    return report(args.school, args.category, args.samples)


if __name__ == "__main__":
    sys.exit(main())
