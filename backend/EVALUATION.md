# CampusQ RAG Evaluation

> **Operational quality gate:** see [`evals/QUALITY_GATE.md`](evals/QUALITY_GATE.md) for
> deploy/expansion thresholds and `python evals/quality_gate.py --tier smoke`.

How we measure whether changes to retrieval or the system prompt actually
improve answer quality, instead of judging by a few manual curl tests.

## Why

Manual testing ("ask it a question, eyeball the answer") doesn't scale and
doesn't catch regressions. It's how the rule-10 refusal bug shipped earlier —
it looked right on the one question we tried, then broke on a slightly
different phrasing. We need a fixed set of test questions with known-correct
answers, scored automatically every time we change `build_system_prompt`,
retrieval logic, or chunking.

We use [Ragas](https://docs.ragas.io/) for this. It's an open-source
evaluation library: you give it a dataset of questions + grading criteria,
it runs them through your actual RAG endpoint, and scores each response with
an LLM judge (pass/fail, not crude keyword/word-overlap matching).

## What we're NOT doing

- **Not** using BLEU/ROUGE/METEOR/Perplexity — built for fixed-reference
  translation/summarization, not open-ended Q&A with many valid phrasings.
- **Not** scoring groundedness by word-overlap — too easily fooled by
  paraphrasing (flags correct paraphrases as hallucinated, misses subtly
  wrong answers that reuse context vocabulary).
- **Not** using Azure AI Evaluators — same underlying idea (LLM-judged
  groundedness/relevance), but tied to Azure infrastructure we don't use.
  Ragas gets the same LLM-judge approach running locally against OpenAI,
  which we already have credentials for.

## Setup

```bash
cd backend
pip install ragas[examples]
export OPENAI_API_KEY="..."   # already used elsewhere in this project
```

## Project layout

```
backend/evals/
├── datasets/
│   └── test_dataset.csv      # questions + grading notes (the golden set)
├── experiments/              # CSV output of each evaluation run
└── evals.py                  # the evaluation script
```

## The golden dataset

`datasets/test_dataset.csv` holds real questions with grading notes — what a
correct answer must contain. Pull these from `queries.log`,
`course_misses.log`, and `no_context.log` so the set reflects real student
phrasing, not hypothetical questions.

| query | grading_notes |
|---|---|
| "Can I take COMP 3000 without COMP 2401?" | must state COMP 2401 is a prerequisite for COMP 3000 |
| "I want to drop COMP 2402, how do I do that?" | must mention formal withdrawal via Carleton Central; must NOT just return course metadata |
| "What counts as good academic standing at Carleton?" | must state CGPA minimum (4.00 / C-); must mention Carleton Central audit tool |
| "What's the deadline to appeal a grade?" | must reference the grade appeal process/deadline from context |

Aim for 20-30 rows covering: course lookups, program requirements, schedule
questions, deadline questions, the rule-10 tool-mention cases, and known
failure modes (e.g. the course-code-with-action-verb interceptor bug).

Grading notes should describe required content, not exact wording — we're
checking correctness, not phrasing.

## The metric

An LLM-judged pass/fail metric, not a hand-rolled formula:

```python
from ragas.metrics import DiscreteMetric

correctness = DiscreteMetric(
    name="correctness",
    prompt=(
        "Check if the response satisfies the grading notes. "
        "Return 'pass' or 'fail'.\n"
        "Response: {response}\nGrading Notes: {grading_notes}"
    ),
    allowed_values=["pass", "fail"],
)
```

## The experiment loop

Calls the real `/api/chat` endpoint (form-encoded, not JSON — see
`chat_endpoint` in `main.py`) so the eval exercises the actual code path,
including the course-code interceptor, namespace retrieval, and
`build_system_prompt`.

```python
import requests
from ragas import experiment

@experiment()
async def run_experiment(row):
    resp = requests.post(
        "http://127.0.0.1:8000/api/chat",
        data={"question": row["query"], "history": "[]"},
    )
    answer = resp.json().get("answer", "")

    score = correctness.score(response=answer, grading_notes=row["grading_notes"])

    return {
        **row,
        "response": answer,
        "score": score.value,
        "reason": score.reason,
    }
```

Run it with the dev server up:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 &
python evals.py
```

Results land in `evals/experiments/<name>.csv` — one row per question, with
pass/fail and the judge's reasoning.

## When to run this

- Before/after any change to `build_system_prompt` in `main.py`.
- Before/after any change to retrieval logic (namespace search, query
  rewriting, the course-code interceptor).
- Before/after changing the embedding model or chunking strategy.

Compare the new experiment CSV against the previous run. A prompt change
that "feels" better but drops pass rate on the golden set is a regression,
not an improvement — trust the eval over the vibe.

## Known gaps to add test cases for

- Course-code interceptor short-circuiting action questions (e.g. "drop
  COMP 2402") before they reach the LLM — confirmed bug, not yet fixed.
- Rule 10 tool-mentions for cases beyond CGPA/withdrawal (registration,
  transcripts, deferrals, timetables) — only CGPA/withdrawal have been
  manually verified so far.
- Ambiguous program questions where multiple programs' requirements could
  get mixed into context.
