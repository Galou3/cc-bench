_TABLE = [
    (1000, "M"), (500, "D"), (100, "C"), (50, "L"),
    (10, "X"), (5, "V"), (1, "I"),
]

_SYMBOLS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def int_to_roman(n: int) -> str:
    # Naive additive build: misses subtractive notation (4 -> "IIII").
    out = []
    for value, symbol in _TABLE:
        count, n = divmod(n, value)
        out.append(symbol * count)
    return "".join(out)


def roman_to_int(s: str) -> int:
    # Naive parse: no validation, accepts non-canonical/invalid input.
    total = 0
    prev = 0
    for ch in reversed(s):
        val = _SYMBOLS.get(ch, 0)
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total