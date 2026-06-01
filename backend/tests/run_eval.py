"""
run_eval.py — Automated accuracy harness for CampusQ.

Fires all 65 test questions at the LIVE /api/chat/stream endpoint, captures the
streamed answer + sources, then reads the matching line from queries.log to pull
the real retrieval signals (top_score, chunks, had_context) straight from main.py.

Produces eval_results.csv with everything you need for the two-pattern analysis:
  • had_context = False        → DATA GAP   (the namespace doesn't have it)
  • low top_score  + wrong     → WEAK RETRIEVAL (chunking / embeddings — e.g. acronyms)
  • high top_score + wrong     → PROMPT ISSUE   (context was there, LLM ignored it)

You still grade Score (0/1/2) by hand — only YOU know if the answer is correct.
The harness fills in the diagnostic column automatically so you know WHERE to look.

Prereqs:
  • Backend running on http://localhost:8000  (uvicorn main:app --reload)
  • Run from the backend/ dir:  py run_eval.py
"""

import os
import csv
import json
import time
import requests

API_URL = os.getenv("CAMPUSQ_API_URL", "http://localhost:8000")
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_THIS_DIR)
# queries.log is written by main.py into backend/ (one level up from tests/)
QUERIES_LOG = os.path.join(_BACKEND_DIR, "queries.log")
# results land alongside this script, inside tests/
OUT_CSV = os.path.join(_THIS_DIR, "eval_results.csv")

# (category, question, expected answer / grading guidance)
TESTS: list[tuple[str, str, str]] = [
    # ── Course Lookups ───────────────────────────────────────────────────────
    ("Course Lookups", "What is COMP 1005 about and what are its prerequisites?", "Intro to CS, Python/programming basics, exact prereqs listed."),
    ("Course Lookups", "How many credits is BUSI 2501?", "0.5 credits."),
    ("Course Lookups", "What is the difference between COMP 3000 and COMP 3007?", "3000 is OS; 3007 is Programming Paradigms."),
    ("Course Lookups", "What are the prerequisites for SYSC 3110?", "Exact SYSC/COMP prereqs."),
    ("Course Lookups", "Is there a lab component in CHEM 1001?", "Confirm yes/no from description."),
    ("Course Lookups", "What does COMS 2700 cover?", "Summarize calendar description."),
    ("Course Lookups", "Can I take MATH 2007 without taking MATH 1007 first?", "No — 1007 is the prereq."),
    ("Course Lookups", "What level is PSYC 3801 and what does it require?", "3000-level, list prereqs."),
    ("Course Lookups", "List all ERTH courses at the 2000 level.", "Reasonably complete set of ERTH 2XXX."),
    ("Course Lookups", "What is LAWS 2501 about?", "Summarize Law and State description."),

    # ── Program Requirements ─────────────────────────────────────────────────
    ("Program Requirements", "What are the required courses for Computer Science B.C.S. Honours?", "Core COMP, MATH, STAT requirements."),
    ("Program Requirements", "How many credits do I need to graduate with a B.Com. Honours?", "20.0 credits."),
    ("Program Requirements", "What is the difference between the CS Cybersecurity Stream and the standalone Cybersecurity B.Cyber. Honours?", "BCS stream vs distinct degree."),
    ("Program Requirements", "What courses are required for the Minor in Business?", "Core BUSI 1000/2000-level courses."),
    ("Program Requirements", "Can I do a Combined Honours in Computer Science and Mathematics?", "Yes; outline structure."),
    ("Program Requirements", "What is required for the Concentration in Finance within the B.Com.?", "Specific 3000/4000 BUSI finance courses."),
    ("Program Requirements", "What are the first year courses for B.Sc. Computer Science?", "COMP 1405/1406, MATH 1007, MATH 1104, electives."),
    ("Program Requirements", "How many credits is the Post-Baccalaureate Diploma in Accounting?", "~4.5-5.0 credits."),
    ("Program Requirements", "What is the difference between B.Co.M.S. Honours and B.Co.M.S. Honours with Concentration?", "General vs targeted credits."),
    ("Program Requirements", "What courses does the Concentration in Marketing require?", "Specific BUSI marketing courses."),
    ("Program Requirements", "What are the core required courses for all B.Sc. programs?", "Experimental science requirement + math."),
    ("Program Requirements", "What streams are available in Physics?", "Astrophysics, experimental, theory."),
    ("Program Requirements", "What is required for Earth Sciences in Vertebrate Paleontology B.Sc. Honours?", "Specific ERTH and BIOL blend."),
    ("Program Requirements", "What electives are required for the B.A. Honours in History?", "Breadth requirements + history electives."),
    ("Program Requirements", "How do I complete a Minor in Communication and Media Studies?", "4.0 credits incl. COMS 1001/1002."),

    # ── Academic Regulations ─────────────────────────────────────────────────
    ("Academic Regulations", "What is the minimum CGPA to stay in good academic standing?", "ACE thresholds (4.0 or 5.0 by credits)."),
    ("Academic Regulations", "What happens if I fail a required course?", "Must repeat; most recent grade counts."),
    ("Academic Regulations", "How does the academic continuation evaluation (ACE) work?", "Term assessment; Good Standing, AW, etc."),
    ("Academic Regulations", "What is the difference between WDN and EX on a transcript?", "WDN = withdrawn; EX = exempt/transfer."),
    ("Academic Regulations", "Can I repeat a course I passed to improve my grade?", "Yes, but latest grade counts even if lower."),
    ("Academic Regulations", "What is the maximum number of credits I can take per term?", "Generally 2.5; overload needs override."),
    ("Academic Regulations", "How does deferred exam eligibility work?", "Documentation filed within 3 days."),
    ("Academic Regulations", "What counts as academic misconduct at Carleton?", "Plagiarism, unauthorized collaboration, cheating."),
    ("Academic Regulations", "What is the grade point value of a B+ at Carleton?", "9.0 on the 12-point scale."),
    ("Academic Regulations", "How is the Major CGPA calculated differently from the overall CGPA?", "Major = core courses only."),

    # ── Registration Procedures ──────────────────────────────────────────────
    ("Registration Procedures", "How do I add a course after the first week of classes?", "Carleton Central until add deadline; override if needed."),
    ("Registration Procedures", "What is a time ticket and how does it work?", "Registration window by year standing."),
    ("Registration Procedures", "What is the difference between dropping a course and withdrawing from it?", "Drop = refund; withdraw = WDN, no refund."),
    ("Registration Procedures", "How do I get a registration override?", "Submit Registration Override Request."),
    ("Registration Procedures", "What happens if I miss the add/drop deadline?", "Can't add; may petition for backdated withdrawal."),
    ("Registration Procedures", "How do I register for an honours thesis course?", "Departmental permission / supervisor first."),
    ("Registration Procedures", "What is block registration and which programs use it?", "Pre-set schedules, primarily Engineering."),
    ("Registration Procedures", "How do I request academic consideration for missed coursework?", "Self-declaration form / contact instructor."),
    ("Registration Procedures", "How do I appeal a grade at Carleton?", "Informal review with prof, then formal appeal."),
    ("Registration Procedures", "What is a Letter of Permission and when do I need one?", "To take a course elsewhere and transfer credit."),

    # ── Deadlines & Dates ────────────────────────────────────────────────────
    ("Deadlines & Dates", "When does Fall 2026 registration open for returning students?", "July 2026 dates."),
    ("Deadlines & Dates", "What is the last day to drop a full fall course without academic notation?", "Late Sept / Sept 30."),
    ("Deadlines & Dates", "When do Fall 2026 final exams start?", "Around Dec 9-12."),
    ("Deadlines & Dates", "When is the fall 2026 payment deadline?", "Around Aug 25."),
    ("Deadlines & Dates", "What is the last day to add a course in Winter 2027?", "Mid-January."),

    # ── Services / Campus Life ───────────────────────────────────────────────
    ("Services / Campus Life", "How do I apply for co-op at Carleton?", "Co-op office; CGPA requirements."),
    ("Services / Campus Life", "What financial aid is available to undergraduate students?", "OSAP, bursaries, scholarships, work-study."),
    ("Services / Campus Life", "How do I get a transcript sent to another university?", "Official transcript via Carleton Central / MyCreds."),
    ("Services / Campus Life", "What is the process to defer an exam?", "Registrar portal within 3 days."),
    ("Services / Campus Life", "How do I verify my enrolment for a bank or employer?", "Certificate of Enrolment from Carleton Central."),

    # ── Edge Cases & Tricky ──────────────────────────────────────────────────
    ("Edge Cases & Tricky", "How many credits do I need to graduate?", "SHOULD ASK for clarification (program)."),
    ("Edge Cases & Tricky", "What courses do I need in first year?", "SHOULD ASK for clarification (program)."),
    ("Edge Cases & Tricky", "Is Professor Smith a good prof?", "SHOULD DECLINE — out of scope."),
    ("Edge Cases & Tricky", "What is the tuition fee for international students in 2026-27?", "Tests fee data / hallucination."),
    ("Edge Cases & Tricky", "Can I take COMP 4000 in my first year?", "SHOULD SAY NO (4000-level prereqs)."),
    ("Edge Cases & Tricky", "What is the GPA equivalent of a B- on a 4.0 scale?", "Should clarify Carleton uses 12-point (B- = 7.0)."),
    ("Edge Cases & Tricky", "I got a 72% in a course what letter grade is that?", "Should map to B-."),
    ("Edge Cases & Tricky", "What happens to my CGPA if I get an EX grade?", "EX does not affect CGPA."),
    ("Edge Cases & Tricky", "Does Carleton have a CS masters program?", "Should note it handles undergrad inquiries."),
    ("Edge Cases & Tricky", "What is COMP 9999?", "SHOULD CONFIRM does not exist — no hallucination."),
]


def read_last_log_line() -> dict | None:
    """Return the most recent queries.log entry, or None."""
    try:
        with open(QUERIES_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if line:
                return json.loads(line)
    except Exception:
        pass
    return None


def ask(question: str) -> tuple[str, int]:
    """POST to the live stream endpoint. Returns (answer_text, source_count)."""
    answer = ""
    source_count = 0
    try:
        resp = requests.post(
            f"{API_URL}/api/chat/stream",
            data={"question": question, "history": "[]"},
            stream=True,
            timeout=120,
        )
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data: "):
                continue
            try:
                parsed = json.loads(raw[6:])
            except Exception:
                continue
            if parsed.get("type") == "token":
                answer += parsed.get("content", "")
            elif parsed.get("type") == "sources":
                source_count = len(parsed.get("data", []))
    except Exception as e:
        answer = f"[REQUEST ERROR: {e}]"
    return answer.strip(), source_count


def diagnose(log: dict | None) -> str:
    """Auto-classify the retrieval signal so you know WHERE a wrong answer fails."""
    if not log:
        return "NO LOG"
    if log.get("type") == "stream_course":
        return "COURSE CARD (direct fetch)"
    if not log.get("had_context"):
        return "DATA GAP (no context)"
    score = log.get("top_score")
    if score is None:
        return "NO SCORE"
    if score < 0.35:
        return f"WEAK RETRIEVAL ({score}) → chunking/embeddings"
    if score < 0.50:
        return f"MODERATE ({score})"
    return f"STRONG RETRIEVAL ({score}) → if wrong, PROMPT issue"


def main():
    print("=" * 60)
    print("CampusQ — Automated Eval Harness")
    print("=" * 60)
    print(f"Target: {API_URL}\nQuestions: {len(TESTS)}\n")

    # health check
    try:
        requests.get(API_URL, timeout=5)
    except Exception:
        print(f"⚠  Could not reach {API_URL}. Is the backend running?")
        print("   Start it with:  uvicorn main:app --reload\n")
        return

    rows = []
    for i, (cat, q, expected) in enumerate(TESTS, 1):
        print(f"[{i}/{len(TESTS)}] {cat[:18]:<18} {q[:50]}")
        answer, src_count = ask(q)
        time.sleep(0.3)  # let the log flush
        log = read_last_log_line()
        rows.append({
            "Category": cat,
            "Question": q,
            "Expected / Guidance": expected,
            "Actual Answer": answer,
            "Score (0/1/2)": "",          # you grade this
            "Diagnostic": diagnose(log),
            "top_score": log.get("top_score") if log else "",
            "chunks": log.get("chunks") if log else "",
            "had_context": log.get("had_context") if log else "",
            "type": log.get("type") if log else "",
            "sources": src_count,
            "ms": log.get("ms") if log else "",
            "Notes": "",
        })

    fieldnames = [
        "Category", "Question", "Expected / Guidance", "Actual Answer",
        "Score (0/1/2)", "Diagnostic", "top_score", "chunks",
        "had_context", "type", "sources", "ms", "Notes",
    ]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # quick summary
    data_gaps = sum(1 for r in rows if "DATA GAP" in r["Diagnostic"])
    weak = sum(1 for r in rows if "WEAK" in r["Diagnostic"])
    strong = sum(1 for r in rows if "STRONG" in r["Diagnostic"])
    cards = sum(1 for r in rows if "COURSE CARD" in r["Diagnostic"])

    print(f"\n{'='*60}")
    print(f"DONE → {OUT_CSV}")
    print(f"{'='*60}")
    print(f"  Course-card answers : {cards}")
    print(f"  Strong retrieval    : {strong}   (if wrong → prompt issue)")
    print(f"  Weak retrieval      : {weak}   (chunking/embeddings)")
    print(f"  Data gaps           : {data_gaps}   (namespace missing the info)")
    print(f"\nNext: open eval_results.csv, fill the Score column (0/1/2),")
    print(f"then sort by Diagnostic to see exactly where failures cluster.\n")


if __name__ == "__main__":
    main()
