"""Module for Position class."""

from dataclasses import dataclass


@dataclass
class Position:
    """
    Position class represents line and column number of a node/token in the
    Kotlin code. Line and column starts from 1.
    """
    line: int
    column: int

    __slots__ = ("line", "column")

    def __str__(self):
        return f"line {self.line} column {self.column}"
