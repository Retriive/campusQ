# Quality Gate

**The scoreboard.** Before we deploy or expand to a new school, we run fixed test questions and pass/fail automatically.

No more "it looked fine when I tried one question."

---

## The three gates

| Gate | Command | # Questions | Must pass | Blocks what |
|---|---|---:|---:|---|
| **Smoke** | `--tier smoke` | 10 | **100%** (10/10) | Production deploys |
| **Core** | `--tier core` | 32 | **85%** (27+/32) | School #2, big marketing |
| **Full** | `--tier full` | 32 | **80%** floor | Triggers investigation |

---

## How to run

**Prerequisites:** Backend running on port 8000. `OPENAI_API_KEY` in `backend/.env`.

```powershell
cd backend
py evals\quality_gate.py --tier smoke
py evals\quality_gate.py --tier core
```

**Against production:**

```powershell
$env:CAMPUSQ_API_URL = "https://your-render-url.onrender.com"
py evals\quality_gate.py --tier smoke
```

### Reading the result

```
Result     : 10/10 passed (100.0%)
Gate       : ✅ PASSED
```

| Exit code | Meaning |
|---:|---|
| 0 | Passed — OK to proceed |
| 1 | Failed — do not deploy / expand |
| 2 | Setup error — API down or missing keys |

Results save to: `backend/evals/experiments/` (CSV + JSON)

---

## The 10 smoke questions (deploy gate)

These must **all pass** before every production deploy:

| # | Question | What we're testing |
|---|---|---|
| 1 | Can I take COMP 3000 without COMP 2401? | Prerequisite logic |
| 2 | How do I drop COMP 2402? | Registration + asks for term |
| 3 | When does the first ACE evaluation happen? | Academic regulations (5.5 credits) |
| 4 | Last day to withdraw from a fall course? | Deadline accuracy |
| 5 | How many credits to graduate? | Asks which program (no guessing) |
| 6 | Who teaches SYSC 3110 in Fall 2026? | Schedule / instructor |
| 7 | What is COMP 9999? | No hallucination, no sources |
| 8 | What's a B- worth at Carleton? | 12-point grading scale |
| 9 | How many times can an Engineering student attempt a course? | Academic regulations (3 attempts) |
| 10 | Drop vs withdraw difference? | Registration policy |

---

## The 22 core questions (expansion gate)

Smoke 10 + 22 more covering:

- Course lookups (COMP 1005, BUSI 2501, MATH prereqs)
- Program requirements (CS Honours, B.Com credits)
- Regulations (fail required course, B+ grade points, ACE)
- Registration (add course, overrides, appeals)
- Deadlines (fall drop, exams, payment)
- Schedule (SYSC open, SYSC times)
- Edge cases (prof ratings decline, COMP 4000 first year, EX grade, GPA scale)

Full list: `backend/evals/datasets/golden.csv`

---

## How scoring works

Each question gets two checks:

1. **Automatic rules** — must contain / must not contain certain phrases; no sources on "I don't know"
2. **AI judge** — reads the answer + grading notes → pass or fail with reason

**Both must pass** for the question to count.

---

## When to run

| When | Run |
|---|---|
| Before every Render deploy | `--tier smoke` |
| Before merging AI/prompt/retrieval changes | `--tier core` |
| Weekly during Carleton pilot | `--tier core` |
| After re-scraping Carleton data | `--tier core` |
| Before launching school #2 | `--tier core` on **production** |

---

## If a test fails

1. Open the latest CSV in `backend/evals/experiments/`
2. Find `passed = False` rows
3. Read `reason` and `answer` columns
4. Fix the root cause:

| If reason suggests… | Fix in… |
|---|---|
| Wrong facts, weird answer | `main.py` system prompt |
| Wrong chunks retrieved | `retrieval.py` |
| Missing info entirely | Scrapers + re-index |
| Bad test expectation | `golden.csv` grading notes |

5. Re-run the gate

---

## Adding a new test question

Edit `backend/evals/datasets/golden.csv`:

| Column | What to put |
|---|---|
| `tier` | `smoke`, `core`, or `full` |
| `id` | Unique ID like `core-23` |
| `category` | e.g. `Registration` |
| `question` | Exact question text |
| `grading_notes` | What a correct answer must include |
| `must_contain` | Required phrases (all must appear), separated by `\|` |
| `must_contain_any` | At least one must appear, separated by `\|` |
| `must_not_contain` | Forbidden phrases in answer or sources |
| `require_no_sources` | `yes` if "I don't know" answers must have zero sources |

**Good sources for new questions:**

- Thumbs-down in `feedback.log`
- Questions with no data in `no_context.log`
- Real student questions from `queries.log`

---

## Known issues to watch (as of last run)

| ID | Issue | Status |
|---|---|---|
| `core-15` | GPA on 4.0 scale → wrong RateMyProfessors answer | **Bug — fix needed** |
| `core-03` | MATH 2007 prereq — AI may be right, test may be wrong | **Verify calendar** |

Update this table when fixed.

---

## Changing pass thresholds

Thresholds are in `backend/evals/quality_gate.py` → `GATE_THRESHOLDS`.

Changing them is a **product decision** — talk to Mahad first.

---

## Team rules (summary)

> **No production deploy if smoke fails.**  
> **No school #2 if core is below 85%.**  
> **Below 80% on core → feature freeze until fixed.**

Full policy: [TEAM_RULES.md](TEAM_RULES.md)
