from version import parse_version


def test_full_version():
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("10.20.30") == (10, 20, 30)


def test_pads_missing_minor_and_patch():
    assert parse_version("1") == (1, 0, 0)
    assert parse_version("2.5") == (2, 5, 0)


def test_returns_ints_not_strings():
    v = parse_version("3.4.5")
    assert all(isinstance(part, int) for part in v)
