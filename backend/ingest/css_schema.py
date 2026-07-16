"""Generate-once, extract-free structured extraction via cached CSS schemas.

Borrowed from Crawl4AI's JsonCssExtractionStrategy.generate_schema, adapted to
CampusQ. University sites are template-driven: a catalog's course blocks, a
department's program cards, a schedule's rows — each is ONE repeating layout
across hundreds of records. Paying an LLM per page to re-read that layout is
wasteful and non-deterministic.

Instead:
  1. Once per (school, category), an LLM reads a sample page and writes a CSS
     schema — a baseSelector for the repeating element plus a selector per field.
     The schema is validated against the real HTML and self-healed if selectors
     miss (up to `max_refinements` rounds), then cached to disk.
  2. Every subsequent page — and every re-crawl — is extracted with pure
     BeautifulSoup, zero tokens, deterministic output. This turns "LLM per page"
     into "LLM per template": typically a 10x–1000x token cut, and reproducible
     across runs (no model drift).

The deterministic engine (`apply_schema`) and coverage measurement
(`field_coverage`) have no LLM/network dependency and are fully unit-testable.
Only `generate_schema` calls the LLM, via the same injectable callable the rest
of the pipeline uses (extract.OpenAILLM), so it too is testable with a fake.

Records come out in EXACTLY the same shape as the regex/LLM extractors
(extract._course_record etc.), so vectors stay drop-in compatible.
"""

from __future__ import annotations

import json
import os
import re

from bs4 import BeautifulSoup

from .extract import _ANY_CODE_RE, _course_record, _stable_id

# Fields the schema should target, per category. The LLM is asked to write a
# selector for each; the record mapper below reads them back by these names.
CATEGORY_FIELDS: dict[str, list[str]] = {
    "courses": ["code", "name", "credits", "description", "prerequisites"],
    "programs": ["title", "text"],
    "schedule": ["code", "section", "instructor", "time", "term"],
    "generic": ["title", "text"],
}

# A field below this fill rate across the sample's base elements is treated as a
# broken selector and triggers a self-heal round.
_MIN_FIELD_COVERAGE = 0.5
_MAX_HTML_CHARS = 12000  # cap the sample HTML we hand the LLM (token budget)


# ══════════════════════════════════════════════════════════════════════════
# Deterministic engine — no LLM, no network
# ══════════════════════════════════════════════════════════════════════════

def _field_value(element, field: dict) -> str:
    """Resolve one field against one base element. Never raises — a bad
    selector yields the field's default (or "") so a single broken selector
    can't abort a whole page."""
    selector = field.get("selector", "")
    try:
        target = element.select_one(selector) if selector else element
    except Exception:
        target = None
    if target is None:
        return str(field.get("default", ""))

    ftype = field.get("type", "text")
    if ftype == "attribute":
        raw = target.get(field.get("attribute", ""), "")
    elif ftype == "html":
        raw = target.decode_contents()
    else:  # "text" (and any unknown type) → visible text
        raw = target.get_text(" ", strip=True)

    value = re.sub(r"\s+", " ", str(raw)).strip()

    pattern = field.get("pattern")
    if pattern:
        m = re.search(pattern, value)
        value = (m.group(field.get("group", 0)) if m else "").strip()

    return value or str(field.get("default", ""))


def apply_schema(schema: dict, html: str) -> list[dict]:
    """Run a cached schema against a page. Pure BeautifulSoup, zero tokens.
    Returns one dict per matched base element, keyed by field name."""
    base = schema.get("baseSelector")
    fields = schema.get("fields") or []
    if not base:
        return []
    soup = BeautifulSoup(html, "html.parser")
    try:
        elements = soup.select(base)
    except Exception:
        return []

    items: list[dict] = []
    for el in elements:
        item = {f["name"]: _field_value(el, f) for f in fields if f.get("name")}
        if any(v for v in item.values()):
            items.append(item)
    return items


def field_coverage(schema: dict, html: str) -> tuple[int, dict[str, float]]:
    """(#base elements matched, {field: fraction non-empty}). The signal the
    self-heal loop and stale-schema detection use."""
    items = apply_schema(schema, html)
    n = len(items)
    if n == 0:
        return 0, {f["name"]: 0.0 for f in schema.get("fields", []) if f.get("name")}
    coverage = {}
    for f in schema.get("fields", []):
        name = f.get("name")
        if not name:
            continue
        coverage[name] = sum(1 for it in items if it.get(name)) / n
    return n, coverage


# ══════════════════════════════════════════════════════════════════════════
# Schema generation — the ONE LLM call per template, with self-heal
# ══════════════════════════════════════════════════════════════════════════

_SCHEMA_SYSTEM = """You write CSS extraction schemas for a web scraper. Given an HTML sample and a list of target fields, return ONE JSON object and nothing else:
{"baseSelector": "<css selector for the repeating record element>", "fields": [{"name": "<field>", "selector": "<css selector RELATIVE to the base element>", "type": "text"}]}
Rules:
- baseSelector must select the repeating block (e.g. one course, one program card) — many elements, one per record. Never select the whole page or a unique container.
- Each field selector is relative to a base element. Omit "selector" (or use "") to read the base element itself.
- Prefer durable selectors: semantic tags, data-* attributes, and meaning-bearing class names. NEVER use hashed/CSS-in-JS classes (e.g. .css-1a2b3c, .sc-bdnxRM) or nth-child.
- Use type "text" for visible text, "attribute" (+ "attribute": "href") for attributes.
- Return valid JSON parseable by json.loads. No comments, no prose, no code fences."""


def _build_user_prompt(html: str, fields: list[str], feedback: str = "") -> str:
    sample = html[:_MAX_HTML_CHARS]
    parts = [
        f"Target fields: {', '.join(fields)}",
        "",
        "HTML sample:",
        sample,
    ]
    if feedback:
        parts += ["", "Your previous schema had problems — fix them:", feedback]
    return "\n".join(parts)


def _parse_schema(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(data, dict) or not data.get("baseSelector"):
        return {}
    fields = [f for f in data.get("fields", []) if isinstance(f, dict) and f.get("name")]
    return {"baseSelector": data["baseSelector"], "fields": fields}


def _feedback(schema: dict, html: str, fields: list[str]) -> str:
    """Diagnostic handed back to the LLM when a schema underperforms."""
    n, coverage = field_coverage(schema, html)
    if n == 0:
        soup = BeautifulSoup(html, "html.parser")
        tags = [t.name for t in soup.find_all(True, recursive=True)][:40]
        return (f"baseSelector '{schema['baseSelector']}' matched 0 elements. "
                f"Tags present near the top: {', '.join(dict.fromkeys(tags))}. "
                f"Pick a selector for the repeating record element.")
    weak = [f for f in fields if coverage.get(f, 0.0) < _MIN_FIELD_COVERAGE]
    return (f"baseSelector matched {n} elements. "
            f"These field selectors returned empty on most elements: {', '.join(weak)}. "
            f"Fix their selectors (they must be relative to a base element).")


def _schema_is_good(schema: dict, html: str, fields: list[str]) -> bool:
    n, coverage = field_coverage(schema, html)
    if n == 0:
        return False
    # Require the majority of target fields to populate on most records.
    populated = sum(1 for f in fields if coverage.get(f, 0.0) >= _MIN_FIELD_COVERAGE)
    return populated >= max(1, (len(fields) + 1) // 2)


def generate_schema(html: str, category: str, llm, *, max_refinements: int = 3,
                    log=lambda *_: None) -> dict:
    """Ask the LLM to author a CSS schema for `category`, then validate + self-heal
    against the real HTML. Returns {} if no usable schema emerges (caller then
    falls back to LLM-per-page extraction)."""
    fields = CATEGORY_FIELDS.get(category, CATEGORY_FIELDS["generic"])
    feedback = ""
    best: dict = {}
    for attempt in range(max_refinements + 1):
        raw = llm(_SCHEMA_SYSTEM, _build_user_prompt(html, fields, feedback))
        schema = _parse_schema(raw)
        if not schema:
            log(f"    schema gen attempt {attempt + 1}: unparseable, retrying")
            feedback = "Your last response was not valid JSON. Return only the JSON object."
            continue
        n, coverage = field_coverage(schema, html)
        log(f"    schema gen attempt {attempt + 1}: {n} records, coverage="
            + ", ".join(f"{k}={v:.0%}" for k, v in coverage.items()))
        if _schema_is_good(schema, html, fields):
            return schema
        best = schema if n > 0 else best
        feedback = _feedback(schema, html, fields)
    # Best effort: return the best non-empty schema even if imperfect.
    return best


# ══════════════════════════════════════════════════════════════════════════
# On-disk schema cache
# ══════════════════════════════════════════════════════════════════════════

class SchemaStore:
    """Per-school JSON file mapping category -> cached schema. Lives on the same
    persistent disk as the raw lake so schemas survive across runs."""

    def __init__(self, base_dir: str):
        self.dir = os.path.join(base_dir, "ingest_schemas")

    def _path(self, school: str) -> str:
        return os.path.join(self.dir, f"{school}.json")

    def _load(self, school: str) -> dict:
        try:
            with open(self._path(school), "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def get(self, school: str, category: str) -> dict:
        return self._load(school).get(category, {})

    def put(self, school: str, category: str, schema: dict) -> None:
        data = self._load(school)
        data[category] = schema
        os.makedirs(self.dir, exist_ok=True)
        with open(self._path(school), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_or_generate(self, school: str, category: str, html: str, llm,
                        *, log=lambda *_: None) -> dict:
        cached = self.get(school, category)
        if cached:
            return cached
        log(f"  generating CSS schema for {school}/{category} (one LLM call)")
        schema = generate_schema(html, category, llm, log=log)
        if schema:
            self.put(school, category, schema)
        return schema


# ══════════════════════════════════════════════════════════════════════════
# Field dicts -> the same record contract the other extractors emit
# ══════════════════════════════════════════════════════════════════════════

def _parse_credits(raw: str, default: float = 0.5) -> float:
    m = re.search(r"[\d.]+", raw or "")
    try:
        return float(m.group(0)) if m else default
    except ValueError:
        return default


def records_from_items(items: list[dict], category: str, source_url: str) -> list[dict]:
    """Map schema-extracted field dicts into id/embed_text/metadata records,
    identical in shape to the regex/LLM extractors so retrieval is unaffected."""
    records: list[dict] = []
    seen: set[str] = set()

    if category == "courses":
        for it in items:
            code = (it.get("code") or "").strip()
            name = (it.get("name") or "").strip()
            if not code or not name or not _ANY_CODE_RE.search(code.upper()):
                continue
            rec = _course_record(
                code=code,
                name=name,
                credits=_parse_credits(it.get("credits")),
                description=(it.get("description") or "").strip(),
                prereq_text=(it.get("prerequisites") or "").strip().rstrip("."),
                source_url=source_url,
            )
            if rec["id"] in seen:
                continue
            seen.add(rec["id"])
            records.append(rec)
        return records

    # Generic: build a self-contained chunk per record from its fields.
    for it in items:
        title = (it.get("title") or it.get("name") or "").strip()
        body = (it.get("text") or it.get("description") or "").strip()
        if not body:
            # No dedicated body field — stitch the remaining fields together.
            body = ". ".join(v.strip() for k, v in it.items()
                             if k not in ("title", "name") and v and v.strip())
        if not body or len(body) < 40:
            continue
        rid = _stable_id(source_url, title.lower(), body[:200])
        if rid in seen:
            continue
        seen.add(rid)
        records.append({
            "id": f"{category}-{rid}",
            "embed_text": f"{title}. {body}",
            "metadata": {
                "title": title or category,
                "category": category,
                "text": body[:2500],
                "source": source_url,
            },
        })
    return records
