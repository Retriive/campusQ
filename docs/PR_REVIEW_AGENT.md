# PR Review Agent

Automatically reviews GitHub pull requests assigned to you — **no API keys in GitHub, no manual steps after setup**.

Uses a **Cursor Automation** in your dashboard. Your key stays in Cursor, not in repo secrets.

---

## How it works

```
PR assigned to you (or review requested)
        ↓
Cursor Automation fires (your Cursor account)
        ↓
Agent reads CampusQ rubric → posts review on GitHub
```

Assign yourself on a PR (or get requested as reviewer). The agent reviews it and posts feedback within a few minutes.

---

## One-time setup (~5 minutes)

1. Go to [cursor.com/automations](https://cursor.com/automations) → **New automation**

2. **Name:** `CampusQ PR review`

3. **Trigger:** GitHub → `Retriive/campusQ`
   - PR opened
   - PR pushed (new commits)
   - Review requested

4. **Repository:** `Retriive/campusQ`

5. **Tools:** enable **Comment on pull request**

6. **Prompt:** copy everything from [`.cursor/automations/pr-review-assigned.prompt.md`](../.cursor/automations/pr-review-assigned.prompt.md)

7. **Save and enable**

No GitHub secrets. No `CURSOR_API_KEY` in the repo. Runs under your Cursor auth.

---

## Test it

1. Have a teammate open a small PR (or use one where you're **not** the author)
2. Assign yourself (or request your review) on GitHub
3. Within a few minutes, check the PR for a review containing:
   ```html
   <!-- campusq-pr-review-agent -->
   ```
4. Check [cursor.com/agents](https://cursor.com/agents) if nothing appears — the run log shows errors

---

## What triggers a review

| Event | When |
|-------|------|
| Review requested | You're added as a reviewer |
| PR opened / updated | You're assignee or reviewer on the PR |

The automation prompt tells the agent to **skip** if:

- You're the PR author
- Latest commit already has `<!-- campusq-pr-review-agent -->`

---

## What it checks

| Area | Source |
|------|--------|
| PR description template | [HOW_WE_WORK.md](HOW_WE_WORK.md) |
| Deploy / expansion gates | [TEAM_RULES.md](TEAM_RULES.md) |
| Which tests to run | [QUALITY_GATE.md](QUALITY_GATE.md) |
| File ownership & risk | [PROJECT_MAP.md](PROJECT_MAP.md) |

### Automatic gate detection

| Changed files | Required gate |
|---------------|---------------|
| `main.py`, `retrieval.py`, `citations.py`, scrapers, `golden.csv` | **core** (≥27/32) |
| Other `backend/` files | **smoke** (10/10) |
| `docs/` or `frontend/` only | **none** (N/A OK) |

---

## Manual use (optional)

From a cloned repo with `gh auth login`:

```bash
# List PRs waiting for you
python3 scripts/pr_review/review_assigned_prs.py list --include-reviewer

# Inspect one PR
python3 scripts/pr_review/review_assigned_prs.py context --number 12
```

In Cursor chat:

> Review all PRs assigned to me on CampusQ. Use the review-assigned-prs skill.

---

## Files

| Path | Purpose |
|------|---------|
| `.cursor/automations/pr-review-assigned.prompt.md` | Paste into Cursor Automation |
| `.cursor/skills/review-assigned-prs/SKILL.md` | Full review rubric |
| `scripts/pr_review/review_assigned_prs.py` | CLI helpers (list, context, post) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Nothing happens | Automation enabled? GitHub connected in Cursor settings? |
| Skips your PR | By design if you're the author — test on someone else's PR |
| Duplicate reviews | Agent should skip if marker exists on latest commit |
| Wrong repo | Confirm trigger is `Retriive/campusQ` |
| Team wants shared ownership | Promote to Team-owned automation in Cursor (uses team service account) |
