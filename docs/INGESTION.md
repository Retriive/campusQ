# The ingestion pipeline — one pipeline, any format, any school

This replaces the hand-written per-page scrapers and the wipe-then-rescrape
flow. You give it URLs; it handles the rest — tables, collapsible sections,
lists, paragraphs, and PDFs all land in Pinecone in the exact metadata shapes
the chat backend already expects.

## The 60-second version

```bash
cd backend
py -m ingest.run --school carleton --list                  # what's configured
py -m ingest.run --school carleton --category dates --dry-run   # extract, write preview, touch nothing
py -m ingest.run --school carleton --category dates        # re-ingest changed pages
py -m ingest.run --school carleton --force                 # full re-crawl, everything
```

`--dry-run` writes `ingest_preview_<school>_<category>.jsonl` so you can read
every record before anything is written to Pinecone. Always dry-run a new
source first.

## How it stays safe (the parts that matter)

- **Never empty.** Promotion upserts over live vectors by stable ID, then
  removes stale IDs. There is no "wipe first" window. A run that dies halfway
  leaves the old data fully serving. `wipe.py` is no longer part of the flow.
- **Change detection.** Every page's content is hashed (SQLite:
  `ingest_state.db`). Re-runs only re-extract pages that changed — so a
  nightly scheduled run costs almost nothing during quiet weeks.
- **Shrink guard.** A full re-crawl that produces less than half of what's
  currently live is assumed broken and **aborts before writing**. Override
  with `--force` only when the shrink is real (e.g. a program was removed).
- **Stale cleanup only on full coverage.** Incremental runs (some pages
  skipped as unchanged) never delete vectors — deletion only happens when
  every page in the category was re-extracted this run.

## Adding a source (or a whole school)

Sources live in `backend/schools/<school>/sources.json`:

```json
{
  "category": "tuition",                          // = Pinecone namespace
  "url": "https://carleton.ca/studentaccounts/tuition-fees/",
  "extractor": "llm_generic",                     // or auto / course_regex / llm_dates
  "follow_links": true,                           // also crawl same-prefix links
  "max_pages": 25,
  "min_records": 5                                // verification floor
}
```

**A new school = a new `sources.json`.** No scraper code. Category names
become Pinecone namespaces, so match the ones `retrieval.py` searches.

A source can also set `"connector"` (`web` default, `sitemap`, `ics`,
`filedrop`) to ingest from sitemaps, iCalendar feeds, or a local folder of
documents — see [AGENTS.md](AGENTS.md#3-connectors-sourcesjson-connector-field)
for when to use each.

Admins can also add single URLs at runtime from **`/internal/sources`** (behind
the admin key) — those are stored in SQLite and merged with the config file at
run time. The same page has "Re-scrape" buttons per category and shows run
history, so whoever operates CampusQ for a school never needs a terminal.

## Extractors

| Extractor | What it does | Cost |
|---|---|---|
| `course_regex` | Deterministic parser for Carleton's calendar format (ported from the proven scraper). **Only a free shortcut** — when it matches nothing, `llm_courses` takes over automatically. | free |
| `llm_courses` | Universal course extraction for ANY university's catalog format — UofT's `CSC236H1`, Waterloo's `CS 135`, uOttawa's `ITI 1121` all come out as the same structured record (code, name, credits, prereqs, description), so course cards, prereq graphs, and instant lookups work at every school. | ~fractions of a cent per page |
| `llm_dates` | Emits `{title, date, term, category}` records. Handles date tables, lists, prose. | ~fractions of a cent per page |
| `llm_generic` | Restructures any page into self-contained, student-question-sized chunks. Faithful-copy rules: numbers, fees, dates, form names preserved verbatim. | ~fractions of a cent per page |
| `auto` | Picks by category: courses→regex-with-LLM-fallback, dates→llm_dates, else llm_generic. | — |

A new school's `sources.json` can set `"extractor": "llm_courses"` directly to
skip the Carleton regex attempt entirely.

Both LLM prompts treat page content as **data, not instructions** (prompt
injection from a hostile page is explicitly guarded against), and extraction
happens once per changed page — not per student question — so cost stays
negligible.

## Environment

Same `.env` as the backend: `OPENAI_API_KEY` (extraction + embeddings),
`PINECONE_API_KEY`. Optional: `INGEST_MODEL` (default `gpt-4o-mini`),
`PINECONE_INDEX_NAME` (default `knowledge-base`).

## Testing

`python -m pytest tests/test_ingest.py -q` — fully offline (fixture pages,
fake LLM/embeddings/Pinecone), covers the format matrix and every safety rail.

## What still uses the old scrapers

`schedule` ingestion (`ingest_schedule.py`) and the structured
`program_requirements.json` builder are unchanged for now — they have bespoke
logic worth porting carefully in a follow-up. Everything else routes through
this pipeline.
