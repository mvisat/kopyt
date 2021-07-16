import unittest

from kopyt import node
from . import TestParserBase


class TestParserWhen(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.WhenExpression:
        return super().do_test("parse_expression", code, node.WhenExpression,
                               test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_expression", code)

    def test_parser_when(self):
        code = """\
when (x) {
    1 -> println("x == 1")
    2 -> println("x == 2")
    is String -> foo()
    is Int -> bar()
    else -> {
        println("x is neither 1 nor 2")
    }
}"""
        result = self.do_test(code)
        self.assertIsNotNone(result.subject)
        self.assertEqual(len(result.entries), 5)

    def test_parser_when_without_subject(self):
        code = """\
when {
    true -> println("true")
    false -> println("false")
}"""
        result = self.do_test(code)
        self.assertIsNone(result.subject)
        self.assertEqual(len(result.entries), 2)

    def test_parser_when_one_line(self):
        code = 'when (x) { 1 -> println("x == 1") 2 -> println("x == 2") else -> println("x is neither 1 nor 2") }'
        result = self.do_test(code, False)
        self.assertIsNotNone(result.subject)
        self.assertEqual(len(result.entries), 3)

    def test_parser_when_with_semicolon(self):
        code = """when(x) { 1 -> println("x == 1"); 2 -> println("x == 2"); else -> println("x is neither 1 nor 2");
}"""
        result = self.do_test(code, False)
        self.assertIsNotNone(result.subject)
        self.assertEqual(len(result.entries), 3)

    def test_parser_when_with_if_expression_without_else(self):
        code = """\
when {
    x -> if (true) { }
    else -> true
}"""
        result = self.do_test(code, False)
        self.assertIsNone(result.subject)
        self.assertEqual(len(result.entries), 2)

    def test_parser_when_expecting_entry(self):
        code = 'when(x) { 1 -> true;; else -> false }'
        self.do_test_exception(code)


class TestParserWhenSubject(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.WhenSubject:
        return super().do_test("parse_when_subject", code, node.WhenSubject,
                               test_str)

    def test_parser_when_subject(self):
        code = "(x)"
        result = self.do_test(code)
        self.assertIsNone(result.declaration)
        self.assertEqual("x", str(result.value))

    def test_parser_when_subject_declaration(self):
        code = "(val x = f())"
        result = self.do_test(code)
        self.assertIsNotNone(result.declaration)
        self.assertEqual("x", str(result.declaration))
        self.assertEqual("f()", str(result.value))

    def test_parser_when_subject_declaration_annotations(self):
        code = "(@Annotated val x = f())"
        result = self.do_test(code)
        self.assertEqual(1, len(result.annotations))
        self.assertIsNotNone(result.declaration)
        self.assertEqual("x", str(result.declaration))
        self.assertEqual("f()", str(result.value))


class TestParserWhenEntry(TestParserBase):
    def do_test(self,
                code: str,
                expected_type: node.WhenEntry,
                test_str: bool = True) -> node.WhenEntry:
        expected_types = (node.WhenEntry, expected_type)
        return super().do_test("parse_when_entry", code, expected_types,
                               test_str)

    def test_parser_when_entry(self):
        code = "in 1 .. 10 -> true"
        result: node.WhenConditionEntry = self.do_test(code,
                                                       node.WhenConditionEntry)
        self.assertEqual(1, len(result.conditions))
        self.assertIsNotNone(result.body)

    def test_parser_when_entry_multiple(self):
        code = "in 1 .. 10, is String, 1 -> true"
        result: node.WhenConditionEntry = self.do_test(code,
                                                       node.WhenConditionEntry)
        self.assertEqual(3, len(result.conditions))
        self.assertIsNotNone(result.body)

    def test_parser_when_entry_multiple_trailing_comma(self):
        code = "in 1 .. 10, is String,\n\n-> true"
        result: node.WhenConditionEntry = self.do_test(code,
                                                       node.WhenConditionEntry,
                                                       False)
        self.assertEqual(2, len(result.conditions))
        self.assertIsNotNone(result.body)

    def test_parser_when_entry_else(self):
        code = "else -> true"
        result: node.WhenElseEntry = self.do_test(code, node.WhenElseEntry)
        self.assertIsNotNone(result.body)

    def test_parser_when_entry_with_block(self):
        codes = [
            "1 ->{\n}",
            "else -> { }",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.WhenEntry, False)
                self.assertIsInstance(result.body, node.Block)


class TestParserWhenCondition(TestParserBase):
    def do_test(self,
                code: str,
                expected_type: node.WhenCondition,
                test_str: bool = True) -> node.WhenCondition:
        return super().do_test("parse_when_condition", code, expected_type,
                               test_str)

    def test_parser_when_condition_in(self):
        code = "in 1..10"
        self.do_test(code, node.RangeTest, False)

    def test_parser_when_condition_not_in(self):
        code = "!in 1..10"
        self.do_test(code, node.RangeTest, False)

    def test_parser_when_condition_is(self):
        code = "is String"
        self.do_test(code, node.TypeTest)

    def test_parser_when_condition_not_is(self):
        code = "!is String"
        self.do_test(code, node.TypeTest)

    def test_parser_when_condition_expression(self):
        code = "true"
        self.do_test(code, node.Expression)


class TestParserRangeTest(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.RangeTest:
        return super().do_test("parse_range_test", code, node.RangeTest,
                               test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_range_test", code)

    def test_parser_range_test_in(self):
        code = "in 1..10"
        result = self.do_test(code, False)
        self.assertEqual("in", result.operator)
        self.assertEqual("1 .. 10", str(result.operand))

    def test_parser_range_test_in_variable(self):
        code = "in validNumbers"
        result = self.do_test(code, False)
        self.assertEqual("in", result.operator)
        self.assertEqual("validNumbers", str(result.operand))

    def test_parser_range_test_not_in(self):
        code = "!in 1..10"
        result = self.do_test(code, False)
        self.assertEqual("!in", result.operator)
        self.assertEqual("1 .. 10", str(result.operand))

    def test_parser_range_test_not_in_variable(self):
        code = "!in validNumbers"
        result = self.do_test(code, False)
        self.assertEqual("!in", result.operator)
        self.assertEqual("validNumbers", str(result.operand))

    def test_parser_range_test_expecting_expr(self):
        codes = [
            "in ->",
            "!in ->",
            "a",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)


class TestParserTypeTest(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.TypeTest:
        return super().do_test("parse_type_test", code, node.TypeTest,
                               test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_type_test", code)

    def test_parser_type_test_is(self):
        code = "is String"
        result = self.do_test(code)
        self.assertEqual("is", result.operator)
        self.assertEqual("String", str(result.operand))

    def test_parser_type_test_is_newlines(self):
        code = "is\n\nString"
        result = self.do_test(code, False)
        self.assertEqual("is", result.operator)
        self.assertEqual("String", str(result.operand))

    def test_parser_type_test_not_is(self):
        code = "!is String"
        result = self.do_test(code)
        self.assertEqual("!is", result.operator)
        self.assertEqual("String", str(result.operand))

    def test_parser_type_test_not_is_newlines(self):
        code = "!is\n\nString"
        result = self.do_test(code, False)
        self.assertEqual("!is", result.operator)
        self.assertEqual("String", str(result.operand))

    def test_parser_type_test_expecting_type(self):
        codes = [
            "is 1..10",
            "!is 1..10",
            "a",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)


if __name__ == "__main__":
    unittest.main()
