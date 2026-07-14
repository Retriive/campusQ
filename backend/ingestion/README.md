# CampusQ ingestion (canonical)

Use this namespace for all ingestion workflows:

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

## Legacy paths

- `backend/ingest/` remains as a compatibility shim for older imports.
- `backend/run_pipeline.py` and `backend/scrapers/active/` are legacy scraper
  orchestration paths and are no longer the canonical ingestion workflow.
