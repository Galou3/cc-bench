def parse_version(s):
    parts = [int(p) for p in s.split(".")]
    parts += [0] * (3 - len(parts))
    return tuple(parts[:3])
