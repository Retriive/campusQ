# CampusQ ingestion (canonical)

Use this namespace for all ingestion workflows:

- CLI: `py -m ingestion.run --school carleton --list`
- Incremental run: `py -m ingestion.run --school carleton`
- One category: `py -m ingestion.run --school carleton --category dates`
- Full refresh: `py -m ingestion.run --school carleton --force`

## Legacy paths

- `backend/ingest/` remains as a compatibility shim for older imports.
- `backend/run_pipeline.py` and `backend/scrapers/active/` are legacy scraper
  orchestration paths and are no longer the canonical ingestion workflow.
