"""Tests for the query-embedding TTL cache (issue #53)."""
from embedding_cache import EmbeddingCache


class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_hit_avoids_recompute():
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return [0.1, 0.2]

    cache = EmbeddingCache(ttl_s=300)
    assert cache.get_or_compute("k", compute) == [0.1, 0.2]
    assert cache.get_or_compute("k", compute) == [0.1, 0.2]
    assert calls["n"] == 1           # second call served from cache
    assert cache.hits == 1 and cache.misses == 1


def test_distinct_keys_recompute():
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return [float(calls["n"])]

    cache = EmbeddingCache()
    cache.get_or_compute("a", compute)
    cache.get_or_compute("b", compute)
    assert calls["n"] == 2


def test_ttl_expiry_recomputes():
    clock = _Clock()
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return [1.0]

    cache = EmbeddingCache(ttl_s=60, clock=clock)
    cache.get_or_compute("k", compute)
    clock.t += 59
    cache.get_or_compute("k", compute)   # still fresh
    assert calls["n"] == 1
    clock.t += 2                          # now past TTL
    cache.get_or_compute("k", compute)
    assert calls["n"] == 2


def test_lru_eviction_bounds_size():
    cache = EmbeddingCache(max_entries=2)
    cache.get_or_compute("a", lambda: [1.0])
    cache.get_or_compute("b", lambda: [2.0])
    cache.get_or_compute("a", lambda: [1.0])  # touch a → b is now LRU
    cache.get_or_compute("c", lambda: [3.0])  # evicts b
    assert len(cache._store) == 2
    assert "b" not in cache._store
    assert "a" in cache._store and "c" in cache._store


def test_recompute_after_eviction():
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return [float(calls["n"])]

    cache = EmbeddingCache(max_entries=1)
    cache.get_or_compute("a", compute)
    cache.get_or_compute("b", compute)   # evicts a
    cache.get_or_compute("a", compute)   # a must recompute
    assert calls["n"] == 3
