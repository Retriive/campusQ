"""Retrieval helpers: intent routing, namespace selection, and reranking."""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from collections import Counter

# Intent → namespace score boosts (additive, capped at 1.0)
INTENT_NAMESPACE_BOOSTS: dict[str, dict[str, float]] = {
    "prerequisites": {"courses": 0.20},
    "deadlines": {"dates": 0.25},
    "regulations": {"regulations": 0.22},
    "registration": {"registrar": 0.28, "dates": 0.10},
    "program_requirements": {"programs": 0.22},
    "services": {"services": 0.18, "registrar": 0.08, "library": 0.12},
    "course_lookup": {"courses": 0.18},
    "general": {},
}

LIBRARY_QUERY_KEYWORDS = (
    "library", "macodrum", "study space", "silent study", "study room",
    "loud noise", "noisy", "quiet floor", "silent floor",
)

PROGRAM_SKIP_NS = frozenset({"tuition", "library", "facts", "services"})

PROGRAM_QUERY_KEYWORDS = (
    "program", "required courses", "year 1", "year 2", "year 3", "year 4",
    "stream", "engineering", "bachelor", "degree requirements", "curriculum",
    "what courses do i need", "courses for my", "courses in the",
    "difference between", " vs ", " versus ", "compare", "comparison",
    "software eng", "software engineering", "computer science",
    "which degree", "what's the difference", "what is the difference",
    "honours", "major in", "minor in", "b.cs", "b.eng", "beng", "bcs",
)

SCHEDULE_KEYWORDS = (
    "open", "closed", "available", "offered", "offering",
    "section", "crn", "waitlist", "full",
    "who teaches", "who is teaching", "instructor", "professor", "prof",
    "taught by", "who teach",
    "when is", "what time", "what day", "what days", "which day",
    "schedule", "meets", "meeting",
    "what semester", "what term", "which semester", "which term",
    "fall 2026", "winter 2027", "summer 2026",
    "f26", "w27", "su26",
)

DEADLINE_KEYWORDS = (
    "last day", "deadline", "when is", "when does", "when do", "due date",
    "withdraw", "withdrawal", "add", "drop", "refund", "payment",
    "registration", "exam", "exams", "begin", "start", "end", "term begins",
    "time ticket", "reading week", "break", "holiday", "closed",
)

ACTION_KEYWORDS = (
    "how do i drop", "how to drop", "want to drop", "i want to drop",
    "how do i withdraw", "how to withdraw", "want to withdraw",
    "how do i register", "how to register", "how do i add",
    "how to add a course", "registration override", "how do i appeal",
)

QUERY_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-/\.]{1,}")
COURSE_CODE_RE = re.compile(r"\b([A-Za-z]{3,4})\s*([0-9]{4}[A-Za-z]?)\b")
QUERY_STOPWORDS = frozenset({
    "a", "about", "after", "all", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "between", "by", "can", "could", "did",
    "do", "does", "for", "from", "get", "has", "have", "how", "i", "if", "in",
    "into", "is", "it", "its", "me", "my", "of", "on", "or", "our", "should",
    "so", "that", "the", "their", "them", "there", "these", "they", "this",
    "to", "us", "was", "we", "what", "when", "where", "which", "who", "why",
    "with", "would", "you", "your",
})


@dataclass
class RankedChunk:
    """Mutable scored chunk for sorting / reranking."""
    id: str
    metadata: dict
    score: float
    namespace: str

    @classmethod
    def from_match(cls, match, namespace: str, score: float | None = None) -> RankedChunk:
        return cls(
            id=match.id,
            metadata=match.metadata,
            score=score if score is not None else match.score,
            namespace=namespace,
        )


@dataclass
class QueryFlags:
    is_program_query: bool
    is_schedule_query: bool
    is_deadline_query: bool
    is_action_query: bool
    is_library_query: bool = False


def query_terms(query: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for tok in QUERY_TOKEN_RE.findall(query.lower()):
        if len(tok) < 2 or tok in QUERY_STOPWORDS or tok in seen:
            continue
        seen.add(tok)
        tokens.append(tok)
    return tokens


def query_course_codes(query: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for dept, num in COURSE_CODE_RE.findall(query):
        code = f"{dept.upper()} {num.upper()}"
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def course_code_filter_values(code: str) -> list[str]:
    """Return common metadata forms for an exact course-code filter."""
    normalized = _normalize_space(code.upper())
    compact = normalized.replace(" ", "")
    if compact == normalized:
        return [normalized]
    return [normalized, compact]


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _combined_chunk_text(metadata: dict) -> str:
    parts = [
        metadata.get("title", ""),
        metadata.get("program", ""),
        metadata.get("course_code", ""),
        metadata.get("text", ""),
    ]
    return _normalize_space(" ".join(str(p) for p in parts if p)).lower()


def _lexical_overlap_bonus(tokens: list[str], chunk_text: str) -> float:
    if not tokens or not chunk_text:
        return 0.0
    bounded = tokens[:10]
    hit_count = sum(
        1
        for tok in bounded
        if re.search(rf"\b{re.escape(tok)}\b", chunk_text)
    )
    ratio = hit_count / max(1, len(bounded))
    return min(0.18, ratio * 0.18)


def _course_code_bonus(codes: list[str], chunk_text: str) -> float:
    if not codes or not chunk_text:
        return 0.0
    for code in codes:
        if code in chunk_text.upper():
            return 0.18
    return 0.0


def _chunk_quality_penalty(metadata: dict) -> float:
    text = (metadata.get("text") or "").strip()
    if not text:
        return -0.10
    penalty = 0.0
    if len(text) < 80:
        penalty -= 0.05
    unique_words = {w for w in re.findall(r"[a-zA-Z]{2,}", text.lower())}
    if len(unique_words) < 12:
        penalty -= 0.04
    return penalty


def apply_query_aware_adjustments(
    chunk: RankedChunk,
    *,
    tokens: list[str],
    course_codes: list[str],
    flags: QueryFlags,
) -> float:
    text = _combined_chunk_text(chunk.metadata)
    score = chunk.score
    score += _lexical_overlap_bonus(tokens, text)
    score += _course_code_bonus(course_codes, text)
    score += _chunk_quality_penalty(chunk.metadata)

    if flags.is_deadline_query and any(
        k in text for k in ("deadline", "withdraw", "drop", "add deadline", "last day", "time ticket")
    ):
        score += 0.08
    if flags.is_action_query and any(
        k in text for k in ("carleton central", "registration", "override", "withdrawal", "drop")
    ):
        score += 0.08

    return max(0.0, min(1.0, score))


def chunk_fingerprint(chunk: RankedChunk) -> str:
    source = _normalize_space((chunk.metadata.get("source") or chunk.metadata.get("url") or "").lower())
    title = _normalize_space((chunk.metadata.get("title") or chunk.metadata.get("program") or "").lower())
    snippet = _normalize_space((chunk.metadata.get("text") or "")[:260].lower())
    return f"{chunk.namespace}|{source}|{title}|{snippet}"


def dedupe_chunks(chunks: list[RankedChunk]) -> list[RankedChunk]:
    seen_ids: set[str] = set()
    seen_fingerprints: set[str] = set()
    out: list[RankedChunk] = []
    for chunk in chunks:
        if chunk.id in seen_ids:
            continue
        seen_ids.add(chunk.id)
        fp = chunk_fingerprint(chunk)
        if fp and fp in seen_fingerprints:
            continue
        seen_fingerprints.add(fp)
        out.append(chunk)
    return out


def _namespace_limits(flags: QueryFlags) -> dict[str, int]:
    limits = {
        "courses": 8,
        "programs": 10,
        "regulations": 8,
        "registrar": 8,
        "services": 6,
        "dates": 8,
        "tuition": 4,
        "library": 4,
        "facts": 4,
        "schedule": 8,
    }
    if flags.is_program_query:
        limits["programs"] = 16
    if flags.is_schedule_query:
        limits["schedule"] = 14
    if flags.is_deadline_query:
        limits["dates"] = 14
    if flags.is_action_query:
        limits["registrar"] = 12
    if flags.is_library_query:
        limits["library"] = 12
    return limits


def diverse_pool(chunks: list[RankedChunk], limit: int, flags: QueryFlags) -> list[RankedChunk]:
    if len(chunks) <= limit:
        return chunks

    namespace_limits = _namespace_limits(flags)
    source_cap = 3 if flags.is_program_query else 2
    source_counts: Counter[str] = Counter()
    namespace_counts: Counter[str] = Counter()
    selected: list[RankedChunk] = []
    deferred: list[RankedChunk] = []

    for chunk in chunks:
        source = (
            _normalize_space((chunk.metadata.get("source") or chunk.metadata.get("url") or "").lower())
            or chunk.id
        )
        ns_limit = namespace_limits.get(chunk.namespace, 6)
        if source_counts[source] >= source_cap or namespace_counts[chunk.namespace] >= ns_limit:
            deferred.append(chunk)
            continue
        selected.append(chunk)
        source_counts[source] += 1
        namespace_counts[chunk.namespace] += 1
        if len(selected) >= limit:
            return selected

    for chunk in deferred:
        selected.append(chunk)
        if len(selected) >= limit:
            break
    return selected


def namespace_top_k(ns: str, flags: QueryFlags, token_count: int, has_course_codes: bool) -> int:
    base = 8
    if flags.is_program_query:
        base = 25 if ns == "programs" else 5

    complexity_bonus = 4 if token_count >= 10 else (2 if token_count >= 6 else 0)
    code_bonus = 3 if has_course_codes and ns in ("courses", "schedule") else 0
    top_k = base + complexity_bonus + code_bonus

    if ns == "schedule" and flags.is_schedule_query:
        top_k = max(top_k, 15)
    if ns == "dates" and (flags.is_deadline_query or flags.is_action_query):
        top_k = max(top_k, 15)
    if ns == "registrar" and flags.is_action_query:
        top_k = max(top_k, 12)
    if ns == "library" and flags.is_library_query:
        top_k = max(top_k, 14)
    return min(30, max(4, top_k))


def is_program_related_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in PROGRAM_QUERY_KEYWORDS)


def is_software_eng_vs_cs_comparison(query: str) -> bool:
    q = query.lower()
    has_se = "software eng" in q or "software engineering" in q
    has_cs = (
        "computer science" in q
        or bool(re.search(r"\bcs\b", q))
        or "b.cs" in q
        or "bcs" in q
    )
    return has_se and has_cs


def _program_chunk_label(chunk: RankedChunk) -> str:
    meta = chunk.metadata
    return (meta.get("title") or meta.get("program") or meta.get("text", ""))[:400].lower()


def adjust_se_cs_comparison_score(chunk: RankedChunk) -> float:
    """Boost base B.C.S. + B.Eng SE; demote CS stream chunks for SE vs CS questions."""
    if chunk.namespace != "programs":
        return chunk.score
    label = _program_chunk_label(chunk)
    score = chunk.score
    if "stream" in label and "computer science" in label:
        return max(0.0, score - 0.20)
    if re.search(r"computer science b\.?c\.?s\.? honours \(20", label):
        return min(1.0, score + 0.25)
    if re.search(r"computer science b\.?c\.?s\.? major \(20", label):
        return min(1.0, score + 0.20)
    if "software engineering" in label and (
        "b.eng" in label or "bachelor of engineering" in label or "21.0 credit" in label
    ):
        return min(1.0, score + 0.18)
    return score


def detect_query_flags(query: str) -> QueryFlags:
    q = query.lower()
    return QueryFlags(
        is_program_query=is_program_related_query(query),
        is_schedule_query=any(kw in q for kw in SCHEDULE_KEYWORDS),
        is_deadline_query=any(kw in q for kw in DEADLINE_KEYWORDS),
        is_action_query=any(kw in q for kw in ACTION_KEYWORDS),
        is_library_query=any(kw in q for kw in LIBRARY_QUERY_KEYWORDS),
    )


def namespaces_for_query(flags: QueryFlags) -> list[str]:
    all_ns = [
        "courses", "programs", "regulations", "registrar", "services",
        "dates", "tuition", "library", "facts", "schedule",
    ]
    if flags.is_program_query:
        return [ns for ns in all_ns if ns not in PROGRAM_SKIP_NS]
    return all_ns


def _apply_intent_boost(score: float, namespace: str, intent: str) -> float:
    boost = INTENT_NAMESPACE_BOOSTS.get(intent, {}).get(namespace, 0.0)
    return min(1.0, score + boost)


def _chunk_text(match_metadata: dict, max_len: int = 2000) -> str:
    return (match_metadata.get("text") or "")[:max_len]


def _boosted_namespace_score(base_score: float, namespace: str, flags: QueryFlags, intent: str) -> float:
    score = base_score
    if flags.is_schedule_query and namespace == "schedule":
        score = min(1.0, score + 0.25)
    if flags.is_deadline_query and namespace == "dates":
        score = min(1.0, score + 0.25)
    if flags.is_action_query and namespace in ("registrar", "dates"):
        score = min(1.0, score + 0.20)
    if flags.is_library_query and namespace == "library":
        score = min(1.0, score + 0.28)
    return _apply_intent_boost(score, namespace, intent)


def _rerank_preview(chunk: RankedChunk, max_len: int = 350) -> str:
    meta = chunk.metadata
    labels = [
        str(meta.get("course_code") or "").strip(),
        str(meta.get("course_name") or "").strip(),
        str(meta.get("program") or "").strip(),
        str(meta.get("title") or "").strip(),
        str(meta.get("section") or "").strip(),
        str(meta.get("term") or "").strip(),
        str(meta.get("category") or "").strip(),
    ]
    label = " | ".join(part for part in labels if part)[:220]
    body = _chunk_text(meta, max_len).replace("\n", " ").strip()
    if not body:
        body = _combined_chunk_text(meta)[:max_len]
    if label and body:
        return f"{label} :: {body}"
    return label or body


def rerank_with_cohere(query: str, chunks: list[RankedChunk], top_n: int) -> list[RankedChunk] | None:
    api_key = os.getenv("COHERE_API_KEY", "").strip()
    if not api_key or len(chunks) <= top_n:
        return None
    try:
        import cohere
    except ImportError:
        return None

    try:
        client = cohere.Client(api_key=api_key)
        documents = [_chunk_text(c.metadata) for c in chunks]
        response = client.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=documents,
            top_n=min(top_n, len(chunks)),
        )
        out: list[RankedChunk] = []
        for item in response.results:
            src = chunks[item.index]
            out.append(RankedChunk(
                id=src.id,
                metadata=src.metadata,
                namespace=src.namespace,
                score=float(item.relevance_score),
            ))
        return out
    except Exception as exc:
        print(f"Cohere rerank failed, falling back to LLM: {exc}")
        return None


def rerank_with_llm(
    openai_client,
    query: str,
    chunks: list[RankedChunk],
    top_n: int,
    model: str,
) -> list[RankedChunk]:
    if len(chunks) <= top_n:
        return chunks

    lines = []
    for i, chunk in enumerate(chunks[:30]):
        preview = _rerank_preview(chunk)
        lines.append(f"[{i}] ({chunk.namespace}, score={chunk.score:.2f}) {preview}")

    prompt = f"""You are a retrieval reranker for Carleton University academic Q&A.

User question: {query}

Below are numbered text chunks retrieved from Pinecone. Pick the {top_n} chunks most useful for answering the question accurately. Prefer chunks that directly answer the question; avoid fee schedules or unrelated pages when the question is about programs, registration, or regulations.

Chunks:
{chr(10).join(lines)}

Return JSON only: {{"indices": [<int>, ...]}} with up to {top_n} indices in relevance order."""

    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        indices = json.loads(response.choices[0].message.content).get("indices", [])
        out: list[RankedChunk] = []
        seen: set[int] = set()
        for idx in indices:
            if not isinstance(idx, int) or idx < 0 or idx >= len(chunks) or idx in seen:
                continue
            seen.add(idx)
            out.append(chunks[idx])
            if len(out) >= top_n:
                break
        if out:
            return out
    except Exception as exc:
        print(f"LLM rerank failed, using vector scores: {exc}")

    return chunks[:top_n]


# LLM rerank is a second GPT round-trip (~1–2s). Default off — Cohere when
# configured, otherwise keep vector-ranked pool order. Flip ALLOW_LLM_RERANK
# if you need the slower fallback.
_ALLOW_LLM_RERANK = os.getenv("ALLOW_LLM_RERANK", "").strip().lower() in ("1", "true", "yes", "on")

# Soft cap so a burst of namespace/exact queries cannot spawn unbounded threads.
_RETRIEVAL_MAX_WORKERS = max(2, min(12, int(os.getenv("RETRIEVAL_MAX_WORKERS", "8"))))


def rerank_chunks(
    openai_client,
    query: str,
    chunks: list[RankedChunk],
    top_n: int,
    chat_model: str,
) -> list[RankedChunk]:
    if len(chunks) <= top_n:
        return chunks
    # Already strongly ordered by score — skip network rerank when the head is clear.
    if chunks[0].score >= 0.82 and (chunks[0].score - chunks[min(top_n, len(chunks) - 1)].score) >= 0.12:
        print(f"Rerank: skipped (strong top scores) → {top_n} chunks")
        return chunks[:top_n]
    cohere_result = rerank_with_cohere(query, chunks, top_n)
    if cohere_result:
        print(f"Rerank: Cohere → {len(cohere_result)} chunks")
        return cohere_result
    if _ALLOW_LLM_RERANK:
        llm_result = rerank_with_llm(openai_client, query, chunks, top_n, chat_model)
        print(f"Rerank: LLM fallback → {len(llm_result)} chunks")
        return llm_result
    print(f"Rerank: vector scores (LLM fallback off) → {top_n} chunks")
    return chunks[:top_n]


def _shape_match_chunk(
    match,
    ns: str,
    score: float,
    *,
    user_query: str,
    tokens: list[str],
    course_codes: list[str],
    flags: QueryFlags,
) -> RankedChunk:
    chunk = RankedChunk.from_match(match, ns, score)
    if is_software_eng_vs_cs_comparison(user_query):
        chunk = RankedChunk(
            id=chunk.id,
            metadata=chunk.metadata,
            namespace=chunk.namespace,
            score=adjust_se_cs_comparison_score(chunk),
        )
    return RankedChunk(
        id=chunk.id,
        metadata=chunk.metadata,
        namespace=chunk.namespace,
        score=apply_query_aware_adjustments(
            chunk,
            tokens=tokens,
            course_codes=course_codes,
            flags=flags,
        ),
    )


def retrieve_and_rerank(
    *,
    index,
    user_query: str,
    query_embedding: list[float],
    intent: str,
    course_matches: list[tuple],
    openai_client,
    chat_model: str,
    retrieve_top_k: int = 30,
    rerank_top_n: int = 10,
) -> tuple[list[tuple], QueryFlags]:
    """
    Pinecone multi-namespace retrieval → intent boosts → rerank → (RankedChunk, ns) tuples.
    """
    flags = detect_query_flags(user_query)
    tokens = query_terms(user_query)
    course_codes = query_course_codes(user_query)

    chunks: list[RankedChunk] = []
    namespaces = namespaces_for_query(flags)

    def _query_namespace(ns: str):
        top_k = namespace_top_k(
            ns, flags, token_count=len(tokens), has_course_codes=bool(course_codes)
        )
        return ns, index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=ns,
        )

    # Parallelize independent namespace RTTs — biggest TTFT win on shared hosting.
    with ThreadPoolExecutor(max_workers=min(_RETRIEVAL_MAX_WORKERS, max(1, len(namespaces)))) as pool:
        futures = [pool.submit(_query_namespace, ns) for ns in namespaces]
        for fut in as_completed(futures):
            try:
                ns, ns_results = fut.result()
            except Exception as exc:
                print(f"Namespace query failed: {exc}")
                continue
            for m in ns_results.matches or []:
                score = _boosted_namespace_score(m.score, ns, flags, intent)
                chunks.append(
                    _shape_match_chunk(
                        m,
                        ns,
                        score,
                        user_query=user_query,
                        tokens=tokens,
                        course_codes=course_codes,
                        flags=flags,
                    )
                )

    # Exact-code metadata fetch to recover recall when vector search misses
    # explicit course lookups or schedule questions.
    if course_codes:
        existing_ids = {c.id for c in chunks}
        exact_namespaces = ["courses"]
        if flags.is_schedule_query:
            exact_namespaces.append("schedule")

        exact_jobs: list[tuple[str, str, str]] = []
        for code in course_codes:
            for filter_code in course_code_filter_values(code):
                for ns in exact_namespaces:
                    exact_jobs.append((code, filter_code, ns))

        def _exact_query(job: tuple[str, str, str]):
            _code, filter_code, ns = job
            return job, index.query(
                vector=query_embedding,
                top_k=12 if ns == "schedule" else 8,
                include_metadata=True,
                namespace=ns,
                filter={"course_code": {"$eq": filter_code}},
            )

        with ThreadPoolExecutor(max_workers=min(_RETRIEVAL_MAX_WORKERS, max(1, len(exact_jobs)))) as pool:
            futures = [pool.submit(_exact_query, job) for job in exact_jobs]
            for fut in as_completed(futures):
                try:
                    (_code, filter_code, ns), exact_results = fut.result()
                except Exception as exc:
                    print(f"Exact code filter error: {exc}")
                    continue
                for m in exact_results.matches or []:
                    if m.id in existing_ids:
                        continue
                    base_floor = 0.90 if ns == "schedule" else 0.88
                    boosted = _boosted_namespace_score(max(m.score, base_floor), ns, flags, intent)
                    chunks.append(
                        _shape_match_chunk(
                            m,
                            ns,
                            boosted,
                            user_query=user_query,
                            tokens=tokens,
                            course_codes=course_codes,
                            flags=flags,
                        )
                    )
                    existing_ids.add(m.id)

    # Metadata-filtered schedule fetch by course code (parallel when multi-course)
    if flags.is_schedule_query and course_matches:
        existing_ids = {c.id for c in chunks}
        sched_codes = [f"{dept.upper()} {num}" for dept, num in course_matches]

        def _sched_query(code: str):
            return code, index.query(
                vector=query_embedding,
                top_k=10,
                include_metadata=True,
                namespace="schedule",
                filter={"course_code": {"$eq": code}},
            )

        with ThreadPoolExecutor(max_workers=min(_RETRIEVAL_MAX_WORKERS, max(1, len(sched_codes)))) as pool:
            futures = [pool.submit(_sched_query, code) for code in sched_codes]
            for fut in as_completed(futures):
                try:
                    _code, sched = fut.result()
                except Exception as exc:
                    print(f"Schedule filter error: {exc}")
                    continue
                for m in sched.matches or []:
                    if m.id in existing_ids:
                        continue
                    chunks.append(
                        _shape_match_chunk(
                            m,
                            "schedule",
                            max(m.score, 0.85),
                            user_query=user_query,
                            tokens=tokens,
                            course_codes=course_codes,
                            flags=flags,
                        )
                    )
                    existing_ids.add(m.id)

    chunks = dedupe_chunks(chunks)

    # Optional hybrid fusion: BM25 keyword hits (exact codes, acronyms, form
    # names) merged in via RRF, which also sets the pool order. Any failure
    # degrades to pure vector search — chat never breaks because of this.
    if os.getenv("HYBRID_SEARCH", "").strip().lower() in ("1", "true", "yes", "on"):
        try:
            from search.hybrid import fuse
            from search.lexical import LexicalIndex

            lexical_hits = LexicalIndex().search(
                user_query, namespaces=namespaces_for_query(flags), limit=15)
            if lexical_hits:
                chunks = fuse(
                    chunks, lexical_hits,
                    make_chunk=lambda cid, meta, ns, score: RankedChunk(
                        id=cid, metadata=meta, namespace=ns, score=score),
                )
                print(f"Hybrid: fused {len(lexical_hits)} lexical hits into pool")
        except Exception as exc:
            print(f"Hybrid search unavailable, vector-only: {exc}")
    chunks = dedupe_chunks(chunks)
    chunks.sort(key=lambda c: c.score, reverse=True)
    pool = diverse_pool(chunks, limit=retrieve_top_k, flags=flags)
    ranked = rerank_chunks(openai_client, user_query, pool, rerank_top_n, chat_model)

    return [(c, c.namespace) for c in ranked], flags
