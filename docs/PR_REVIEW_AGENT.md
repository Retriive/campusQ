# PR Review Agent

A Cursor agent workflow that finds GitHub pull requests assigned to you and reviews them using CampusQ team rules.

---

## What it does

1. Lists open PRs assigned to your GitHub account
2. Pulls the full diff and metadata for each PR
3. Applies the CampusQ review rubric (quality gates, PR hygiene, security, code areas)
4. Drafts a structured review — and posts it to GitHub when you approve

---

## Quick start

### 1. Prerequisites

- [GitHub CLI](https://cli.github.com/) installed: `gh --version`
- Authenticated: `gh auth login`
- Repo cloned locally

### 2. List your assigned PRs

```bash
python scripts/pr_review/review_assigned_prs.py list
```

### 3. Run the Cursor agent

In Cursor, start a Cloud Agent (or chat) with:

> Review all pull requests assigned to me on CampusQ. Use the review-assigned-prs skill. Show me drafts before posting.

The agent reads `.cursor/skills/review-assigned-prs/SKILL.md` and follows the rubric automatically.

### 4. Review a single PR manually

```bash
python scripts/pr_review/review_assigned_prs.py context --number 12
```

Add `--json` for machine-readable output.

---

## Review rubric (summary)

The agent checks every PR against:

| Area | Source doc |
|------|------------|
| PR description template | [HOW_WE_WORK.md](HOW_WE_WORK.md) |
| Deploy / expansion gates | [TEAM_RULES.md](TEAM_RULES.md) |
| Which tests to run | [QUALITY_GATE.md](QUALITY_GATE.md) |
| File ownership & risk | [PROJECT_MAP.md](PROJECT_MAP.md) |

### Automatic gate detection

| Changed files | Required gate |
|---------------|---------------|
| `main.py`, `retrieval.py`, `citations.py`, scrapers, `golden.csv` | **core** (≥27/32) |
| Other `backend/` files | **smoke** (10/10) |
| `docs/` or `frontend/` only (no API) | **none** (N/A OK) |

### Blockers the agent flags

- Missing PR description sections (What / Why / How to test)
- Backend changes without documented gate results
- Possible secrets in the diff
- `golden.csv` threshold edits without Mahad sign-off
- Scope creep (unrelated changes bundled)

---

## Posting a review

After the agent drafts a review and you approve:

```bash
python scripts/pr_review/review_assigned_prs.py post \
  --number 12 \
  --event REQUEST_CHANGES \
  --body-file /tmp/review.md
```

Events: `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`.

---

## Assigning PRs for review

On GitHub, open a PR → **Reviewers** → assign yourself or a teammate.

The agent only picks up PRs where you are listed as **assignee** (not just reviewer). To also catch reviewer-assigned PRs, ask the agent:

> Also list PRs where I'm a requested reviewer.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No open PRs assigned` | Assign yourself on GitHub, or use `--assignee your-username` |
| `gh: Resource not accessible` | Re-run `gh auth login` with `repo` scope |
| Agent doesn't know the rubric | Say "use the review-assigned-prs skill" |
| Diff too large | Agent gets first 80k chars; use `gh pr diff N` for full diff |

---

## Files

| Path | Purpose |
|------|---------|
| `.cursor/skills/review-assigned-prs/SKILL.md` | Agent instructions & rubric |
| `scripts/pr_review/review_assigned_prs.py` | CLI to list, fetch, and post reviews |
| `docs/PR_REVIEW_AGENT.md` | This guide |

---

## Example agent prompt

Copy-paste into Cursor when you want a review session:

```
Review all GitHub PRs assigned to me on retriive/campusq.

For each PR:
1. Fetch context with scripts/pr_review/review_assigned_prs.py
2. Apply the CampusQ review rubric from the review-assigned-prs skill
3. Draft a structured review (verdict, checklist, findings)
4. Show me all drafts before posting anything
```
