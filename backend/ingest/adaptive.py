"""Saturation-based adaptive crawling — stop following links once the crawl
stops learning anything new.

Borrowed from Crawl4AI's AdaptiveCrawler, whose "information foraging" logic
tracks diminishing returns and halts when new-term discovery flattens. We use
just that saturation signal (no embeddings, no LLM): as each linked page is
fetched, measure what fraction of its terms are new to the running vocabulary.
When several pages in a row add almost nothing, the section is saturated and
crawling the rest of the candidate links is wasted requests.

This is opt-in per source (Source.adaptive). It's meant for discovery — pointing
the crawler at a new school's site where nobody has hand-listed how many pages
are worth reading. It is NOT for exhaustive fan-outs like Carleton's course
catalog, where every department page carries genuinely new courses and you want
all of them; those sources leave adaptive off and fetch up to max_pages.
"""

from __future__ import annotations

from .fit import tokenize


class SaturationTracker:
    """Feed it each page's text in crawl order; ask should_stop() after each.

    Stops once, after a warmup of `min_pages`, `patience` consecutive pages have
    each contributed a new-term fraction below `novelty_threshold`. Pages too
    thin to judge (< `min_page_tokens` terms) are ignored entirely — they
    neither advance the warmup nor count toward the low-novelty streak, so a
    stray empty page can't trip an early stop on its own.
    """

    def __init__(self, *, min_pages: int = 5, patience: int = 3,
                 novelty_threshold: float = 0.05, min_page_tokens: int = 20):
        self.min_pages = min_pages
        self.patience = patience
        self.novelty_threshold = novelty_threshold
        self.min_page_tokens = min_page_tokens
        self.vocab: set[str] = set()
        self.pages_seen = 0
        self._low_streak = 0

    def observe(self, text: str) -> float:
        """Record a page; return its novelty (fraction of terms new to the
        running vocabulary). A thin page returns 1.0 and is not counted."""
        terms = set(tokenize(text))
        if len(terms) < self.min_page_tokens:
            return 1.0

        new = terms - self.vocab
        novelty = len(new) / len(terms)
        self.vocab |= terms
        self.pages_seen += 1

        if novelty < self.novelty_threshold:
            self._low_streak += 1
        else:
            self._low_streak = 0
        return novelty

    def should_stop(self) -> bool:
        return self.pages_seen >= self.min_pages and self._low_streak >= self.patience
