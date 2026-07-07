"""
CampusQ universal ingestion pipeline.

One pipeline, any format, any school:

  registry  — which URLs to ingest per school (schools/<school>/sources.json
              + sources added at runtime through the admin API)
  state     — SQLite crawl state: content hashes (change detection) + run history
  fetch     — polite fetcher: robots.txt, retries, HTML→clean text, PDF→text
  extract   — deterministic fast-paths (course regex) + universal LLM extraction
  upsert    — batch embedding, sanity verification, zero-downtime promote
  pipeline  — orchestrates a run;  run.py is the CLI

Replaces the wipe-then-rescrape flow: promotion upserts over live vectors by
stable ID and only then removes stale IDs, so the index is never empty.
"""
