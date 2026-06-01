"""
scrape_registrar.py — Scrapes all Carleton registration and registrar pages.

Covers: academic dates, course selection guides, registration steps, waitlisting,
overrides, audits, advising, student documents, exams, grades, graduation,
petitions, appeals, and more.

Also directly indexes the academic glossary provided manually.

Namespace: "registrar"
Safe to re-run — stable IDs overwrite previous vectors.
Run: py scrape_registrar.py
"""

import os
import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup, NavigableString
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

NAMESPACE = "registrar"
EMBED_MODEL = "text-embedding-3-small"

# ── All curated URLs ──────────────────────────────────────────────────────────

URLS = [
    # NOTE: Academic dates are handled by scrape_dates.py (structured, one
    # vector per deadline) — the raw dates page chunks poorly, so it's excluded here.

    # New student onboarding
    ("New Student Checklist",       "https://carleton.ca/registration/new-ug/new-student-checklist/"),
    ("Returning Student Checklist", "https://carleton.ca/registration/returning-student-checklist/"),

    # Course selection guides (one per program)
    ("Course Selection Guide",                              "https://carleton.ca/registration/course-selection-guide/"),
    ("Course Selection Guide — B.Acc.",                     "https://carleton.ca/registration/course-selection-guide/baccounting/"),
    ("Course Selection Guide — B.A.S.",                     "https://carleton.ca/registration/course-selection-guide/bas/"),
    ("Course Selection Guide — B.A.",                       "https://carleton.ca/registration/course-selection-guide/ba/"),
    ("Course Selection Guide — B.Cog.Sc.",                  "https://carleton.ca/registration/course-selection-guide/b-cog-sci/"),
    ("Course Selection Guide — B.Com.",                     "https://carleton.ca/registration/course-selection-guide/bcomm/"),
    ("Course Selection Guide — B.Co.M.S.",                  "https://carleton.ca/registration/course-selection-guide/b-comms/"),
    ("Course Selection Guide — B.C.S.",                     "https://carleton.ca/registration/course-selection-guide/bcs/"),
    ("Course Selection Guide — B.Cyber.",                   "https://carleton.ca/registration/course-selection-guide/bcyber/"),
    ("Course Selection Guide — B.D.S.",                     "https://carleton.ca/registration/course-selection-guide/bds/"),
    ("Course Selection Guide — B.Econ.",                    "https://carleton.ca/registration/course-selection-guide/b-econ/"),
    ("Course Selection Guide — B.Eng.",                     "https://carleton.ca/registration/course-selection-guide/b-eng/"),
    ("Course Selection Guide — B.G.In.S.",                  "https://carleton.ca/registration/course-selection-guide/bgins/"),
    ("Course Selection Guide — B.H.Sc.",                    "https://carleton.ca/registration/course-selection-guide/b-hsc/"),
    ("Course Selection Guide — B.Hum.",                     "https://carleton.ca/registration/course-selection-guide/b-hum/"),
    ("Course Selection Guide — B.I.D.",                     "https://carleton.ca/registration/course-selection-guide/bid/"),
    ("Course Selection Guide — B.I.T.",                     "https://carleton.ca/registration/course-selection-guide/bit/"),
    ("Course Selection Guide — B.I.B.",                     "https://carleton.ca/registration/course-selection-guide/bib/"),
    ("Course Selection Guide — B.J.",                       "https://carleton.ca/registration/course-selection-guide/b-jour/"),
    ("Course Selection Guide — B.J.Hum.",                   "https://carleton.ca/registration/course-selection-guide/bjour-bhum/"),
    ("Course Selection Guide — B.Math.",                    "https://carleton.ca/registration/course-selection-guide/b-math/"),
    ("Course Selection Guide — B.M.P.D.",                   "https://carleton.ca/registration/course-selection-guide/bmpd/"),
    ("Course Selection Guide — B.Mus.",                     "https://carleton.ca/registration/course-selection-guide/b-mus/"),
    ("Course Selection Guide — B.Sc.N.",                    "https://carleton.ca/registration/course-selection-guide/bnursing/"),
    ("Course Selection Guide — B.P.A.P.M.",                 "https://carleton.ca/registration/course-selection-guide/bpapm/"),
    ("Course Selection Guide — B.Sc.",                      "https://carleton.ca/registration/course-selection-guide/bsc/"),
    ("Course Selection Guide — B.S.W.",                     "https://carleton.ca/registration/course-selection-guide/bsw/"),

    # Registration process
    ("Time Tickets for Registration",   "https://carleton.ca/registration/dates/timetickets/"),
    ("Registration Steps Overview",     "https://carleton.ca/registration/registration-steps/"),
    ("Registration Step 1",             "https://carleton.ca/registration/registration-steps/step-1/"),
    ("Registration Step 2",             "https://carleton.ca/registration/registration-steps/step-2/"),
    ("Registration Step 3",             "https://carleton.ca/registration/registration-steps/step-3/"),
    ("Registration Step 4",             "https://carleton.ca/registration/registration-steps/step-4/"),
    ("Waitlisting",                     "https://carleton.ca/registration/waitlisting/"),
    ("Registration Override Requests",  "https://carleton.ca/registration/override-requests/"),
    ("Course Delivery Types",           "https://carleton.ca/registration/course-delivery-types/"),
    ("Registration Terminology",        "https://carleton.ca/registration/terminology/"),
    ("Thesis / Project / Essay Registration", "https://carleton.ca/registration/honours-thesis-registration/"),
    ("Block Registration",              "https://carleton.ca/registration/block-registration/"),
    ("Programs with Block Registration","https://carleton.ca/registration/block-registration/block-programs/"),
    ("Access to Courses",               "https://carleton.ca/registration/access-to-courses/"),
    ("Registration Support",            "https://carleton.ca/registration/registration-support/"),

    # Non-degree / special students
    ("Non-Degree Students",             "https://carleton.ca/registration/non-degree-students/"),
    ("Special Students",                "https://carleton.ca/registration/special-students/"),
    ("Auditing Students",               "https://carleton.ca/registration/non-degree-students/auditing-students/"),
    ("Incoming Exchange Students",      "https://carleton.ca/registration/non-degree-students/incoming-exchange/"),
    ("Incoming Letter of Permission",   "https://carleton.ca/registration/non-degree-students/incoming-lop/"),
    ("uOttawa Exchange",                "https://carleton.ca/registration/non-degree-students/uottawa-exchange/"),
    ("Registrar — uOttawa Exchange",    "https://carleton.ca/registrar/university-ottawa/"),
    ("Non-Degree Courses",              "https://carleton.ca/registration/non-degree/"),
    ("Micro-Credentials",               "https://carleton.ca/registration/non-degree-students/micro-credentials/"),
    ("Professional Development",        "https://carleton.ca/registration/non-degree-students/professional-development/"),
    ("Micro-Credentials FAQ",           "https://carleton.ca/registration/non-degree-students/micro-credentials-faq/"),

    # Audit & advising
    ("Academic Audit",                  "https://carleton.ca/registration/academic-audit/"),
    ("How to Read Your Audit",          "https://carleton.ca/academicadvising/how-to-read-your-audit/"),
    ("What-If Audit",                   "https://carleton.ca/academicadvising/what-if-audit/"),
    ("Why Add Planned Courses",         "https://carleton.ca/academicadvising/why-add-planned-courses/"),
    ("Meet with an Advisor",            "https://carleton.ca/academicadvising/aac-request-form/"),

    # Student documents
    ("Verify Enrolment",                "https://carleton.ca/registrar/student-documents/verify-enrolment/"),
    ("Confirmation of Graduation",      "https://carleton.ca/registrar/student-documents/confirmation-of-graduation-letters/"),
    ("Diplomas",                        "https://carleton.ca/registrar/student-documents/diplomas/"),
    ("Transcripts",                     "https://carleton.ca/registrar/student-documents/transcripts/"),
    ("VOSS",                            "https://carleton.ca/registrar/student-documents/voss/"),
    ("Verify Degree",                   "https://carleton.ca/registrar/student-documents/verify-degree/"),
    ("Certificate of Enrolment",        "https://carleton.ca/registrar/certificateofenrolment/"),

    # Exams & grades
    ("Exam Deferral",                   "https://carleton.ca/registrar/deferral/"),
    ("Missed Deferral",                 "https://carleton.ca/registrar/deferral/missed-deferral/"),
    ("On Exam Day",                     "https://carleton.ca/ses/examination-services/on-exam-day/"),
    ("Distance Exams",                  "https://carleton.ca/ses/examination-services/distance-exams/"),
    ("Exams and Grades",                "https://carleton.ca/registrar/exams-and-grades/"),

    # Academic standing & appeals
    ("Academic Integrity Policy",       "https://carleton.ca/registrar/academic-integrity/"),
    ("Term Work Consideration",         "https://carleton.ca/registrar/academic-consideration-coursework/"),
    ("Grade Appeal",                    "https://carleton.ca/registrar/appeal-of-grade/"),
    ("Petitions and Appeals",           "https://carleton.ca/registrar/petition/"),
    ("Academic Continuation Evaluation (ACE)", "https://carleton.ca/registrar/ace/"),
    ("Academic Status Report (ASR)",    "https://carleton.ca/registrar/progress/academic-status-report/"),
    ("Registrar Policies",              "https://carleton.ca/registrar/about/policies/"),

    # Program & graduation
    ("Program Elements",                "https://carleton.ca/registrar/program-elements/"),
    ("Graduation",                      "https://carleton.ca/registrar/progress/graduation/"),
    ("Graduation Information",          "https://carleton.ca/registrar/progress/graduation/graduation-information/"),
    ("Major CGPA Check",                "https://carleton.ca/registrar/progress/major-cgpa-check/"),
    ("International Exchange",          "https://carleton.ca/registrar/international-exchange/"),
    ("Letter of Permission",            "https://carleton.ca/registrar/letter-of-permission/"),
    ("Letter of Permission Guide",      "https://carleton.ca/registrar/letter-of-permission/guide/"),
    ("Special Student Information",     "https://carleton.ca/registrar/special-student-information/"),

    # Personal / admin
    ("Name Change",                     "https://carleton.ca/registrar/name-change/"),
    ("Exemption from International Fees", "https://carleton.ca/registrar/exemptions-international-fees/"),
    ("Exemption from Out-of-Province Fees", "https://carleton.ca/registrar/out-of-province-fees/"),
    ("Parental Leave Request",          "https://carleton.ca/registrar/parental-leave-request/"),
    ("Third Party Authorization",       "https://carleton.ca/registrar/third-party/"),

    # Academic Advising
    ("Changing Your Major",             "https://carleton.ca/academicadvising/changing-your-major/"),
    ("Changing Your Degree",            "https://carleton.ca/academicadvising/changing-your-degree/"),
    ("Adding or Dropping Minors / Concentrations", "https://carleton.ca/academicadvising/adding-or-dropping-minorsconcentration/"),
    ("Reduced Course Load",             "https://carleton.ca/academicadvising/reduced-course-load/"),
    ("Academic Advising FAQ",           "https://carleton.ca/academicadvising/audit-faqs/"),
]

# ── Academic Glossary (provided manually) ────────────────────────────────────

GLOSSARY_TEXT = """Academic Terminology Glossary — Carleton University

Academic Continuation Evaluation (ACE): The ACE is the end-of-term assessment of student academic standing in undergraduate degree programs and special studies. The possible outcomes of an ACE are Eligible to Continue, Academic Warning, Required to Withdraw for Two Terms, Continue in Non-Honours, Continue in Alternate, Dismissed from Program, or Required to Withdraw for Two Years.

Accelerated Pathway: An admission pathway for certain graduate programs, whereby students in a participating Carleton undergraduate honours program may take up to 1.0 credits of graduate-level courses that will be applied towards both the undergraduate degree requirements and, upon admission, their graduate program of study.

Advanced Entry: An admission pathway for certain graduate programs that systematically removes a practicum, foundational course requirement, or overlap in required courses. This reduces the number of credits required for completion of the master's or Ph.D. program.

Advanced Standing: At the graduate level, a status conferred onto students who receive transfer credit upon admission.

Auditing Student: A student who attends a course for interest and not for credit. Formal registration is required.

Bachelor's Program: An undergraduate, non-honours academic program of study requiring a minimum of 15.0 credits.

Calendar: The official publication of academic regulations, academic programs and course descriptions as approved by the Senate.

Certificate: An undergraduate certificate is a stand-alone Credential that may be taken concurrently with a bachelor's program or independently. It is normally constituted by a structured set of at least four credits of sequential courses of different levels in a particular discipline or area of study.

Challenge for Credit: Undergraduate academic course credit gained through examination based on a student's prior learning experience. A successful challenge for credit is noted as CH. A CH is neither included in the CGPA calculation nor used to satisfy the degree program residency requirement.

Concentration: A program Element recorded on the transcript and diploma constituted by at least 3.5 credits of required courses at the undergraduate level, concentrating on a particular area of study within the program.

Co-operative Education: An undergraduate or graduate Option comprising work periods combined with academic study to acquire work-related experience.

Core: A course or group of courses that are a subset of the courses that constitute a major in an undergraduate program, subject to specific CGPA requirements.

Course: A unit of teaching that may count as credit towards a Credential. Courses have unique eight-character alphanumeric course codes, titles and descriptions. The credit value is indicated in square brackets following the course number.

Course Numbering: The first number in a course designation indicates the knowledge level. 0000-level courses satisfy prerequisites. 1000-level are introductory. 2000/3000-level are intermediate. 4000-level are advanced. 5000/6000-level are graduate.

Course Outline: Instructors must provide students a written Course Outline on or before the first teaching day, specifying all elements contributing to the final grade and the overall grade breakdown.

Courses Set Aside: Courses that do not contribute to graduation requirements: Extra to the Degree (ETD), No Credit for Degree (NCD), or Forfeit (repeated/precluded courses).

Credential: An academic qualification awarded by the University Senate upon successful completion of an academic program. All credentials are degrees, diplomas, or certificates.

Credit: The academic value of a course (for example, 0.0, 0.5, 1.0).

Cumulative Grade Point Average (CGPA): The key assessment tool for Academic Continuation Evaluation and graduation requirements. The CGPA is the average of grade points earned on all courses counting towards graduation.

Degree: A Credential at the Bachelor, Master, or Doctoral level awarded upon successful completion of prescribed program requirements.

Diploma (Post-baccalaureate): A stand-alone undergraduate credential for candidates already possessing a bachelor's degree. Normally constituted by at least three and a maximum of five credits of advanced undergraduate courses.

Dual Degree: A joint partnership where a co-enrolment agreement exists between Carleton and another post-secondary institution. Students simultaneously complete programs at both institutions, receiving two diplomas.

Element: Undergraduate elements are majors, minors, concentrations, and streams. Elements are recorded on the transcript and diploma.

Equivalency: Courses considered similar enough to preclude one another, commonly referred to as cross-listed courses (Also Listed As).

Experiential Learning: Application of theory and academic content to real-world experiences within the classroom, community, or workplace.

Free Elective: Any approved credit course normally at the 1000-level or higher that may be taken to make up the number of credits required for a degree program.

Good Academic Standing: Signifies a student is meeting the requirements for continuation in their program as defined in Section 3.2.6 of the Academic Regulations.

Honours Bachelor's Program: An undergraduate Bachelor's program requiring a minimum of 20.0 credits, which may demand a higher academic standard than a non-honours program.

Internship: Constituted through a course or sequence of courses providing students with work experience directly related to their degree program. Two types: Program Internship (at least 4.0 credits) and Course Internship (individual course).

Learning Outcomes: Discipline-specific statements describing observable skills or abilities all students are expected to acquire by the end of a course or program.

Letter of Permission: A formal document issued by the University Registrar approving a student to register in a course at another institution in lieu of a Carleton course.

Major: A program Element recorded on the transcript and diploma. The minimum number of required credits in the major within a 20-credit program is 8.0 credits; within a 15-credit program is 6.0 credits.

Major CGPA: Calculated as the average grade points earned on the courses that constitute the major.

Mention : francais: An undergraduate Option noted on the transcript denoting specified courses taken in French.

Minor: A program Element at the undergraduate level. Each Minor requires at least 4.0 and at most 5.0 credits.

Option: An optional addition to a program: undergraduate options include co-operative education, study abroad, Mention: francais, program internship.

Pathway: A route to program completion such as stream, thesis, research essay, research project, or course only. Recorded on the transcript but not the diploma.

Prerequisite: A required course or courses that must be completed successfully before registering in a course.

Preclusion: Courses containing sufficient content in common that credit may not be earned for more than one of them.

Program: A specified combination of academic requirements leading to a credential. Five types at undergraduate level: Single-Discipline, Thematic, Single-Discipline Honours, Combined Honours, and Thematic Honours.

Restricted Elective: Courses required to fulfil elective requirements in an undergraduate program that are prescribed by the program (not free electives).

Specialization: At the undergraduate level, an element similar to a concentration within specific programs like B.G.In.S.

Special Students: Students not admitted to a program or degree leading to a Credential.

Status (Full-time/Part-time): Undergraduate students are full-time when registered in at least 1.5 credits per term (60% course load). Part-time is less than 1.5 credits per term.

Stream: A program Element constituted by at least 1.5 credits of courses facilitating focus on a particular area of study. Streams are selected after admission, designed to be completed when started in second year.

Term GPA: The ratio of grade points earned on a course or courses to the total credit value completed in the term of assessment.

Topics Courses: Selected Topics courses address topics within a narrow range of a common theme. Students may not repeat selected topics courses for credit. Special Topics address topics from a broader range and may be repeated when topics vary.

Transfer Credit: Academic credit granted for individual courses successfully completed at another institution, either upon admission or while registered with a Letter of Permission or on exchange.

Transcript: The official record of a student's academic registration and accomplishments at Carleton University.

Undeclared Students: Undergraduate students admitted to a degree who have not chosen a program. Students are normally required to declare a major upon or before completing 3.5 credits.

Withdrawal: A formal process for discontinuing studies in a course or a program. Undergraduate students who have been away for nine or more consecutive terms will be withdrawn and must re-apply for admission."""


# ── Scraping ──────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ").replace("​", "")).strip()


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "CampusQ-Bot/1.0"})
        if r.status_code != 200:
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"    ✗ Fetch error: {e}")
        return None


def extract_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "form"]):
        tag.decompose()

    main = (
        soup.find("div", class_=re.compile(r"entry-content|page-content|main-content|content-area", re.I)) or
        soup.find("main") or
        soup.find("article") or
        soup.find("div", id=re.compile(r"content|main", re.I)) or
        soup.find("body")
    )

    if not main:
        return ""

    lines = []
    for elem in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "dt", "dd"]):
        text = clean(elem.get_text(" ", strip=True))
        if text and len(text) > 3:
            lines.append(text)

    return "\n".join(lines)


def chunk_text(title: str, text: str, max_words: int = 500) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = []
    word_count = 0

    for para in paragraphs:
        words = len(para.split())
        if word_count + words > max_words and current:
            chunks.append("\n".join(current))
            current = []
            word_count = 0
        current.append(para)
        word_count += words

    if current:
        chunks.append("\n".join(current))

    return [c for c in chunks if len(c) > 80]


# ── Upload ────────────────────────────────────────────────────────────────────

def upload(label: str, url: str, chunks: list[str]) -> int:
    if not chunks:
        return 0

    texts = [f"{label}\n{c[:900]}" for c in chunks]
    response = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)

    vectors = []
    for i, emb_data in enumerate(response.data):
        raw_id = f"{url}-{i}"
        chunk_id = hashlib.md5(raw_id.encode()).hexdigest()[:20]
        vectors.append({
            "id": chunk_id,
            "values": emb_data.embedding,
            "metadata": {
                "title": label,
                "text": f"{label}\n\n{chunks[i][:2000]}",
                "source": url,
                "chunk": i,
            },
        })

    index.upsert(vectors=vectors, namespace=NAMESPACE)
    return len(vectors)


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 55)
    print("CampusQ — Registrar Scraper")
    print("=" * 55 + "\n")

    total = 0

    # 1. Index the glossary directly (no HTTP needed)
    print("Indexing academic glossary...")
    chunks = chunk_text("Academic Terminology Glossary", GLOSSARY_TEXT, max_words=400)
    n = upload("Academic Terminology Glossary — Carleton University", "https://carleton.ca/registration/terminology/", chunks)
    total += n
    print(f"  ✓ Glossary — {n} chunks\n")

    # 2. Scrape all curated URLs
    print(f"Scraping {len(URLS)} pages...\n")
    for i, (label, url) in enumerate(URLS):
        print(f"[{i+1}/{len(URLS)}] {label}")
        soup = fetch_page(url)
        if not soup:
            print(f"  ✗ Could not fetch")
            time.sleep(0.5)
            continue

        text = extract_text(soup)
        if len(text) < 100:
            print(f"  — no content")
            time.sleep(0.3)
            continue

        chunks = chunk_text(label, text)
        n = upload(label, url, chunks)
        total += n
        print(f"  ✓ {n} chunks")
        time.sleep(0.5)

    print(f"\n{'='*55}")
    print(f"DONE — {total} total vectors in '{NAMESPACE}' namespace")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
