import unittest

from kopyt import Parser
from kopyt import node
from . import TestParserBase


class TestParserShebangLine(TestParserBase):
    def do_test(self, code: str) -> node.ShebangLine:
        result = super().do_test("parse_shebang_line", code, node.ShebangLine,
                                 False)
        self.assertEqual(code.rstrip(), str(result))
        return result

    def test_parser_shebang_line_basic(self):
        code = "#!/bin/sh\n"
        result = self.do_test(code)
        self.assertEqual(code.rstrip(), result.value)

    def test_parser_shebang_line_space(self):
        code = "#!/usr/bin/env kotlinc -script\r\n"
        result = self.do_test(code)
        self.assertEqual(code.rstrip(), result.value)


class TestParserPackageHeader(TestParserBase):
    def do_test(self, code: str) -> node.PackageHeader:
        result = super().do_test("parse_package_header", code,
                                 node.PackageHeader, False)
        self.assertEqual(code.rstrip().rstrip(";"), str(result))
        return result

    def test_parser_package_header_basic(self):
        code = "package a"
        result = self.do_test(code)
        self.assertEqual("a", result.name)

    def test_parser_package_header_subpackage(self):
        code = "package a.b.c;\n"
        result = self.do_test(code)
        self.assertEqual("a.b.c", result.name)


class TestParserImportHeader(TestParserBase):
    def do_test(self, code: str) -> node.ImportHeader:
        result = super().do_test("parse_import_header", code,
                                 node.ImportHeader, False)
        self.assertEqual(code.rstrip().rstrip(";"), str(result))
        return result

    def test_parser_import_header_basic(self):
        code = "import a"
        result = self.do_test(code)
        self.assertEqual("a", result.name)
        self.assertFalse(result.wildcard)
        self.assertIsNone(result.alias)

    def test_parser_import_header_subpackage(self):
        code = "import a.b;"
        result = self.do_test(code)
        self.assertEqual("a.b", result.name)
        self.assertFalse(result.wildcard)
        self.assertIsNone(result.alias)

    def test_parser_import_header_wildcard(self):
        code = "import a.b.*\n"
        result = self.do_test(code)
        self.assertEqual("a.b", result.name)
        self.assertTrue(result.wildcard)
        self.assertIsNone(result.alias)

    def test_parser_import_header_alias(self):
        code = "import a.b as c;\n"
        result = self.do_test(code)
        self.assertEqual("a.b", result.name)
        self.assertFalse(result.wildcard)
        self.assertEqual("c", result.alias)

    def test_parser_import_list(self):
        parser = Parser("""\
import a
import a.b;

import a.b.*


// comment
import a.b as c
""")
        result = parser.parse_import_list()
        self.assertEqual(len(result), 4)


if __name__ == "__main__":
    unittest.main()
