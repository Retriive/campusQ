# How the AI Works

Plain-English guide to CampusQ's brain. No PhD required.

---

## The one-sentence version

CampusQ **searches Carleton's official data**, picks the best pieces, and **asks GPT to answer using only that data** — with source links students can verify.

---

## The pipeline (what happens when a student asks a question)

```
Student types a question
        ↓
1. FIGURE OUT what kind of question it is
   (prerequisite? deadline? registration? program?)
        ↓
2. SEARCH Pinecone across categories
   (courses, programs, regulations, dates, registrar, schedule…)
   → finds ~30 text chunks
        ↓
3. RERANK — pick the best 10 chunks
   (Cohere reranker, or GPT fallback)
        ↓
4. SEND those 10 chunks + question to GPT-4o mini
        ↓
5. RETURN answer + source links
```

---

## The two types of answers

### Type A — Structured tools (most accurate)

Some features **don't use the chatbot** for the actual data:

| Feature | How it works |
|---|---|
| **Program Explorer** | Reads `program_requirements.json` — instant, no AI |
| **Deadline tracker** | Structured date data |
| **Course lookup by code** | Direct database fetch |

**Rule:** If we can answer without AI, we should. That's why Program Explorer is always right.

### Type B — Chat (RAG)

Everything else goes through the pipeline above. This is where quality work happens.

---

## Where the data lives (Pinecone namespaces)

Think of Pinecone as a filing cabinet. Each drawer is a **namespace**:

| Namespace | What's in it |
|---|---|
| `courses` | Course descriptions, prerequisites, credits |
| `programs` | Degree requirements |
| `regulations` | Academic rules, CGPA, grading |
| `registrar` | Registration, overrides, appeals |
| `dates` | Deadlines (add, drop, withdraw, exams) |
| `schedule` | Who teaches what, when, open/closed sections |
| `services` | Co-op, financial aid, transcripts |
| `tuition` | Fees |
| `facts` | General university facts |

**Intent routing** steers the search to the right drawers. Example: "How do I drop a course?" boosts `registrar` and `dates`.

---

## What makes answers go wrong (3 failure types)

When a test fails, it's usually one of these:

| Type | What happened | Fix |
|---|---|---|
| **Data gap** | We don't have the info indexed | Run scrapers, add data to Pinecone |
| **Bad retrieval** | We have it but didn't find the right chunk | Reranker, chunking, intent routing |
| **Bad generation** | Right chunks found but GPT answered wrong | System prompt, model change |

The quality gate CSV tells you which type — look at the `reason` column.

---

## Special behaviors (built on purpose)

| Behavior | Example |
|---|---|
| **Asks for clarification** | "How many credits to graduate?" → asks which program |
| **Says "I don't know"** | "What is COMP 9999?" → won't invent a fake course |
| **No sources on "I don't know"** | COMP 9999 → answer only, no citation pills |
| **Asks for term** | "Drop COMP 2402" → asks Fall/Winter/Summer before giving a deadline |
| **Declines prof ratings** | "Is Professor Smith good?" → RateMyProfessors suggestion |
| **Points to Carleton Central** | Registration, CGPA, transcripts → mentions official tools |

---

## Key files (for developers)

| File | What it does |
|---|---|
| `backend/main.py` | API endpoints, chat flow, system prompt |
| `backend/retrieval.py` | Search + intent boosts + reranker |
| `backend/citations.py` | Source link formatting |
| `backend/ingestion/` | Canonical ingestion pipeline namespace |
| `backend/scrapers/` | Legacy scraper workflow (reference/archive) |
| `backend/evals/quality_gate.py` | Automated quality tests |

---

## Refreshing university data

When Carleton updates the calendar:

```bash
cd backend
py -m ingestion.run --school carleton --force
```

For a single category:

```bash
py -m ingestion.run --school carleton --category courses
py -m ingestion.run --school carleton --category dates
```

---

## Model & cost

| Component | Model |
|---|---|
| Chat answers | GPT-4o mini |
| Embeddings (search) | text-embedding-3-small |
| Reranker (preferred) | Cohere rerank-english-v3.0 |
| Reranker (fallback) | GPT-4o mini |
| Quality test judge | GPT-4o mini |

---

## Further reading

- [Quality gate](QUALITY_GATE.md) — how we test this
- [Team rules](TEAM_RULES.md) — when we're allowed to ship
- [Project map](PROJECT_MAP.md) — every folder explained
