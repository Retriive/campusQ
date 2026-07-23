# How We Get University Data (Ingestion)

Plain-English guide to how CampusQ crawls a university's website and turns it
into the data students search. No engineering background required.

---

## The one-sentence version

CampusQ **reads a university's public web pages, cleans them up, turns them
into tidy records, double-checks them, and files them into Pinecone** — all
driven by a single config file per school, with no custom scraper code.

---

## The big idea: config, not code

Adding a new university used to mean writing a new scraper program. Not
anymore. Now you write **one JSON file** that lists the pages to read:

```
backend/schools/<school>/sources.json
```

Each entry in that file is a **source** — one starting URL plus instructions
for how to read it. The pipeline does the rest. Today only **Carleton** is
live.

A source looks like this:

```json
{
  "category": "courses",
  "url": "https://calendar.carleton.ca/undergrad/courses/",
  "extractor": "course_regex",
  "follow_links": true,
  "max_pages": 200,
  "min_records": 500
}
```

| Field | Plain meaning |
|---|---|
| `category` | Which "drawer" in Pinecone this feeds (`courses`, `library`, `dates`…) |
| `url` | Where to start reading |
| `extractor` | How to turn the page into records (see [Step 4](#step-4--turn-pages-into-records)) |
| `follow_links` | If true, also read pages linked from this one (same URL prefix) |
| `max_pages` | Safety cap on how many pages to read |
| `min_records` | "Expect at least this many records, or something's wrong" |
| `fit` | Trim page down to the relevant parts before reading (optional) |
| `adaptive` | Stop early once pages stop adding anything new (optional) |

---

## The pipeline (what happens on a run)

```
sources.json  →  for each source:

  1. GATHER pages        follow links if configured; stop early if "adaptive"
        ↓
  2. FETCH each page     download over HTTPS, clean to plain text, checksum it
        ↓
  3. CHANGE CHECK        unchanged since last run? skip it (unless --force)
        ↓
  4. EXTRACT records     regex / cached CSS schema / AI → tidy structured records
        ↓
  5. CHECK the records   dedupe, quarantine bad ones, verify counts
        ↓
  6. PROMOTE to Pinecone  save the good records; remove truly-gone ones
```

Every step below maps to real code in `backend/ingest/`.

---

### Step 1 — Gather pages

`ingest/pipeline.py` → `_gather_pages`

- Reads the source's starting URL.
- If `follow_links` is on, it finds every link on the page that shares the
  same URL prefix and reads those too. This is how **one** "courses" source
  automatically fans out to ~200 department pages without anyone listing them
  by hand.
- If `adaptive` is on, a **saturation tracker** (`ingest/adaptive.py`) watches
  how many *new words* each page adds. Once several pages in a row add almost
  nothing, it stops — no point reading 50 more near-identical pages. (Carleton's
  courses keep this **off**, because every department page has genuinely new
  courses we want.)

---

### Step 2 — Fetch and clean each page

`ingest/fetch.py`

Downloads the page and turns messy HTML (or a PDF) into clean, readable text.

**What it handles well:**
- **HTML** — strips menus, headers, footers, and scripts; flattens tables into
  readable rows (so a fees or deadlines table doesn't turn to mush).
- **PDFs** — read with PyMuPDF, the same library the chat file-upload uses.

**It's a polite, safe robot:**
- Obeys `robots.txt`, identifies itself as `CampusQBot`, and waits half a
  second between hits to the same site so it never hammers a server.
- **Security guard (important):** because an admin can paste in any URL, the
  fetcher refuses non-HTTPS links and refuses any address that points at a
  private/internal network — and it re-checks this on every redirect. This
  stops the crawler from being tricked into reaching internal systems.

**The one real limitation:** it reads the page as raw HTML — it does **not**
run JavaScript. Pages that build their content with in-browser widgets (e.g.
the library's LibCal hours) come back thin or empty. See
[What's not covered yet](#whats-not-covered-yet).

Each cleaned page gets a **checksum** (a fingerprint of its text). That
fingerprint powers the next step.

---

### Step 3 — Change detection (skip what hasn't changed)

`ingest/pipeline.py` + `ingest/state.py`

The fingerprint from Step 2 is compared to the one stored from last time.

- **Same fingerprint** → the page hasn't changed → **skip it** (fast, free).
- **Different** → re-read and re-extract it.
- `--force` overrides this and re-does everything.

Every fetched page's cleaned text is also saved to a **raw lake**
(`/data/raw/<school>/` + a SQLite table). That means you can re-run the
"extract" step later **without re-crawling the university** — handy for
improving the extractors. That mode is `--reextract`.

---

### Step 4 — Turn pages into records

`ingest/extract.py` (and `ingest/css_schema.py`)

A **record** is one tidy, self-contained fact ready to be searched — a course,
a deadline, a library service. There are three ways to make them, cheapest
first:

| Extractor | How it works | Cost | When |
|---|---|---|---|
| **`course_regex`** | A precise pattern reads Carleton's course format directly | Free & instant | Known, fixed formats |
| **`css_schema`** | AI learns the page's layout **once**, then reads every page with no AI | AI once per template | Repeating layouts (course lists, cards) |
| **`llm_*`** | AI reads the text and writes structured records | AI per page | Anything else / any new school |

The clever part: **they all produce the exact same record shape.** So a course
from Carleton's regex and a course from another school's AI extractor look
identical downstream. And `course_regex` **automatically falls back to AI** if
it doesn't recognize the format — coverage never drops.

Optional trim before extracting (`ingest/fit.py`): a lightweight relevance
filter can prune a page down to just the blocks about the topic (dropping
leftover menus and footers) so the AI reads less noise and costs less.

> **Safety note:** the AI prompts explicitly treat page text as *data, not
> instructions*, and forbid inventing dates or numbers — a guard against a
> web page trying to trick the extractor.

---

### Step 5 — Check the records before saving

`ingest/validate.py` + `ingest/upsert.py`

Nothing reaches Pinecone until it passes checks:

- **Dedupe** — the same course listed on two pages collapses into one.
- **Quarantine** — records that look wrong (a deadline in the year 1999, the
  same deadline with two different dates, impossible course credits) are set
  aside instead of published. The previously-good version keeps serving.
- **Verify counts** — if a run suddenly produces far fewer records than are
  already live (the `min_records` floor, plus a "did it shrink >50%?" guard),
  the run **stops** rather than wiping good data.

---

### Step 6 — Promote to Pinecone

`ingest/upsert.py`

- Good records are embedded and **upserted** (saved/updated) in Pinecone,
  keyed by a stable ID so re-runs update in place instead of duplicating.
- **Stale cleanup is careful:** records that no longer exist on the site are
  removed **only** when the whole category was fully re-read this run. If any
  page was skipped (an incremental run), nothing gets deleted — a skipped page
  isn't proof its data is gone.
- The same records are mirrored into a local keyword index so keyword +
  vector search stay in sync.

---

## How to run it

From the `backend/` folder, with `OPENAI_API_KEY` and `PINECONE_API_KEY` set
in `.env`:

```bash
# See what's configured and recent run history
py -m ingestion.run --school carleton --list

# Preview only — extracts everything, writes a file, touches nothing live
py -m ingestion.run --school carleton --category library --dry-run

# Real incremental run (only changed pages)
py -m ingestion.run --school carleton

# One category at a time
py -m ingestion.run --school carleton --category courses

# Force a full re-crawl and re-extract
py -m ingestion.run --school carleton --force

# Re-extract from saved pages, no crawling (iterate on extractors)
py -m ingestion.run --school carleton --reextract
```

**Golden rule:** run `--dry-run` first. In dry-run nothing touches Pinecone —
you get a preview file to eyeball before committing.

### The modes at a glance

| Mode | Crawls? | Writes to Pinecone? | Use it to… |
|---|---|---|---|
| normal | yes | yes | Do a real update |
| `--dry-run` | yes | **no** | Preview records safely |
| `--force` | yes (all) | yes | Rebuild from scratch |
| `--reextract` | **no** | yes | Improve extractors offline |

---

## Where the code lives

Canonical command surface is `backend/ingestion/` (`py -m ingestion.run`); the
actual logic lives in `backend/ingest/`:

| File | Job |
|---|---|
| `pipeline.py` | Orchestrates the whole run (Steps 1–6) |
| `fetch.py` | Download + clean pages; robots/politeness/security guard |
| `registry.py` | Reads `sources.json`; the `Source` config contract |
| `adaptive.py` | "Stop early when pages stop adding new info" |
| `fit.py` | Trim a page to the relevant blocks before extracting |
| `extract.py` | Regex + AI extractors → tidy records |
| `css_schema.py` | Learn a page layout once, then extract with no AI |
| `validate.py` | Quarantine bad/contradictory records |
| `upsert.py` | Embed, verify counts, save to Pinecone, clean up stale |
| `state.py` | The run history + raw lake (SQLite) |

---

## What's not covered yet

- **JavaScript-rendered pages.** The fetcher reads raw HTML and doesn't run
  in-browser scripts, so widget-driven pages (like LibCal library hours) come
  back thin. Filling this gap would mean an opt-in "render in a browser"
  fetch mode for just those sources — the config already has room for it.
- **Non-web connectors.** `sitemap`, `ics`, and `filedrop` connectors are
  declared in the config format but not built yet; only the `web` connector
  works today.
- **Curated-on-purpose data.** Carleton's `dates` and `facts` are intentionally
  **not** scraped — they're hand-maintained in `calendar_feed.py` and
  `scrape_facts.py` because human-verified data beats scraping for those.

---

## TL;DR for non-engineers

1. We list a school's pages in one config file.
2. A polite, security-hardened robot reads those pages and cleans them up.
3. It skips anything that hasn't changed since last time.
4. It turns each page into tidy records — using a free pattern, a learned
   layout, or AI, whichever is cheapest that works.
5. It quarantines anything suspicious and refuses to publish if the numbers
   look wrong.
6. The good records land in Pinecone, where student questions search them.

Always preview with `--dry-run` before a real run.
