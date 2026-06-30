def parse_version(s):
    # BUG: does not pad missing minor/patch, so "1" -> (1,) and "2.5" -> (2, 5)
    # instead of being normalised to a 3-tuple.
    parts = s.split(".")
    return tuple(int(p) for p in parts)
