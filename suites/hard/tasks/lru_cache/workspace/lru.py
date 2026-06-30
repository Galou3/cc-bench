class LRUCache:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._data = {}

    def get(self, key):
        # NOTE: does not refresh recency
        return self._data.get(key, -1)

    def put(self, key, value) -> None:
        # NOTE: updating an existing key does not refresh recency,
        # and recency is never tracked on get
        self._data[key] = value
        if len(self._data) > self.capacity:
            oldest = next(iter(self._data))
            del self._data[oldest]
