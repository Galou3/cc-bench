from intervals import merge_intervals


def test_empty():
    assert merge_intervals([]) == []


def test_single():
    assert merge_intervals([[3, 7]]) == [[3, 7]]


def test_touching_merges():
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]


def test_chain_of_touching():
    assert merge_intervals([[1, 2], [2, 3], [3, 4]]) == [[1, 4]]


def test_fully_nested():
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]


def test_nested_unsorted():
    assert merge_intervals([[2, 3], [1, 10], [4, 5]]) == [[1, 10]]


def test_unsorted_input():
    assert merge_intervals([[8, 10], [1, 3], [2, 6], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]


def test_duplicates():
    assert merge_intervals([[1, 4], [1, 4], [1, 4]]) == [[1, 4]]


def test_disjoint_kept_separate():
    assert merge_intervals([[1, 2], [4, 5]]) == [[1, 2], [4, 5]]


def test_negative_values():
    assert merge_intervals([[-5, -2], [-3, 0], [5, 6]]) == [[-5, 0], [5, 6]]


def test_zero_width_touching():
    assert merge_intervals([[1, 1], [1, 3]]) == [[1, 3]]


def test_input_not_mutated():
    data = [[1, 2], [2, 3]]
    snapshot = [list(x) for x in data]
    merge_intervals(data)
    assert data == snapshot
