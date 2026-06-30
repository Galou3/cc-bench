from jsonpath import get_path


def test_nested_dicts():
    data = {"a": {"b": {"c": 42}}}
    assert get_path(data, "a.b.c") == 42


def test_bare_key():
    assert get_path({"a": 1}, "a") == 1


def test_list_index_then_key():
    data = {"items": [{"name": "x"}, {"name": "y"}, {"name": "z"}]}
    assert get_path(data, "items[2].name") == "z"


def test_key_then_index():
    assert get_path({"a": [10, 20, 30]}, "a[0]") == 10


def test_nested_mixed():
    data = {"a": {"b": [{"c": 1}, {"c": 2}]}}
    assert get_path(data, "a.b[1].c") == 2


def test_missing_key_returns_default():
    data = {"a": {"b": 1}}
    assert get_path(data, "a.x", default="MISSING") == "MISSING"
    assert get_path(data, "x") is None


def test_index_out_of_range_returns_default():
    assert get_path({"items": [1, 2, 3]}, "items[5]", default=-1) == -1


def test_index_on_dict_returns_default():
    assert get_path({"a": {"x": 1}}, "a[0]", default="D") == "D"


def test_index_on_dict_with_int_key_returns_default():
    # indexing a dict is a type mismatch even if the dict has an int key 0
    assert get_path({"a": {0: "zero"}}, "a[0]", default="D") == "D"


def test_key_on_list_returns_default():
    assert get_path({"items": [1, 2, 3]}, "items.name", default="D") == "D"


def test_key_on_scalar_returns_default():
    assert get_path({"a": 5}, "a.b", default="D") == "D"


def test_default_propagates_through_overlong_path():
    data = {"a": {"b": {"c": 1}}}
    assert get_path(data, "a.b.c.d.e", default="D") == "D"


def test_falsy_value_not_replaced_by_default():
    data = {"a": 0, "b": None, "c": False, "d": ""}
    assert get_path(data, "a", default="D") == 0
    assert get_path(data, "b", default="D") is None
    assert get_path(data, "c", default="D") is False
    assert get_path(data, "d", default="D") == ""
