"""Module for lexer and tokens classes."""

from collections import deque
from dataclasses import dataclass
from enum import IntEnum
from typing import (
    Type,
    Iterator,
    Optional,
    Iterable,
    Union,
)
import string
import unicodedata

from .exception import LexerException
from .position import Position


@dataclass
class Token:
    """Base class for tokens produced by lexer."""
    value: str
    position: Position

    __slots__ = ("value", "position")

    def __str__(self) -> str:
        return self.value

    def __ne__(self, o: object) -> bool:
        if isinstance(o, str):
            return self.value != o
        if isinstance(o, type):
            return not isinstance(self, o)
        return super().__ne__(o)


@dataclass
class ShebangLine(Token):
    pass


class OptionalNewLines:
    """A special class to denote zero or multiple new lines
    while parsing the code.
    """


@dataclass
class NewLine(OptionalNewLines, Token):
    pass


@dataclass
class DelimitedComment(Token):
    pass


@dataclass
class LineComment(Token):
    pass


@dataclass
class Separator(Token):
    pass


@dataclass
class LiteralConstant(Token):
    pass


@dataclass
class RealLiteral(LiteralConstant):
    pass


@dataclass
class FloatLiteral(RealLiteral):
    pass


@dataclass
class DoubleLiteral(RealLiteral):
    pass


@dataclass
class IntegerLiteral(LiteralConstant):
    pass


@dataclass
class HexLiteral(LiteralConstant):
    pass


@dataclass
class BinLiteral(LiteralConstant):
    pass


@dataclass
class UnsignedLiteral(LiteralConstant):
    pass


@dataclass
class LongLiteral(LiteralConstant):
    pass


@dataclass
class BooleanLiteral(LiteralConstant):
    pass


@dataclass
class NullLiteral(LiteralConstant):
    pass


@dataclass
class CharacterLiteral(LiteralConstant):
    pass


@dataclass
class StringLiteral(Token):
    pass


@dataclass
class LineStringLiteral(StringLiteral):
    pass


@dataclass
class MultiLineStringLiteral(StringLiteral):
    pass


@dataclass
class Operator(Token):
    pass


@dataclass
class At(Token):
    pass


@dataclass
class Reserved(Token):
    pass


@dataclass
class Identifier(Token):
    pass


@dataclass
class HardKeyword(Token):
    pass


@dataclass
class EOF(Token):
    pass


SEPARATOR_VALUES = frozenset((".", ",", "(", ")", "[", "]", "{", "}", ";"))

OPERATOR_VALUES = frozenset((
    "++",
    "--",
    "?",
    "-",
    "+",
    "++",
    "--",
    "!",
    ":",
    "::",
    "*",
    "/",
    "%",
    "+",
    "-",
    "..",
    "?:",
    "<",
    ">",
    "<=",
    ">=",
    "==",
    "!=",
    "===",
    "!==",
    "&&",
    "||",
    "*",
    "=",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "!in",
    "!is",
    "->",
))
OPERATOR_VALUES_MAX_LEN = max(map(len, OPERATOR_VALUES))

OPERATOR_VALUES_PER_LEN = [[v for v in OPERATOR_VALUES if len(v) == i]
                           for i in range(1, OPERATOR_VALUES_MAX_LEN + 1)]

IDENT_START_CATEGORIES = frozenset((
    "Ll",
    "Lm",
    "Lo",
    "Lt",
    "Lu",
    "Nl",
))

IDENT_PART_CATEGORIES = IDENT_START_CATEGORIES | frozenset(("Nd", ))

# https://kotlinlang.org/docs/keyword-reference.html#hard-keywords
HARD_KEYWORDS = frozenset((
    # "as", # -> Operator
    "break",
    "class",
    "continue",
    "do",
    "else",
    # "false", # -> BooleanLiteral
    "for",
    "fun",
    "if",
    # "in", # -> Operator
    "interface",
    # "is", # -> Operator
    # "null", # -> NullLiteral
    "object",
    "package",
    "return",
    "super",
    "this",
    "throw",
    # "true", # -> BooleanLiteral
    "try",
    "typealias",
    "typeof",
    "val",
    "var",
    "when",
    "while",
))


class StackMode(IntEnum):
    DEFAULT = 0
    INSIDE = 1


class Lexer(Iterable[Token]):
    """
    Yields tokens by lexing Kotlin code.
    """
    def __init__(self, data: str, yield_comments: bool = True) -> None:
        self.data = data
        self.yield_comments = yield_comments

        self.i = 0
        self.length = len(data)
        self.lines = [1] * self.length
        self.columns = [1] * self.length
        self._compute_line_and_column()

    def __iter__(self) -> Iterator[Token]:
        """Process the code and produces a generator of Kotlin tokens.

        Yields:
            Tokens.

        Raises:
            LexerException: an error occured while lexing the code.
        """
        stack_mode = deque([StackMode.DEFAULT])

        while self.i < self.length:
            c = self.data[self.i]
            if self.i + 1 < self.length:
                c_next = self.data[self.i + 1]
                c_start = c + c_next
            else:
                c_next = None
                c_start = c

            if c.isspace():
                if c in ("\n", "\r"):
                    new_lines = self._read_new_line(c, c_next)
                    if stack_mode[-1] == StackMode.DEFAULT:
                        yield new_lines
                else:
                    self._consume_whitespaces()

            elif c_start == "//":
                comment = self._read_line_comment()
                if self.yield_comments:
                    yield comment

            elif c_start == "/*":
                comment = self._read_delimited_comment()
                if self.yield_comments:
                    yield comment

            elif c_start == "#!":
                yield self._read_shebang_line()

            # special case for "..." reserved operator and ".." range operator
            elif c_start == "..":
                if self.i + 2 < self.length and self.data[self.i + 2] == ".":
                    yield self._read_reserved(3)
                else:
                    yield self._read_operator()

            elif c == "." and c_next and c_next.isdigit():
                yield self._read_integer_or_real_literal()

            elif c == "@":
                yield self._read_at()

            elif c in SEPARATOR_VALUES:
                if c == "{":
                    stack_mode.append(StackMode.DEFAULT)
                elif c in ("(", "["):
                    stack_mode.append(StackMode.INSIDE)
                elif c in (")", "]", "}") and stack_mode:
                    stack_mode.pop()
                yield self._read_separator()

            elif c == '"':
                yield self._read_string_literal()

            elif c == "'":
                yield self._read_character_literal()

            elif c.isdigit():
                yield self._read_digit_literal(c, c_next)

            elif c == "`":
                yield self._read_escaped_identifier()

            elif c == "_" or unicodedata.category(c) in IDENT_START_CATEGORIES:
                yield self._read_identifier_or_keyword()

            # edge case for "?::", should yield "?" and "::"
            elif c_start == "?:" and self.i + 2 < self.length and self.data[
                    self.i + 2] == ":":
                yield self._read_token(Operator, self.i + 1)
                yield self._read_token(Operator, self.i + 2)

            elif self._try_operator():
                yield self._read_operator()

            else:
                self._error(f"unexpected character {c!r}")

    @property
    def eof(self) -> EOF:
        """Returns token used to indicate an end of file."""
        return EOF("", Position(self.lines[-1], self.columns[-1] + 1))

    def _compute_line_and_column(self) -> None:
        """Pre-compute line and column number for each characters."""
        cur_line = 1
        cur_column = 1

        for i in range(self.length):
            self.lines[i] = cur_line
            self.columns[i] = cur_column

            c = self.data[i]
            c_next = self.data[i + 1] if i + 1 < self.length else None
            if c == "\n" or (c == "\r" and c_next != "\n"):
                cur_line += 1
                cur_column = 1
            else:
                cur_column += 1

    def _error(self, message: str) -> None:
        line = self.lines[self.i]
        column = self.columns[self.i]
        message = f"{message} at line {line} column {column}"
        error = LexerException(message)
        raise error

    def _consume_whitespaces(self) -> None:
        while self.i < self.length:
            c = self.data[self.i]
            if c.isspace() and c not in ("\n", "\r"):
                self.i += 1
            else:
                return

    def _read_token(self, token_type: Type[Token], end: int) -> Token:
        value = self.data[self.i:end]
        position = Position(self.lines[self.i], self.columns[self.i])
        self.i = end
        return token_type(value, position)

    def _read_new_line(self, c: str, c_next: Optional[str]) -> NewLine:
        crlf = c == "\r" and c_next == "\n"
        if crlf:
            end = self.i + 2
        else:
            end = self.i + 1
        return self._read_token(NewLine, end)

    def _read_delimited_comment(self) -> DelimitedComment:
        i = self.i + 2
        count = 1
        while i < self.length and count > 0:
            c = self.data[i]
            if i + 1 < self.length:
                c_next = self.data[i + 1]
                c_start = c + c_next
            else:
                c_next = None
                c_start = c

            if c_start == "*/":
                count -= 1
                i += 2
            elif c_start == "/*":
                count += 1
                i += 2
            else:
                i += 1
        if count > 0:
            self._error("unterminated delimited comment")
        return self._read_token(DelimitedComment, i)

    def _read_line_comment(self) -> LineComment:
        for i in range(self.i + 2, self.length):
            if self.data[i] in ("\n", "\r"):
                end = i
                break
        else:
            end = self.length
        return self._read_token(LineComment, end)

    def _read_shebang_line(self) -> ShebangLine:
        for i in range(self.i + 2, self.length):
            if self.data[i] in ("\n", "\r"):
                end = i
                break
        else:
            end = self.length
        return self._read_token(ShebangLine, end)

    def _read_at(self) -> At:
        return self._read_token(At, self.i + 1)

    def _read_separator(self) -> Separator:
        return self._read_token(Separator, self.i + 1)

    def _skip_escape_sequence(self, start: int) -> int:
        i = start + 1
        if i >= self.length:
            self._error("expecting escape sequence")

        esc = self.data[i]
        if esc in "utbrn'\"\\$":
            i += 1
            if esc == "u":
                if i + 4 >= self.length:
                    self._error("unterminated unichar literal")
                for j in range(i, min(self.length, i + 4)):
                    if self.data[j] not in string.hexdigits:
                        self._error(f"illegal hex digit {self.data[j]!r}")
                i += 4
        else:
            self._error(f"illegal escape character {esc!r}")
        return i

    def _skip_string_expression(self, start: int) -> int:
        i = start + 2
        count = 1
        while i < self.length and count > 0:
            c = self.data[i]
            if c == "}":
                i += 1
                count -= 1
            elif c == "\\":
                i = self._skip_escape_sequence(i)
            elif c == "$" and i + 1 < self.length and self.data[i + 1] == "{":
                i = self._skip_string_expression(i)
            elif c == "{":
                i += 1
                count += 1
            else:
                i += 1
        else:
            if count > 0:
                self._error("unterminated string expression")
        return i

    def _skip_string_literal(self, single_line: bool) -> int:
        if single_line:
            len_quote = 1
        else:
            len_quote = 3

        i = self.i + len_quote
        while i < self.length:
            c = self.data[i]
            if c == "\"":
                if single_line:
                    i += 1
                    break

                count = 1
                for j in range(i + 1, self.length):
                    if self.data[j] != "\"":
                        break
                    count += 1

                if count >= len_quote:
                    i += count
                    break
                else:
                    i += 1
            elif c == "$" and i + 1 < self.length and self.data[i + 1] == "{":
                i = self._skip_string_expression(i)
            elif single_line and c == "\\":
                i = self._skip_escape_sequence(i)
            else:
                i += 1
        else:
            self._error("unterminated string literal")
        return i

    def _read_line_string_literal(self) -> LineStringLiteral:
        end = self._skip_string_literal(True)
        return self._read_token(LineStringLiteral, end)

    def _read_multi_line_string_literal(self) -> MultiLineStringLiteral:
        end = self._skip_string_literal(False)
        return self._read_token(MultiLineStringLiteral, end)

    def _read_string_literal(self) -> StringLiteral:
        if self.i + 2 < self.length and self.data[self.i:self.i + 3] == '"""':
            return self._read_multi_line_string_literal()
        return self._read_line_string_literal()

    def _read_character_literal(self) -> CharacterLiteral:
        i = self.i + 1
        if i >= self.length:
            self._error("unterminated character literal")

        if self.data[i] == "\\":
            i = self._skip_escape_sequence(i)
        elif self.data[i] != "'":
            i += 1

        if i >= self.length or self.data[i] != "'":
            self._error("expecting \"'\" on character literal")
        else:
            i += 1
        return self._read_token(CharacterLiteral, i)

    def _peek_unsigned_and_long(self, start: int) -> int:
        i = start
        if i < self.length and self.data[i] in "uU":
            i += 1
        if i < self.length and self.data[i] == "L":
            i += 1
        return i

    def _peek_digits(self, start: int, digits: str) -> int:
        for i in range(start, self.length):
            c = self.data[i]
            if c in digits or c == "_":
                continue
            return i
        return self.length

    def _determine_integer_type(self, end: int, default: type) -> type:
        if self.data[end - 1] in "uU" or self.data[end - 2] in "uU":
            return UnsignedLiteral
        if self.data[end - 1] == "L":
            return LongLiteral
        return default

    def _read_integer_or_real_literal(
            self) -> Union[IntegerLiteral, RealLiteral]:
        i = self._peek_digits(self.i, string.digits)
        if i >= self.length or self.data[i] not in ".eEfF":
            i = self._peek_unsigned_and_long(i)
            int_type = self._determine_integer_type(i, IntegerLiteral)
            return self._read_token(int_type, i)

        if i < self.length and self.data[i] == ".":
            # handle range test and expression, e.g. 1..10, 0.toLong()
            if i + 1 < self.length and not self.data[i + 1].isdigit():
                return self._read_token(IntegerLiteral, i)
            i += 1
            i = self._peek_digits(i, string.digits)

        if i < self.length and self.data[i] in "eE":
            i += 1
            if i < self.length and self.data[i] in "-+":
                i += 1
            i = self._peek_digits(i, string.digits)

        if i < self.length and self.data[i] in "fF":
            i += 1
            token_type = FloatLiteral
        else:
            token_type = DoubleLiteral
        return self._read_token(token_type, i)

    def _read_hex_literal(self) -> HexLiteral:
        j = self._peek_digits(self.i + 2, string.hexdigits)
        j = self._peek_unsigned_and_long(j)
        hex_type = self._determine_integer_type(j, HexLiteral)
        return self._read_token(hex_type, j)

    def _read_bin_literal(self) -> BinLiteral:
        j = self._peek_digits(self.i + 2, "01")
        j = self._peek_unsigned_and_long(j)
        bin_type = self._determine_integer_type(j, BinLiteral)
        return self._read_token(bin_type, j)

    def _read_digit_literal(self, c: str, c_next: str) -> Token:
        if c == "0":
            if c_next and c_next in "xX":
                return self._read_hex_literal()
            if c_next and c_next in "bB":
                return self._read_bin_literal()
        return self._read_integer_or_real_literal()

    def _try_operator(self) -> bool:
        max_len = min(self.length - self.i, OPERATOR_VALUES_MAX_LEN)
        for l in range(max_len, 0, -1):
            if self.data[self.i:self.i + l] in OPERATOR_VALUES_PER_LEN[l - 1]:
                return True
        return False

    def _read_operator(self) -> Operator:
        max_len = min(self.length - self.i, OPERATOR_VALUES_MAX_LEN)
        for l in range(max_len, 0, -1):
            tmp = self.data[self.i:self.i + l]
            if tmp in OPERATOR_VALUES_PER_LEN[l - 1]:
                # edge case: !isEnabled is not !is + Enabled
                if (l == 3 and tmp in ("!in", "!is")
                        and self.i + l < self.length and unicodedata.category(
                            self.data[self.i + l]) in ("Ll", "Lu")):
                    continue
                return self._read_token(Operator, self.i + l)
        raise AssertionError

    def _read_reserved(self, length: int) -> Reserved:
        return self._read_token(Reserved, self.i + length)

    def _read_escaped_identifier(self) -> Identifier:
        for i in range(self.i + 1, self.length):
            c = self.data[i]
            if c == "`":
                end = i + 1
                break
            elif c in ("\n", "\r"):
                self._error("unexpected new lines in escaped identifier")
        else:
            end = self.length
            self._error("unterminated escaped identifier")

        if end == self.i + 2:
            self._error("empty escaped identifier")
        return self._read_token(Identifier, end)

    def _read_identifier_or_keyword(self) -> Token:
        for i in range(self.i + 1, self.length):
            c = self.data[i]
            if c == "_":
                continue
            elif unicodedata.category(c) in IDENT_PART_CATEGORIES:
                continue
            end = i
            break
        else:
            end = self.length

        ident = self.data[self.i:end]
        if ident == "null":
            token_type = NullLiteral
        elif ident in ("true", "false"):
            token_type = BooleanLiteral
        elif ident == "as":
            if end < self.length and self.data[end] == "?":
                ident += "?"
                end += 1
            token_type = Operator
        elif ident in ("is", "in"):
            token_type = Operator
        elif ident in ("return", "continue", "break", "this", "super"):
            if end < self.length and self.data[end] == "@":
                ident += "@"
                end += 1
            token_type = HardKeyword
        elif ident in HARD_KEYWORDS:
            token_type = HardKeyword
        else:
            token_type = Identifier
        return self._read_token(token_type, end)
