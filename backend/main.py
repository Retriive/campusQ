import os
import json
import re
import time
import uuid
import contextvars
from datetime import datetime, date

# Request-scoped session id — set once per request, read by log_query.
# Avoids threading session_id through every log call site.
_current_session: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="none")
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pinecone import Pinecone
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import fitz  # PyMuPDF

from citations import (
    build_context_and_citations,
    citation_from_course,
    finalize_citations,
    should_emit_citations,
)
from retrieval import retrieve_and_rerank

load_dotenv()

app = FastAPI()

# ── Logging setup ─────────────────────────────────────────────────────────────

# On Render: mount a persistent disk at /data so logs survive redeploys.
# Locally (no /data): falls back to the backend/ directory.
LOG_DIR = "/data" if os.path.isdir("/data") else os.path.dirname(os.path.abspath(__file__))

def _log(filename: str, data: dict):
    """Append a JSON line to a log file. Thread-safe for single-process use."""
    path = os.path.join(LOG_DIR, filename)
    line = json.dumps(data, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)

# Maps the most common course-code prefixes to a readable department/subject.
# Used for analytics — what subject areas are students asking about?
DEPT_BY_PREFIX = {
    "COMP": "Computer Science", "SYSC": "Systems Engineering", "BUSI": "Business",
    "MATH": "Mathematics", "STAT": "Statistics", "PSYC": "Psychology",
    "ECON": "Economics", "BIOL": "Biology", "CHEM": "Chemistry", "PHYS": "Physics",
    "ERTH": "Earth Sciences", "ENGL": "English", "HIST": "History", "LAWS": "Law",
    "COMS": "Communication & Media", "JOUR": "Journalism", "PSCI": "Political Science",
    "SOCI": "Sociology", "PHIL": "Philosophy", "ELEC": "Electrical Eng",
    "MECH": "Mechanical Eng", "CIVE": "Civil Eng", "AERO": "Aerospace Eng",
    "ARCH": "Architecture", "NURS": "Nursing", "HLTH": "Health Sciences",
    "NEUR": "Neuroscience", "FILM": "Film Studies", "MUSI": "Music",
    "GEOG": "Geography", "CRCJ": "Criminology", "BIT":  "Information Technology",
    "DATA": "Data Science", "GINS": "Global & International Studies",
}

# Keyword fallbacks when no course code is present in the query.
DEPT_BY_KEYWORD = [
    ("computer science", "Computer Science"), ("cybersecurity", "Computer Science"),
    ("business", "Business"), ("commerce", "Business"), ("b.com", "Business"),
    ("engineering", "Engineering"), ("psychology", "Psychology"),
    ("economics", "Economics"), ("biology", "Biology"), ("chemistry", "Chemistry"),
    ("physics", "Physics"), ("nursing", "Nursing"), ("journalism", "Journalism"),
    ("communication", "Communication & Media"), ("law", "Law"),
    ("data science", "Data Science"), ("math", "Mathematics"),
]

# Question-intent classification (what KIND of thing is being asked) — separate
# from query_type (which is the retrieval path). This is what advising cares about.
def classify_intent(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["prerequisite", "prereq", "before taking", "without taking"]):
        return "prerequisites"
    if any(k in q for k in ["deadline", "last day", "when is", "when do", "when does", "what date"]):
        return "deadlines"
    if any(k in q for k in ["cgpa", "gpa", "good standing", "fail", "repeat", "withdraw", "ace ", "academic standing"]):
        return "regulations"
    if "engineering" in q and any(k in q for k in ["how many times", "attempt", "retake", "try again"]):
        return "regulations"
    if any(k in q for k in ["register", "registration", "add a course", "drop", "override", "waitlist", "time ticket"]):
        return "registration"
    if any(k in q for k in ["required courses", "graduate", "degree", "program", "stream", "concentration", "minor", "credits to"]):
        return "program_requirements"
    if any(k in q for k in ["co-op", "transcript", "financial aid", "bursary", "scholarship", "defer", "enrolment"]):
        return "services"
    if re.search(r'[a-zA-Z]{4}\s*\d{4}', query):
        return "course_lookup"
    return "general"


ENGINEERING_ATTEMPTS_CONTEXT = """[Authoritative — Engineering course attempt limit, Calendar §3.2.2]

A student in the Bachelor of Engineering degree may attempt a course no more than three times.
An attempt includes courses where the student earned a final letter grade, SAT, UNS, CR, or NR."""


def is_engineering_attempt_limit_query(query: str) -> bool:
    q = query.lower()
    if "engineering" not in q and "b.eng" not in q:
        return False
    return any(k in q for k in ("how many times", "attempt", "retake", "try again"))


def prepend_engineering_attempts_context(context_text: str, query: str) -> str:
    if not is_engineering_attempt_limit_query(query):
        return context_text
    if context_text:
        return f"{ENGINEERING_ATTEMPTS_CONTEXT}\n\n{context_text}"
    return ENGINEERING_ATTEMPTS_CONTEXT


def detect_department(query: str, course_codes: list[str]) -> str:
    """Best-effort subject/department for analytics."""
    if course_codes:
        prefix = course_codes[0].split()[0].upper()
        return DEPT_BY_PREFIX.get(prefix, prefix)
    q = query.lower()
    for kw, dept in DEPT_BY_KEYWORD:
        if kw in q:
            return dept
    return "general"


def log_query(
    query: str,
    query_type: str,          # retrieval path: "course_lookup" | "rag" | "stream_course" | "stream_rag"
    chunks_retrieved: int,
    top_score: float | None,
    course_codes_found: list[str],
    response_ms: int,
    had_context: bool,
    user_id: str = "anonymous",
    session_id: str | None = None,
):
    _log("queries.log", {
        "ts": datetime.utcnow().isoformat(),
        "id": str(uuid.uuid4())[:8],
        "session": session_id or _current_session.get(),
        "user": user_id,
        "department": detect_department(query, course_codes_found),
        "intent": classify_intent(query),
        "type": query_type,
        "query": query[:300],
        "chunks": chunks_retrieved,
        "top_score": round(top_score, 3) if top_score is not None else None,
        "courses_found": course_codes_found,
        "had_context": had_context,
        "ms": response_ms,
    })

def log_course_miss(course_code: str, query: str):
    """Log when a course code in a query isn't found in Pinecone."""
    _log("course_misses.log", {
        "ts": datetime.utcnow().isoformat(),
        "course": course_code,
        "query": query[:200],
    })

def log_no_context(query: str, query_type: str):
    """Log when RAG returns zero usable chunks — indicates a data gap."""
    _log("no_context.log", {
        "ts": datetime.utcnow().isoformat(),
        "type": query_type,
        "query": query[:300],
    })

def log_feedback(session_id: str, question: str, answer: str, rating: str):
    """Per-answer thumbs up/down — the strongest pitch metric (self-reported helpfulness)."""
    _log("feedback.log", {
        "ts": datetime.utcnow().isoformat(),
        "session": session_id or "none",
        "rating": rating,                 # "up" | "down"
        "department": detect_department(question, []),
        "intent": classify_intent(question),
        "question": question[:300],
        "answer": answer[:500],
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
async_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

SIMILARITY_THRESHOLD = 0.25
CHAT_MODEL = "gpt-4o-mini"


def rewrite_query_for_embedding(user_query: str) -> str:
    if len(user_query) <= 60:
        return user_query
    try:
        rewrite_response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a search query optimizer for a Carleton University academic knowledge base. "
                        "Rewrite the user's question into a concise, keyword-rich search query (max 2 sentences) "
                        "that will retrieve the most relevant course, program, or policy information. "
                        "Output ONLY the rewritten query, no explanation."
                    ),
                },
                {"role": "user", "content": user_query},
            ],
            max_tokens=80,
            temperature=0,
        )
        return rewrite_response.choices[0].message.content.strip()
    except Exception:
        return user_query


def extract_clean_description(doc_text: str) -> str:
    """
    Extracts just the readable course description from raw calendar text.
    Strips boilerplate suffixes like Prerequisite(s), Precludes, Lectures, etc.
    Raw text format:
      Line 0: course code
      Line 1: credits
      Line 2: course name
      Line 3+: description (plus mixed-in boilerplate)
    """
    lines = [l.strip() for l in doc_text.split("\n") if l.strip()]

    if len(lines) > 3:
        desc_parts = lines[3:]
    elif lines:
        desc_parts = [lines[-1]]
    else:
        return doc_text

    full_desc = " ".join(desc_parts)

    # Strip course name from start of description if it was captured as first line of body
    # e.g. "Introduction to African Studies I Introduction to African studies..."
    if len(lines) > 2:
        course_name = lines[2].strip()
        if full_desc.startswith(course_name):
            full_desc = full_desc[len(course_name):].strip()

    # Trim everything from the first occurrence of these boilerplate phrases onward
    cutoff_patterns = [
        r"Precludes additional credit",
        r"Prerequisite\(s\)\s*:",
        r"Includes:\s*Experiential Learning",
        r"Lectures?\s+\w+\s+hours?",
        r"Also listed as",
        r"Not available for",
        r"Note[:\s]",
    ]
    for pattern in cutoff_patterns:
        m = re.search(pattern, full_desc, re.IGNORECASE)
        if m:
            full_desc = full_desc[:m.start()].strip().rstrip(".")

    return full_desc or " ".join(desc_parts)


def rag_lookup_prerequisites(course_code: str) -> str:
    """
    When the O(1) metadata fetch has no prerequisite info, do a targeted
    semantic search for the prerequisite sentence in the indexed chunks.
    Returns the raw prerequisite string, or "" if not found.
    """
    try:
        query = f"{course_code} prerequisite required courses"
        embedding = openai_client.embeddings.create(
            input=query,
            model="text-embedding-3-small",
        ).data[0].embedding
        results = index.query(
            vector=embedding,
            top_k=5,
            include_metadata=True,
            namespace="courses",
        )
        for match in results.matches:
            if match.score < 0.5:
                continue
            chunk_text = match.metadata.get("text", "")
            # only look in chunks that mention this course code
            if course_code.replace(" ", "").upper() not in chunk_text.upper().replace(" ", "").replace("\xa0", ""):
                continue
            m = re.search(
                r'Prerequisite\(s\)\s*[: ]\s*(.+?)(?=\s*(?:Precludes|Lectures\s+\w+|Also listed|Not available|\Z))',
                chunk_text, re.IGNORECASE | re.DOTALL
            )
            if m:
                return m.group(1).strip().rstrip(".")
            # also try the metadata prereq field on this chunk
            mp = match.metadata.get("prerequisites", "")
            if mp and mp.lower() not in ("none", ""):
                return mp.strip()
    except Exception as e:
        print(f"RAG prereq fallback error for {course_code}: {e}")
    return ""


def parse_course_from_metadata(metadata: dict, clean_code: str) -> dict:
    doc_text = metadata.get("text", "")
    lines = [l.strip() for l in doc_text.split("\n") if l.strip()]
    course_name = lines[2] if len(lines) > 2 else "Course Details"
    raw_credits = metadata.get("credits", "0.5")
    cred_match = re.search(r"[\d\.]+", str(raw_credits))
    credits_val = float(cred_match.group()) if cred_match else 0.5
    # --- Prerequisite extraction ---
    # Priority: 1) prerequisite_text field (full OR/AND), 2) doc_text regex, 3) codes only, 4) RAG
    prereq_text = ""
    stored = metadata.get("prerequisite_text", "")
    if stored and stored.lower() not in ("none", ""):
        prereq_text = stored.strip()
    else:
        prereq_match = re.search(
            r'Prerequisite\(s\)\s*[: ]\s*(.+?)(?=\s*(?:Precludes|Lectures\s+\w+|Also listed|Not available|$))',
            doc_text, re.IGNORECASE | re.DOTALL
        )
        if prereq_match:
            prereq_text = prereq_match.group(1).strip().rstrip(".")
        else:
            meta_prereq = metadata.get("prerequisites", "")
            if meta_prereq and meta_prereq.lower() not in ("none", ""):
                prereq_text = meta_prereq.strip()
            else:
                prereq_text = rag_lookup_prerequisites(clean_code)
    # Also build a clean code array (for the prereq visualizer) from whatever we found
    if prereq_text:
        raw_codes = re.findall(r'[A-Z]{3,4}[\xa0 ]+\d{4}', prereq_text)
        prereqs_array = list(dict.fromkeys(p.replace('\xa0', ' ').strip() for p in raw_codes))
    else:
        prereqs_array = []

    clean_desc = extract_clean_description(doc_text)
    return {
        "courseCode": metadata.get("course_code", clean_code),
        "courseName": course_name,
        "credits": credits_val,
        "description": clean_desc,
        "prerequisites": prereqs_array,
        "prerequisiteText": prereq_text or "None",
    }


def build_system_prompt(context_text: str, attachment_text: str | None = None) -> str:
    today = date.today().strftime("%B %d, %Y")
    attachment_section = f"\n\nSTUDENT-UPLOADED DOCUMENT:\n{attachment_text if attachment_text else 'None.'}" if attachment_text is not None else ""
    return f"""You are CampusQ, an AI assistant for Carleton University students. You answer questions about courses, programs, prerequisites, regulations, and academic life using the Carleton Academic Calendar.

You are independent — not officially affiliated with Carleton University.

Today's date is {today}. Use this to answer questions about upcoming deadlines, current term, or time-sensitive information.

RULES:
1. Answer from the CONTEXT below. It is your source of truth.
2. For course lookups: state the course code, name, credits, prerequisites, and description clearly.
3. For program requirements: list courses by year if the context has them. If context is partial, say so — never guess missing years.
4. For follow-up questions, use both the context AND the conversation history. Be direct.
5. NEVER invent course codes, credit values, or requirements not in the context.
6. If the context doesn't have the answer, say: "That's outside of what I currently know. If you think this should be covered, use the Report a Problem button and we'll add it."
7. Be concise. No walls of text. No unnecessary caveats.
8. Only mention calendar.carleton.ca when you genuinely can't answer — not as a reflex.
9. OUT-OF-SCOPE: If asked about professor quality, ratings, reviews, or teaching style (e.g. "is Professor X good?", "how is X as a teacher?"), say: "I don't have professor ratings — try RateMyProfessors.ca for student reviews." Do NOT apply this to factual questions like "who teaches X?" or "who is the instructor?" — those are schedule questions, answer them from the context.
10. POINT TO EXISTING CARLETON TOOLS: Carleton already provides self-service tools for many tasks. When a question matches one of these, go ahead and answer normally (including doing any math the student asks for), but always close with a short mention of the official tool so they know it exists for next time:
   - CGPA calculations / "what-if" grade scenarios → Carleton Central's What-If Audit (carleton.ca/academicadvising/what-if-audit). E.g. after answering, add something like: "For more scenarios like this using your real transcript, check out Carleton Central's What-If Audit."
   - Checking current CGPA, major CGPA, or academic standing → Carleton Central audit
   - Registering, dropping, or waitlisting for courses → Carleton Central registration
   - Transcripts, enrolment verification, confirmation of graduation → Carleton Central / Student Documents
   - Exam deferrals, grade appeals, petitions → the registrar's relevant request form (use context link if available)
   - Course timetables/seat availability → Carleton Central Schedule Builder
   Keep the mention brief — one sentence, not a disclaimer paragraph. Don't repeat it if it was already mentioned earlier in the conversation for the same topic.

ACTION QUESTIONS — IMPORTANT:
For drop, withdraw, register, or add-course questions:
- Explain the Carleton Central process from context.
- If the student names a course but not a term (Fall/Winter/Summer), ask which term they mean before stating a specific deadline — deadlines differ by term and by drop vs withdraw.
- Do not answer with only course catalog metadata.

ENGINEERING COURSE ATTEMPTS — IMPORTANT:
For Bachelor of Engineering students asking how many times they can attempt/retake a course:
- The limit is three attempts per course (Calendar §3.2.2).
- State "three times" clearly in your answer.

PROGRAM COMPARISON — SOFTWARE ENGINEERING vs COMPUTER SCIENCE:
When asked to compare Software Engineering and Computer Science at Carleton:
- Compare Bachelor of Engineering (Software Engineering) vs the base Bachelor of Computer Science (B.C.S. Honours/Major) — NOT a CS stream.
- Do NOT primarily describe "Computer Science Software Engineering Stream" or another stream as the whole CS program.
- Cover degree type (B.Eng vs B.C.S.), approximate credits, faculty/school, and focus (engineering systems vs CS theory/programming).

CLARIFYING QUESTIONS — IMPORTANT:
Some questions are too vague to answer accurately without knowing the student's program. If the question is program-dependent and the student hasn't specified their program, ask ONE short clarifying question instead of guessing.

Examples of when to ask:
- "How many credits to graduate?" → Ask: "Which program are you in? Credit requirements vary — Engineering is typically 20.0, most Arts and Science programs are around 15.0–20.0."
- "What courses do I need?" → Ask: "Which program and year are you in?"
- "What are my electives?" → Ask: "Which program are you in?"
- "Am I on track to graduate?" → Ask: "What program are you in and how many credits have you completed?"

Do NOT ask for clarification when:
- The question mentions a specific program or course already
- The answer is universal (e.g. grading scale, exam policies)
- You already know the program from earlier in the conversation

SCHEDULE QUESTIONS — IMPORTANT:
- If a student asks whether a course is offered in a specific term and the context shows that course in a DIFFERENT term, say: "[Course] is not offered in [requested term], but it IS offered in [terms from context]." Do NOT say "outside of what I currently know" in this case.
- Only say "outside of what I currently know" if the course does not appear anywhere in the schedule context.
- If the context contains schedule data for a course, always use it to answer — even if the term in the context differs from what was asked.

CONTEXT:
{context_text if context_text else "No context retrieved."}{attachment_section}"""


@app.get("/")
async def health_check():
    return {"status": "CampusQ Brain is active and listening."}


@app.get("/api/documents")
async def get_documents():
    try:
        stats = index.describe_index_stats()
        return {"count": stats.total_vector_count}
    except Exception as e:
        print(f"Stats Error: {e}")
        return {"count": 0}


# ── Structured program requirements ──────────────────────────────────────────
_PROGRAM_REQS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "program_requirements.json")
_PROGRAM_REQS_CACHE: dict | None = None

def _load_program_reqs() -> dict:
    global _PROGRAM_REQS_CACHE
    if _PROGRAM_REQS_CACHE is None:
        try:
            with open(_PROGRAM_REQS_PATH, "r", encoding="utf-8") as f:
                _PROGRAM_REQS_CACHE = json.load(f)
        except Exception:
            _PROGRAM_REQS_CACHE = {}
    return _PROGRAM_REQS_CACHE

@app.get("/api/program-requirements")
async def program_requirements(slug: str = ""):
    """No slug -> index of programs+variants; slug -> that program's structured requirements."""
    data = _load_program_reqs()
    if not slug:
        return {"programs": [{"slug": k, "variants": list(v["variants"].keys())} for k, v in data.items()]}
    prog = data.get(slug)
    if not prog:
        return {"found": False}
    return {"found": True, "slug": slug, **prog}


@app.get("/api/degree-plan")
async def degree_plan(slug: str = "", variant: str = ""):
    """
    Returns all required course nodes + prerequisite edges for a program variant.
    Used by the My Plan tree view.
    """
    data = _load_program_reqs()
    prog = data.get(slug)
    if not prog or not variant:
        return {"courses": [], "edges": []}

    groups = prog.get("variants", {}).get(variant)
    if not groups:
        return {"courses": [], "edges": []}

    # Collect all unique course codes required by this variant
    COURSE_RE = re.compile(r'\b([A-Z]{3,4}[\xa0 ]+\d{4}[A-Z]?)\b')
    required_codes: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for c in group.get("courses", []):
            raw = c.get("code", "")
            for m in COURSE_RE.findall(raw):
                code = m.replace('\xa0', ' ').strip()
                if code not in seen:
                    seen.add(code)
                    required_codes.append(code)

    required_set = set(required_codes)

    # Fetch each course from Pinecone to get name, credits, prereqs
    course_nodes = []
    prereq_map: dict[str, list[str]] = {}

    for code in required_codes:
        course_id = code.replace(" ", "")
        try:
            result = index.fetch(ids=[course_id], namespace="courses")
            if result and "vectors" in result and course_id in result["vectors"]:
                meta = result["vectors"][course_id]["metadata"]
                parsed = parse_course_from_metadata(meta, code)
                course_nodes.append({
                    "code": code,
                    "name": parsed.get("courseName", code),
                    "credits": parsed.get("credits", 0.5),
                })
                prereq_map[code] = parsed.get("prerequisites", [])
            else:
                course_nodes.append({"code": code, "name": code, "credits": 0.5})
                prereq_map[code] = []
        except Exception:
            course_nodes.append({"code": code, "name": code, "credits": 0.5})
            prereq_map[code] = []

    # Build edges — only between courses in the required set
    edges = []
    seen_edges: set[tuple] = set()
    for target, prereqs in prereq_map.items():
        for src in prereqs:
            src_norm = src.replace('\xa0', ' ').strip()
            if src_norm in required_set and src_norm != target:
                key = (src_norm, target)
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges.append({"source": src_norm, "target": target})

    return {"courses": course_nodes, "edges": edges}


@app.get("/api/course/{course_code}")
async def course_lookup(course_code: str):
    clean_code = course_code.upper().strip()
    course_id = clean_code.replace(" ", "")
    try:
        result = index.fetch(ids=[course_id], namespace="courses")
        if result and "vectors" in result and course_id in result["vectors"]:
            metadata = result["vectors"][course_id]["metadata"]
            structured = parse_course_from_metadata(metadata, clean_code)
            return {"found": True, **structured}
        return {"found": False, "message": f"Could not find exact course data for {clean_code}."}
    except Exception as e:
        return {"found": False, "error": str(e)}


@app.post("/api/report")
async def submit_report(
    message: str = Form(...),
    query: str = Form(""),
):
    """Problem reports from the 'Report a Problem' modal (separate from thumbs feedback)."""
    _log("reports.log", {
        "ts": datetime.utcnow().isoformat(),
        "id": str(uuid.uuid4())[:8],
        "query": query[:300],
        "message": message[:1000],
    })
    return {"success": True}


@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(...),
    history: str = Form("[]"),
    session_id: str = Form("none"),
    user_id: str = Form("anonymous"),
    file: UploadFile = File(None),
):
    _current_session.set(session_id)
    user_query = question
    t_start = time.time()

    # Inject last-mentioned course code from history for vague follow-up queries
    if not re.search(r'[A-Z]{3,4}\s*\d{4}', user_query, re.IGNORECASE):
        try:
            _hist = json.loads(history)
            for _msg in reversed(_hist):
                _content = _msg.get("content", "") if isinstance(_msg, dict) else ""
                _found = re.search(r'([A-Z]{3,4}\s*\d{4})', _content, re.IGNORECASE)
                if _found:
                    user_query = f"{user_query} ({_found.group(1)})"
                    break
        except Exception:
            pass

    print(f"Searching database for: {user_query}")

    _TERM_WORDS = {"fall", "fall", "term", "year", "from", "this", "last", "next", "that", "what", "when", "with", "they", "them", "into", "will", "have", "been", "also", "than", "then", "each", "more", "does", "over", "just", "some", "only", "even", "such"}
    course_matches = [(d, n) for d, n in re.findall(r'([a-zA-Z]{4})\s*(\d{4})', user_query, re.IGNORECASE) if d.lower() not in _TERM_WORDS]

    if course_matches and not file:
        responses = []
        sources = []
        structured_courses = []
        not_found_codes = []
        seen_codes = set()

        for match in course_matches:
            clean_code = f"{match[0].upper()} {match[1]}"
            if clean_code in seen_codes:
                continue
            seen_codes.add(clean_code)
            course_id = clean_code.replace(" ", "")
            print(f"Interceptor fetching: {course_id}")

            try:
                result = index.fetch(ids=[course_id], namespace="courses")
                if result and "vectors" in result and course_id in result["vectors"]:
                    metadata = result["vectors"][course_id]["metadata"]
                    structured = parse_course_from_metadata(metadata, clean_code)
                    structured_courses.append(structured)
                    source_url = metadata.get("source", f"{match[0].upper()} Calendar")
                    responses.append(clean_code)
                    sources.append({
                        "doc": source_url,
                        "section": "Direct Database Match",
                        "snippet": "Exact course details retrieved instantly.",
                    })
                else:
                    not_found_codes.append(clean_code)
            except Exception as e:
                print(f"Fetch error for {course_id}: {e}")
                not_found_codes.append(clean_code)

        if structured_courses:
            ms = int((time.time() - t_start) * 1000)
            log_query(
                query=user_query,
                query_type="course_lookup",
                chunks_retrieved=len(structured_courses),
                top_score=None,
                course_codes_found=[c["courseCode"] for c in structured_courses],
                response_ms=ms,
                had_context=True,
                user_id=user_id,
            )
            found_msg = f"Found {len(structured_courses)} course(s) for you."
            if not_found_codes:
                found_msg += f" Note: {', '.join(not_found_codes)} were not found via direct lookup."
            return {"answer": found_msg, "courses": structured_courses, "sources": sources}

        # Log any missed codes before falling through to RAG
        for code in not_found_codes:
            log_course_miss(code, user_query)
        print(f"Interceptor missed all codes {not_found_codes} — falling through to RAG")

    attachment_text = ""
    try:
        if file:
            content = await file.read()
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                attachment_text += page.get_text("text") + "\n"

        search_query = rewrite_query_for_embedding(user_query)
        print(f"Embedding query: {search_query}")

        query_embedding = openai_client.embeddings.create(
            input=search_query,
            model="text-embedding-3-small",
        ).data[0].embedding

        all_matches, query_flags = retrieve_and_rerank(
            index=index,
            user_query=user_query,
            query_embedding=query_embedding,
            intent=classify_intent(user_query),
            course_matches=course_matches,
            openai_client=openai_client,
            chat_model=CHAT_MODEL,
        )
        is_program_query = query_flags.is_program_query

        context_text, sources, chunks_used = build_context_and_citations(
            all_matches, is_program_query, SIMILARITY_THRESHOLD
        )
        context_text = prepend_engineering_attempts_context(context_text, user_query)

        top_score = all_matches[0][0].score if all_matches else None
        print(f"RAG: {chunks_used} chunks passed threshold {SIMILARITY_THRESHOLD}")

        if not context_text and not attachment_text:
            log_no_context(user_query, "rag")
            ms = int((time.time() - t_start) * 1000)
            log_query(
                query=user_query,
                query_type="rag",
                chunks_retrieved=0,
                top_score=top_score,
                course_codes_found=[],
                response_ms=ms,
                had_context=False,
                user_id=user_id,
            )
            return {
                "answer": (
                    "That's outside of what I currently know. "
                    "If you think this should be covered, use the Report a Problem button and we'll add it."
                ),
                "sources": [],
            }

        system_prompt = build_system_prompt(context_text, attachment_text)

        past_messages = json.loads(history)
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in past_messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        api_messages.append({"role": "user", "content": user_query})

        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=api_messages,
            temperature=0.4,
        )

        answer = response.choices[0].message.content
        if not should_emit_citations(answer, chunks_used):
            sources = []

        if file:
            sources.append({
                "url": file.filename,
                "title": file.filename,
                "section": "Student-Uploaded Document",
            })

        ms = int((time.time() - t_start) * 1000)
        log_query(
            query=user_query,
            query_type="rag",
            chunks_retrieved=chunks_used,
            top_score=top_score,
            course_codes_found=[],
            response_ms=ms,
            had_context=True,
            user_id=user_id,
        )
        return {"answer": answer, "sources": sources}

    except Exception as e:
        ms = int((time.time() - t_start) * 1000)
        log_query(
            query=user_query,
            query_type="rag_error",
            chunks_retrieved=0,
            top_score=None,
            course_codes_found=[],
            response_ms=ms,
            had_context=False,
        )
        print(f"Error: {e}")
        return {"answer": "Sorry, CampusQ ran into an error processing your request. Please try again.", "sources": []}


@app.post("/api/chat/stream")
async def chat_stream(
    question: str = Form(...),
    history: str = Form("[]"),
    session_id: str = Form("none"),
    user_id: str = Form("anonymous"),
):
    _current_session.set(session_id)
    user_query = question

    t_start = time.time()

    # If the query has no course code but is a follow-up (e.g. "what semester is this taught?"),
    # inject the last-mentioned course code from history so RAG can find the right data.
    _course_in_query = re.search(r'[A-Z]{3,4}\s*\d{4}', user_query, re.IGNORECASE)
    if not _course_in_query:
        try:
            _hist = json.loads(history)
            for _msg in reversed(_hist):
                _content = _msg.get("content", "") if isinstance(_msg, dict) else ""
                _found = re.search(r'([A-Z]{3,4}\s*\d{4})', _content, re.IGNORECASE)
                if _found:
                    user_query = f"{user_query} ({_found.group(1)})"
                    break
        except Exception:
            pass

    # Patterns that indicate the user wants course details directly (pill cards shown)
    DIRECT_LOOKUP_PATTERNS = re.compile(
        r'^(what is|what\'s|tell me about|describe|show me|info on|information on|details (on|about)|look up|lookup)\s+[a-zA-Z]{4}\s*\d{4}',
        re.IGNORECASE
    )

    async def generate():
        _TERM_WORDS = {"fall", "term", "year", "from", "this", "last", "next", "that", "what", "when", "with", "they", "them", "into", "will", "have", "been", "also", "than", "then", "each", "more", "does", "over", "just", "some", "only", "even", "such"}
        course_matches = [(d, n) for d, n in re.findall(r'([a-zA-Z]{4})\s*(\d{4})', user_query, re.IGNORECASE) if d.lower() not in _TERM_WORDS]

        # Only show pill cards when user is directly asking for course details
        is_direct_lookup = bool(DIRECT_LOOKUP_PATTERNS.match(user_query.strip()))

        structured_courses = []
        if course_matches:
            missed_codes = []
            seen_codes = set()

            for match in course_matches:
                clean_code = f"{match[0].upper()} {match[1]}"
                if clean_code in seen_codes:
                    continue
                seen_codes.add(clean_code)
                course_id = clean_code.replace(" ", "")

                try:
                    result = index.fetch(ids=[course_id], namespace="courses")
                    if result and "vectors" in result and course_id in result["vectors"]:
                        metadata = result["vectors"][course_id]["metadata"]
                        structured = parse_course_from_metadata(metadata, clean_code)
                        structured_courses.append(structured)
                    else:
                        missed_codes.append(clean_code)
                        log_course_miss(clean_code, user_query)
                except Exception as e:
                    print(f"Stream interceptor error: {e}")
                    missed_codes.append(clean_code)

        # Always fall through to RAG/AI

        try:
            search_query = rewrite_query_for_embedding(user_query)
            query_embedding = openai_client.embeddings.create(
                input=search_query,
                model="text-embedding-3-small",
            ).data[0].embedding

            all_matches, query_flags = retrieve_and_rerank(
                index=index,
                user_query=user_query,
                query_embedding=query_embedding,
                intent=classify_intent(user_query),
                course_matches=course_matches,
                openai_client=openai_client,
                chat_model=CHAT_MODEL,
            )
            is_program_query = query_flags.is_program_query
            is_schedule_query = query_flags.is_schedule_query

            context_text, sources_list, chunks_used = build_context_and_citations(
                all_matches, is_program_query, SIMILARITY_THRESHOLD
            )
            context_text = prepend_engineering_attempts_context(context_text, user_query)
            top_score = all_matches[0][0].score if all_matches else None

            # If course cards were fetched, add their data directly to context
            course_citations = []
            if course_matches and structured_courses:
                course_context = "\n--- Course Data (fetched directly) ---\n"
                for c in structured_courses:
                    course_context += f"{c['courseCode']} — {c['courseName']} [{c['credits']} credits]\n"
                    course_context += f"Description: {c['description']}\n"
                    prereqs = c.get('prerequisiteText') or (", ".join(c['prerequisites']) if c['prerequisites'] else "None")
                    course_context += f"Prerequisites: {prereqs}\n\n"
                    course_citations.append(citation_from_course(c))
                context_text = course_context + context_text
                sources_list = finalize_citations(course_citations + sources_list, is_program_query)

            if not context_text:
                log_no_context(user_query, "stream_rag")

            system_prompt = build_system_prompt(context_text)

            past_messages = json.loads(history)
            api_messages = [{"role": "system", "content": system_prompt}]
            for msg in past_messages:
                api_messages.append({"role": msg["role"], "content": msg["content"]})
            api_messages.append({"role": "user", "content": user_query})

            stream = await async_openai_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=api_messages,
                temperature=0.4,
                stream=True,
            )

            full_answer = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_answer += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

            # Emit pill cards only for direct lookups ("what is COMP 1005")
            if structured_courses and is_direct_lookup and not is_schedule_query:
                yield f"data: {json.dumps({'type': 'courses', 'data': structured_courses})}\n\n"

            if sources_list and should_emit_citations(full_answer, chunks_used):
                yield f"data: {json.dumps({'type': 'sources', 'data': sources_list})}\n\n"

            # Log after stream completes
            ms = int((time.time() - t_start) * 1000)
            log_query(
                query=user_query,
                query_type="stream_rag",
                chunks_retrieved=chunks_used,
                top_score=top_score,
                course_codes_found=[],
                response_ms=ms,
                had_context=bool(context_text),
                user_id=user_id,
            )

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            ms = int((time.time() - t_start) * 1000)
            log_query(
                query=user_query,
                query_type="stream_error",
                chunks_retrieved=0,
                top_score=None,
                course_codes_found=[],
                response_ms=ms,
                had_context=False,
            )
            print(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'token', 'content': 'Sorry, CampusQ ran into an error. Please try again.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/feedback")
async def feedback_endpoint(
    rating: str = Form(...),              # "up" | "down"
    question: str = Form(""),
    answer: str = Form(""),
    session_id: str = Form("none"),
):
    if rating not in ("up", "down"):
        return {"ok": False, "error": "rating must be 'up' or 'down'"}
    log_feedback(session_id, question, answer, rating)
    return {"ok": True}


@app.post("/api/waitlist")
async def waitlist_endpoint(
    email: str = Form(...),
    school: str = Form(...),
):
    email = email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        return {"ok": False, "error": "invalid email"}
    _log("waitlist.log", {
        "ts": datetime.utcnow().isoformat(),
        "email": email,
        "school": school,
    })
    return {"ok": True}


# ── Advisor Dashboard (read-only, anonymized — open access) ───────────────────
from dashboard import build_dashboard_data, build_digest_text, build_waitlist_data

@app.get("/api/dashboard")
async def dashboard_data(days: int | None = 7):
    """days=7,14,30,90 or omit for all-time (days=None via ?days=0)"""
    d = None if days == 0 else days
    return {"ok": True, "data": build_dashboard_data(LOG_DIR, days=d)}

@app.get("/api/dashboard/digest")
async def dashboard_digest():
    return {"ok": True, "digest": build_digest_text(LOG_DIR)}

@app.get("/api/dashboard/waitlist")
async def dashboard_waitlist(days: int | None = 30):
    d = None if days == 0 else days
    return {"ok": True, "data": build_waitlist_data(LOG_DIR, days=d)}


# ── Weekly team brief scheduler (in-process, opt-in) ──────────────────────────
# Sends the internal team brief every Monday 8am Eastern, from inside this
# always-on backend so it can read the logs on the persistent /data disk.
# No extra service needed. Arm it with ENABLE_BRIEF_SCHEDULER=true in the env.
def _weekly_brief_job():
    # Dedupe across web workers sharing this instance's filesystem: the first
    # worker to atomically create the week's lock file is the one that sends.
    try:
        week_tag = datetime.utcnow().strftime("%G-W%V")
        lock_path = os.path.join(LOG_DIR, f".brief_sent_{week_tag}")
        try:
            os.close(os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        except FileExistsError:
            return  # already sent this week
        from send_team_brief import send_brief
        send_brief(LOG_DIR, quiet=True)
        print(f"[scheduler] weekly team brief sent ({week_tag})")
    except Exception as exc:
        print(f"[scheduler] weekly team brief failed: {exc}")


def _start_brief_scheduler():
    if os.getenv("ENABLE_BRIEF_SCHEDULER", "").strip().lower() not in ("1", "true", "yes", "on"):
        return
    try:
        import pytz
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        tz = pytz.timezone("America/Toronto")
        scheduler = BackgroundScheduler(daemon=True, timezone=tz)
        scheduler.add_job(
            _weekly_brief_job,
            CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=tz),
            id="weekly_team_brief",
            coalesce=True,
            misfire_grace_time=3600,
        )
        scheduler.start()
        print("[scheduler] weekly team brief armed: Mondays 08:00 America/Toronto")
    except Exception as exc:
        print(f"[scheduler] could not start: {exc}")


_start_brief_scheduler()
