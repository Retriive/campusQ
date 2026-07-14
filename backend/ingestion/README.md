# CampusQ ingestion (canonical)

Use this namespace for all ingestion workflows:

## Carleton cutover runbook (first real run)

`schools/carleton/sources.json` covers courses, library, registrar,
regulations, programs, tuition, and services (financial aid, ISSO, advising,
ITS, health, housing, dining, and more) via one-hop hub fan-out. Not scraped
on purpose: `dates` stays curated in `calendar_feed.py`, `facts` in
`scrape_facts.py` (both hand-verified; scraping would downgrade them), and
`schedule` stays on the Banner-driven `ingest_schedule.py`.

A full all-category run fetches on the order of 1,000 pages politely
(~0.5s/page ≈ 10–20 min) and runs every changed page through gpt-4o-mini
extraction — expect a few dollars of OpenAI cost on the first run, then far
less incrementally (unchanged pages are skipped).

Run from `backend/` with `OPENAI_API_KEY` + `PINECONE_API_KEY` in `.env`:

```bash
py scripts/audit_index.py                                        # 1. baseline counts
py -m ingestion.run --school carleton --category library --dry-run   # 2. preview, no writes
py scripts/preview_report.py carleton library                   # 2b. quality report on the preview
py -m ingestion.run --school carleton --category library        # 3. small category first
py -m ingestion.run --school carleton --category courses --dry-run   # 4. preview (~200 pages, slow)
py -m ingestion.run --school carleton --category courses        # 5. real run
py scripts/audit_index.py                                        # 6. compare counts
py -m ingestion.run --school carleton --list                     # 7. check runs + quarantine
py evals/quality_gate.py --tier core                             # 8. gate before trusting it
```

Safety nets already active: verification floors (`min_records`), the >50%
shrink guard, validator quarantine, and stale-delete only on full coverage.
Course IDs are the course codes themselves, so the new pipeline overwrites
the legacy vectors in place; library vectors use a new ID scheme and replace
the legacy ones on the first full run. If anything looks wrong in a preview,
nothing has touched Pinecone yet.

- CLI: `py -m ingestion.run --school carleton --list`
- Incremental run: `py -m ingestion.run --school carleton`
- One category: `py -m ingestion.run --school carleton --category dates`
- Full refresh: `py -m ingestion.run --school carleton --force`
- Replay from raw lake (no crawling): `py -m ingestion.run --school carleton --reextract`

Every crawl persists cleaned page text into a raw lake (`/data/raw/<school>/`
+ the `raw_pages` SQLite table), so `--reextract` re-runs extraction offline —
iterate on extractor prompts/validators without re-hitting the university.
Promoted vectors carry a `scraped_at` metadata stamp; audit what's live and
how fresh with `py scripts/audit_index.py`.

## Validation + quarantine

Extracted records pass deterministic validators (`ingest/validate.py`) before
verify/promote. Records that fail — deadlines outside a plausible year window,
the same deadline extracted with two different dates, implausible course
credits — are quarantined to SQLite instead of published, and their
previously-live vector keeps serving. Review with
`py -m ingestion.run --school carleton --list` (Recent quarantine section).

## Legacy paths

- `backend/ingest/` remains as a compatibility shim for older imports.
- `backend/run_pipeline.py` and `backend/scrapers/active/` are legacy scraper
  orchestration paths and are no longer the canonical ingestion workflow.
