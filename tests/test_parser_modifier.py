from typing import Iterable
import unittest

from kopyt import Parser
from kopyt import node
from . import TestParserBase


class TestParserAnnotation(TestParserBase):
    def do_test(self,
                codes: Iterable[str],
                expected_type: type,
                test_str: bool = True) -> None:
        for code in codes:
            with self.subTest(code=code):
                expected_types = (node.Annotation, expected_type)
                super().do_test("parse_annotation",
                                code,
                                expected_types,
                                test_str=test_str)

    def test_parser_annotation_single(self):
        codes = [
            '@Inject',
            '@Ann(1)',
            '@Special("example")',
            '@Target(AnnotationTarget.FUNCTION)',
            '@AnnWithArrayMethod(names = ["abc", "foo", "bar"])',
            '@field:Ann',
            '@get:Ann(1)',
            '@param:Special("example")',
        ]
        self.do_test(codes, node.SingleAnnotation)

    def test_parser_annotation_multi(self):
        codes = [
            '@[Inject]',
            '@[Inject Ann]',
            '@[Ann(1)]',
            '@[Special("example") Ann(1)]',
            '@get:[Inject Ann(1)]',
        ]
        self.do_test(codes, node.MultiAnnotation)


class TestParserAnnotations(TestParserBase):
    def test_parser_annotations_empty(self):
        codes = (
            "fun foo",
            "open class bar",
        )
        for code in codes:
            with self.subTest(code=code):
                parser = Parser(code)
                result = parser.parse_annotations()
                self.assertEqual(0, len(result))

    def test_parser_annotations_single(self):
        codes = [
            '@Inject @Ann',
            '@get:Inject @Ann',
        ]
        for code in codes:
            parser = Parser(code)
            result = parser.parse_annotations()
            for annotation in result:
                self.assertIsInstance(annotation, node.SingleAnnotation)
            self.assertEqual(" ".join(map(str, result)), code)

    def test_parser_annotations_multi(self):
        codes = [
            '@[Inject] @[Ann]',
            '@[Inject Ann] @[Special("example")]',
        ]
        for code in codes:
            parser = Parser(code)
            result = parser.parse_annotations()
            for annotation in result:
                self.assertIsInstance(annotation, node.MultiAnnotation)
            self.assertEqual(" ".join(map(str, result)), code)

    def test_parser_annotations_with_modifiers(self):
        codes = [
            '@Inject enum',
            '@Inject override open',
        ]
        for code in codes:
            parser = Parser(code)
            result = parser.parse_modifiers()
            for annotation in result:
                self.assertIsInstance(annotation, (str, node.Annotation))
            self.assertEqual(" ".join(map(str, result)), code)

    def test_parser_annotations_with_modifiers_empty(self):
        codes = (
            "class foo",
            "fun bar",
        )
        for code in codes:
            with self.subTest(code=code):
                parser = Parser(code)
                result = parser.parse_modifiers()
                self.assertEqual(0, len(result))

    def test_parser_annotations_restricted_modifiers(self):
        codes = [
            'enum open',
            'abstract override',
        ]
        for code in codes:
            parser = Parser(code)
            result = parser.parse_modifiers(("override", ))
            self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
