"""Pipeline orchestrator — one call runs a school's ingestion end to end.

Per category:
  1. resolve sources (sources.json + admin-added)
  2. fetch pages (following same-prefix links where configured); every fetched
     page's cleaned text is persisted into the raw lake (/data/raw + SQLite)
  3. change detection — unchanged pages are skipped unless force=True
  4. extract typed records (regex fast-path or LLM)
  5. verify (min counts, shrink guard) — BEFORE touching Pinecone
  6. promote (upsert over live by stable ID; stale-delete only on full coverage)

Replay (--reextract): steps 4-6 re-run against the raw lake with no network,
so extractor changes can be iterated on without re-crawling the university.

Stale deletion only happens when every page in the category was extracted this
run (full coverage): an incremental run that skipped unchanged pages must not
delete the vectors those pages produced last time.
"""

from __future__ import annotations

import json
import os
import traceback
from dataclasses import dataclass, field

from . import adaptive as adaptive_mod
from . import css_schema as css_schema_mod
from . import extract as extract_mod
from . import fetch as fetch_mod
from . import fit as fit_mod
from . import upsert as upsert_mod
from . import validate as validate_mod
from .registry import Source, load_sources
from .state import IngestState

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW_DIR = "/data" if os.path.isdir("/data") else BACKEND_DIR
RAW_DIR = os.path.join(PREVIEW_DIR, "raw")


@dataclass
class CategoryResult:
    category: str
    status: str                    # ok | failed | dry_run | skipped
    pages_fetched: int = 0
    pages_changed: int = 0
    records: int = 0
    quarantined: int = 0
    upserted: int = 0
    stale_deleted: int = 0
    message: str = ""
    preview_path: str = ""


@dataclass
class RunResult:
    school: str
    results: list[CategoryResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.status in ("ok", "dry_run", "skipped") for r in self.results)


def _raw_path(school: str, content_hash: str) -> str:
    return os.path.join(RAW_DIR, school, f"{content_hash}.txt")


def _persist_raw(state: IngestState, page: fetch_mod.FetchedPage, school: str,
                 category: str, extractor: str, log):
    """Write a fetched page's cleaned text into the raw lake (content-addressed
    file + SQLite row). Lets extractors be re-run offline via --reextract
    without re-crawling the university. Best-effort: a lake failure must not
    fail the ingestion run."""
    try:
        path = _raw_path(school, page.content_hash)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.isfile(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(page.text)
        state.save_raw_page(page.url, school, category, extractor,
                            page.kind, page.content_hash, path)
    except Exception as exc:
        log(f"    raw lake write skipped for {page.url}: {exc}")


def _replay_pages(state: IngestState, school: str, category: str,
                  result: CategoryResult, llm, log) -> list[dict]:
    """Re-extract records from the raw lake — no network. Every raw page is
    processed (full coverage), so verify + stale cleanup behave like a forced
    full crawl."""
    records: list[dict] = []
    for row in state.raw_pages_for(school, category):
        result.pages_fetched += 1
        try:
            with open(row["path"], "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as exc:
            log(f"  ✗ raw read {row['url']}: {exc}")
            continue
        try:
            page_records = extract_mod.extract(row["extractor"], text, row["url"], category, llm)
            records.extend(page_records)
            log(f"  ✓ (replay) {row['url']} → {len(page_records)} records ({row['extractor']})")
        except Exception as exc:
            log(f"  ✗ extract (replay) {row['url']}: {exc}")
    return records


def _gather_pages(source: Source, log) -> list[fetch_mod.FetchedPage]:
    """Fetch a source's page, fanning out to same-prefix links if configured.
    Non-web sources (sitemap, ics, filedrop) delegate to their connector."""
    if source.connector != "web":
        try:
            from connectors import get_connector
        except ImportError as exc:
            # The connectors module doesn't exist yet — fail this source with a
            # clear message instead of an ImportError traceback mid-run.
            raise fetch_mod.FetchError(
                f"connector '{source.connector}' is not implemented yet "
                f"(no connectors module) — use connector 'web' for {source.url}"
            ) from exc
        return get_connector(source.connector)(source, log)

    pages: list[fetch_mod.FetchedPage] = []
    root = fetch_mod.fetch_page(source.url)

    if not source.follow_links:
        return [root]

    urls = fetch_mod.discover_links(root, source.include_prefix)[: source.max_pages]
    log(f"  {source.url} → {len(urls)} linked pages")

    # Adaptive sources stop early once linked pages stop adding new information;
    # exhaustive fan-outs (adaptive=False) fetch every candidate up to max_pages.
    tracker = adaptive_mod.SaturationTracker() if source.adaptive else None
    for i, url in enumerate(urls):
        try:
            page = fetch_mod.fetch_page(url)
        except fetch_mod.FetchError as exc:
            log(f"    ✗ {url}: {exc}")
            continue
        pages.append(page)
        if tracker is not None:
            tracker.observe(page.text)
            if tracker.should_stop():
                log(f"    ⤶ adaptive stop: content saturated after {len(pages)} pages "
                    f"({len(urls) - i - 1} candidates skipped)")
                break
    # Root pages of link-following sources are usually just link hubs;
    # include the root only if it has real content of its own.
    if len(root.text) > 500:
        pages.insert(0, root)
    return pages


def _extract_css_schema(page: fetch_mod.FetchedPage, school: str, category: str,
                        schema_store, llm, log) -> list[dict]:
    """Zero-LLM structured extraction via a cached CSS schema. The schema is
    generated once per (school, category) from the first HTML page and reused
    for every page and every re-crawl. Falls back to the LLM extractor when the
    page isn't HTML, no schema can be built, or the schema matches nothing on a
    page (a template variant / stale selectors) — so coverage never regresses.
    """
    fallback = "llm_courses" if category == "courses" else "llm_generic"
    if page.kind != "html" or not page.html:
        return extract_mod.extract(fallback, page.text, page.url, category, llm)

    schema = schema_store.get_or_generate(school, category, page.html, llm, log=log)
    if schema:
        items = css_schema_mod.apply_schema(schema, page.html)
        records = css_schema_mod.records_from_items(items, category, page.url)
        if records:
            return records
        log(f"    css_schema matched nothing on {page.url} — LLM fallback")
    return extract_mod.extract(fallback, page.text, page.url, category, llm)


def run_category(school: str, category: str, sources: list[Source], state: IngestState,
                 *, force: bool = False, dry_run: bool = False, replay: bool = False,
                 openai_client=None, index=None, llm=None, log=print) -> CategoryResult:
    result = CategoryResult(category=category, status="ok")
    run_id = state.start_run(school, category)

    try:
        if llm is None:
            llm = extract_mod.OpenAILLM()

        records: list[dict] = []
        skipped_pages = 0
        schema_store = css_schema_mod.SchemaStore(PREVIEW_DIR)

        if replay:
            records = _replay_pages(state, school, category, result, llm, log)
            if result.pages_fetched == 0:
                result.status = "failed"
                result.message = (f"No raw pages stored for {school}/{category} — "
                                  f"run a normal ingest first to populate the raw lake.")
                state.finish_run(run_id, "failed", 0, 0, 0, result.message)
                return result
            result.pages_changed = result.pages_fetched

        for source in ([] if replay else [s for s in sources if s.category == category]):
            extractor = source.resolve_extractor()
            try:
                pages = _gather_pages(source, log)
            except fetch_mod.FetchError as exc:
                log(f"  ✗ {source.url}: {exc}")
                state.record_page(source.url, school, category, None, "error", str(exc))
                continue

            for page in pages:
                result.pages_fetched += 1
                # Persist every fetched page (even unchanged/skipped ones) so the
                # raw lake always mirrors the latest crawl.
                _persist_raw(state, page, school, category, extractor, log)
                previous_hash = state.get_page_hash(page.url)
                changed = previous_hash != page.content_hash

                if not changed and not force:
                    skipped_pages += 1
                    state.record_page(page.url, school, category, page.content_hash, "skipped")
                    continue

                if changed:
                    result.pages_changed += 1

                # BM25 fit-filter: prune boilerplate to category-relevant blocks
                # before extraction. Skipped for course_regex (layout-sensitive)
                # and css_schema (works on raw HTML, not cleaned text). The raw
                # lake still stores full page text, so --reextract stays lossless.
                text = page.text
                if source.fit and extractor not in ("course_regex", "css_schema"):
                    fr = fit_mod.fit_text(text, fit_mod.query_for(category, source.fit_query))
                    if fr.reduced:
                        log(f"    ⧉ fit: kept {fr.blocks_kept}/{fr.blocks_total} blocks, "
                            f"−{fr.pct_removed}% chars")
                    text = fr.text

                try:
                    if extractor == "css_schema":
                        page_records = _extract_css_schema(
                            page, school, category, schema_store, llm, log)
                    else:
                        page_records = extract_mod.extract(extractor, text, page.url, category, llm)
                    records.extend(page_records)
                    state.record_page(page.url, school, category, page.content_hash, "ok", changed=changed)
                    log(f"  ✓ {page.url} → {len(page_records)} records ({extractor})")
                except Exception as exc:
                    state.record_page(page.url, school, category, page.content_hash, "error", str(exc))
                    log(f"  ✗ extract {page.url}: {exc}")

        # Dedupe across pages (a course can appear on two department pages)
        by_id: dict[str, dict] = {}
        for r in records:
            by_id[r["id"]] = r
        records = list(by_id.values())

        # Per-record validation: quarantine bad or contradictory records
        # instead of publishing them. A failed validation distrusts the NEW
        # value, not the old one — so quarantined IDs also keep their
        # previously-live vector (excluded from stale deletion below).
        records, quarantined = validate_mod.screen(records, category)
        result.quarantined = len(quarantined)
        for rec, reasons in quarantined:
            if not dry_run:
                state.add_quarantine(school, category, rec, reasons, run_id)
            log(f"  ⚠ quarantined {rec['id']}: {'; '.join(reasons)}")
        result.records = len(records)

        if result.pages_fetched > 0 and not records and skipped_pages == result.pages_fetched:
            result.status = "skipped"
            result.message = "No pages changed since last run — nothing to do. Use force to re-extract."
            state.finish_run(run_id, "ok", result.pages_fetched, 0, 0, result.message)
            return result

        min_records = max((s.min_records for s in sources if s.category == category), default=1)

        if dry_run:
            result.status = "dry_run"
            result.preview_path = os.path.join(
                PREVIEW_DIR, f"ingest_preview_{school}_{category}.jsonl")
            with open(result.preview_path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            result.message = (
                f"{len(records)} records written to preview (no Pinecone writes)"
                + (f", {result.quarantined} quarantined" if result.quarantined else "")
            )
            state.finish_run(run_id, "dry_run", result.pages_fetched, result.pages_changed,
                             len(records), result.message)
            return result

        if index is None:
            from pinecone import Pinecone
            index = Pinecone(api_key=os.getenv("PINECONE_API_KEY")).Index(
                os.getenv("PINECONE_INDEX_NAME", "knowledge-base"))

        # Full coverage = safe to remove vectors this run didn't produce.
        full_coverage = skipped_pages == 0
        previous = upsert_mod.live_count(index, category)
        if full_coverage:
            upsert_mod.verify(records, min_records, previous, force=force)
        elif not records:
            result.status = "skipped"
            result.message = "Changed pages produced no records; live data untouched."
            state.finish_run(run_id, "ok", result.pages_fetched, result.pages_changed, 0, result.message)
            return result

        vectors = upsert_mod.embed_records(records, openai_client)
        stats = upsert_mod.promote(index, category, records, vectors,
                                   delete_stale=full_coverage,
                                   keep_ids=frozenset(rec["id"] for rec, _ in quarantined),
                                   log=log)
        result.upserted = stats["upserted"]
        result.stale_deleted = stats["stale_deleted"]

        # Mirror into the local BM25 index so hybrid search stays in lockstep
        # with Pinecone. Best-effort: a mirror failure must not fail the run.
        try:
            from search.lexical import LexicalIndex
            LexicalIndex().mirror_promotion(category, records, delete_stale=full_coverage)
        except Exception as exc:
            log(f"  lexical mirror skipped: {exc}")

        result.message = (
            f"{stats['upserted']} live, {stats['stale_deleted']} stale removed"
            + (f", {result.quarantined} quarantined" if result.quarantined else "")
            + ("" if full_coverage else " (incremental — stale cleanup skipped)")
        )
        state.finish_run(run_id, "ok", result.pages_fetched, result.pages_changed,
                         len(records), result.message)

    except upsert_mod.VerificationError as exc:
        result.status = "failed"
        result.message = f"VERIFICATION BLOCKED PROMOTION: {exc}"
        state.finish_run(run_id, "failed", result.pages_fetched, result.pages_changed,
                         result.records, result.message)
    except Exception as exc:
        result.status = "failed"
        result.message = f"{type(exc).__name__}: {exc}"
        log(traceback.format_exc())
        state.finish_run(run_id, "failed", result.pages_fetched, result.pages_changed,
                         result.records, result.message)

    return result


def run_ingest(school: str, category: str | None = None, *, force: bool = False,
               dry_run: bool = False, replay: bool = False, backend_dir: str = BACKEND_DIR,
               openai_client=None, index=None, llm=None,
               state: IngestState | None = None, log=print) -> RunResult:
    state = state or IngestState()
    sources = load_sources(school, backend_dir, state.extra_sources(school))

    if replay:
        # Replay works from the raw lake alone; sources (if configured) still
        # supply min_records floors, but aren't required.
        lake_categories = list(dict.fromkeys(r["category"] for r in state.raw_pages_for(school)))
        if not lake_categories:
            raise ValueError(f"No raw pages stored for school '{school}' — "
                             f"run a normal ingest first to populate the raw lake.")
        wanted = [category] if category else lake_categories
    else:
        if not sources:
            raise ValueError(f"No sources configured for school '{school}' "
                             f"(expected {backend_dir}/schools/{school}/sources.json)")
        wanted = [category] if category else list(dict.fromkeys(s.category for s in sources))

    run = RunResult(school=school)

    for cat in wanted:
        log(f"\n[{school} / {cat}]")
        run.results.append(run_category(
            school, cat, sources, state, force=force, dry_run=dry_run, replay=replay,
            openai_client=openai_client, index=index, llm=llm, log=log))

    return run
