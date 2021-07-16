import unittest

from kopyt import node
from . import TestParserBase


class TestParserAssignment(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.Assignment:
        return super().do_test("parse_assignment",
                               code,
                               node.Assignment,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_assignment", code)

    def test_parser_assignment(self):
        code = "a = b"
        result = self.do_test(code)
        assignable: node.DirectlyAssignableExpression = result.assignable
        self.assertIsInstance(assignable, node.DirectlyAssignableExpression)
        self.assertEqual("=", result.operator)
        self.assertEqual("b", str(result.value))

    def test_parser_assignment_parenthesized(self):
        code = "(a) = b"
        result = self.do_test(code)
        assignable: node.ParenthesizedDirectlyAssignableExpression = result.assignable
        self.assertIsInstance(assignable,
                              node.ParenthesizedDirectlyAssignableExpression)
        self.assertEqual("=", result.operator)
        self.assertEqual("b", str(result.value))

    def test_parser_assignment_suffix(self):
        code = "a[0] = b"
        result = self.do_test(code)
        assignable: node.DirectlyAssignableExpression = result.assignable
        self.assertIsInstance(assignable, node.DirectlyAssignableExpression)
        self.assertEqual("=", result.operator)

    def test_parser_assignment_safe(self):
        code = "x?.y[0] = z"
        result = self.do_test(code)
        assignable: node.DirectlyAssignableExpression = result.assignable
        self.assertIsInstance(assignable, node.DirectlyAssignableExpression)
        self.assertEqual("x?.y[0]", str(assignable))
        self.assertEqual("=", result.operator)

    def test_parser_assignment_and(self):
        operators = ('+=', '-=', '*=', '/=', '%=')
        for operator in operators:
            code = f"a {operator} 1"
            with self.subTest(code=code):
                result = self.do_test(code)
                self.assertEqual(operator, result.operator)

    def test_parser_assignment_and_parenthesized(self):
        operators = ('+=', '-=', '*=', '/=', '%=')
        for operator in operators:
            code = f"(a) {operator} 1"
            with self.subTest(code=code):
                result = self.do_test(code)
                self.assertEqual(operator, result.operator)

    def test_parser_assignment_expecting_assignment(self):
        codes = [
            "a + 1",
            "a >= 1",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)

    def test_parser_assignment_expecting_assignable_suffix(self):
        codes = (
            "foo() = 1",
            "foo<bar>() = 1",
            "foo().filter { it.length > 0 } = 1",
        )
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)


if __name__ == "__main__":
    unittest.main()
