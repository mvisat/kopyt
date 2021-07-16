import unittest

from kopyt import node
from . import TestParserBase


class TestParserVariable(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.VariableDeclaration:
        return super().do_test("parse_variable_declaration",
                               code,
                               node.VariableDeclaration,
                               test_str=test_str)

    def test_parser_variable(self):
        code = "a"
        result = self.do_test(code)
        self.assertEqual(0, len(result.annotations))
        self.assertEqual("a", result.name)
        self.assertIsNone(result.type)

    def test_parser_variable_type(self):
        code = "a: Int"
        result = self.do_test(code)
        self.assertEqual(0, len(result.annotations))
        self.assertEqual("a", result.name)
        self.assertIsNotNone(result.type)
        self.assertEqual("Int", str(result.type))

    def test_parser_variable_annotations(self):
        code = "@Annotated a: Int"
        result = self.do_test(code)
        self.assertEqual(1, len(result.annotations))
        self.assertEqual("a", result.name)
        self.assertIsNotNone(result.type)
        self.assertEqual("Int", str(result.type))


class TestParserMultiVariable(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.MultiVariableDeclaration:
        return super().do_test("parse_multi_variable_declaration",
                               code,
                               node.MultiVariableDeclaration,
                               test_str=test_str)

    def test_parser_multi_variable(self):
        code = "(a)"
        result = self.do_test(code)
        self.assertEqual(1, len(result))
        self.assertEqual(0, len(result[0].annotations))
        self.assertEqual("a", result[0].name)
        self.assertIsNone(result[0].type)

    def test_parser_multi_variable_trailing_comma(self):
        code = """\
(
    a,
)"""
        result = self.do_test(code, False)
        self.assertEqual(1, len(result))
        self.assertEqual(0, len(result[0].annotations))
        self.assertEqual("a", result[0].name)
        self.assertIsNone(result[0].type)

    def test_parser_multi_variable_multiple(self):
        code = "(a, b: Int)"
        result = self.do_test(code)
        self.assertEqual(2, len(result))
        self.assertEqual(0, len(result[0].annotations))
        self.assertEqual("a", result[0].name)
        self.assertIsNone(result[0].type)
        self.assertEqual("b", result[1].name)
        self.assertIsNotNone(result[1].type)
        self.assertEqual("Int", str(result[1].type))


if __name__ == "__main__":
    unittest.main()
