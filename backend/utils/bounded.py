"""
A dict that keeps only the most recently written keys, for per-user state kept in memory
(the last reply, recent messages): without a limit it would grow with every user id a
request names.
"""

from collections import OrderedDict
from typing import Any, Callable, Optional

# Users whose in-memory conversation state is kept; the app itself has one child profile
MAX_USERS = 1000


class BoundedDict(OrderedDict):
    """
    An OrderedDict holding at most maxsize keys: writing a new key past the limit drops the
    key written longest ago. With default_factory, reading a missing key creates it (like
    defaultdict).
    """

    def __init__(self, maxsize: int = MAX_USERS, default_factory: Optional[Callable[[], Any]] = None):
        super().__init__()
        self.maxsize = maxsize
        self.default_factory = default_factory

    def __setitem__(self, key, value) -> None:
        super().__setitem__(key, value)
        self.move_to_end(key)
        while len(self) > self.maxsize:
            self.popitem(last=False)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        value = self.default_factory()
        self[key] = value
        return value
