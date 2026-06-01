"""
scrape_facts.py — Structured fact vectors for high-frequency questions that
chunk poorly from large regulation/program pages.

Same strategy as scrape_dates.py: one focused, synonym-rich vector per fact
so common student questions retrieve at high confidence.

Namespace: "facts"
Run: py scrape_facts.py
"""

import os
import re
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "facts"
EMBED_MODEL = "text-embedding-3-small"

# Each fact: (id, title, body)
# Body is rich, synonym-heavy so varied phrasings retrieve it.
FACTS = [

    # ── Course repeat policy ─────────────────────────────────────────────────
    (
        "course-repeat-policy",
        "Course Repeat Policy at Carleton University",
        """Course Repeat Policy — Carleton University

Students may repeat a course they have already passed in order to improve their grade.
When a course is repeated, only the most recent grade counts toward the CGPA — even if
the new grade is lower than the original grade. The earlier grade is placed in the
"Forfeit" category and no longer affects the CGPA.

Key points:
- You CAN repeat a passed course. There is no rule against it.
- Only the LATEST attempt counts toward your CGPA, regardless of which grade is higher.
- The previous grade is forfeited — it does not count toward graduation credits.
- If you repeat a course and get a lower grade, your CGPA will drop.
- Repeated courses are noted on your transcript.

Related terms: redo a course, retake a course, repeat for higher grade, replace grade,
improve CGPA, course repetition, forfeit grade, previous attempt.""",
    ),

    # ── Adding a course after the first week ─────────────────────────────────
    (
        "adding-course-late",
        "How to Add a Course After the First Week at Carleton",
        """Adding a Course After the First Week — Carleton University

The standard add/change deadline is approximately two weeks after the start of term.
After the first week but before the official add deadline, you can still add courses
directly through Carleton Central without any special permission.

After the official add deadline:
- You cannot add a course through Carleton Central on your own.
- You must submit a Registration Override Request (ROR) through Carleton Central.
- The instructor and department must approve the override.
- Late adds are not guaranteed — it is at the discretion of the department.
- Late additions may result in missed coursework that cannot be made up.

Key dates (Fall 2026):
- Last day to add full fall / fall-winter courses: September 22, 2026
- After this date: Override Request required

For Winter 2027:
- Last day to add full winter courses: January 19, 2027

Steps to request an override:
1. Log into Carleton Central
2. Go to Registration Override Request
3. Select the course and provide a reason
4. Wait for departmental approval

Related terms: late add, add after deadline, registration override, ROR, enroll late,
missed the add deadline, can I still add a course, course addition after week one.""",
    ),

    # ── B.Com graduation credit requirements ─────────────────────────────────
    (
        "bcom-graduation-credits",
        "B.Com. Honours Graduation Credit Requirements at Carleton",
        """Bachelor of Commerce (B.Com.) Honours — Graduation Requirements

Total credits required to graduate: 20.0 credits

Credit breakdown:
- Credits included in the Major CGPA: 12.0 credits
  - Required core business courses (BUSI, ECON, MATH, STAT, PSYC, SOCI)
  - 1.0 credit in BUSI at the 4000-level
  - BUSI 4601 Business Ethics (0.5 credits)
  - BUSI 4609 Strategic Management (0.5 credits)
- Credits NOT included in the Major CGPA: 8.0 credits (free electives)

Minimum CGPA to graduate: 4.00 overall and in the major

Concentration: Students in a concentration complete 4.0-4.5 credits within the
12.0 major credits toward a specific area (Accounting, Finance, Marketing, etc.)

Non-Honours B.Com.: Also 20.0 credits total, with 11.0 credits in the major.

Related terms: how many credits to graduate commerce, B.Com credits, bachelor of commerce
graduation requirements, how long is the commerce degree, sprott graduation, bcom honours
credits needed, how many credits does bcom require, commerce degree length.""",
    ),

    # ── Carleton 12-point GPA scale ──────────────────────────────────────────
    (
        "carleton-gpa-scale",
        "Carleton University 12-Point GPA Grading Scale",
        """Carleton University uses a 12-point grading scale — NOT a 4.0 scale.

Grade point values:
A+ = 12    (90-100%)
A  = 11    (85-89%)
A- = 10    (80-84%)
B+ = 9     (77-79%)
B  = 8     (73-76%)
B- = 7     (70-72%)
C+ = 6     (67-69%)
C  = 5     (63-66%)
C- = 4     (60-62%)
D+ = 3     (57-59%)
D  = 2     (53-56%)
D- = 1     (50-52%)
F  = 0     (0-49%)

CGPA is calculated as: sum(grade points x credits) / sum(credits)

Percentage to letter grade conversions:
- 72% = B-  (7 points)
- 75% = B   (8 points)
- 80% = A-  (10 points)
- 85% = A   (11 points)

The minimum passing grade for most courses is D- (50%).
The minimum CGPA for good standing in most programs is 4.00 (C-).
Dean's List / High Achievement is typically A- (10.0) or above.

Related terms: GPA scale, grade points, letter grade percentage, what is my GPA,
Carleton grading, 4.0 equivalent, grade conversion, what letter grade is 72 percent,
what is a B+ worth, grade point average Carleton, 12 point scale.""",
    ),

    # ── WDN vs drop vs EX ────────────────────────────────────────────────────
    (
        "wdn-drop-ex-difference",
        "Difference Between Dropping, Withdrawing (WDN), and EX Grade at Carleton",
        """Dropping a Course vs Withdrawing (WDN) vs EX Grade — Carleton University

DROPPING a course (before the fee adjustment deadline):
- No record on transcript
- Full or partial tuition refund depending on timing
- No academic penalty
- Deadline: approximately 2-3 weeks after term starts

WITHDRAWING from a course (WDN — after the fee adjustment deadline):
- WDN notation appears on transcript
- No refund
- Does NOT affect your CGPA (WDN is not included in CGPA calculation)
- You still owe tuition for the course
- Deadline: approximately 6-8 weeks before end of term (varies)
- After the withdrawal deadline, you cannot withdraw and will receive a grade

EX grade (Exempt):
- Awarded for transfer credit from another institution
- Appears on transcript as EX
- Does NOT count toward CGPA
- Does count toward credits for graduation purposes
- You did not take the course at Carleton — it was recognized from elsewhere

Summary:
- Drop = no record, possible refund
- WDN = on transcript, no CGPA impact, no refund
- EX = transfer credit recognition, counts for graduation, no CGPA impact

Related terms: difference between drop and withdraw, WDN transcript, what does WDN mean,
exempt grade, EX grade CGPA, does WDN hurt GPA, does EX count toward graduation,
academic withdrawal notation, late withdrawal.""",
    ),

    # ── What happens if you fail a required course ───────────────────────────
    (
        "fail-required-course",
        "What Happens If You Fail a Required Course at Carleton",
        """Failing a Required Course at Carleton University

If you fail a required course:
1. You must repeat the course — it is required for your degree and must be passed.
2. The failed grade (F = 0 points) counts in your CGPA until you retake the course.
3. When you repeat and pass, the new grade replaces the old one in your CGPA.
4. The F grade is moved to the Forfeit category and no longer counts.

Academic standing impact:
- A failing grade lowers your CGPA immediately.
- If your CGPA drops below the minimum threshold, you may receive an Academic Warning
  or be Required to Withdraw through the Academic Continuation Evaluation (ACE).
- You should retake the failed course as soon as possible to recover your CGPA.

Important: If you fail and then pass a course, only the latest grade counts.
If you fail twice, both F grades are on your record until the most recent attempt.

Related terms: failed a course, F grade, what happens if I fail, repeat after failing,
must retake, required course fail, failed required class, CGPA after failing,
academic consequences of failing.""",
    ),
]


def run():
    print("=" * 55)
    print("CampusQ - Structured Facts Ingestion")
    print("=" * 55 + "\n")

    texts = [f"{title}\n\n{body}" for (_, title, body) in FACTS]

    print(f"Embedding {len(texts)} fact vectors...")
    resp = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)

    vectors = []
    for i, emb in enumerate(resp.data):
        fact_id, title, body = FACTS[i]
        vectors.append({
            "id": f"fact-{fact_id}",
            "values": emb.embedding,
            "metadata": {
                "title": title,
                "text": f"{title}\n\n{body}",
                "source": "https://calendar.carleton.ca",
                "category": "structured_fact",
            },
        })

    index.upsert(vectors=vectors, namespace=NAMESPACE)

    print(f"Done - {len(vectors)} fact vectors in '{NAMESPACE}' namespace\n")
    for v in vectors:
        print(f"  - {v['metadata']['title']}")


if __name__ == "__main__":
    run()
