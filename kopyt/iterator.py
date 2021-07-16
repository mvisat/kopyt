"""Module for iterator utility."""

from typing import (
    Iterator,
    Iterable,
    TypeVar,
)
from collections import deque
from contextlib import contextmanager

__all__ = ["PeekableIterator"]

T = TypeVar("T")


class PeekableIterator(Iterator[T]):
    def __init__(self, iterable: Iterable[T], default: T = None):
        self._iterator = iter(iterable)
        self._default = default
        self._cache = deque()
        self._markers = deque()
        self._value: T = None

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        if self._cache:
            self._value = self._cache.popleft()
        else:
            self._value = next(self._iterator, self._default)

        if self._markers:
            self._markers[-1].append(self._value)

        return self._value

    def __enter__(self):
        self._push_marker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type or exc_val or exc_tb:
            self._pop_marker(True)
        else:
            self._pop_marker(False)

    @property
    def last(self) -> T:
        return self._value

    def peek(self, i: int = 0) -> T:
        """Peek an object from a specified offset in the current state.

        Args:
            - i: Offset to peek.

        Returns:
            Object in specified offset. If offset passes the iterator maximum's
            state, returns default value specified from initializer.
        """
        assert i >= 0

        length = len(self._cache)
        if length <= i:
            try:
                for _ in range(i - length + 1):
                    self._cache.append(next(self._iterator))
            except StopIteration:
                return self._default

        self._value = self._cache[i]
        return self._value

    @contextmanager
    def simulate(self) -> Iterator[None]:
        """Enter the simulator mode. While in this mode, requesting next
        elements does not change the next elements after exiting this mode.

        Sample usage:
        ```
        iterator = PeekableIterator([0, 1, 2])
        # entering simulator mode
        with iterator.simulate():
            assert next(iterator) == 0
            assert next(iterator) == 1
        # exiting simulator mode
        assert next(iterator) == 0
        """
        self._push_marker()
        try:
            yield
        finally:
            self._pop_marker(reset=True)

    def _push_marker(self) -> None:
        self._markers.append(deque())

    def _pop_marker(self, reset: bool) -> None:
        marker = self._markers.pop()
        if not marker:
            return

        if reset:
            if len(self._cache) > len(marker):
                self._cache.extendleft(reversed(marker))
            else:
                marker.extend(self._cache)
                self._cache = marker
        elif self._markers:
            self._markers[-1].extend(marker)
