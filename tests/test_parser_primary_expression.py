from typing import Iterable
import unittest

from kopyt import Parser
from kopyt import node
from . import TestParserBase


class TestParserPrimaryExpression(TestParserBase):
    def do_test(self,
                codes: Iterable[str],
                expected_type: type,
                test_str: bool = True) -> node.PrimaryExpression:
        for code in codes:
            with self.subTest(code=code):
                expected_types = (node.PrimaryExpression, expected_type)
                super().do_test("parse_expression",
                                code,
                                expected_types,
                                test_str=test_str)

    def do_test_exception(self, codes: Iterable[str], func: str) -> None:
        for code in codes:
            with self.subTest(code=code):
                super().do_test_exception(func, code)

    def test_parser_primary_expression_parenthesized(self):
        codes = [
            "(1)",
            "(true)",
        ]
        self.do_test(codes, node.ParenthesizedExpression)

    def test_parser_primary_expression_parenthesized_multilines(self):
        codes = [
            """(
                1
                +
                2
                )""",
        ]
        self.do_test(codes, node.ParenthesizedExpression, False)

    def test_parser_primary_expression_simple_identifier(self):
        codes = [
            "`foo`",
            "bar",
            "_foo_bar",
        ]
        self.do_test(codes, node.SimpleIdentifier)

    def test_parser_primary_expression_literal_constant(self):
        codes = [
            "1",
            "1.23",
        ]
        self.do_test(codes, node.LiteralConstant)

    def test_parser_primary_expression_literal_constant_exception(self):
        codes = [
            "(1)",
            '"123"',
        ]
        self.do_test_exception(codes, "parse_literal_constant")

    def test_parser_primary_expression_string_literal(self):
        codes = [
            '"string"',
            '"""multi\nline"""',
        ]
        self.do_test(codes, node.StringLiteral)

    def test_parser_primary_expression_string_literal_exception(self):
        codes = [
            "(1)",
            "123",
        ]
        self.do_test_exception(codes, "parse_string_literal")

    def test_parser_primary_expression_lambda_literal(self):
        codes = [
            "{ a, b -> a + b }",
            "{ (a, b) -> a + b }",
            "{ (a, b): Tuple -> a + b }",
            "{ i: Int -> i + 1 }",
            "{ times -> this.repeat(times) }",
            "{ a, b -> a.length < b.length }",
            "{ x: Int, y: Int -> x + y }",
            "{ acc, e -> acc * e }",
            "{ println(\"...\") }",
            "{ it > 0 }",
            "{ it.length == 5 }",
            "{ it }",
            "{ _, value -> println(\"$value!\") }",
            """\
{
    val shouldFilter = it > 0
    shouldFilter
}""",
        ]
        self.do_test(codes, node.LambdaLiteral)

    def test_parser_primary_expression_lambda_literal_trailing_comma(self):
        parser = Parser("{ a, b, -> a + b }")
        result = parser.parse_primary_expression()
        self.assertIsInstance(result, node.PrimaryExpression)
        self.assertIsInstance(result, node.FunctionLiteral)
        self.assertIsInstance(result, node.LambdaLiteral)

    def test_parser_primary_expression_anonymous_function(self):
        codes = [
            "fun(x)", "fun(x: Int)", "fun(x: Int = 1)", "fun(x: Int): Int",
            "fun(x: Int, y: Int): Int = x + y",
            "fun Int.(other: Int): Int = this + other",
            "fun(seq: T) where T : CharSequence, T : Appendable", """\
fun(x: Int, y: Int): Int {
    return x + y
}"""
        ]
        self.do_test(codes, node.AnonymousFunction)

    def test_parser_primary_expression_function_literal_exception(self):
        codes = ["123"]
        self.do_test_exception(codes, "parse_function_literal")

    def test_parser_primary_expression_object_literal(self):
        codes = [
            "object", "object : MouseAdapter()", """\
object : A(1), B {
    override val y = 15
}"""
        ]
        self.do_test(codes, node.ObjectLiteral)

    def test_parser_primary_expression_collection_literal(self):
        codes = [
            "[]",
            "[1]",
            "[1, 2]",
        ]
        self.do_test(codes, node.CollectionLiteral)

    def test_parser_primary_expression_this_expression(self):
        codes = [
            "this",
            "this@foo",
        ]
        self.do_test(codes, node.ThisExpression)

    def test_parser_primary_expression_super_expression(self):
        codes = [
            "super",
            "super@foo",
            "super<Foo>",
            "super<Foo>@bar",
        ]
        self.do_test(codes, node.SuperExpression)

    def test_parser_primary_expression_if_expression(self):
        codes = [
            "if (true) 1 else 0",
        ]
        self.do_test(codes, node.IfExpression)

    def test_parser_primary_expression_when_expression(self):
        codes = [
            "when { }",
        ]
        self.do_test(codes, node.WhenExpression)

    def test_parser_primary_expression_try_expression(self):
        codes = [
            "try { } finally { }",
        ]
        self.do_test(codes, node.TryExpression)

    def test_parser_primary_expression_jump_expression(self):
        codes = [
            "return",
            "continue",
            "break",
        ]
        self.do_test(codes, node.JumpExpression)


if __name__ == "__main__":
    unittest.main()
