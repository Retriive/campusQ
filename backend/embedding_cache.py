"""Bounded TTL cache for query embeddings (issue #53).

Embedding the same query text calls OpenAI every request; popular/repeated
queries — and retries of the same question — recompute an identical vector.
This caches vectors by exact (model, text) key for a short TTL, with LRU
eviction and a hard size bound so memory stays predictable.

Kept free of the OpenAI client on purpose: callers pass a `compute` callable,
which makes the cache deterministic and unit-testable without network or keys.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Callable


class EmbeddingCache:
    def __init__(self, ttl_s: float = 300.0, max_entries: int = 512, clock: Callable[[], float] = time.time):
        self._ttl = ttl_s
        self._max = max_entries
        self._clock = clock
        self._store: "OrderedDict[str, tuple[float, list[float]]]" = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get_or_compute(self, key: str, compute: Callable[[], list[float]]) -> list[float]:
        now = self._clock()
        with self._lock:
            entry = self._store.get(key)
            if entry is not None and now - entry[0] < self._ttl:
                self._store.move_to_end(key)
                self.hits += 1
                return entry[1]
            # Expired entry is stale — drop it so we don't serve it below.
            if entry is not None:
                del self._store[key]

        # Compute outside the lock: embedding is a slow network call and must
        # not serialize all cache users behind one request.
        self.misses += 1
        vector = compute()

        with self._lock:
            self._store[key] = (now, vector)
            self._store.move_to_end(key)
            while len(self._store) > self._max:
                self._store.popitem(last=False)  # evict least-recently-used
        return vector

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
