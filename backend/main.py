import os
import json
import re
import time
import uuid
from datetime import datetime
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

LOG_DIR = os.path.dirname(os.path.abspath(__file__))

def _log(filename: str, data: dict):
    """Append a JSON line to a log file. Thread-safe for single-process use."""
    path = os.path.join(LOG_DIR, filename)
    line = json.dumps(data, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)

def log_query(
    query: str,
    query_type: str,          # "course_lookup" | "rag" | "stream_course" | "stream_rag"
    chunks_retrieved: int,
    top_score: float | None,
    course_codes_found: list[str],
    response_ms: int,
    had_context: bool,
    user_id: str = "anonymous",
):
    _log("queries.log", {
        "ts": datetime.utcnow().isoformat(),
        "id": str(uuid.uuid4())[:8],
        "user": user_id,
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


@app.post("/api/feedback")
async def submit_feedback(
    message: str = Form(...),
    query: str = Form(""),
):
    _log("feedback.log", {
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
    file: UploadFile = File(None),
):
    user_query = question
    t_start = time.time()
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

        all_matches = []
        for ns in ["courses", "programs", "regulations", "registrar", "services"]:
            top_k = top_k_programs if ns == "programs" else top_k_other
            ns_results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=ns,
            )
            if ns_results.matches:
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
            )
            return {
                "answer": (
                    "I don't have enough information in my knowledge base to answer that confidently. "
                    "For the most accurate information, please check calendar.carleton.ca or contact your academic advisor."
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
6. If the context doesn't have the answer, say: "I don't have that in my database — check calendar.carleton.ca or speak with your academic advisor."
7. Be concise. No walls of text. No unnecessary caveats.
8. Only mention calendar.carleton.ca when you genuinely can't answer — not as a reflex.

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
):
    user_query = question

    t_start = time.time()

    async def generate():
        course_matches = re.findall(r'([a-zA-Z]{4})\s*(\d{4})', user_query, re.IGNORECASE)

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

            if structured_courses:
                ms = int((time.time() - t_start) * 1000)
                log_query(
                    query=user_query,
                    query_type="stream_course",
                    chunks_retrieved=len(structured_courses),
                    top_score=None,
                    course_codes_found=[c["courseCode"] for c in structured_courses],
                    response_ms=ms,
                    had_context=True,
                )
                count = len(structured_courses)
                text = f"Here {'are' if count > 1 else 'is'} the {'courses' if count > 1 else 'course'} you asked about."
                yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"
                yield f"data: {json.dumps({'type': 'courses', 'data': structured_courses})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

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

            all_matches = []
            for ns in ["courses", "programs", "regulations", "registrar", "services"]:
                top_k = top_k_programs if ns == "programs" else top_k_other
                ns_results = index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    namespace=ns,
                )
                if ns_results.matches:
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
6. If the context doesn't have the answer, say: "I don't have that in my database — check calendar.carleton.ca or speak with your academic advisor."
7. Be concise. No walls of text. No unnecessary caveats.
8. Only mention calendar.carleton.ca when you genuinely can't answer — not as a reflex.

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
