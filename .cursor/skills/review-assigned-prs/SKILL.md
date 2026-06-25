# Review assigned GitHub pull requests

Use this skill when the user wants to review PRs assigned to them on the CampusQ repo.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- Repo cloned locally at the workspace root
- Read access to `docs/HOW_WE_WORK.md`, `docs/TEAM_RULES.md`, and `docs/QUALITY_GATE.md`

## Workflow

### 1. Discover assigned PRs

```bash
python scripts/pr_review/review_assigned_prs.py list
```

Optional flags:

- `--assignee USER` — GitHub username (default: `@me`)
- `--repo OWNER/REPO` — defaults to `retriive/campusq`
- `--json` — machine-readable output for the agent

If no PRs are assigned, tell the user and stop.

### 2. Fetch full context for each PR

```bash
python scripts/pr_review/review_assigned_prs.py context --number <N>
```

This returns: title, body, author, branch, changed files, diff (truncated if huge), required quality gate tier, and checklist gaps.

### 3. Review each PR using the CampusQ rubric

Read the diff and apply every section below. Be specific — cite file paths and line numbers when possible.

#### A. PR hygiene (from `docs/HOW_WE_WORK.md`)

| Check | Pass criteria |
|-------|---------------|
| Description | Has **What changed**, **Why**, **How to test** |
| Quality gate | Checkbox filled with actual result, or marked N/A with justification |
| Branch name | Lowercase, hyphenated, describes the work |
| Scope | One feature or fix — flag if unrelated changes bundled |
| Secrets | No API keys, `.env` values, or tokens in diff or PR body |

#### B. Required quality gate (from `docs/TEAM_RULES.md` + `docs/QUALITY_GATE.md`)

Use the `required_gate` field from `context` output:

| Gate | When required |
|------|---------------|
| **core** | `main.py`, `retrieval.py`, `citations.py`, scrapers, `golden.csv`, model changes |
| **smoke** | Other backend/API changes touching chat |
| **none** | Docs-only, frontend-only with no API changes |

If the PR claims a gate was run, verify the result is noted (e.g. "10/10"). If backend files changed but no gate mentioned → **request changes**.

#### C. Code review by area

| Area | Focus |
|------|-------|
| `backend/main.py` | Prompt changes affect every answer; check for regressions on existing rules |
| `backend/retrieval.py` | Intent routing, reranker — could break course lookups |
| `backend/citations.py` | Source link formatting |
| `backend/scrapers/` | Data correctness; suggest core gate after re-index |
| `backend/evals/` | New test questions must have clear expected behavior |
| `frontend/` | UI regressions, env var usage (`NEXT_PUBLIC_*` only) |
| `docs/` | Accuracy, broken links |

#### D. Security & safety

- No committed secrets or hardcoded keys
- No `wipe.py` or destructive ops without explicit approval
- Auth/Clerk config changes need extra scrutiny
- Prompt changes: check for jailbreak weakening or scope expansion

#### E. Verdict

Choose one:

- **Approve** — ready to merge (or ready after author confirms gate results)
- **Request changes** — blockers found; list each with fix suggestion
- **Comment** — feedback only, no blockers

### 4. Post the review (only when user asks to publish)

```bash
python scripts/pr_review/review_assigned_prs.py post \
  --number <N> \
  --event APPROVE|REQUEST_CHANGES|COMMENT \
  --body-file /tmp/review.md
```

Draft the review body in markdown:

```markdown
## CampusQ PR review

**Verdict:** Approve | Request changes | Comment

### Summary
[1-2 sentences]

### Checklist
- [x] or [ ] PR description complete
- [x] or [ ] Quality gate appropriate and documented
- [x] or [ ] No secrets in diff
- [x] or [ ] Scope is focused

### Required gate
**Tier:** smoke | core | none
**Status:** [noted in PR / missing / N/A justified]

### Findings
#### Must fix (blockers)
- ...

#### Suggestions (non-blocking)
- ...

#### What looks good
- ...
```

**Always show the draft to the user before posting** unless they explicitly said "review and post all assigned PRs."

### 5. Multi-PR batch

When multiple PRs are assigned, review them one at a time. Summarize at the end:

| PR | Verdict | Top blocker |
|----|---------|-------------|
| #N | ... | ... |

## Repo-specific gotchas

- `golden.csv` threshold edits need Mahad's sign-off
- `main.py` system prompt changes need core gate (32 questions, 85%+)
- Production deploy requires smoke 10/10 on **production URL**, not just local
- `frontend_archived/` is dead code — flag if someone edits it by mistake

## If `gh` fails

- `gh auth login` — re-authenticate
- `gh pr list --assignee @me` — manual fallback
- Check token has `repo` and `pull_requests` scopes
