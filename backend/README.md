# CampusQ Backend

FastAPI server that powers CampusQ chat, retrieval, and quality testing.

**New to the project?** Start at the [main README](../README.md) and [Getting Started](../docs/GETTING_STARTED.md).

---

## What this folder does

| File / folder | Purpose |
|---------------|---------|
| `main.py` | FastAPI app entrypoint (chat + admin APIs) |
| `retrieval.py` | Search Pinecone, rerank results |
| `citations.py` | Format and filter source links |
| `ingestion/` | **Canonical ingestion workflow + CLI wrappers** |
| `ingest/` | Backward-compatible ingestion namespace (legacy import path) |
| `scrapers/` | Legacy scraper workflow kept for reference only |
| `scripts/` | One-off operational/debug scripts (non-pytest) |
| `evals/` | Automated quality tests |
| `tests/` | Deterministic pytest unit/integration tests only |
| `data/` | Scraped calendar text files |
| `requirements.txt` | Python dependencies |

---

## Run locally

```powershell
cd backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## Environment variables

Create `backend/.env`:

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
COHERE_API_KEY=...   # optional — better reranking
```

---

## Main endpoints

| Endpoint | What it does |
|----------|--------------|
| `POST /api/chat` | Main chat (used by frontend) |
| `POST /api/chat/stream` | Streaming chat |
| `GET /` | Health check |
| `GET /docs` | Interactive API docs |

---

## Ingestion (canonical workflow)

Use the canonical ingestion namespace:

```powershell
py -m ingestion.run --school carleton --list
py -m ingestion.run --school carleton --category dates
py -m ingestion.run --school carleton --force
```

Legacy commands still work, but they now print a deprecation notice:

- `py run_pipeline.py ...`
- imports from `ingest.*`

---

## Run quality tests

Server must be running first.

```powershell
py evals\quality_gate.py --tier smoke
py evals\quality_gate.py --tier core
py evals\run_eval.py
py evals\schedule_chatbot_eval.py
```

Full guide: [docs/QUALITY_GATE.md](../docs/QUALITY_GATE.md)

---

## Logs (useful for debugging)

| File | What's in it |
|------|--------------|
| `feedback.log` | User thumbs up/down |
| `no_context.log` | Questions where retrieval found nothing |
| `evals/experiments/` | Quality gate CSV + JSON reports |

---

## Key concepts

**Namespaces** — Pinecone stores data in buckets: `courses`, `programs`, `policies`, `services`, `general`.

**Intent routing** — Questions are classified (course, program, policy, etc.) so search looks in the right buckets.

**Reranking** — After initial search, results are re-scored so the best chunks reach the AI.

Details: [How the AI Works](../docs/HOW_THE_AI_WORKS.md)
