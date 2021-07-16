import unittest

from kopyt import node
from . import TestParserBase


class TestParserBinaryExpression(TestParserBase):
    operators = ()
    node_type = node.Expression

    def do_test(self,
                code: str,
                test_str: bool = True) -> node.BinaryExpression:
        expected_types = (node.Expression, node.BinaryExpression)
        return super().do_test("parse_expression",
                               code,
                               expected_types,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_expression", code)

    def test_parser_binary_expression_simple(self):
        for operator in self.operators:
            code = f"a {operator} b"
            with self.subTest(code=code):
                self.do_test(code)

    def test_parser_binary_expression_compound(self):
        for operator in self.operators:
            code = f"a {operator} b {operator} c"
            with self.subTest(code=code):
                result = self.do_test(code)
                self.assertIsInstance(result.left, self.node_type)
                self.assertEqual("c", str(result.right))

    def test_parser_binary_expression_expecting_expression(self):
        codes = [
            *(f"a {operator}" for operator in self.operators),
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)


class TestParserDisjunction(TestParserBinaryExpression):
    operators = "||",
    node_type = node.Disjunction


class TestParserConjunction(TestParserBinaryExpression):
    operators = "&&",
    node_type = node.Conjunction


class TestParserEquality(TestParserBinaryExpression):
    operators = "==", "!=", "===", "!=="
    node_type = node.Equality


class TestParserComparison(TestParserBinaryExpression):
    operators = "<", ">", "<=", ">="
    node_type = node.Comparison


class TestParserInfixOperation(TestParserBinaryExpression):
    operators = "in", "!in", "is", "!is"
    node_type = node.InfixOperation


class TestParserElvisExpression(TestParserBinaryExpression):
    operators = "?:",
    node_type = node.ElvisExpression


class TestParserInfixFunctionCall(TestParserBinaryExpression):
    operators = "shl", "add",
    node_type = node.InfixFunctionCall


class TestParserRangeExpression(TestParserBinaryExpression):
    operators = "..",
    node_type = node.RangeExpression


class TestParserAdditiveExpression(TestParserBinaryExpression):
    operators = "+", "-"
    node_type = node.AdditiveExpression


class TestParserMultiplicativeExpression(TestParserBinaryExpression):
    operators = "*", "/", "%"
    node_type = node.MultiplicativeExpression


class TestParserAsExpression(TestParserBinaryExpression):
    operators = "as", "as?"
    node_type = node.AsExpression


class TestParserUnaryExpression(TestParserBase):
    def do_test(self,
                code: str,
                expected_type: type,
                test_str: bool = True) -> node.UnaryExpression:
        expected_types = (node.Expression, node.UnaryExpression, expected_type)
        return super().do_test("parse_expression",
                               code,
                               expected_types,
                               test_str=test_str)

    def do_test_exception(self,
                          code: str,
                          parse_func: str = "parse_expression") -> None:
        return super().do_test_exception(parse_func, code)


class TestParserPrefixUnaryExpression(TestParserUnaryExpression):
    def test_parse_prefix_unary_expression_operator(self):
        operators = "++", "--", "-", "+", "!"
        for operator in operators:
            code = f"{operator}a"
            with self.subTest(code=code):
                result = self.do_test(code, node.PrefixUnaryExpression)
                self.assertEqual(1, len(result.prefixes))
                self.assertEqual(operator, str(result.prefixes[0]))

    def test_parse_prefix_unary_expression_label(self):
        labels = "loop@",
        for label in labels:
            code = f"{label} a"
            with self.subTest(code=code):
                result = self.do_test(code, node.PrefixUnaryExpression)
                self.assertEqual(1, len(result.prefixes))
                self.assertEqual(label, str(result.prefixes[0]), label)

    def test_parse_prefix_unary_expression_annotation(self):
        annotations = "@Ann",
        for annotation in annotations:
            code = f"{annotation} a"
            with self.subTest(code=code):
                result = self.do_test(code, node.PrefixUnaryExpression)
                self.assertEqual(len(result.prefixes), 1)
                self.assertEqual(annotation, str(result.prefixes[0]))

    def test_parse_prefix_unary_expression_expecting_expression(self):
        codes = ["++", "loop@", "@Ann"]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)

    def test_parse_prefix_unary_expression_wrong_prefix(self):
        code = "?."
        self.do_test_exception(code, "parse_unary_prefix")


class TestParserPostfixUnaryExpression(TestParserUnaryExpression):
    def test_parser_postfix_unary_expression_operator(self):
        operators = "++", "--", "!!"
        for operator in operators:
            code = f"a{operator}"
            with self.subTest(code=code):
                result = self.do_test(code, node.PostfixUnaryExpression)
                self.assertEqual(1, len(result.suffixes))
                self.assertEqual(operator, str(result.suffixes[0]))

    def test_parser_postfix_unary_expression_navigation_suffix(self):
        codes = [
            "a.b",
            "a?.b",
            "a.(b)",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.PostfixUnaryExpression)
                self.assertEqual(1, len(result.suffixes))
                self.assertIsInstance(result.suffixes[0],
                                      node.NavigationSuffix)

    def test_parser_postfix_unary_expression_navigation_suffix_callable_reference(
            self):
        code = "a?.x::class"
        result = self.do_test(code, node.PostfixUnaryExpression)
        self.assertEqual(2, len(result.suffixes))
        self.assertIsInstance(result.suffixes[1], node.NavigationSuffix)

    def test_parser_postfix_unary_expression_navigation_suffix_exception(self):
        codes = [
            ".-1",
            "?",
            "?.",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code, "parse_navigation_suffix")

    def test_parser_postfix_unary_expression_indexing_suffix(self):
        codes = [
            "a[0]",
            "A[x, y]",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.PostfixUnaryExpression)
                self.assertEqual(1, len(result.suffixes))
                self.assertIsInstance(result.suffixes[0], node.IndexingSuffix)

    def test_parser_postfix_unary_expression_indexing_suffix_trailing_comma(
            self):
        codes = [
            "a[0, ]",
            "A[x,\ny,\n\n]",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.PostfixUnaryExpression, False)
                self.assertEqual(1, len(result.suffixes))
                self.assertIsInstance(result.suffixes[0], node.IndexingSuffix)

    def test_parser_postfix_unary_expression_indexing_suffix_multilines(self):
        codes = [
            """\
a[
    0,
    1
    +
    2,
]""",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.PostfixUnaryExpression, False)
                self.assertEqual(1, len(result.suffixes))
                self.assertIsInstance(result.suffixes[0], node.IndexingSuffix)

    def test_parser_postfix_unary_expression_call_suffix(self):
        codes = [
            "lazy { Delegate() }",
            "lazy foo@{ Delegate() }",
            "foo<bar>(baz) @Annotated {}",
            "call()",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.PostfixUnaryExpression)
                self.assertEqual(1, len(result.suffixes))
                self.assertIsInstance(result.suffixes[0], node.CallSuffix)


class TestParserCallableReference(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.Expression:
        return super().do_test("parse_expression",
                               code,
                               node.Expression,
                               test_str=test_str)

    def test_parser_callable_reference(self):
        codes = [
            "::isOdd",
            "comparator::compare",
            "x::class",
            "a.b::class",
            "Nullable?::foo",
            "Generic<Arg>::foo",
            "Generic<Arg>()::foo",
            "this::foo",
            "(Parenthesized)::foo",
            "(ParenNullable)?::foo",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code)
                self.assertIsInstance(
                    result,
                    (node.CallableReference, node.PostfixUnaryExpression))
                if isinstance(result,
                              node.PostfixUnaryExpression) and result.suffixes:
                    self.assertEqual(result.suffixes[-1].operator, "::")


if __name__ == "__main__":
    unittest.main()
