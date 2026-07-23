# CampusQ

**CampusQ** is Retriive's AI academic assistant for university students. Students ask questions about courses, programs, deadlines, and registration — and get answers backed by official university data. Every question also feeds an anonymized weekly intelligence report for advising staff: what students are asking, where official content has gaps, and how much demand happens after hours.

**Live today:** Carleton University (beta)  
**Coming soon:** uOttawa, UofT, Waterloo, Western, McGill (waitlist landing pages)

---

## Start here (team)

| I want to… | Read this |
|---|---|
| Run the app on my laptop | [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) |
| Understand how the AI works | [docs/HOW_THE_AI_WORKS.md](docs/HOW_THE_AI_WORKS.md) |
| Understand how we get university data | [docs/HOW_INGESTION_WORKS.md](docs/HOW_INGESTION_WORKS.md) |
| Run the quality tests before deploy | [docs/QUALITY_GATE.md](docs/QUALITY_GATE.md) |
| See what each folder does | [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md) |
| Know our ship / no-ship rules | [docs/TEAM_RULES.md](docs/TEAM_RULES.md) |
| Pitch CampusQ (positioning, deck, one-liner) | [docs/PITCH.md](docs/PITCH.md) |
| **Start contributing (team rules)** | **[docs/HOW_WE_WORK.md](docs/HOW_WE_WORK.md)** |

---

## Quick start (5 minutes)

### 1. Clone

```bash
git clone https://github.com/Retriive/campusQ.git
cd campusQ
```

### 2. Backend

```bash
cd backend
py -m pip install -r requirements.txt    # Windows — use py -m on Windows
```

Create `backend/.env`:

```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
COHERE_API_KEY=...          # optional — better reranking
```

Start the API:

```bash
py -m uvicorn main:app --reload --port 8000
```

### 3. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

### 4. Run quality check

```bash
cd backend
py evals/quality_gate.py --tier smoke
```

**10/10 = OK to deploy.** See [docs/QUALITY_GATE.md](docs/QUALITY_GATE.md).

---

## Repo layout

```
campusQ/
├── backend/          # Python API — AI, search, scrapers
├── frontend/         # Next.js app — what students see
├── docs/             # Team documentation (start here)
└── README.md         # This file
```

---

## Tech stack (simple version)

| Piece | What we use |
|---|---|
| Student app | Next.js + React |
| API | Python + FastAPI |
| AI answers | OpenAI GPT-4o mini |
| Search / memory | Pinecone (vector database) |
| University data | Scrapers → Pinecone |
| Hosting | Vercel (frontend) + Render (backend) |
| Auth | Clerk |

---

## Current quality scores (local baseline — update after each run)

| Test | Questions | Pass bar | Last known |
|---|---:|---:|---|
| Smoke (deploy) | 10 | 100% | 10/10 ✅ |
| Core (expansion) | 32 | 85% | 30/32 ✅ |

Run tests yourself — don't trust stale numbers. See [docs/QUALITY_GATE.md](docs/QUALITY_GATE.md).

---

## Who to ask

| Topic | Where to look |
|---|---|
| "How do I run it?" | [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) |
| "Why did the AI answer wrong?" | [docs/HOW_THE_AI_WORKS.md](docs/HOW_THE_AI_WORKS.md) → Failure types |
| "Can we deploy?" | [docs/TEAM_RULES.md](docs/TEAM_RULES.md) |
| "How do I add a test question?" | [docs/QUALITY_GATE.md](docs/QUALITY_GATE.md) → Adding questions |

---

**Retriive** · CampusQ · [GitHub](https://github.com/Retriive/campusQ)
