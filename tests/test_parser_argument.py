import unittest

from kopyt import node
from . import TestParserBase


class TestParserValueArgument(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.ValueArguments:
        result = super().do_test("parse_value_arguments",
                                 code,
                                 node.ValueArguments,
                                 test_str=test_str)
        for arg in result:
            self.assertIsInstance(arg, node.ValueArgument)
        return result

    def test_parser_value_argument(self):
        code = "(1)"
        result = self.do_test(code)
        self.assertEqual(1, len(result))

    def test_parser_value_argument_multiple(self):
        code = "(1, 2)"
        result = self.do_test(code)
        self.assertEqual(2, len(result))

    def test_parser_value_argument_trailing_comma(self):
        code = "(1, 2, )"
        result = self.do_test(code, False)
        self.assertEqual(2, len(result))

    def test_parser_value_argument_annotation(self):
        code = "(@A 1, @B 2)"
        result = self.do_test(code)
        for arg in result:
            self.assertIsNotNone(arg.annotation)

    def test_parser_value_argument_name(self):
        code = "(1, b = 2)"
        result = self.do_test(code)
        self.assertEqual(2, len(result))
        self.assertIsNone(result[0].name)
        self.assertEqual("1", str(result[0].value))
        self.assertEqual("b", result[1].name)
        self.assertEqual("2", str(result[1].value))

    def test_parser_value_argument_spread(self):
        code = "(a, *b)"
        result = self.do_test(code)
        self.assertEqual(2, len(result))
        self.assertFalse(result[0].spread)
        self.assertTrue(result[1].spread)

    def test_parser_value_argument_name_spread(self):
        code = "(a, b = *c)"
        result = self.do_test(code)
        self.assertEqual(2, len(result))
        self.assertIsNone(result[0].name)
        self.assertEqual("a", str(result[0].value))
        self.assertFalse(result[0].spread)
        self.assertEqual("b", result[1].name)
        self.assertEqual("c", str(result[1].value))
        self.assertTrue(result[1].spread)

    def test_parser_value_argument_multilines(self):
        code = """\
(
1 to 2,
2
to
3,
)"""
        result = self.do_test(code, False)
        self.assertEqual(2, len(result))
        self.assertIsNone(result[0].name)
        self.assertEqual("1 to 2", str(result[0].value))
        self.assertEqual("2 to 3", str(result[1].value))


class TestParserTypeArgument(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.TypeArguments:
        return super().do_test("parse_type_arguments",
                               code,
                               node.TypeArguments,
                               test_str=test_str)

    def test_parser_type_argument_projections(self):
        codes = [
            "<*>",
            "<*, String>",
            "<in Nothing, String>",
            "<Int, *>",
            "<Int, out Any?>",
            "<*, *>",
            "<in Nothing, out Any?>",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code)

    def test_parser_type_argument_trailing_comma(self):
        codes = [
            "<*,\n>",
            "<*,\n\nString,\n\n>",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code, False)


class TestParserTypeProjection(TestParserBase):
    def do_test(self,
                code: str,
                expected_type: type,
                test_str: bool = True) -> node.Node:
        expected_types = (node.TypeProjection, expected_type)
        return super().do_test("parse_type_projection",
                               code,
                               expected_types,
                               test_str=test_str)

    def test_parser_type_projection_star(self):
        code = "*"
        self.do_test(code, node.TypeProjectionStar)

    def test_parser_type_projection_with_type(self):
        code = "out T"
        self.do_test(code, node.TypeProjectionWithType)


if __name__ == "__main__":
    unittest.main()
