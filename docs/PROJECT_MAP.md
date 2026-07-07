# Project Map

What's in each folder and where to look when something breaks.

---

## Top level

```
campusQ/
├── README.md           ← Start here
├── docs/               ← Team guides (you are here)
├── backend/            ← Python API + AI + data
└── frontend/           ← Next.js student app
```

---

## Backend (`backend/`)

| Path | What it is |
|---|---|
| `main.py` | **The brain.** Chat API, system prompt, logging |
| `retrieval.py` | Search Pinecone, intent routing, reranker |
| `citations.py` | Formats source links on answers |
| `dashboard.py` | Advisor analytics API + question clustering |
| `advisor_report.py` | External Student Questions Report (text + HTML) for university staff |
| `send_advisor_report.py` | Emails the advisor report (schedule Mondays, like `send_digest.py`) |
| `run_pipeline.py` | Runs all data scrapers |
| `wipe.py` | Clears Pinecone before full re-index |
| `requirements.txt` | Python dependencies |
| `.env` | API keys (not in git — create locally) |

### Scrapers (`backend/scrapers/active/`)

Scripts that pull Carleton data into Pinecone:

| Script | Data |
|---|---|
| `scrape_courses.py` | Course catalog |
| `scrape_programs.py` | Program requirements |
| `scrape_regulations.py` | Academic regulations |
| `scrape_registrar.py` | Registration info |
| `scrape_dates.py` | Deadlines |
| `ingest_schedule.py` | Class schedules |
| `scrape_campus.py` | Campus services |
| `scrape_tuition.py` | Tuition/fees |
| `scrape_facts.py` | General facts |
| `scrape_library.py` | Library info |

### Quality (`backend/evals/`)

| Path | What it is |
|---|---|
| `quality_gate.py` | **Run this before deploy** |
| `datasets/golden.csv` | Test questions + grading rules |
| `experiments/` | Test results (auto-generated) |
| `QUALITY_GATE.md` | Short pointer → see `docs/QUALITY_GATE.md` |

### Tests (`backend/tests/`)

| File | Tests |
|---|---|
| `test_citations.py` | Citation formatting |
| `test_retrieval_rerank.py` | Query routing |
| `test_gap_report.py` | Question clustering + advisor gap report |
| `test_schedule_chatbot.py` | Schedule questions (manual harness) |
| `run_eval.py` | Older 65-question harness (diagnostics) |

### Data (`backend/data/`)

| File | What it is |
|---|---|
| `program_requirements.json` | Structured program data for Program Explorer |

### Logs (created at runtime, not in git)

| File | What it tracks |
|---|---|
| `queries.log` | Every chat question + retrieval stats |
| `feedback.log` | Thumbs up/down |
| `no_context.log` | Questions where search found nothing |
| `course_misses.log` | Course codes not in database |
| `reports.log` | "Report a Problem" submissions |

---

## Frontend (`frontend/`)

| Path | What it is |
|---|---|
| `app/` | Pages (landing, chat, dashboard, about) |
| `components/campus-q/` | Chat UI, program explorer, deadline tracker |
| `components/landing/` | Multi-university landing pages |
| `lib/` | Shared utilities |

### Key pages

| URL | File | Purpose |
|---|---|---|
| `/` | `app/page.tsx` | Landing page |
| `/chat` | `app/chat/page.tsx` | Main chatbot |
| `/dashboard` | `app/dashboard/page.tsx` | Advisor analytics |
| `/about` | `app/about/page.tsx` | About page |
| `/internal/waitlist` | `app/internal/waitlist/page.tsx` | Waitlist signups (internal) |

---

## Hosting

| What | Where |
|---|---|
| Frontend | Vercel |
| Backend API | Render |
| Vector DB | Pinecone |
| Auth | Clerk |
| Repo | github.com/Retriive/campusQ |

---

## "Something broke" — where to look

| Symptom | Check |
|---|---|
| Wrong answer | `queries.log` → retrieval scores. Then `retrieval.py` / `main.py` prompt |
| No answer / "I don't know" | `no_context.log` → data gap → run scrapers |
| Course not found | `course_misses.log` → `scrape_courses.py` |
| Bad source links | `citations.py` |
| Deploy broke chat | Run smoke gate on production |
| Frontend won't load | `frontend/` console errors, `NEXT_PUBLIC_API_URL` |

---

## Docs index

| Doc | For |
|---|---|
| [GETTING_STARTED.md](GETTING_STARTED.md) | First-time setup |
| [HOW_THE_AI_WORKS.md](HOW_THE_AI_WORKS.md) | Understanding the pipeline |
| [QUALITY_GATE.md](QUALITY_GATE.md) | Testing before deploy |
| [TEAM_RULES.md](TEAM_RULES.md) | Ship / no-ship policy |
| [HOW_WE_WORK.md](HOW_WE_WORK.md) | Contribution rules for the team |
