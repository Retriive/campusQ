"""
schedule_chatbot_eval.py — End-to-end schedule RAG evaluation for CampusQ.

Sends real questions to the local chatbot API and checks answers against
ground truth derived from course_resultsCampusQ.json.

Usage:
    py evals/schedule_chatbot_eval.py
    py evals/schedule_chatbot_eval.py --url https://your-deployed-url.com

Categories tested:
    1. Open/closed availability
    2. Who teaches (instructor lookup)
    3. What time / what days
    4. How many sections / section details
    5. Term availability (offered this term?)
    6. Multi-instructor courses
    7. Closed course awareness
    8. Follow-up / context injection (no course code in question)
    9. CRN lookup
   10. Negative cases (not offered in a term)
"""

import argparse
import json
import os
import time
from collections import defaultdict

import requests

BASE_URL = "http://localhost:8000"
RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "schedule_test_results.json",
)

# ── Ground truth (derived from course_resultsCampusQ.json) ───────────────────
# Each test: question, expected fragments (all must appear in answer, case-insensitive),
# forbidden fragments (none must appear), category, and difficulty.

TEST_CASES = [
    # ── Category 1: Open/Closed Availability ─────────────────────────────────
    {
        "id": "avail-01",
        "category": "Availability",
        "difficulty": "easy",
        "question": "Is SYSC 3110 open in Fall 2026?",
        "must_contain": ["open", "sysc 3110"],
        "must_not_contain": ["outside of what i currently know", "ratemyprofessors"],
        "notes": "SYSC 3110 has 4 open sections in Fall 2026",
    },
    {
        "id": "avail-02",
        "category": "Availability",
        "difficulty": "easy",
        "question": "Is ACCT 5001 open in Summer 2026?",
        "must_contain": ["closed", "acct 5001"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "ACCT 5001 Summer 2026 has Registration Closed status",
    },
    {
        "id": "avail-03",
        "category": "Availability",
        "difficulty": "medium",
        "question": "Can I still register for ECON 1002 this summer?",
        "must_contain": ["econ 1002"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "ECON 1002 Summer 2026 has 3 open sections",
    },
    {
        "id": "avail-04",
        "category": "Availability",
        "difficulty": "medium",
        "question": "Are there any open sections of BIOC 2200 in Fall 2026?",
        "must_contain": ["bioc 2200", "open"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "BIOC 2200 Fall 2026 has 11 open sections",
    },
    {
        "id": "avail-05",
        "category": "Availability",
        "difficulty": "hard",
        "question": "Is SYSC 2004 waitlisted or full in Fall 2026?",
        "must_contain": ["sysc 2004"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "SYSC 2004 Fall 2026 - all open, not waitlisted",
    },

    # ── Category 2: Who Teaches ───────────────────────────────────────────────
    {
        "id": "teach-01",
        "category": "Instructor",
        "difficulty": "easy",
        "question": "Who teaches SYSC 3110 in Fall 2026?",
        "must_contain": ["safaa bedawi", "sysc 3110"],
        "must_not_contain": ["ratemyprofessors", "outside of what i currently know", "professor ratings"],
        "notes": "Safaa Bedawi teaches SYSC 3110 Fall 2026",
    },
    {
        "id": "teach-02",
        "category": "Instructor",
        "difficulty": "easy",
        "question": "Who is the instructor for ELEC 3909 in Fall 2026?",
        "must_contain": ["winnie ye", "elec 3909"],
        "must_not_contain": ["ratemyprofessors", "outside of what i currently know"],
        "notes": "Winnie Ye teaches ELEC 3909 Fall 2026",
    },
    {
        "id": "teach-03",
        "category": "Instructor",
        "difficulty": "medium",
        "question": "Who teaches BUSI 2800 this fall? Are there multiple instructors?",
        "must_contain": ["busi 2800"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "BUSI 2800 Fall 2026: Rowland Few + Emily Jones Joanisse",
    },
    {
        "id": "teach-04",
        "category": "Instructor",
        "difficulty": "medium",
        "question": "Who is teaching SYSC 2004 in Fall 2026?",
        "must_contain": ["lynn marshall"],
        "must_not_contain": ["ratemyprofessors", "outside of what i currently know"],
        "notes": "Lynn Marshall teaches SYSC 2004 Fall 2026",
    },
    {
        "id": "teach-05",
        "category": "Instructor",
        "difficulty": "hard",
        "question": "Does Lynn Marshall teach any courses in Fall 2026?",
        "must_contain": ["lynn marshall"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "Lynn Marshall teaches SYSC 1006 and SYSC 2004 in Fall 2026",
    },

    # ── Category 3: Time / Schedule ───────────────────────────────────────────
    {
        "id": "time-01",
        "category": "Timing",
        "difficulty": "easy",
        "question": "What time is SYSC 2004 offered in Fall 2026?",
        "must_contain": ["sysc 2004"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "SYSC 2004: Tue/Thu 13:05-14:25, lab Tue 18:05-19:55",
    },
    {
        "id": "time-02",
        "category": "Timing",
        "difficulty": "easy",
        "question": "What days is CIVE 4303 offered in Winter 2027?",
        "must_contain": ["cive 4303"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "CIVE 4303: Mon/Wed 17:35-18:55 and Wed 08:35-11:25",
    },
    {
        "id": "time-03",
        "category": "Timing",
        "difficulty": "medium",
        "question": "When does FILM 3402 meet in Winter 2027?",
        "must_contain": ["film 3402", "wed"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "FILM 3402 meets Wednesdays in Winter 2027",
    },
    {
        "id": "time-04",
        "category": "Timing",
        "difficulty": "medium",
        "question": "What time does ECON 1002 run this summer?",
        "must_contain": ["econ 1002"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "ECON 1002 Summer 2026: Mon/Wed 18:05-20:55",
    },

    # ── Category 4: Section Count / CRN ──────────────────────────────────────
    {
        "id": "section-01",
        "category": "Sections",
        "difficulty": "easy",
        "question": "How many sections of SYSC 3110 are available in Fall 2026?",
        "must_contain": ["sysc 3110"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "SYSC 3110 has 4 sections in Fall 2026",
    },
    {
        "id": "section-02",
        "category": "Sections",
        "difficulty": "medium",
        "question": "What is the CRN for SYSC 3110 in Fall 2026?",
        "must_contain": ["sysc 3110"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "CRNs include 30962, 30963, etc.",
    },
    {
        "id": "section-03",
        "category": "Sections",
        "difficulty": "medium",
        "question": "How many sections of BIOC 2200 are open in Fall 2026?",
        "must_contain": ["bioc 2200"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "11 sections, 11 open",
    },

    # ── Category 5: Term Availability ─────────────────────────────────────────
    {
        "id": "term-01",
        "category": "Term Availability",
        "difficulty": "medium",
        "question": "Is SYSC 3110 offered in Winter 2027?",
        "must_contain": ["sysc 3110"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "Check if SYSC 3110 appears in Winter 2027 data",
    },
    {
        "id": "term-02",
        "category": "Term Availability",
        "difficulty": "medium",
        "question": "Is FILM 3402 offered in Fall 2026?",
        "must_contain": ["film 3402"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "FILM 3402 only in Winter 2027",
    },
    {
        "id": "term-03",
        "category": "Term Availability",
        "difficulty": "hard",
        "question": "What terms is CIVE 4303 offered in?",
        "must_contain": ["cive 4303"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "CIVE 4303 is in Winter 2027",
    },

    # ── Category 6: Closed Courses ────────────────────────────────────────────
    {
        "id": "closed-01",
        "category": "Closed",
        "difficulty": "easy",
        "question": "Is ACCT 5012 open in Summer 2026?",
        "must_contain": ["acct 5012", "closed"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "ACCT 5012 Summer 2026: Registration Closed",
    },
    {
        "id": "closed-02",
        "category": "Closed",
        "difficulty": "medium",
        "question": "Can I register for ACCT 5011 this summer?",
        "must_contain": ["acct 5011", "closed"],
        "must_not_contain": ["outside of what i currently know"],
        "notes": "ACCT 5011 Summer 2026: Registration Closed",
    },

    # ── Category 7: Context Injection Follow-ups ──────────────────────────────
    {
        "id": "followup-01",
        "category": "Follow-up",
        "difficulty": "hard",
        "question": "Who teaches SYSC 2100 in Fall 2026?",
        "followup": "What time is that class?",
        "must_contain_followup": ["sysc 2100"],
        "must_not_contain_followup": ["outside of what i currently know"],
        "notes": "SYSC 2100 Fall 2026: Safaa Bedawi, Wed/Fri 16:05-17:25",
    },
    {
        "id": "followup-02",
        "category": "Follow-up",
        "difficulty": "hard",
        "question": "Is ERTH 3405 open in Fall 2026?",
        "followup": "What days does it meet?",
        "must_contain_followup": ["erth 3405"],
        "must_not_contain_followup": ["outside of what i currently know"],
        "notes": "ERTH 3405 Fall 2026: Dariush Motazedian, Wed + Thu",
    },

    # ── Category 8: Negative / Not Offered ───────────────────────────────────
    {
        "id": "neg-01",
        "category": "Negative",
        "difficulty": "hard",
        "question": "Is SYSC 3110 offered in Summer 2026?",
        "must_contain": ["sysc 3110"],
        "must_not_contain": [],
        "notes": "SYSC 3110 not in Summer 2026 — chatbot should say not found or not offered",
    },
]


def ask_stream(question: str, history: list | None = None) -> str:
    """Send question to streaming endpoint and collect all tokens."""
    if history is None:
        history = []
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            data={
                "question": question,
                "history": json.dumps(history),
                "session_id": "test-session",
                "user_id": "test-runner",
            },
            stream=True,
            timeout=30,
        )
        response.raise_for_status()
        text = ""
        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                try:
                    payload = json.loads(line[6:])
                    if payload.get("type") == "token":
                        text += payload.get("content", "")
                except Exception:
                    pass
        return text.strip()
    except Exception as exc:
        return f"[ERROR: {exc}]"


def evaluate(answer: str, must_contain: list, must_not_contain: list) -> tuple[bool, list]:
    """Returns (passed, list_of_failures)."""
    answer_lower = answer.lower()
    failures = []
    for phrase in must_contain:
        if phrase.lower() not in answer_lower:
            failures.append(f"MISSING: '{phrase}'")
    for phrase in must_not_contain:
        if phrase.lower() in answer_lower:
            failures.append(f"FORBIDDEN: '{phrase}'")
    return len(failures) == 0, failures


def run_tests(base_url: str):
    global BASE_URL
    BASE_URL = base_url.rstrip("/")

    results = []
    passed = 0
    failed = 0

    print(f"\n{'=' * 70}")
    print(f"CampusQ Schedule Test Suite — {len(TEST_CASES)} tests")
    print(f"Target: {BASE_URL}")
    print(f"{'=' * 70}\n")

    for test_case in TEST_CASES:
        is_followup_test = "followup" in test_case

        if is_followup_test:
            answer1 = ask_stream(test_case["question"])
            history = [
                {"role": "user", "content": test_case["question"]},
                {"role": "assistant", "content": answer1},
            ]
            time.sleep(0.5)
            answer = ask_stream(test_case["followup"], history=history)
            must_contain = test_case.get("must_contain_followup", [])
            must_not_contain = test_case.get("must_not_contain_followup", [])
            display_q = f"{test_case['question']} -> {test_case['followup']}"
        else:
            answer = ask_stream(test_case["question"])
            must_contain = test_case.get("must_contain", [])
            must_not_contain = test_case.get("must_not_contain", [])
            display_q = test_case["question"]

        ok, failures = evaluate(answer, must_contain, must_not_contain)

        if ok:
            passed += 1
        else:
            failed += 1

        results.append({**test_case, "answer": answer, "passed": ok, "failures": failures})

        indicator = "[PASS]" if ok else "[FAIL]"
        print(f"{indicator} [{test_case['id']}] [{test_case['category']}] {display_q}")
        if not ok:
            for failure in failures:
                print(f"       {failure}")
            print(f"       Answer: {answer[:200]!r}")
        else:
            print(f"       Answer: {answer[:120]!r}")
        print()

        time.sleep(0.8)

    print(f"{'=' * 70}")
    print(f"RESULTS: {passed}/{len(TEST_CASES)} passed  ({failed} failed)")
    print(f"{'=' * 70}\n")

    by_cat = defaultdict(lambda: {"pass": 0, "fail": 0})
    for row in results:
        category = row["category"]
        if row["passed"]:
            by_cat[category]["pass"] += 1
        else:
            by_cat[category]["fail"] += 1

    print("By category:")
    for category, counts in sorted(by_cat.items()):
        total = counts["pass"] + counts["fail"]
        print(f"  {category:<22} {counts['pass']}/{total}")

    print()

    by_diff = defaultdict(lambda: {"pass": 0, "fail": 0})
    for row in results:
        difficulty = row["difficulty"]
        if row["passed"]:
            by_diff[difficulty]["pass"] += 1
        else:
            by_diff[difficulty]["fail"] += 1

    print("By difficulty:")
    for difficulty in ["easy", "medium", "hard"]:
        counts = by_diff[difficulty]
        total = counts["pass"] + counts["fail"]
        if total:
            print(f"  {difficulty:<10} {counts['pass']}/{total}")

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to {RESULTS_PATH}")

    return passed, failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000", help="Chatbot base URL")
    args = parser.parse_args()
    run_tests(args.url)
