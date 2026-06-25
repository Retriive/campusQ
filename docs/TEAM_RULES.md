# Team Rules

Simple rules for when CampusQ is ready to ship, expand, or freeze.

---

## The three rules

### Rule 1 — Deploy gate
> **Do not deploy to production if smoke tests fail.**

Smoke = 10 questions, must be **10/10**.

```powershell
py evals\quality_gate.py --tier smoke
```

Run against **production URL** before every Render deploy — not just local.

---

### Rule 2 — Expansion gate
> **Do not launch school #2 or run big marketing until core tests pass at 85%+.**

Core = 32 questions, need **27+ correct**.

```powershell
py evals\quality_gate.py --tier core
```

---

### Rule 3 — Quality sprint
> **If core drops below 80%, freeze new features until quality is fixed.**

No new landing pages, no new tools, no new schools — fix the scoreboard first.

---

## What requires a quality gate run

| Change | Run |
|---|---|
| Deploy to Render | Smoke on production |
| Edit system prompt (`main.py`) | Core |
| Edit retrieval / reranker (`retrieval.py`) | Core |
| Change chat model | Core |
| Re-scrape / re-index Carleton data | Core |
| New feature that touches chat | Smoke minimum |

---

## What does NOT need a gate (but still PR review)

- Landing page copy / styling (no AI changes)
- Dashboard UI tweaks
- Internal waitlist page
- Frontend-only changes that don't touch chat API

---

## Deploy checklist

Copy this for every production deploy:

```
[ ] PR reviewed and merged to main
[ ] Render backend deployed from main
[ ] Smoke gate on production URL — 10/10
[ ] Quick manual check: drop COMP 2402 + one deadline question
[ ] Vercel frontend deployed (if frontend changed)
```

---

## Who owns what

| Area | Typical owner | Key files |
|---|---|---|
| AI / chat quality | Backend dev | `main.py`, `retrieval.py`, `citations.py` |
| Quality tests | Anyone on team | `evals/quality_gate.py`, `golden.csv` |
| University data | Backend dev | `scrapers/`, `run_pipeline.py` |
| Student app | Frontend dev | `frontend/` |
| Deploy | Whoever ships | Render + Vercel dashboards |
| Product calls | Mahad | Thresholds, expansion timing |

---

## Carleton beta vs school #2

| Stage | What "ready" means |
|---|---|
| **Carleton closed beta** | Smoke passes on prod. Advisor backup + Report a Problem available. |
| **Carleton public pilot** | Core 85%+ on prod. Thumbs-up trend positive. |
| **School #2** | Core 85%+ on prod. Carleton case study with usage stats. Repeatable scrape pipeline. |

---

## When in doubt

1. Run smoke
2. If it fails, don't ship
3. If it passes, ship
4. Trust the gate over gut feel

---

## Links

- **[How we work on the codebase](HOW_WE_WORK.md)** — rules for cofounders & contributors
- [How to run tests](QUALITY_GATE.md)
- [How to set up locally](GETTING_STARTED.md)
- [How the AI works](HOW_THE_AI_WORKS.md)
