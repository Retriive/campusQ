"""BM25 "fit" filter — prune a fetched page down to the blocks that are
actually about the category before extraction and embedding.

Borrowed from Crawl4AI's BM25ContentFilter idea, adapted to CampusQ: instead of
scoring blocks against a live user query, we score them against a fixed per-
category "topic query" (what that Pinecone namespace is about). Navigation
residue, cross-sell boxes, and contact-info footers that survived html_to_text
score near zero and get dropped, so the LLM extractors see less noise and burn
fewer tokens, and the vectors we embed carry less boilerplate.

Deliberately conservative — it never returns an empty page, and when the topic
query finds no purchase at all (score signal is flat) it returns the text
unchanged rather than guess. It is NOT applied to the structure-sensitive
course_regex fast path, whose parser depends on exact line layout.

Pure-Python Okapi BM25; no new dependency.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

# Topic seeds per category — the vocabulary a relevant block is expected to use.
# Kept short and high-signal; BM25's idf handles the weighting. A source can
# override with its own query (Source.fit_query) for oddly-shaped pages.
DEFAULT_QUERIES: dict[str, str] = {
    "dates": "deadline date registration withdrawal exam payment tuition term add drop classes holiday",
    "registrar": "registration enrol enrolment deadline transcript record add drop swap course",
    "programs": "program degree requirement major minor honours stream concentration credit course year",
    "regulations": "regulation policy academic standing petition appeal probation requirement graduation",
    "library": "library hours study room borrowing loan services access research reserves computers",
    "tuition": "tuition fee cost payment refund installment deposit charge deadline",
    "services": "service support student health counselling advising help centre office",
    "campus": "campus building location parking transit food residence map hours",
    "facts": "student enrolment founded ranking faculty campus fact history",
}

# Minimal stopword set — dropping these sharpens BM25 relevance without a full
# NLP dependency. Everything else (including domain terms) is kept.
_STOPWORDS = frozenset(
    "the a an and or of to in for on at by is are be as with from this that "
    "it its into your you we our their they them will can may not no if".split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# BM25 tuning — the standard Okapi defaults.
_K1 = 1.5
_B = 0.75


def tokenize(text: str) -> list[str]:
    """Lowercase alnum tokens, minus stopwords and single characters. Shared
    with the saturation tracker so both see the same notion of a 'term'."""
    return [t for t in _TOKEN_RE.findall(text.lower())
            if len(t) > 1 and t not in _STOPWORDS]


def query_for(category: str, override: str = "") -> str:
    """Topic query for a category — the source override wins, else the default,
    else the category name itself (better than nothing for unknown namespaces)."""
    if override.strip():
        return override
    return DEFAULT_QUERIES.get(category, category)


@dataclass
class FitResult:
    text: str            # kept text (may equal the input)
    blocks_kept: int
    blocks_total: int
    chars_before: int
    chars_after: int

    @property
    def reduced(self) -> bool:
        return self.chars_after < self.chars_before

    @property
    def pct_removed(self) -> int:
        if not self.chars_before:
            return 0
        return round(100 * (self.chars_before - self.chars_after) / self.chars_before)


def _split_blocks(text: str) -> list[str]:
    """html_to_text / pdf_to_text separate logical sections with blank lines, so
    a blank-line split is our block boundary."""
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def fit_text(text: str, query: str, *, threshold: float = 0.30,
             min_blocks: int = 4) -> FitResult:
    """Keep the blocks whose BM25 score against `query` clears `threshold`
    (fraction of the top block's score); drop the rest, preserving order.

    Safeguards, in priority order:
      - Pages with fewer than `min_blocks` blocks are left untouched (nothing to
        gain, and short pages are easy to over-prune).
      - If no block matches the query at all, the text is returned unchanged —
        a flat score signal means we can't tell signal from noise.
      - The single highest-scoring block is always kept, so the result is never
        empty even at a high threshold.
    """
    chars_before = len(text)
    blocks = _split_blocks(text)
    if len(blocks) < min_blocks:
        return FitResult(text, len(blocks), len(blocks), chars_before, chars_before)

    q_terms = set(tokenize(query))
    tokenized = [tokenize(b) for b in blocks]
    scores = _bm25_scores(q_terms, tokenized)

    top = max(scores)
    if top <= 0.0:
        # No query term occurs anywhere — don't guess, keep the page as-is.
        return FitResult(text, len(blocks), len(blocks), chars_before, chars_before)

    cutoff = threshold * top
    best = max(range(len(scores)), key=lambda i: scores[i])
    kept = [blocks[i] for i, s in enumerate(scores) if s >= cutoff or i == best]

    fitted = "\n\n".join(kept)
    return FitResult(fitted, len(kept), len(blocks), chars_before, len(fitted))


def _bm25_scores(q_terms: set[str], docs: list[list[str]]) -> list[float]:
    """Okapi BM25 score of each doc (block) against the query term set."""
    n = len(docs)
    lengths = [len(d) for d in docs]
    avgdl = (sum(lengths) / n) if n else 0.0

    # Document frequency of each query term across blocks.
    df: dict[str, int] = {}
    for term in q_terms:
        df[term] = sum(1 for d in docs if term in d)

    idf: dict[str, float] = {}
    for term, n_q in df.items():
        # BM25 idf with the +1 smoothing that keeps it non-negative.
        idf[term] = math.log(1 + (n - n_q + 0.5) / (n_q + 0.5))

    scores: list[float] = []
    for d, dl in zip(docs, lengths):
        if not dl:
            scores.append(0.0)
            continue
        counts: dict[str, int] = {}
        for tok in d:
            if tok in q_terms:
                counts[tok] = counts.get(tok, 0) + 1
        s = 0.0
        norm = _K1 * (1 - _B + _B * dl / avgdl) if avgdl else _K1
        for term, tf in counts.items():
            s += idf[term] * (tf * (_K1 + 1)) / (tf + norm)
        scores.append(s)
    return scores
