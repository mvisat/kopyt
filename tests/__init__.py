from typing import Any, Iterable, Union
import unittest

from kopyt import Parser
from kopyt import node
from kopyt.exception import ParserException

__all__ = ["TestParserBase"]


class TestParserBase(unittest.TestCase):
    def do_test(self,
                parse_func: str,
                code: str,
                expected_types: Union[type, Iterable[type]],
                test_str: bool = True,
                **kwargs: Any) -> node.Node:
        parser = Parser(code)
        self.assertTrue(hasattr(parser, parse_func))
        parse_func = getattr(parser, parse_func)
        result: node.Node = parse_func(**kwargs)

        try:
            iter(expected_types)
        except TypeError:
            expected_types = (expected_types, )

        for expected_type in expected_types:
            self.assertIsInstance(result, expected_type)

        if test_str:
            self.assertEqual(code, str(result))

        return result

    def do_test_exception(self, parse_func: str, code: str,
                          **kwargs: Any) -> None:
        parser = Parser(code)
        self.assertTrue(hasattr(parser, parse_func))
        parse_func = getattr(parser, parse_func)
        with self.assertRaises(ParserException):
            parse_func(**kwargs)
