import re

_INDEX_RE = re.compile(r"\[(-?\d+)\]")


def get_path(data, path, default=None):
    current = data
    for part in path.split("."):
        bracket = part.find("[")
        if bracket == -1:
            key, indices = part, []
        else:
            key = part[:bracket]
            indices = _INDEX_RE.findall(part[bracket:])
        if key != "":
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        for raw in indices:
            i = int(raw)
            if not isinstance(current, list):
                return default
            if i < -len(current) or i >= len(current):
                return default
            current = current[i]
    return current
