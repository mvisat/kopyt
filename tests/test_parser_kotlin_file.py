import unittest

from kopyt import node
from . import TestParserBase


class TestParserKotlinFile(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.KotlinFile:
        return super().do_test("parse",
                               code,
                               node.KotlinFile,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse", code)

    def test_parser_kotlin_file_basic(self):
        code = """\
package main

import a

fun main() {
    println("Hello, world!")
}"""
        result = self.do_test(code)
        self.assertIsNone(result.shebang)
        self.assertEqual(0, len(result.annotations))
        self.assertIsNotNone(result.package)
        self.assertEqual(1, len(result.imports))
        self.assertEqual(1, len(result.declarations))

    def test_parser_kotlin_file_shebang(self):
        code = """\
#!/usr/bin/env kotlinc

package main

fun main() {
    println("Hello, world!")
}"""
        result = self.do_test(code)
        self.assertIsNotNone(result.shebang)
        self.assertEqual(0, len(result.annotations))
        self.assertIsNotNone(result.package)
        self.assertEqual(0, len(result.imports))
        self.assertEqual(1, len(result.declarations))

    def test_parser_kotlin_file_annotations(self):
        code = """\
@file:JvmName("Foo")

fun main() {
    println("Hello, world!")
}"""
        result = self.do_test(code)
        self.assertIsNone(result.shebang)
        self.assertEqual(1, len(result.annotations))
        self.assertIsNone(result.package)
        self.assertEqual(0, len(result.imports))
        self.assertEqual(1, len(result.declarations))

    def test_parser_kotlin_file_imports(self):
        code = """\
package main

import a
import a.b
import a.b.*
import a.b.c as d"""
        result = self.do_test(code)
        self.assertIsNone(result.shebang)
        self.assertEqual(0, len(result.annotations))
        self.assertIsNotNone(result.package)
        self.assertEqual(4, len(result.imports))
        self.assertEqual(0, len(result.declarations))

    def test_parser_kotlin_file_expecting_declaration(self):
        code = "println(1)"
        self.do_test_exception(code)


if __name__ == "__main__":
    unittest.main()
