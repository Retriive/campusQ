# Task: GitHub Actions smoke gate on production

**Assigned to:** Abdulla  
**Reviewer:** Mahad (required before merge)  
**Area:** CI / ops — one-off task, not a standing owner role  
**Status:** Assigned — not started  
**GitHub issue:** [#16](https://github.com/Retriive/campusQ/issues/16)

---

## Goal

Add a GitHub Actions workflow that runs the **smoke quality gate against production** automatically — so nobody has to remember to run it manually before or after deploy.

**Pass bar:** 10/10 on smoke. See [TEAM_RULES.md](../TEAM_RULES.md).

---

## Why this matters

Today the deploy rule is:

> Do not deploy to production if smoke tests fail.

But smoke only runs when someone runs it locally. This workflow makes that rule **enforceable** — failed prod smoke shows up in the Actions tab instead of silently shipping a broken chatbot.

---

## What already exists

| Piece | Location |
|-------|----------|
| Smoke test script | `backend/evals/quality_gate.py --tier smoke` |
| Golden questions | `backend/evals/datasets/golden.csv` (10 smoke rows) |
| Prod URL override | `--api-url` flag or `CAMPUSQ_API_URL` env var |
| Docs | [QUALITY_GATE.md](../QUALITY_GATE.md), [GitHub Actions docs](https://docs.github.com/en/actions) |

**Manual run against prod today:**

```bash
cd backend
pip install -r requirements.txt requests   # requests used by quality_gate.py
export OPENAI_API_KEY=sk-...
export CAMPUSQ_API_URL=https://your-render-url.onrender.com
python evals/quality_gate.py --tier smoke --api-url "$CAMPUSQ_API_URL"
```

Exit codes: `0` = passed, `1` = failed, `2` = setup error (API down, missing keys).

---

## Your scope

### 1. Create workflow file

Add something like `.github/workflows/smoke-gate.yml` that:

| Requirement | Detail |
|-------------|--------|
| **Runs smoke** | `python evals/quality_gate.py --tier smoke` from `backend/` |
| **Targets prod** | `CAMPUSQ_API_URL` from repo secret (Mahad provides Render URL) |
| **Judge key** | `OPENAI_API_KEY` from repo secret |
| **Fails correctly** | Workflow fails when script exits `1` (not 10/10) |
| **Triggers** | `push` to `main` + `workflow_dispatch` (manual re-run) |

**Optional (discuss with Mahad):** `schedule` cron (e.g. daily) to catch prod drift without a deploy.

### 2. Document secrets setup

Add a short section to [QUALITY_GATE.md](../QUALITY_GATE.md) (or a comment at top of the workflow):

| Secret | Who sets it | Value |
|--------|-------------|-------|
| `CAMPUSQ_API_URL` | Mahad | Production Render backend URL (no trailing slash) |
| `OPENAI_API_KEY` | Mahad | Key for the LLM judge in `quality_gate.py` |

GitHub path: **Repo → Settings → Secrets and variables → Actions → New repository secret**

### 3. Do not break existing workflows

`pr-review-agent.yml` already exists — add a **new** workflow file; don't modify the PR review agent unless needed.

---

## Suggested workflow skeleton

Adapt as needed — this is a starting point, not copy-paste gospel:

```yaml
name: Smoke gate (production)

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        working-directory: backend
        run: |
          pip install -r requirements.txt requests

      - name: Run smoke gate against production
        working-directory: backend
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          CAMPUSQ_API_URL: ${{ secrets.CAMPUSQ_API_URL }}
        run: |
          python evals/quality_gate.py --tier smoke --api-url "$CAMPUSQ_API_URL"
```

**Note:** Mahad must add secrets before the first run can pass.

---

## Out of scope

- Core / full gate in CI (32-question runs — optional follow-up)
- Changing `golden.csv` or pass thresholds
- Auto-deploy to Render or Vercel
- Blocking PR merges (only runs on `main` push unless Mahad wants `pull_request` too)

---

## How to work

### 1. Branch

```bash
git checkout main
git pull
git checkout -b feature/github-actions-smoke-abdulla
```

### 2. Test locally first

Confirm smoke passes against prod from your machine (Mahad gives you the URL + key, or use your own `.env`):

```bash
cd backend
python evals/quality_gate.py --tier smoke --api-url "https://..."
```

### 3. Test the workflow

- Open PR with the workflow file
- After Mahad adds secrets, use **Actions → Smoke gate → Run workflow** (`workflow_dispatch`)
- Or merge and confirm the `push` to `main` run is green

### 4. PR description

Include:

- Which events trigger the workflow
- Which secrets Mahad must add (and that you verified a green run)
- Screenshot or link to a successful Actions run
- What a failed run looks like (e.g. link to logs, "check which smoke-XX failed")

---

## Definition of done

- [ ] `.github/workflows/smoke-gate.yml` (or equivalent) merged to `main`
- [ ] Secrets documented; Mahad added `CAMPUSQ_API_URL` + `OPENAI_API_KEY`
- [ ] At least one **green** Actions run against production
- [ ] Short note in `docs/QUALITY_GATE.md` about CI smoke
- [ ] Mahad reviewed and approved

---

## If smoke fails in CI but passes locally

| Check | Action |
|-------|--------|
| Wrong API URL | Confirm secret matches Render prod URL |
| Render cold start | Add retry or longer timeout in workflow |
| Prod not deployed yet | Run workflow after deploy completes |
| Flaky question | Post failure log to Mahad — may be a real prod bug |

---

## Links

- [Quality gate guide](../QUALITY_GATE.md)
- [Team deploy rules](../TEAM_RULES.md)
- [How we work](../HOW_WE_WORK.md)
- Issue: https://github.com/Retriive/campusQ/issues/16
