import unittest

from kopyt import node
from . import TestParserBase


class TestParserTry(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.TryExpression:
        return super().do_test("parse_expression",
                               code,
                               node.TryExpression,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_expression", code)

    def test_parser_try(self):
        code = "try { } catch (e: Exception) { } finally { }"
        result = self.do_test(code)
        self.assertIsInstance(result.try_block, node.Block)
        self.assertEqual(1, len(result.catch_blocks))
        self.assertIsInstance(result.catch_blocks[0], node.CatchBlock)
        self.assertIsInstance(result.finally_block, node.FinallyBlock)

    def test_parser_try_multiple_catches(self):
        code = """\
try {
    println(1)
} catch (a: Exception1) {
    println(2)
} catch (b: Exception2) {
    println(3)
} finally {
    println(4)
}"""
        result = self.do_test(code)
        self.assertIsInstance(result.try_block, node.Block)
        self.assertEqual(2, len(result.catch_blocks))
        self.assertIsInstance(result.catch_blocks[0], node.CatchBlock)
        self.assertIsInstance(result.catch_blocks[1], node.CatchBlock)
        self.assertIsInstance(result.finally_block, node.FinallyBlock)

    def test_parser_try_without_finally(self):
        code = """\
try {
    println(1)
} catch (a: Exception1) {
    println(2)
}"""
        result = self.do_test(code)
        self.assertIsInstance(result.try_block, node.Block)
        self.assertEqual(1, len(result.catch_blocks))
        self.assertIsInstance(result.catch_blocks[0], node.CatchBlock)
        self.assertIsNone(result.finally_block)

    def test_parser_try_without_catch(self):
        code = """\
try {
    println(1)
} finally {
    println(2)
}"""
        result = self.do_test(code)
        self.assertIsInstance(result.try_block, node.Block)
        self.assertEqual(0, len(result.catch_blocks))
        self.assertIsInstance(result.finally_block, node.FinallyBlock)

    def test_parser_try_expecting_try_block(self):
        code = "try"
        self.do_test_exception(code)

    def test_parser_try_expecting_catch_or_finally_block(self):
        code = "try { }"
        self.do_test_exception(code)

    def test_parser_try_multiple_try_blocks(self):
        code = "try { } try { } finally { }"
        self.do_test_exception(code)


class TestParserTryCatchBlock(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.CatchBlock:
        return super().do_test("parse_catch_block",
                               code,
                               node.CatchBlock,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_catch_block", code)

    def test_parser_catch_block(self):
        code = "catch (e: Exception) { }"
        result = self.do_test(code)
        self.assertEqual("e", result.name)
        self.assertEqual("Exception", str(result.type))

    def test_parser_try_catch_block_trailing_comma(self):
        code = """catch
(e: Exception
,)
{ }
"""
        result = self.do_test(code, False)
        self.assertEqual("e", result.name)
        self.assertEqual("Exception", str(result.type))

    def test_parser_try_catch_block_annotations(self):
        code = "catch (@[Inject] e: Exception) { }"
        result = self.do_test(code)
        self.assertEqual(1, len(result.annotations))
        self.assertEqual(result.name, "e")
        self.assertEqual(str(result.type), "Exception")

    def test_parser_try_catch_block_expecting_parenthesis(self):
        code = "catch { }"
        self.do_test_exception(code)

    def test_parser_try_catch_block_expecting_type(self):
        code = "catch () { }"
        self.do_test_exception(code)

    def test_parser_try_catch_block_expecting_name(self):
        code = "catch (Exception) { }"
        self.do_test_exception(code)

    def test_parser_try_catch_block_expecting_colon(self):
        code = "catch (Exception a) { }"
        self.do_test_exception(code)


class TestParserTryFinallyBlock(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.FinallyBlock:
        return super().do_test("parse_finally_block",
                               code,
                               node.FinallyBlock,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_finally_block", code)

    def test_parser_try_finally_block(self):
        code = "finally { }"
        self.do_test(code)

    def test_parser_try_finally_block_newlines(self):
        code = """\
finally
{

}"""
        self.do_test(code, False)

    def test_parser_try_finally_block_expecting_block(self):
        code = "finally"
        self.do_test_exception(code)


if __name__ == "__main__":
    unittest.main()
