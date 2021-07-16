import unittest

from kopyt.lexer import (
    At,
    BinLiteral,
    BooleanLiteral,
    CharacterLiteral,
    DelimitedComment,
    DoubleLiteral,
    FloatLiteral,
    HardKeyword,
    HexLiteral,
    Identifier,
    IntegerLiteral,
    LineComment,
    LineStringLiteral,
    LongLiteral,
    MultiLineStringLiteral,
    NewLine,
    NullLiteral,
    Operator,
    Position,
    Reserved,
    Separator,
    ShebangLine,
    UnsignedLiteral,
)
from kopyt.lexer import HARD_KEYWORDS, OPERATOR_VALUES, SEPARATOR_VALUES
from kopyt.lexer import Lexer
from kopyt.exception import LexerException


class TestToken(unittest.TestCase):
    def setUp(self) -> None:
        self.token_int = IntegerLiteral("1", Position(1, 1))
        self.token_str = LineStringLiteral("\"a\"", Position(1, 1))

    def test_token_neq(self):
        self.assertTrue(self.token_int != 1)
        self.assertTrue(self.token_int != "a")
        self.assertTrue(self.token_int != LineStringLiteral)
        self.assertTrue(self.token_str != "1")
        self.assertTrue(self.token_str != IntegerLiteral)


class TestLexer(unittest.TestCase):
    def tokens(self, code: str):
        return [token for token in Lexer(code)]

    def token(self, code: str):
        return self.tokens(code)[0]

    def test_lexer_new_line(self):
        codes = [
            "\n",
            "\r",
            "\r\n",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, NewLine)
            self.assertEqual(token.value, code)

    def test_lexer_delimited_comment(self):
        codes = [
            "/**/",
            "/*/*a*/b*/",
            "/*a\n/*b*/\nc*/",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, DelimitedComment)
            self.assertEqual(token.value, code)

        codes = [
            "/*"
            "/**",
            "/*/**/",
        ]
        for code in codes:
            with self.assertRaises(LexerException):
                self.token(code)

    def test_lexer_line_comment(self):
        codes = [
            "//",
            "// /*comment",
            "////",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, LineComment)
            self.assertEqual(token.value, code)

    def test_lexer_shebang_line(self):
        codes = [
            "#!/bin/sh",
            "#!/usr/bin/env kotlin",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, ShebangLine)
            self.assertEqual(token.value, code)

    def test_lexer_integer_literal(self):
        codes = [
            "123",
            "123_456",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, IntegerLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_hex_literal(self):
        codes = [
            "0x1",
            "0X69420_AF",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, HexLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_bin_literal(self):
        codes = [
            "0b1",
            "0B11_00",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, BinLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_unsigned_literal(self):
        codes = [
            "0u",
            "1U",
            "2uL",
            "3_000UL",
            "0x0u",
            "0x1UL",
            "0b1u",
            "0b0UL",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, UnsignedLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_long_literal(self):
        codes = [
            "0b1L",
            "0x0L",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, LongLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_double_literal(self):
        codes = [
            ".123",
            ".123_456",
            "0.123",
            "0.123_456",
            "123_456.789_0",
            "0.1e+2",
            "0.1e-2_345",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, DoubleLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_float_literal(self):
        codes = [
            ".123f",
            ".123_456f",
            "0.123f",
            "0.123_456f",
            "123_456.789_0f",
            "0.1e+2f",
            "0.1e-2_345f",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, FloatLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_line_string_literal(self):
        codes = [
            '""',
            '"abc"',
            '"a\\\"b"',
            '"a\\nb"',
            '"foo${"bar"}"',
            '"foo${"bar${baz("123")}"}"',
            '"foo${"b\\"ar"}baz"',
            '"foo${ } } bar"',
            '"foo${ bar.map { it.x to it .y } } baz"',
        ]
        for code in codes:
            with self.subTest(code=code):
                token = self.token(code)
                self.assertIsInstance(token, LineStringLiteral)
                self.assertEqual(token.value, code)

        codes = [
            '"',
            '"a',
            '"\\a"',
            '"foo${"',
        ]
        for code in codes:
            with self.subTest(code=code):
                with self.assertRaises(LexerException):
                    self.token(code)

    def test_lexer_multi_line_string_literal(self):
        codes = [
            '""""""',
            '"""""""',
            '"""\na\nb\n"""',
            '"""foo${"bar"}"""',
            '"""foo${"""bar"""}"""',
            '"""foo${"""bar${"baz"}foo"""}"""',
            '"""foo${"""b\\"ar"""}baz"""',
            '"""foo\\dbar"""',
        ]
        for code in codes:
            with self.subTest(code=code):
                token = self.token(code)
                self.assertIsInstance(token, MultiLineStringLiteral)
                self.assertEqual(token.value, code)

        codes = [
            '"""',
            '"""""',
            '"""""x""',
        ]
        for code in codes:
            with self.subTest(code=code):
                with self.assertRaises(LexerException):
                    self.token(code)

    def test_lexer_character_literal(self):
        codes = [
            "''",
            "'a'",
            "'\\''",
            "'\\n'",
            "'\\u0000'",
            "'\\uaaaa'",
            "'\\uFFFF'",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, CharacterLiteral)
            self.assertEqual(token.value, code)

        codes = [
            "'",
            "'''",
            "'ab'",
            "'\\u0'",
            "'\\u000z'",
            "'\\",
        ]
        for code in codes:
            with self.assertRaises(LexerException):
                self.token(code)

    def test_lexer_null_literal(self):
        codes = [
            "null",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, NullLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_boolean_literal(self):
        codes = [
            "true",
            "false",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, BooleanLiteral)
            self.assertEqual(token.value, code)

    def test_lexer_escaped_identifier(self):
        codes = [
            "`a`",
            "`a_b`",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, Identifier)
            self.assertEqual(token.value, code)

        codes = [
            "`",
            "``",
            "`\n`",
        ]
        for code in codes:
            with self.assertRaises(LexerException):
                self.token(code)

    def test_lexer_identifier(self):
        codes = [
            "const",
            "i",
            "_private",
            "A_b_c ",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, Identifier)
            self.assertEqual(token.value, code.strip())

    def test_lexer_at(self):
        codes = [
            "@",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, At)
            self.assertEqual(token.value, code)

    def test_lexer_separator(self):
        codes = SEPARATOR_VALUES
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, Separator)
            self.assertEqual(token.value, code)

    def test_lexer_operator(self):
        codes = OPERATOR_VALUES
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, Operator)
            self.assertEqual(token.value, code)

        codes = [
            "in",
            "!in",
            "is",
            "!is",
            "as",
            "as?",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, Operator)
            self.assertEqual(token.value, code)

    def test_lexer_hard_keyword(self):
        codes = HARD_KEYWORDS
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, HardKeyword)
            self.assertEqual(token.value, code)

        codes = [
            "return",
            "return@",
            "continue",
            "continue@",
            "break",
            "break@",
            "this",
            "this@",
            "super",
            "super@",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, HardKeyword)
            self.assertEqual(token.value, code)

    def test_lexer_reserved(self):
        codes = [
            "...",
        ]
        for code in codes:
            token = self.token(code)
            self.assertIsInstance(token, Reserved)
            self.assertEqual(token.value, code)

    def test_lexer_range_test(self):
        tokens = self.tokens("in 1..10 -> println()")
        expecteds = ("in", "1", "..", "10", "->", "println", "(", ")")
        for token, expected in zip(tokens, expecteds):
            self.assertEqual(token.value, expected)

    def test_lexer_number_expression(self):
        tokens = self.tokens("0.toLong()")
        expecteds = ("0", ".", "toLong", "(", ")")
        for token, expected in zip(tokens, expecteds):
            self.assertEqual(token.value, expected)

    def test_lexer_nullable_reference(self):
        tokens = self.tokens("nullable?::foo")
        expecteds = ("nullable", "?", "::", "foo")
        for token, expected in zip(tokens, expecteds):
            self.assertEqual(token.value, expected)

    def test_lexer_not_is(self):
        tokens = self.tokens("!isEnabled")
        expecteds = ("!", "isEnabled")
        for token, expected in zip(tokens, expecteds):
            self.assertEqual(token.value, expected)

    def test_lexer_not_in(self):
        tokens = self.tokens("!inArray")
        expecteds = ("!", "inArray")
        for token, expected in zip(tokens, expecteds):
            self.assertEqual(token.value, expected)

    def test_lexer_integration(self):
        code = """\
x = /* comment */ true + 1_234 // comment
y /*/*
comment
*/*/ +=\t1.23e4
@annotated(val=1)
"""
        tokens = self.tokens(code)
        expected_tokens = [
            Identifier("x", Position(1, 1)),
            Operator("=", Position(1, 3)),
            DelimitedComment("/* comment */", Position(1, 5)),
            BooleanLiteral("true", Position(1, 19)),
            Operator("+", Position(1, 24)),
            IntegerLiteral("1_234", Position(1, 26)),
            LineComment("// comment", Position(1, 32)),
            NewLine("\n", Position(1, 42)),
            Identifier("y", Position(2, 1)),
            DelimitedComment("/*/*\ncomment\n*/*/", Position(2, 3)),
            Operator("+=", Position(4, 6)),
            DoubleLiteral("1.23e4", Position(4, 9)),
        ]
        for token, expected in zip(tokens, expected_tokens):
            self.assertIsInstance(token, expected.__class__)
            self.assertEqual(token.value, expected.value)
            self.assertEqual(token.position, expected.position)

    def test_lexer_illegal_character(self):
        codes = [
            "\\",
        ]
        for code in codes:
            with self.assertRaises(LexerException):
                self.token(code)


if __name__ == "__main__":
    unittest.main()
