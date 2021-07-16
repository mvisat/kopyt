import unittest

from kopyt import node
from . import TestParserBase


class TestParserFunction(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.FunctionDeclaration:
        return super().do_test("parse_declaration",
                               code,
                               node.FunctionDeclaration,
                               test_str=test_str)

    def test_parser_function(self):
        code = "fun double(x: Int): Int { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("double", result.name)
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("x: Int", str(result.parameters[0]))
        self.assertEqual("Int", str(result.type))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_annotation(self):
        code = "override fun double(x: Int): Int { }"
        result = self.do_test(code)
        self.assertEqual(1, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("double", result.name)
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("x: Int", str(result.parameters[0]))
        self.assertEqual("Int", str(result.type))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_without_body(self):
        code = "fun double()"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("double", result.name)
        self.assertEqual(0, len(result.parameters))
        self.assertIsNone(result.type)
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_function_body_semi(self):
        code = "fun double(x: Int): Int {;}"
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("double", result.name)
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("x: Int", str(result.parameters[0]))
        self.assertEqual("Int", str(result.type))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_with_expression(self):
        code = "fun foo() = 1"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("foo", result.name)
        self.assertEqual(0, len(result.parameters))
        self.assertIsNone(result.type)
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_trailing_comma(self):
        code = """\
fun powerOf(
    number: Int,
    exponent: Int, // trailing comma
) { }"""
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("powerOf", result.name)
        self.assertEqual(2, len(result.parameters))
        self.assertEqual("number: Int", str(result.parameters[0]))
        self.assertEqual("exponent: Int", str(result.parameters[1]))
        self.assertIsNone(result.type)
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_default_arguments(self):
        code = """\
fun read(
    b: ByteArray,
    off: Int = 0,
    len: Int = b.size,
) { }"""
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("read", result.name)
        self.assertEqual(3, len(result.parameters))
        self.assertEqual("b: ByteArray", str(result.parameters[0]))
        self.assertEqual("off: Int = 0", str(result.parameters[1]))
        self.assertEqual("len: Int = b.size", str(result.parameters[2]))
        self.assertIsNone(result.type)
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_generic(self):
        code = "fun <T> asList(vararg ts: T): List<T> { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertIsNotNone(result.generics)
        self.assertEqual("<T>", str(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("asList", result.name)
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("vararg ts: T", str(result.parameters[0]))
        self.assertIsNotNone(result.type)
        self.assertEqual("List<T>", str(result.type))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_generic_constraint(self):
        code = "fun <T> asList(vararg ts: T): List<T> where T : CharSequence { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertIsNotNone(result.generics)
        self.assertEqual("<T>", str(result.generics))
        self.assertIsNone(result.receiver)
        self.assertEqual("asList", result.name)
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("vararg ts: T", str(result.parameters[0]))
        self.assertIsNotNone(result.type)
        self.assertEqual("List<T>", str(result.type))
        self.assertIsNotNone(result.constraints)
        self.assertEqual("where T : CharSequence", str(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_receiver(self):
        code = "fun <T> MutableList<T>.swap(index1: Int, index2: Int) { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertIsNotNone(result.generics)
        self.assertEqual("<T>", str(result.generics))
        self.assertIsNotNone(result.receiver)
        self.assertEqual("MutableList<T>", str(result.receiver))
        self.assertEqual("swap", result.name)
        self.assertEqual(2, len(result.parameters))
        self.assertIsNone(result.type)
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_nullable_receiver(self):
        code = "fun Any?.toString(): String { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.receiver)
        self.assertEqual("Any?", str(result.receiver))
        self.assertEqual("toString", result.name)
        self.assertEqual(0, len(result.parameters))
        self.assertIsNotNone(result.type)
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_function_parenthesized_receiver(self):
        code = "fun (A.B.C).toString(): String { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.receiver)
        self.assertEqual("(A.B.C)", str(result.receiver))
        self.assertEqual("toString", result.name)
        self.assertEqual(0, len(result.parameters))
        self.assertIsNotNone(result.type)
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)


if __name__ == "__main__":
    unittest.main()
