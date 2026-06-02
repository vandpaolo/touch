# Unit tests for the content-addressed tessellation cache (ADR-0010).
import pytest

from touch_backend.mesh_cache import MeshCache


def test_key_is_deterministic_and_content_addressed():
    assert MeshCache.key("box()") == MeshCache.key("box()")
    assert MeshCache.key("box()") != MeshCache.key("box() ")


def test_get_miss_returns_none():
    cache = MeshCache()
    assert cache.get(MeshCache.key("box()")) is None


def test_put_then_get_roundtrips():
    cache = MeshCache()
    mesh = object()
    key = MeshCache.key("box()")
    cache.put(key, mesh)
    assert cache.get(key) is mesh


def test_lru_evicts_least_recently_used():
    cache = MeshCache(capacity=2)
    a, b, c = (MeshCache.key(s) for s in ("a", "b", "c"))
    cache.put(a, "A")
    cache.put(b, "B")
    cache.get(a)  # touch a -> b becomes least-recent
    cache.put(c, "C")  # evicts b
    assert cache.get(a) == "A"
    assert cache.get(c) == "C"
    assert cache.get(b) is None
    assert len(cache) == 2


def test_capacity_must_be_positive():
    with pytest.raises(ValueError):
        MeshCache(capacity=0)
