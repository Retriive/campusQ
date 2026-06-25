# How We Work on CampusQ

Rules for cofounders and team members working in the codebase.  
**Read this before your first PR.**

---

## The 7 rules (memorize these)

### 1. Never push directly to `main`
All changes go through a **pull request**. No exceptions.

### 2. Never commit secrets
API keys live in `backend/.env` only — that file is **not** in git.  
Don't paste keys in Slack, PRs, or chat.

### 3. Run smoke before you ask to deploy
If your change touches the chatbot or backend API:

```powershell
cd backend
py evals\quality_gate.py --tier smoke
```

**10/10 required** before production deploy. See [TEAM_RULES.md](TEAM_RULES.md).

### 4. Small PRs win
One feature or one fix per PR. Easier to review, easier to revert.

### 5. If smoke breaks, you fix it
Don't merge if smoke fails. Don't deploy if smoke fails on production.

### 6. Ask before changing the scoreboard
Editing `golden.csv` thresholds or pass rates = talk to **Mahad** first.

### 7. When stuck, read the docs
Start at [README.md](../README.md) → pick the guide for your task.

---

## Day 1 — get running (everyone)

| Step | Action |
|------|--------|
| 1 | Get GitHub access to [Retriive/campusQ](https://github.com/Retriive/campusQ) |
| 2 | Clone: `git clone https://github.com/Retriive/campusQ.git` |
| 3 | Ask Mahad for API keys → create `backend/.env` |
| 4 | Follow [GETTING_STARTED.md](GETTING_STARTED.md) — run backend + frontend |
| 5 | Run smoke once to confirm your setup works |
| 6 | Read [PROJECT_MAP.md](PROJECT_MAP.md) — know where things live |

**Your folder path (Windows):** `C:\Users\Mahad\CampusQ\campusQ`  
(Repo is `campusQ` inside `CampusQ`.)

---

## How we ship code

```
1. Pull latest main
2. Create a branch
3. Make your change
4. Test locally
5. Push branch → open PR on GitHub
6. Someone reviews (Mahad or teammate)
7. Merge to main
8. Deploy (Render / Vercel) — only after smoke on prod if backend changed
```

### Branch naming

Use clear names:

```
feature/add-uottawa-landing
fix/citation-titles
docs/update-readme
```

No random branch names. Lowercase, hyphens, describe the work.

### PR description (copy this template)

```markdown
## What changed
[1-2 sentences]

## Why
[Student impact or bug being fixed]

## How to test
1. ...
2. ...

## Quality gate
[ ] Smoke run locally — result: __/10
[ ] N/A — frontend only, no chat changes
```

### Who merges?

| Change type | Who approves |
|-------------|--------------|
| Copy, styling, docs | Any cofounder |
| Chat / AI / retrieval | Mahad or designated backend lead |
| Quality gate / golden tests | Mahad |
| Deploy to production | Mahad signs off + smoke on prod |
| New school / expansion | Mahad + product decision |

---

## What to work on (safe starting points)

Good first tasks for new contributors:

| Area | Examples | Risk |
|------|----------|------|
| **Docs** | Fix typos, add FAQs to `docs/` | Low |
| **Frontend UI** | Landing pages, styling, copy | Low |
| **Quality tests** | Add questions to `golden.csv` (with review) | Medium |
| **Logs / analytics** | Parse `feedback.log`, dashboard tweaks | Medium |
| **Scrapers** | Update Carleton data scripts | Medium — run core gate after |
| **Chat / AI** | Prompt, retrieval, model changes | High — core gate required |

---

## What requires extra care

| Don't touch without asking | Why |
|---------------------------|-----|
| `main.py` system prompt | Changes every answer |
| `retrieval.py` / `citations.py` | Changes what AI finds and cites |
| `golden.csv` pass thresholds | Changes deploy policy |
| `wipe.py` / full re-index | Can wipe production data in Pinecone |
| Render / Vercel env vars | Can break production |
| Clerk auth config | Can lock users out |

---

## Testing rules by change type

| You changed… | Run before PR |
|--------------|---------------|
| Chat, prompts, retrieval, model | `py evals\quality_gate.py --tier core` |
| Scrapers / re-indexed data | `py evals\quality_gate.py --tier core` |
| Small backend fix | `py evals\quality_gate.py --tier smoke` |
| Frontend only (no API) | Manual check in browser |
| Docs only | No gate needed |

Full guide: [QUALITY_GATE.md](QUALITY_GATE.md)  
Ship policy: [TEAM_RULES.md](TEAM_RULES.md)

---

## Environment & secrets

### `backend/.env` (required locally)

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
COHERE_API_KEY=...    # optional but recommended
```

### Rules

- **Never** commit `.env`
- **Never** share keys in GitHub issues or PR comments
- Production keys live in **Render** and **Vercel** dashboards only
- If a key leaks → tell Mahad immediately → rotate the key

---

## Repo map (30 seconds)

```
campusQ/
├── backend/     ← Python API, AI, scrapers, quality tests
├── frontend/    ← Next.js student app
├── docs/        ← Team guides (start here)
└── README.md    ← Entry point
```

Details: [PROJECT_MAP.md](PROJECT_MAP.md)

---

## Who owns what

| Area | Primary | Backup |
|------|---------|--------|
| Product & deploy calls | Mahad | — |
| Engineering / architecture | Salama (CTO) | — |
| AI / chat quality | Backend lead | Mahad |
| Frontend / student app | Frontend lead | Any dev |
| University data / scrapers | Backend lead | — |
| Quality gate & tests | Anyone | Mahad reviews |
| Infrastructure (Render, Vercel) | Whoever ships | Mahad |

**Current task — Salama (CTO):** [Prompt guardrails & safety](assignments/SALAMA_PROMPT_GUARDRAILS.md) *(assigned work, not a standing owner role)*

**Not assigned yet?** Pick an area, tell the team in Slack, own it.

---

## Definition of done

A task is **done** when:

- [ ] Code is on a branch (not local-only)
- [ ] PR is open with description + how to test
- [ ] Quality gate run (if applicable) — result noted in PR
- [ ] Reviewed and merged to `main`
- [ ] Deployed (if user-facing) — smoke on **production** if backend changed
- [ ] Mahad knows if it's a student-facing change

---

## Communication

| When | Where |
|------|-------|
| "I'm starting X" | Team chat — avoid duplicate work |
| PR ready for review | GitHub PR + ping reviewer |
| Smoke failed | Post failure + CSV path — don't hide it |
| Production issue | Mahad + `#incidents` or team chat immediately |
| "Can we ship?" | Check smoke on prod first, then ask |

---

## Carleton beta → expansion (reminder)

| Milestone | Gate |
|-----------|------|
| Deploy to production | Smoke **10/10 on prod** |
| Carleton public pilot | Core **≥ 85% on prod** |
| School #2 | Core **≥ 85% on prod** + repeatable pipeline |

---

## Quick links

| Doc | Purpose |
|-----|---------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Clone, env, run locally |
| [HOW_THE_AI_WORKS.md](HOW_THE_AI_WORKS.md) | AI pipeline |
| [QUALITY_GATE.md](QUALITY_GATE.md) | Run tests |
| [TEAM_RULES.md](TEAM_RULES.md) | Deploy / freeze policy |
| [PROJECT_MAP.md](PROJECT_MAP.md) | Folder guide |

---

## First-week checklist (for new cofounders)

```
[ ] Repo cloned and app runs locally
[ ] Smoke test run successfully (10/10)
[ ] Read HOW_WE_WORK.md (this file)
[ ] Read GETTING_STARTED.md + PROJECT_MAP.md
[ ] Picked an area to own (frontend / backend / data / docs)
[ ] Made a small PR (docs or UI tweak) to learn the flow
[ ] Joined GitHub repo with write access
```

---

**Questions?** Ask Mahad.  
**Broken build?** Post in team chat with error + what you ran.  
**Ready to ship?** Smoke on prod first.
