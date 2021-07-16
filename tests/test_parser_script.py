import unittest

from kopyt import node
from . import TestParserBase


class TestParserScript(TestParserBase):
    def do_test(self, code: str, test_str: bool = True) -> node.Script:
        return super().do_test("parse_script",
                               code,
                               node.Script,
                               test_str=test_str)

    def test_parser_script_basic(self):
        code = """\
package main

import a

println("Hello, world!")"""
        result = self.do_test(code)
        self.assertIsNone(result.shebang)
        self.assertEqual(0, len(result.annotations))
        self.assertIsNotNone(result.package)
        self.assertEqual(1, len(result.imports))
        self.assertEqual(1, len(result.statements))

    def test_parser_script_shebang(self):
        code = """\
#!/usr/bin/env kotlinc -script

package main

println("Hello, world!")"""
        result = self.do_test(code)
        self.assertIsNotNone(result.shebang)
        self.assertEqual(0, len(result.annotations))
        self.assertIsNotNone(result.package)
        self.assertEqual(0, len(result.imports))
        self.assertEqual(1, len(result.statements))

    def test_parser_script_annotations(self):
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
        self.assertEqual(1, len(result.statements))

    def test_parser_script_imports(self):
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
        self.assertEqual(0, len(result.statements))


if __name__ == "__main__":
    unittest.main()
