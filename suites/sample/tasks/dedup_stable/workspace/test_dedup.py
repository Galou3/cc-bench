from dedup import dedup


def test_preserves_first_seen_order():
    assert dedup([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert dedup([1, 2, 3]) == [1, 2, 3]


def test_works_with_strings():
    assert dedup(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]


def test_empty_and_singletons():
    assert dedup([]) == []
    assert dedup([42]) == [42]
