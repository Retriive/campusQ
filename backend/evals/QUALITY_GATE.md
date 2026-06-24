# CampusQ Quality Gate

Official quality policy for **Retriive / CampusQ**. This is the scoreboard that decides whether we ship, expand, or hold.

## The gates

| Gate | Command | Questions | Threshold | Blocks |
|---|---|---:|---:|---|
| **Deploy** | `python evals/quality_gate.py --tier smoke` | 10 smoke tests | **100%** | Production deploys |
| **Expansion** | `python evals/quality_gate.py --tier core` | 32 (smoke + core) | **85%** | New school launch, public marketing push |
| **Regression** | `python evals/quality_gate.py --tier full` | 32 (same as core for now) | **80%** | Nothing automatically — triggers investigation |

### What each gate protects

**Smoke (deploy gate)** — the 10 questions that must never break:

1. Prerequisite logic (COMP 3000 / 2401)
2. Registration actions (drop COMP 2402)
3. Academic standing (CGPA)
4. Fall withdrawal deadline
5. Clarifying question on vague graduation question
6. Instructor lookup (SYSC 3110)
7. Non-existent course (COMP 9999) — no hallucination, no sources
8. Grading scale (B- = 7.0)
9. Program comparison (Software Eng vs CS)
10. Drop vs withdraw distinction

**Core (expansion gate)** — smoke + 22 high-value questions across courses, programs, regulations, registration, deadlines, schedule, and edge cases.

**Full (regression floor)** — currently same dataset as core; expand `datasets/golden.csv` over time from `queries.log`, `no_context.log`, and `feedback.log`.

## How to run

```bash
cd backend
uvicorn main:app --reload          # terminal 1

export OPENAI_API_KEY="..."        # required for LLM judge
python evals/quality_gate.py --tier smoke
python evals/quality_gate.py --tier core
```

Against production:

```bash
CAMPUSQ_API_URL=https://your-api.onrender.com python evals/quality_gate.py --tier smoke
```

Exit codes:

- `0` — gate passed
- `1` — gate failed (do not ship / expand)
- `2` — setup error (API down, missing API key)

Results are saved to `evals/experiments/<timestamp>_<tier>.csv` and `.json`.

## When to run

| Event | Run |
|---|---|
| Before every production deploy | `--tier smoke` |
| Before merging prompt / retrieval / model changes | `--tier core` |
| Weekly on Carleton pilot | `--tier core` |
| Before launching school #2 | `--tier core` must pass at 85%+ |
| After major scraper re-index | `--tier core` |

## How scoring works

Each question goes through two layers:

1. **Deterministic checks** — required phrases, forbidden phrases, no-sources-when-unknown
2. **LLM judge** (`gpt-4o-mini` by default) — grades against `grading_notes` in `datasets/golden.csv`

Both must pass for a question to count as passed.

## Retriive policy (CEO decision)

> **No production deploy if smoke gate fails.**
> **No new school launch if core gate is below 85%.**
> **Any core gate run below 80% triggers a quality sprint — features freeze until fixed.**

## Adding questions

Edit `evals/datasets/golden.csv`. Columns:

| Column | Purpose |
|---|---|
| `tier` | `smoke`, `core`, or `full` |
| `id` | unique ID |
| `category` | grouping for reports |
| `question` | exact question text |
| `grading_notes` | what the LLM judge checks |
| `must_contain` | pipe-separated — **all** required in answer (optional) |
| `must_contain_any` | pipe-separated — **at least one** required in answer (optional) |
| `must_not_contain` | pipe-separated forbidden substrings in answer or sources (optional) |
| `require_no_sources` | `yes` if "I don't know" answers must not show sources |

Pull new rows from production logs — especially `feedback.log` (thumbs down) and `no_context.log` (data gaps).

## Changing thresholds

Thresholds live in `evals/quality_gate.py`:

```python
GATE_THRESHOLDS = {
    "smoke": {"min_pass_rate": 1.00, ...},
    "core":  {"min_pass_rate": 0.85, ...},
    "full":  {"min_pass_rate": 0.80, ...},
}
```

Changing thresholds is a product decision — update this doc when you change them.

## Retrieval / reranker (accuracy)

RAG retrieval uses `backend/retrieval.py`:

1. **Intent-based namespace boosts** — registration → registrar, deadlines → dates, etc.
2. **Reranker** — retrieves ~30 chunks, reranks to top 10 before the LLM
   - **Primary:** Cohere `rerank-english-v3.0` if `COHERE_API_KEY` is set
   - **Fallback:** GPT-4o mini LLM rerank (uses existing `OPENAI_API_KEY`)

Optional on Render/production:

```bash
COHERE_API_KEY=...
```

Cohere is cheaper and faster for reranking; the LLM fallback works without it.

