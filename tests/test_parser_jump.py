import unittest

from kopyt import node
from . import TestParserBase


class TestParserJump(TestParserBase):
    def do_test(self,
                code: str,
                expected_type: type,
                test_str: bool = True) -> node.JumpExpression:
        expected_types = (node.JumpExpression, expected_type)
        return super().do_test("parse_jump_expression",
                               code,
                               expected_types,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_jump_expression", code)

    def test_parser_jump_expecting_jump(self):
        code = "1"
        self.do_test_exception(code)

    def test_parser_jump_throw(self):
        code = "throw Exception"
        result: node.ThrowExpression = self.do_test(code, node.ThrowExpression)
        self.assertEqual("Exception", str(result.expression))

    def test_parser_jump_return(self):
        code = "return"
        result: node.ReturnExpression = self.do_test(code,
                                                     node.ReturnExpression)
        self.assertIsNone(result.label)

    def test_parser_jump_return_label(self):
        code = "return@label"
        result: node.ReturnExpression = self.do_test(code,
                                                     node.ReturnExpression)
        self.assertIsNotNone(result.label)
        self.assertIsNotNone("label", str(result.label))
        self.assertIsNone(result.expression)

    def test_parser_jump_return_expression(self):
        code = "return 1"
        result: node.ReturnExpression = self.do_test(code,
                                                     node.ReturnExpression)
        self.assertIsNone(result.label)
        self.assertIsNotNone(result.expression)
        self.assertEqual("1", str(result.expression))

    def test_parser_jump_return_expression_label(self):
        code = "return@label 1"
        result: node.ReturnExpression = self.do_test(code,
                                                     node.ReturnExpression)
        self.assertIsNotNone(result.label)
        self.assertIsNotNone(result.expression)
        self.assertEqual("label", str(result.label))
        self.assertEqual("1", str(result.expression))

    def test_parser_jump_continue(self):
        code = "continue"
        result: node.ContinueExpression = self.do_test(code,
                                                       node.ContinueExpression)
        self.assertIsNone(result.label)

    def test_parser_jump_continue_label(self):
        code = "continue@label"
        result: node.ContinueExpression = self.do_test(code,
                                                       node.ContinueExpression)
        self.assertIsNotNone(result.label)
        self.assertEqual("label", str(result.label))

    def test_parser_jump_break(self):
        code = "break"
        result: node.BreakExpression = self.do_test(code, node.BreakExpression)
        self.assertIsNone(result.label)

    def test_parser_jump_break_label(self):
        code = "break@label"
        result: node.BreakExpression = self.do_test(code, node.BreakExpression)
        self.assertIsNotNone(result.label)
        self.assertEqual("label", str(result.label))


if __name__ == "__main__":
    unittest.main()
