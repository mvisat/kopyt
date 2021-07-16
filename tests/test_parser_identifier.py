import unittest

from kopyt import node
from . import TestParserBase


class TestParserSimpleIdentifier(TestParserBase):
    def do_test(self, code: str) -> node.SimpleIdentifier:
        return super().do_test("parse_simple_identifier", code,
                               node.SimpleIdentifier)

    def test_parser_simple_identifier(self):
        code = "a"
        result = self.do_test(code)
        self.assertEqual(code, result.value)

    def test_parser_simple_identifier_backtick(self):
        code = "`~!@#$`"
        result = self.do_test(code)
        self.assertEqual(code, result.value)

    def test_parser_simple_identifier_underscore(self):
        code = "_a_b_c"
        result = self.do_test(code)
        self.assertEqual(code, result.value)


class TestParserIdentifier(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.Identifier:
        return super().do_test("parse_identifier",
                               code,
                               node.Identifier,
                               test_str=test_str)

    def test_parser_identifier(self):
        code = "a"
        result = self.do_test(code)
        self.assertEqual(code, result.value)

    def test_parser_identifier_multi(self):
        code = "a.b.c"
        result = self.do_test(code)
        self.assertEqual(code, result.value)

    def test_parser_identifier_backtick(self):
        code = "`~!@#$`._a_b"
        result = self.do_test(code)
        self.assertEqual(code, result.value)

    def test_parser_identifier_complex(self):
        code = "_a_b_c.`~!@#$`.a"
        result = self.do_test(code)
        self.assertEqual(code, result.value)

    def test_parser_identifier_newlines(self):
        from re import compile
        ws = compile(r"\s+")
        codes = [
            "a\n.b",
            "a\r\n.b\n.c",
            "a\n.`b`",
            "`~!@#$`\r  .a_b",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, False)
                expected = ws.sub("", code)
                self.assertEqual(expected, result.value)


if __name__ == "__main__":
    unittest.main()
