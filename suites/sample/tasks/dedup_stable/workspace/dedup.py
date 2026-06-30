def dedup(items):
    # BUG: set() drops duplicates but also destroys the original ordering, so the
    # first-seen order the task requires is not preserved.
    return list(set(items))
