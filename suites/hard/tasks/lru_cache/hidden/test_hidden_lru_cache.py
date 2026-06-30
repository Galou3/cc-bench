import pytest

from lru import LRUCache


def test_get_absent_returns_minus_one():
    c = LRUCache(2)
    assert c.get("nope") == -1


def test_basic_put_get():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    assert c.get("b") == 2


def test_eviction_order_basic():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts "a" (least recently used)
    assert c.get("a") == -1
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1  # "a" now most recently used
    c.put("c", 3)           # should evict "b", not "a"
    assert c.get("b") == -1
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_update_existing_key_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # update existing -> "a" most recent, new value
    c.put("c", 3)   # should evict "b", not "a"
    assert c.get("b") == -1
    assert c.get("a") == 10
    assert c.get("c") == 3


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    assert c.get("a") == 1
    c.put("b", 2)   # evicts "a"
    assert c.get("a") == -1
    assert c.get("b") == 2


def test_capacity_one_update():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("a", 2)   # update, no eviction
    assert c.get("a") == 2


def test_invalid_capacity_raises():
    with pytest.raises(ValueError):
        LRUCache(0)
    with pytest.raises(ValueError):
        LRUCache(-3)


def test_longer_sequence_eviction():
    c = LRUCache(3)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)
    assert c.get(1) == 1     # order now: 2,3,1
    c.put(4, 4)              # evicts 2
    assert c.get(2) == -1
    assert c.get(3) == 3     # order now: 1,4,3
    c.put(5, 5)              # evicts 1
    assert c.get(1) == -1
    assert c.get(4) == 4
    assert c.get(5) == 5
