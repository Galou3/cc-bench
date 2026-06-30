import re


def get_path(data, path, default=None):
    current = data
    for part in path.split("."):
        bracket = part.find("[")
        if bracket == -1:
            key, indices = part, []
        else:
            key = part[:bracket]
            indices = re.findall(r"\[(-?\d+)\]", part[bracket:])
        try:
            if key != "":
                current = current[key]
            for raw in indices:
                current = current[int(raw)]
        except (KeyError, IndexError):
            return default
    return current
