import os
import json
import re
import time
import uuid
import contextvars
from datetime import datetime

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
    if any(k in q for k in ["register", "registration", "add a course", "drop", "override", "waitlist", "time ticket"]):
        return "registration"
    if any(k in q for k in ["required courses", "graduate", "degree", "program", "stream", "concentration", "minor", "credits to"]):
        return "program_requirements"
    if any(k in q for k in ["co-op", "transcript", "financial aid", "bursary", "scholarship", "defer", "enrolment"]):
        return "services"
    if re.search(r'[a-zA-Z]{4}\s*\d{4}', query):
        return "course_lookup"
    return "general"


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


def rewrite_query_for_embedding(user_query: str) -> str:
    if len(user_query) <= 60:
        return user_query
    try:
        rewrite_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
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

    course_matches = re.findall(r'([a-zA-Z]{4})\s*(\d{4})', user_query, re.IGNORECASE)

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

        is_program_query = any(kw in user_query.lower() for kw in [
            "program", "required courses", "year 1", "year 2", "year 3", "year 4",
            "stream", "engineering", "bachelor", "degree requirements", "curriculum",
            "what courses do i need", "courses for my", "courses in the"
        ])

        top_k_programs = 25 if is_program_query else 8
        top_k_other = 5 if is_program_query else 8
        keep_total = 30 if is_program_query else 10

        _q_lower = user_query.lower()
        is_schedule_query = any(kw in _q_lower for kw in [
            "open", "closed", "available", "offered", "offering",
            "section", "crn", "waitlist", "full",
            "who teaches", "who is teaching", "instructor", "professor",
            "when is", "what time", "schedule",
            "what semester", "what term", "which semester", "which term",
            "fall 2026", "winter 2027", "summer 2026",
            "f26", "w27", "su26",
        ])

        all_matches = []
        for ns in ["courses", "programs", "regulations", "registrar", "services", "dates", "tuition", "library", "facts", "schedule"]:
            top_k = top_k_programs if ns == "programs" else top_k_other
            # Pull more schedule results when query is clearly schedule-related
            if ns == "schedule" and is_schedule_query:
                top_k = max(top_k, 15)
            ns_results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=ns,
            )
            if ns_results.matches:
                for m in ns_results.matches:
                    # Boost schedule namespace scores so they surface above course catalog entries
                    if ns == "schedule" and is_schedule_query:
                        m.score = min(1.0, m.score + 0.25)
                all_matches.extend(ns_results.matches)

        all_matches.sort(key=lambda m: m.score, reverse=True)
        all_matches = all_matches[:keep_total]

        context_text = ""
        sources = []
        seen_urls = set()
        chunks_used = 0

        for match in all_matches:
            # For program queries: include all program chunks regardless of score
            # (years 3-4 chunks often score lower but are still needed for full context)
            is_program_chunk = "program" in match.metadata or "section" in match.metadata
            if not is_program_query or not is_program_chunk:
                if match.score < SIMILARITY_THRESHOLD:
                    continue
            metadata = match.metadata
            doc_text = metadata.get("text", "")
            doc_source = metadata.get("source", "Unknown Source")
            context_text += f"\n--- Source: {doc_source} (relevance: {match.score:.2f}) ---\n{doc_text}\n"
            chunks_used += 1
            if doc_source not in seen_urls:
                seen_urls.add(doc_source)
                sources.append({
                    "doc": doc_source,
                    "section": "Carleton Academic Calendar",
                    "snippet": doc_text[:150] + "...",
                })

        top_score = all_matches[0].score if all_matches else None
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

        system_prompt = f"""You are CampusQ, an AI assistant for Carleton University students. You answer questions about courses, programs, prerequisites, regulations, and academic life using the Carleton Academic Calendar.

You are independent — not officially affiliated with Carleton University.

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

CONTEXT:
{context_text if context_text else "No context retrieved."}

STUDENT-UPLOADED DOCUMENT:
{attachment_text if attachment_text else "None."}
"""

        past_messages = json.loads(history)
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in past_messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        api_messages.append({"role": "user", "content": user_query})

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages,
            temperature=0.4,
        )

        if file:
            sources.append({
                "doc": file.filename,
                "section": "Student-Uploaded Document",
                "snippet": "File uploaded directly to this conversation.",
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
        return {"answer": response.choices[0].message.content, "sources": sources}

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

    # Keywords that indicate the user is asking a question *about* courses,
    # not just looking them up. These queries need a full AI answer.
    QUESTION_INDICATORS = [
        "can i", "should i", "do i need", "will i", "is it", "are there",
        "difference between", "compare", "better", "which is", "or ", "without",
        "how ", "why ", "what happens", "explain", "tell me",
        "prerequisite", "require", "needed for", "before taking", "instead of",
        "vs ", "versus", "substitute", "count toward", "count for",
        "transfer", "equivalent", "replace", "satisfy",
        # Schedule/availability questions — need RAG, not course cards
        "who teaches", "who is teaching", "instructor", "professor",
        "open", "closed", "available", "offered", "offering", "waitlist",
        "section", "crn", "what time", "when is", "schedule",
        "what semester", "what term", "which semester", "which term",
        "fall 2026", "winter 2027", "summer 2026",
    ]

    async def generate():
        course_matches = re.findall(r'([a-zA-Z]{4})\s*(\d{4})', user_query, re.IGNORECASE)

        # Determine whether this is a question that mentions courses (needs AI answer)
        # or a pure course lookup (fast card path is sufficient)
        query_lower = user_query.lower()
        is_question_about_courses = any(ind in query_lower for ind in QUESTION_INDICATORS)

        if course_matches:
            structured_courses = []
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

            # Pure lookup (e.g. "What is COMP 1005?") — fast card path, no AI needed
            if structured_courses and not is_question_about_courses:
                ms = int((time.time() - t_start) * 1000)
                log_query(
                    query=user_query,
                    query_type="stream_course",
                    chunks_retrieved=len(structured_courses),
                    top_score=None,
                    course_codes_found=[c["courseCode"] for c in structured_courses],
                    response_ms=ms,
                    had_context=True,
                    user_id=user_id,
                )
                yield f"data: {json.dumps({'type': 'courses', 'data': structured_courses})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            # Question about courses — fall through to RAG, attach cards at end

        try:
            search_query = rewrite_query_for_embedding(user_query)
            query_embedding = openai_client.embeddings.create(
                input=search_query,
                model="text-embedding-3-small",
            ).data[0].embedding

            is_program_query = any(kw in user_query.lower() for kw in [
                "program", "required courses", "year 1", "year 2", "year 3", "year 4",
                "stream", "engineering", "bachelor", "degree requirements", "curriculum",
                "what courses do i need", "courses for my", "courses in the"
            ])

            top_k_programs = 25 if is_program_query else 8
            top_k_other = 5 if is_program_query else 8
            keep_total = 30 if is_program_query else 10

            _q_lower = user_query.lower()
            is_schedule_query = any(kw in _q_lower for kw in [
                "open", "closed", "available", "offered", "offering",
                "section", "crn", "waitlist", "full",
                "who teaches", "who is teaching", "instructor",
                "when is", "what time", "schedule",
                "fall 2026", "winter 2027", "summer 2026",
                "f26", "w27", "su26",
            ])

            all_matches = []
            for ns in ["courses", "programs", "regulations", "registrar", "services", "dates", "tuition", "library", "facts", "schedule"]:
                top_k = top_k_programs if ns == "programs" else top_k_other
                if ns == "schedule" and is_schedule_query:
                    top_k = max(top_k, 15)
                ns_results = index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    namespace=ns,
                )
                if ns_results.matches:
                    for m in ns_results.matches:
                        if ns == "schedule" and is_schedule_query:
                            m.score = min(1.0, m.score + 0.25)
                    all_matches.extend(ns_results.matches)

            all_matches.sort(key=lambda m: m.score, reverse=True)
            all_matches = all_matches[:keep_total]

            context_text = ""
            chunks_used = 0
            top_score = all_matches[0].score if all_matches else None

            for match in all_matches:
                is_program_chunk = "program" in match.metadata or "section" in match.metadata
                if not is_program_query or not is_program_chunk:
                    if match.score < SIMILARITY_THRESHOLD:
                        continue
                metadata = match.metadata
                doc_text = metadata.get("text", "")
                doc_source = metadata.get("source", "Unknown Source")
                context_text += f"\n--- Source: {doc_source} (relevance: {match.score:.2f}) ---\n{doc_text}\n"
                chunks_used += 1

            # If course cards were fetched, add their data directly to context
            if course_matches and structured_courses:
                course_context = "\n--- Course Data (fetched directly) ---\n"
                for c in structured_courses:
                    course_context += f"{c['courseCode']} — {c['courseName']} [{c['credits']} credits]\n"
                    course_context += f"Description: {c['description']}\n"
                    prereqs = ", ".join(c['prerequisites']) if c['prerequisites'] else "None"
                    course_context += f"Prerequisites: {prereqs}\n\n"
                context_text = course_context + context_text

            if not context_text:
                log_no_context(user_query, "stream_rag")

            system_prompt = f"""You are CampusQ, an AI assistant for Carleton University students. You answer questions about courses, programs, prerequisites, regulations, and academic life using the Carleton Academic Calendar.

You are independent — not officially affiliated with Carleton University.

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

CONTEXT:
{context_text if context_text else "No context retrieved."}"""

            past_messages = json.loads(history)
            api_messages = [{"role": "system", "content": system_prompt}]
            for msg in past_messages:
                api_messages.append({"role": msg["role"], "content": msg["content"]})
            api_messages.append({"role": "user", "content": user_query})

            stream = await async_openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                temperature=0.4,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

            # Emit course cards as supplementary (for question-about-courses path)
            # Skip cards for schedule/availability queries — the answer is the schedule data
            if course_matches and structured_courses and is_question_about_courses and not is_schedule_query:
                yield f"data: {json.dumps({'type': 'courses', 'data': structured_courses})}\n\n"

            # Emit sources
            sources_list = []
            seen_urls = set()
            for match in all_matches:
                if match.score < SIMILARITY_THRESHOLD:
                    continue
                url = match.metadata.get("source", "")
                title = (
                    match.metadata.get("title") or
                    match.metadata.get("program") or
                    match.metadata.get("heading") or
                    match.metadata.get("section") or ""
                )
                if url and url not in seen_urls and "Unknown" not in url:
                    seen_urls.add(url)
                    sources_list.append({"url": url, "title": title})

            if sources_list:
                yield f"data: {json.dumps({'type': 'sources', 'data': sources_list[:3]})}\n\n"

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


# ── Advisor Dashboard (read-only, anonymized — open access) ───────────────────
from dashboard import build_dashboard_data, build_digest_text

@app.get("/api/dashboard")
async def dashboard_data(days: int | None = 7):
    """days=7,14,30,90 or omit for all-time (days=None via ?days=0)"""
    d = None if days == 0 else days
    return {"ok": True, "data": build_dashboard_data(LOG_DIR, days=d)}

@app.get("/api/dashboard/digest")
async def dashboard_digest():
    return {"ok": True, "digest": build_digest_text(LOG_DIR)}
