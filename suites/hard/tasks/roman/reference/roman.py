_VALUES = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]

_SYMBOLS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def int_to_roman(n: int) -> str:
    if isinstance(n, bool) or not isinstance(n, int) or not (1 <= n <= 3999):
        raise ValueError(f"out of range: {n!r}")
    out = []
    for value, symbol in _VALUES:
        count, n = divmod(n, value)
        out.append(symbol * count)
    return "".join(out)


def roman_to_int(s: str) -> int:
    if not isinstance(s, str) or s == "":
        raise ValueError("empty or non-string")
    if any(ch not in _SYMBOLS for ch in s):
        raise ValueError(f"invalid characters: {s!r}")
    total = 0
    prev = 0
    for ch in reversed(s):
        val = _SYMBOLS[ch]
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    if not (1 <= total <= 3999) or int_to_roman(total) != s:
        raise ValueError(f"not a canonical roman numeral: {s!r}")
    return total