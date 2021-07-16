import unittest

from kopyt import Parser
from kopyt.lexer import Identifier, Operator, OptionalNewLines as NL
from kopyt.exception import ParserException


class TestParser(unittest.TestCase):
    code = "a + 1"
    code_with_nl = "\n\na\r\n+\r\r1\n\r"

    def test_parser_accept(self):
        parser = Parser(self.code)
        self.assertEqual(parser._accept(Identifier).value, "a")

    def test_parser_accept_sequence_returns_first_token(self):
        parser = Parser(self.code)
        self.assertEqual(parser._accept("a", Operator).value, "a")

    def test_parser_accept_mismatch(self):
        parser = Parser(self.code)
        with self.assertRaises(ParserException):
            parser._accept("+")

    def test_parser_accept_mismatch_optionals_not_acceptable(self):
        parser = Parser(self.code_with_nl)
        with self.assertRaises(ParserException):
            parser._accept("a", "+", "1")

    def test_parser_accept_optional(self):
        parser = Parser(self.code_with_nl)
        self.assertEqual(parser._accept(NL, "a", NL).value, "a")

    def test_parser_accept_optional_sequence_returns_first_token(self):
        parser = Parser(self.code_with_nl)
        self.assertEqual(parser._accept(NL, "a", NL, "+", NL, "1").value, "a")

    def test_parser_accept_optionals_are_skipped(self):
        parser = Parser("a")
        self.assertEqual(parser._accept(NL, "a", NL).value, "a")

        parser = Parser("a\n\r\n")
        self.assertEqual(parser._accept("a", NL).value, "a")

    def test_parser_try_accept(self):
        parser = Parser(self.code)
        self.assertEqual(parser._try_accept("a"), True)

    def test_parser_try_accept_advance_the_state(self):
        parser = Parser(self.code)
        self.assertEqual(parser._try_accept("a"), True)
        self.assertEqual(parser._try_accept(Operator), True)
        self.assertEqual(parser._try_accept("1"), True)

    def test_parser_try_accept_sequence(self):
        parser = Parser(self.code)
        self.assertEqual(parser._try_accept("a", Operator, "1"), True)

    def test_parser_try_accept_optionals(self):
        parser = Parser(self.code_with_nl)
        self.assertEqual(parser._try_accept(NL, "a", NL, "+", NL, "1"), True)

    def test_parser_try_accept_optionals_not_acceptable(self):
        parser = Parser(self.code_with_nl)
        self.assertEqual(parser._try_accept("a", "+", "1"), False)

    def test_parser_would_accept(self):
        parser = Parser(self.code)
        self.assertEqual(parser._would_accept("a"), True)

    def test_parser_would_accept_dont_alter_state(self):
        parser = Parser(self.code)
        self.assertEqual(parser._would_accept("a"), True)
        self.assertEqual(parser._would_accept(Operator), False)
        self.assertEqual(parser._would_accept("+"), False)
        self.assertEqual(parser._would_accept("1"), False)

    def test_parser_would_accept_sequence(self):
        parser = Parser(self.code)
        self.assertEqual(parser._would_accept("a", Operator, "1"), True)

    def test_parser_would_accept_optionals(self):
        parser = Parser(self.code_with_nl)
        self.assertEqual(parser._would_accept(NL, "a", NL, "+", NL, "1"), True)

    def test_parser_would_accept_optionals_not_acceptable(self):
        parser = Parser(self.code_with_nl)
        self.assertEqual(parser._would_accept("a", "+", "1"), False)

    def test_parser_would_accept_either(self):
        parser = Parser(self.code)
        self.assertEqual(parser._would_accept_either("a"), True)
        self.assertEqual(parser._would_accept_either("a", "b"), True)
        self.assertEqual(parser._would_accept_either("b", "a"), True)
        self.assertEqual(parser._would_accept_either("b", "+"), False)
        self.assertEqual(parser._would_accept_either(["a", "+", "1"]), True)
        self.assertEqual(parser._would_accept_either(["a", "b", "1"]), False)
        self.assertEqual(
            parser._would_accept_either(["x", "y", "z"], ["a", "+", "1"]),
            True)

    def test_parser_would_accept_either_optionals(self):
        parser = Parser(self.code_with_nl)
        self.assertEqual(
            parser._would_accept_either([NL, "a", NL, "+", NL, "1"]), True)
        self.assertEqual(
            parser._would_accept_either([NL, "a", NL, "b", NL, "1"]), False)
        self.assertEqual(
            parser._would_accept_either([NL, "x", NL, "y", NL, "z"],
                                        [NL, "a", NL, "+", NL, "1"]), True)


if __name__ == "__main__":
    unittest.main()
