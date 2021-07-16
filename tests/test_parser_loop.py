import unittest

from kopyt import node
from . import TestParserBase


class TestParserLoopBase(TestParserBase):
    def do_test(self, code: str,
                expected: node.LoopStatement) -> node.WhileStatement:
        expected_types = (node.LoopStatement, expected)
        return super().do_test("parse_loop_statement", code, expected_types)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_loop_statement", code)


class TestParserLoop(TestParserLoopBase):
    def test_parser_loop_expecting_loop(self):
        code = "if (true) 1 else 0"
        self.do_test_exception(code)


class TestParserFor(TestParserLoopBase):
    def do_test(self, code: str) -> node.ForStatement:
        return super().do_test(code, node.ForStatement)

    def test_parser_for(self):
        code = "for (item in collection) println(item)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.annotations))
        self.assertIsInstance(result.variable, node.VariableDeclaration)
        self.assertEqual("item", str(result.variable))
        self.assertEqual("collection", str(result.container))
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.Statement)

    def test_parser_for_block(self):
        code = """\
for (item in collection) {
    println(item)
}"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.annotations))
        self.assertIsInstance(result.variable, node.VariableDeclaration)
        self.assertEqual("item", str(result.variable))
        self.assertEqual("collection", str(result.container))
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.Block)

    def test_parser_for_without_body(self):
        code = "for (item in collection);"
        result = self.do_test(code)
        self.assertEqual(0, len(result.annotations))
        self.assertIsInstance(result.variable, node.VariableDeclaration)
        self.assertEqual("item", str(result.variable))
        self.assertEqual("collection", str(result.container))
        self.assertIsNone(result.body)

    def test_parser_for_multi_variable(self):
        code = "for ((a, b) in collection);"
        result = self.do_test(code)
        self.assertEqual(0, len(result.annotations))
        self.assertIsInstance(result.variable, node.MultiVariableDeclaration)
        self.assertEqual("(a, b)", str(result.variable))
        self.assertEqual("collection", str(result.container))
        self.assertIsNone(result.body)

    def test_parser_for_annotations(self):
        code = "for (@Annotated item in collection);"
        result = self.do_test(code)
        self.assertEqual(1, len(result.annotations))
        self.assertIsInstance(result.variable, node.VariableDeclaration)
        self.assertEqual("item", str(result.variable))
        self.assertEqual("collection", str(result.container))
        self.assertIsNone(result.body)

    def test_parser_for_expecting_variable(self):
        code = "for (int i = 0; i < 10; i++) println(i)"
        self.do_test_exception(code)


class TestParserWhile(TestParserLoopBase):
    def do_test(self, code: str) -> node.WhileStatement:
        return super().do_test(code, node.WhileStatement)

    def test_parser_while(self):
        code = "while (true) println(1)"
        result = self.do_test(code)
        self.assertEqual("true", str(result.condition))
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.Statement)

    def test_parser_while_block(self):
        code = """\
while (true) {
    println(item)
}"""
        result = self.do_test(code)
        self.assertEqual("true", str(result.condition))
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.Block)

    def test_parser_while_without_body(self):
        code = "while (true);"
        result = self.do_test(code)
        self.assertEqual("true", str(result.condition))
        self.assertIsNone(result.body)

    def test_parser_while_expecting_condition(self):
        code = "while()"
        self.do_test_exception(code)

    def test_parser_while_expecting_body(self):
        code = "while(true)"
        self.do_test_exception(code)


class TestParserDoWhile(TestParserLoopBase):
    def do_test(self, code: str) -> node.DoWhileStatement:
        return super().do_test(code, node.DoWhileStatement)

    def test_parser_do_while(self):
        code = "do println(1) while (true)"
        result = self.do_test(code)
        self.assertEqual("true", str(result.condition))
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.Statement)

    def test_parser_do_while_block(self):
        code = """\
do {
    println(item)
} while (true)"""
        result = self.do_test(code)
        self.assertEqual("true", str(result.condition))
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.Block)

    def test_parser_do_while_without_body(self):
        code = "do while (true)"
        result = self.do_test(code)
        self.assertEqual("true", str(result.condition))
        self.assertIsNone(result.body)

    def test_parser_do_while_expecting_condition(self):
        code = "do println(1)"
        self.do_test_exception(code)

    def test_parser_do_while_expecting_body(self):
        code = "do while()"
        self.do_test_exception(code)


if __name__ == "__main__":
    unittest.main()
