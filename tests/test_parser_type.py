import unittest

from kopyt import node
from . import TestParserBase


class TestParserFunctionType(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.FunctionType:
        result: node.Type = super().do_test("parse_type",
                                            code,
                                            node.Type,
                                            test_str=test_str)
        fun_type: node.FunctionType = result.subtype
        self.assertIsInstance(fun_type, node.FunctionType)
        return fun_type

    def test_parser_function_type(self):
        code = "() -> Unit"
        result = self.do_test(code)
        self.assertIsNone(result.receiver)
        self.assertEqual(0, len(result.parameters))
        self.assertEqual("Unit", str(result.type))

    def test_parser_function_type_annotations(self):
        codes = (
            "@Ann () -> Unit",
            "@Ann\n()\n->\nUnit",
            "@Ann() () -> Unit",
            "@Ann()\n()\n->\nUnit",
            "@Ann(foo()) () -> Unit",
            "@Ann(foo())\n()\n->\nUnit",
        )
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, False)
                self.assertIsNone(result.receiver)
                self.assertEqual(0, len(result.parameters))
                self.assertEqual("Unit", str(result.type))

    def test_parser_function_type_single_parameter(self):
        code = "(Int) -> Int"
        result = self.do_test(code)
        self.assertIsNone(result.receiver)
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("Int", str(result.parameters[0]))
        self.assertEqual("Int", str(result.type))

    def test_parser_function_type_multi_parameters(self):
        code = "(Int, Int) -> Int"
        result = self.do_test(code)
        self.assertIsNone(result.receiver)
        self.assertEqual(2, len(result.parameters))
        self.assertEqual("Int", str(result.parameters[0]))
        self.assertEqual("Int", str(result.parameters[1]))
        self.assertEqual("Int", str(result.type))

    def test_parser_function_type_nested(self):
        code = "() -> () -> Int"
        result = self.do_test(code)
        self.assertIsNone(result.receiver)
        self.assertEqual(0, len(result.parameters))
        self.assertEqual("() -> Int", str(result.type))

    def test_parser_function_type_receiver(self):
        code = "Int.(Int) -> String"
        result = self.do_test(code)
        self.assertIsNotNone(result.receiver)
        self.assertEqual("Int", str(result.receiver))
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("Int", str(result.parameters[0]))
        self.assertEqual("String", str(result.type))

    def test_parser_function_type_annotation(self):
        code = "suspend (Int) -> Int"
        result = self.do_test(code)
        self.assertIsNone(result.receiver)
        self.assertEqual(1, len(result.parameters))
        self.assertEqual("Int", str(result.parameters[0]))
        self.assertEqual("Int", str(result.type))


class TestParserNullableType(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.NullableType:
        result: node.Type = super().do_test("parse_type",
                                            code,
                                            node.Type,
                                            test_str=test_str)
        null_type: node.NullableType = result.subtype
        self.assertIsInstance(null_type, node.NullableType)
        return null_type

    def test_parser_nullable_type(self):
        code = "A?"
        result = self.do_test(code)
        self.assertEqual("A", str(result.subtype))
        self.assertEqual("?", result.nullable)

    def test_parser_nullable_type_multiple(self):
        code = "B???"
        result = self.do_test(code)
        self.assertEqual("B", str(result.subtype))
        self.assertEqual("???", result.nullable)

    def test_parser_nullable_type_annotations(self):
        codes = (
            "@Composable (() -> Unit)?",
            "@Composable() (() -> Unit)?",
            "@Composable () (() -> Unit)?",
        )
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, False)
                self.assertEqual("(() -> Unit)?", str(result))


class TestParserTypeReference(TestParserBase):
    def do_test(self, code) -> node.TypeReference:
        result: node.Type = super().do_test("parse_type", code, node.Type)
        type_ref: node.TypeReference = result.subtype
        self.assertIsInstance(type_ref, node.TypeReference)
        return type_ref

    def test_parser_type_reference(self):
        code = "A"
        result = self.do_test(code)
        self.assertEqual("A", str(result.subtype))

    def test_parser_type_reference_dynamic(self):
        code = "dynamic"
        result = self.do_test(code)
        self.assertEqual("dynamic", str(result.subtype))

    def test_parser_type_reference_generic(self):
        code = "List<T>"
        result = self.do_test(code)
        self.assertEqual("List<T>", str(result.subtype))


class TestParserParenthesizedType(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.ParenthesizedType:
        result: node.Type = super().do_test("parse_type",
                                            code,
                                            node.Type,
                                            test_str=test_str)
        par_type: node.ParenthesizedType = result.subtype
        self.assertIsInstance(par_type, node.ParenthesizedType)
        return par_type

    def test_parser_parenthesized_type_annotations(self):
        codes = (
            "@Ann (() -> Unit)",
            "@Ann\n(()\n->\nUnit)",
            "@Ann() (() -> Unit)",
            "@Ann()\n(()\n->\nUnit)",
            "@Ann(foo()) (() -> Unit)",
            "@Ann(foo())\n(()\n->\nUnit)",
        )
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, False)
                self.assertEqual("(() -> Unit)", str(result))

    def test_parser_parenthesized_type_of_nullable_type(self):
        code = "(A?)"
        result = self.do_test(code)
        self.assertIsInstance(result.subtype.subtype, node.NullableType)
        self.assertEqual("A?", str(result.subtype.subtype))

    def test_parser_parenthesized_type_of_function_type(self):
        code = "(() -> () -> Unit)"
        result = self.do_test(code)
        self.assertIsInstance(result.subtype.subtype, node.FunctionType)
        self.assertEqual("() -> () -> Unit", str(result.subtype.subtype))

    def test_parser_parenthesized_type_of_type_reference(self):
        code = "(List<T>)"
        result = self.do_test(code)
        self.assertIsInstance(result.subtype.subtype, node.TypeReference)
        self.assertEqual("List<T>", str(result.subtype.subtype))

    def test_parser_parenthesized_type_of_parenthesized_type(self):
        code = "((A?))"
        result = self.do_test(code)
        self.assertIsInstance(result.subtype.subtype, node.ParenthesizedType)
        self.assertEqual("(A?)", str(result.subtype.subtype))


class TestParserReceiverType(TestParserBase):
    def do_test(self, code) -> node.ReceiverType:
        return super().do_test("parse_receiver_type", code, node.ReceiverType)

    def test_parser_receiver_type_modifiers(self):
        code = "@Annotation A?"
        result = self.do_test(code)
        self.assertEqual(1, len(result.modifiers))
        self.assertIsInstance(result.subtype, node.NullableType)
        self.assertEqual("A?", str(result.subtype))

    def test_parser_receiver_type_of_nullable_type(self):
        code = "A?"
        result = self.do_test(code)
        self.assertIsInstance(result.subtype, node.NullableType)
        self.assertEqual("A?", str(result.subtype))

    def test_parser_receiver_type_of_type_reference(self):
        code = "Foo<X>.Bar<Y>"
        result = self.do_test(code)
        self.assertIsInstance(result.subtype, node.TypeReference)
        self.assertEqual("Foo<X>.Bar<Y>", str(result.subtype))

    def test_parser_receiver_type_of_parenthesized_type(self):
        code = "(A?)"
        result = self.do_test(code)
        self.assertIsInstance(result.subtype, node.ParenthesizedType)
        self.assertEqual("(A?)", str(result.subtype))


if __name__ == "__main__":
    unittest.main()
