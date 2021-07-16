import unittest

from kopyt.parser import Parser
from kopyt.exception import ParserException
from kopyt import node
from . import TestParserBase


class TestParserStatementBase(TestParserBase):
    def do_test(self,
                code: str,
                expected_type: node.Statement,
                test_str: bool = True) -> node.Statement:
        result: node.Statement = super().do_test("parse_statement", code,
                                                 node.Statement, test_str)
        self.assertIsInstance(result.statement, expected_type)
        return result

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_statement", code)


class TestParserStatement(TestParserStatementBase):
    def test_parser_statement_expecting_statement(self):
        code = "!"
        self.do_test_exception(code)

    def test_parser_statement_label(self):
        codes = ("label@ for (item in collection) { }", )
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.LoopStatement)
                self.assertTrue(1, len(result.labels))
                self.assertEqual("label@", str(result.labels[0]))

    def test_parser_statement_annotation(self):
        codes = ("@Annotation for (item in collection) { }", )
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.LoopStatement)
                self.assertTrue(1, len(result.annotations))
                self.assertEqual("@Annotation", str(result.annotations[0]))

    def test_parser_statement_label_annotation(self):
        codes = (
            "label@ @Annotated open class A",
            "@Annotated label@ open class A",
            "foo@ @Bar baz@ class B",
            "@Foo(1) bar@ @Baz class C",
        )
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.ClassDeclaration, False)
                self.assertTrue(len(result.labels) >= 1)
                self.assertTrue(len(result.annotations) >= 1)

    def test_parser_statement_declaration(self):
        codes = (
            "class A",
            "object B",
            "typealias A = B",
            "fun main() { }",
            "fun suspend() { }",
            "val C = 1",
        )
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code, node.Declaration)

    def test_parser_statement_loop(self):
        codes = (
            "for (item in collection) println(1)",
            "while (true) println(1)",
            "do println(1) while (true)",
        )
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code, node.LoopStatement)

    def test_parser_statement_assignment(self):
        codes = (
            "A = 1",
            "B += 1",
        )
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code, node.Assignment)

    def test_parser_statement_expression(self):
        codes = (
            "1",
            "true || false",
            "x.values().forEach { val x = y }",
            "object : Foo { }",
            "fun() { }",
            "fun (Int).() { }",
            "fun Foo<Bar>.() { }",
        )
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code, node.Expression)

    def test_parser_statement_multilines(self):
        codes = ("""\
println(
    foo
    (
1
+
2
    )
)
""", )
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code, node.Expression, False)


class TestParserBlock(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.Block:
        return super().do_test("parse_block",
                               code,
                               node.Block,
                               test_str=test_str)

    def test_parser_block(self):
        code = """\
{
    println(1)
    println(2)
}"""
        result = self.do_test(code)
        self.assertEqual(2, len(result))

    def test_parser_block_semicolon(self):
        code = """\
{
    println(1);
    println(2);
}"""
        result = self.do_test(code, False)
        self.assertEqual(2, len(result))


class TestParserSemi(unittest.TestCase):
    def test_parser_consume_semi(self):
        code = ";\n\n\n1"
        parser = Parser(code)
        parser._consume_semi()
        result = parser.parse_expression()
        self.assertEqual("1", str(result))

    def test_parser_consume_semi_non_optional(self):
        code = "1"
        parser = Parser(code)
        with self.assertRaises(ParserException):
            parser._consume_semi(optional=False)

    def test_parser_consume_semis(self):
        code = "\n;;\n;1"
        parser = Parser(code)
        parser._consume_semis()
        result = parser.parse_expression()
        self.assertEqual("1", str(result))

    def test_parser_consume_semis_non_optional(self):
        code = "1"
        parser = Parser(code)
        with self.assertRaises(ParserException):
            parser._consume_semis(optional=False)


if __name__ == "__main__":
    unittest.main()
