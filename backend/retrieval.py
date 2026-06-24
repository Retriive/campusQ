"""Retrieval helpers: intent routing, namespace selection, and reranking."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

# Intent → namespace score boosts (additive, capped at 1.0)
INTENT_NAMESPACE_BOOSTS: dict[str, dict[str, float]] = {
    "prerequisites": {"courses": 0.20},
    "deadlines": {"dates": 0.25},
    "regulations": {"regulations": 0.22},
    "registration": {"registrar": 0.28, "dates": 0.10},
    "program_requirements": {"programs": 0.22},
    "services": {"services": 0.18, "registrar": 0.08},
    "course_lookup": {"courses": 0.18},
    "general": {},
}

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


def is_program_related_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in PROGRAM_QUERY_KEYWORDS)


def detect_query_flags(query: str) -> QueryFlags:
    q = query.lower()
    return QueryFlags(
        is_program_query=is_program_related_query(query),
        is_schedule_query=any(kw in q for kw in SCHEDULE_KEYWORDS),
        is_deadline_query=any(kw in q for kw in DEADLINE_KEYWORDS),
        is_action_query=any(kw in q for kw in ACTION_KEYWORDS),
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
        preview = _chunk_text(chunk.metadata, 350).replace("\n", " ")
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


def rerank_chunks(
    openai_client,
    query: str,
    chunks: list[RankedChunk],
    top_n: int,
    chat_model: str,
) -> list[RankedChunk]:
    if len(chunks) <= top_n:
        return chunks
    cohere_result = rerank_with_cohere(query, chunks, top_n)
    if cohere_result:
        print(f"Rerank: Cohere → {len(cohere_result)} chunks")
        return cohere_result
    llm_result = rerank_with_llm(openai_client, query, chunks, top_n, chat_model)
    print(f"Rerank: LLM fallback → {len(llm_result)} chunks")
    return llm_result


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

    top_k_programs = 25 if flags.is_program_query else 8
    top_k_other = 5 if flags.is_program_query else 8

    chunks: list[RankedChunk] = []

    for ns in namespaces_for_query(flags):
        top_k = top_k_programs if ns == "programs" else top_k_other
        if ns == "schedule" and flags.is_schedule_query:
            top_k = max(top_k, 15)
        if ns == "dates" and (flags.is_deadline_query or flags.is_action_query):
            top_k = max(top_k, 15)
        if ns == "registrar" and flags.is_action_query:
            top_k = max(top_k, 12)

        ns_results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=ns,
        )
        for m in ns_results.matches or []:
            score = m.score
            if flags.is_schedule_query and ns == "schedule":
                score = min(1.0, score + 0.25)
            if flags.is_deadline_query and ns == "dates":
                score = min(1.0, score + 0.25)
            if flags.is_action_query and ns in ("registrar", "dates"):
                score = min(1.0, score + 0.20)
            score = _apply_intent_boost(score, ns, intent)
            chunks.append(RankedChunk.from_match(m, ns, score))

    # Metadata-filtered schedule fetch by course code
    if flags.is_schedule_query and course_matches:
        existing_ids = {c.id for c in chunks}
        for dept, num in course_matches:
            code = f"{dept.upper()} {num}"
            try:
                sched = index.query(
                    vector=query_embedding,
                    top_k=10,
                    include_metadata=True,
                    namespace="schedule",
                    filter={"course_code": {"$eq": code}},
                )
                for m in sched.matches or []:
                    if m.id not in existing_ids:
                        chunks.append(RankedChunk.from_match(m, "schedule", max(m.score, 0.85)))
                        existing_ids.add(m.id)
            except Exception as exc:
                print(f"Schedule filter error: {exc}")

    chunks.sort(key=lambda c: c.score, reverse=True)
    pool = chunks[:retrieve_top_k]
    ranked = rerank_chunks(openai_client, user_query, pool, rerank_top_n, chat_model)

    return [(c, c.namespace) for c in ranked], flags
