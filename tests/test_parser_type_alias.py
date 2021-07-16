import unittest

from kopyt import node
from . import TestParserBase


class TestParserTypeAlias(TestParserBase):
    def do_test(self, code) -> node.TypeAlias:
        return super().do_test("parse_declaration", code, node.TypeAlias)

    def test_parser_type_alias_basic(self):
        code = "typealias A = B"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("A", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertEqual("B", str(result.type))

    def test_parser_type_alias_modifiers(self):
        code = "private @Annotated typealias A = B"
        result = self.do_test(code)
        self.assertEqual(2, len(result.modifiers))
        self.assertEqual("A", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertEqual("B", str(result.type))

    def test_parser_type_alias_generic(self):
        code = "typealias Predicate<T> = (T) -> Boolean"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Predicate", result.name)
        self.assertIsNotNone(result.generics)
        self.assertEqual("<T>", str(result.generics))
        self.assertEqual("(T) -> Boolean", str(result.type))


if __name__ == "__main__":
    unittest.main()
