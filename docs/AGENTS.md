# Agent mode, hybrid search, and connectors — what was added and how to test it

Three additions, all **beside** the existing system, none replacing it. The
chatbot your users use today is untouched; each new piece has its own switch.

## 1. Agent mode (`/api/agent/chat`)

The current chat does one retrieval pass and answers. The agent **plans**:
it breaks a question into parts, makes several precise lookups (semantic
search, exact course fetches, structured degree plans), and only then writes
one cited answer. The difference shows on exactly the questions that make
demos impressive:

- *"Compare Software Engineering and CS, and tell me which first-year courses overlap"* — the agent searches each program separately, pulls both degree plans, cross-references.
- *"I've done COMP 1005 and 1006 — what can I take next term?"* — course lookups + prerequisite data + schedule search, chained.

It streams progress events (`"Searching the knowledge base…"`, `"Loading
degree plan…"`) so a future UI can show its work — that visible reasoning is
a selling point in pilots, not just engineering.

**Guardrails:** max 5 tool rounds, 60-second budget, duplicate calls served
from cache, same auth + rate limits as normal chat, same "never invent facts"
prompt rules, same advisor-escalation for high-stakes questions.

**Test locally** (backend running via `uvicorn main:app --reload`):

```bash
curl -N -X POST http://localhost:8000/api/agent/chat \
  -F "question=Compare software engineering and computer science programs" \
  -F "history=[]"
```

You'll see `step` events as it works, then the answer and sources.
**Kill switch:** `AGENT_MODE=off` in `.env` → the endpoint returns 404.
Cost note: a complex question costs 3–6 model calls instead of 1–2 (still
gpt-4o-mini, so a few cents at worst).

## 2. Hybrid search (`HYBRID_SEARCH=true`)

Embeddings understand meaning but fumble exact tokens — acronyms (CUSA,
PMC), form names, fee line items. Hybrid search adds a classic keyword index
(SQLite FTS5 — no new service, no new cost) that mirrors everything the
ingestion pipeline writes to Pinecone, and merges both result lists with
Reciprocal Rank Fusion before the reranker.

- **Off by default.** Turn on with `HYBRID_SEARCH=true` in `.env`.
- If the keyword index is missing or errors, retrieval silently falls back
  to today's pure vector search — it cannot break chat.
- The index (`lexical_index.db`) fills automatically the next time the
  ingestion pipeline runs a category.

**Test locally:** run any ingest category, set the flag, ask something
acronym-heavy, and look for `Hybrid: fused N lexical hits into pool` in the
backend logs.

## 3. Connectors (sources.json `"connector"` field)

Ingestion previously spoke one language: web pages. Now a source can say how
its content arrives:

| Connector | What it ingests | Why it matters |
|---|---|---|
| `web` (default) | A URL, optionally crawling same-prefix links | Today's behavior, unchanged |
| `sitemap` | Every page listed in a sitemap.xml under a prefix | The site's own page inventory — nothing hidden behind JS menus gets missed |
| `ics` | An iCalendar feed → clean dated events | Universities publish academic dates as `.ics`; this is machine-readable truth, no scraping fragility |
| `filedrop` | A local folder of PDFs / HTML / text | The B2B reality: a registrar emails you a fee PDF long before they fix their website. Drop it in a folder, ingest it. |

Example additions to `backend/schools/<school>/sources.json`:

```json
{ "category": "dates", "url": "https://school.ca/academic-dates.ics", "connector": "ics" },
{ "category": "registrar", "url": "C:/CampusQ-drop/registrar-docs", "connector": "filedrop", "extractor": "llm_generic" }
```

Everything downstream is identical: dry-run previews, change detection,
shrink guard, never-empty promotion, and the new lexical mirror all apply to
every connector. `py -m ingest.run --school carleton --category dates --dry-run`
works the same regardless of where the content came from.

## Testing everything offline

```bash
cd backend
py -m pytest tests/test_agents.py tests/test_hybrid_search.py tests/test_connectors.py -q
```

29 tests, no network, no API keys — fakes stand in for the LLM, Pinecone, and
the web, same pattern as `test_ingest.py`.

## What this sets up next

- **Frontend agent view** — the `step` events are already streaming; a UI
  that shows "checked 2 programs, 4 courses" turns invisible quality into a
  visible demo moment.
- **More connectors** — the registry pattern makes SharePoint/Google Drive
  (where registrar offices actually keep documents) a contained follow-up
  each.
- **Namespace-per-school** — the roadmap's multi-tenancy step slots in
  underneath all of this unchanged; agent tools and hybrid search both go
  through the same retrieval layer that will get the school dimension.
