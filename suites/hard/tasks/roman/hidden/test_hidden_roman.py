import pytest

from roman import int_to_roman, roman_to_int


def test_subtractive_int_to_roman():
    assert int_to_roman(4) == "IV"
    assert int_to_roman(9) == "IX"
    assert int_to_roman(40) == "XL"
    assert int_to_roman(90) == "XC"
    assert int_to_roman(400) == "CD"
    assert int_to_roman(900) == "CM"


def test_known_values_int_to_roman():
    assert int_to_roman(1) == "I"
    assert int_to_roman(3) == "III"
    assert int_to_roman(58) == "LVIII"
    assert int_to_roman(1994) == "MCMXCIV"
    assert int_to_roman(3888) == "MMMDCCCLXXXVIII"
    assert int_to_roman(3999) == "MMMCMXCIX"


def test_subtractive_roman_to_int():
    assert roman_to_int("IV") == 4
    assert roman_to_int("IX") == 9
    assert roman_to_int("XL") == 40
    assert roman_to_int("XC") == 90
    assert roman_to_int("CD") == 400
    assert roman_to_int("CM") == 900
    assert roman_to_int("MCMXCIV") == 1994


def test_full_round_trip():
    for n in range(1, 4000):
        assert roman_to_int(int_to_roman(n)) == n


def test_invalid_raises():
    for bad in ["IIII", "IC", "", "ABC", "iv", "mcmxciv",
                "VV", "IL", "MMMM", "XM", "VX", "IXX"]:
        with pytest.raises(ValueError):
            roman_to_int(bad)