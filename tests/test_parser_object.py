import unittest

from kopyt import node
from . import TestParserBase


class TestParserObject(TestParserBase):
    def do_test(self, code: str) -> node.ObjectDeclaration:
        expected_types = (node.Declaration, node.ObjectDeclaration)
        return super().do_test("parse_declaration", code, expected_types)

    def test_parser_object(self):
        code = "object A"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("A", result.name)
        self.assertEqual(0, len(result.supertypes))
        self.assertIsNone(result.body)

    def test_parser_object_modifiers(self):
        code = "private object A"
        result = self.do_test(code)
        self.assertEqual(1, len(result.modifiers))
        self.assertEqual("A", result.name)
        self.assertEqual(0, len(result.supertypes))
        self.assertIsNone(result.body)

    def test_parser_object_body(self):
        code = "object A { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("A", result.name)
        self.assertEqual(0, len(result.supertypes))
        self.assertIsNotNone(result.body)

    def test_parser_object_supertype(self):
        code = """\
object DefaultListener : MouseAdapter() {
    override fun mouseClicked(e: MouseEvent) { }
}"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("DefaultListener", result.name)
        self.assertIsNotNone(result.supertypes)
        self.assertEqual(1, len(result.supertypes))
        self.assertEqual("MouseAdapter()", str(result.supertypes[0]))
        self.assertIsNotNone(result.body)


if __name__ == "__main__":
    unittest.main()
