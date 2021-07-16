import unittest

from kopyt import node
from . import TestParserBase


class TestParserIf(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.IfExpression:
        expected_types = (node.Expression, node.IfExpression)
        return super().do_test("parse_expression",
                               code,
                               expected_types,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_if_expression", code)

    def test_parser_if_body(self):
        code = """\
if (a > b) {
    max = a
} else {
    max = b
}"""
        result = self.do_test(code)
        self.assertIsInstance(result.if_body, node.Block)
        self.assertIsInstance(result.else_body, node.Block)

    def test_parser_if_statement(self):
        code = "if (a > b) a else b"
        result = self.do_test(code)
        self.assertIsInstance(result.if_body, node.Statement)
        self.assertIsInstance(result.else_body, node.Statement)

    def test_parser_if_lambda_literal(self):
        code = "if (a) a else { b -> println(b) }"
        result = self.do_test(code)
        self.assertIsInstance(result.if_body, node.Statement)
        self.assertIsInstance(result.else_body, node.LambdaLiteral)

    def test_parser_if_without_bodies(self):
        codes = [
            "if (condition);",
            "if (condition) else;",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, False)
                self.assertIsNone(result.if_body)
                self.assertIsNone(result.else_body)
                self.assertEqual(str(result), "if (condition);")

    def test_parser_if_without_else(self):
        code = "if (a < b) max = b"
        result = self.do_test(code)
        self.assertIsInstance(result.if_body, node.Statement)
        self.assertIsNone(result.else_body)

    def test_parser_if_expecting_body(self):
        code = "if (condition)"
        self.do_test_exception(code)

    def test_parser_if_expecting_else_body(self):
        code = "if (condition) else"
        self.do_test_exception(code)


if __name__ == "__main__":
    unittest.main()
