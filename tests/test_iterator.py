import unittest

from kopyt.iterator import PeekableIterator


class TestPeekableIterator(unittest.TestCase):
    def setUp(self) -> None:
        self.N = 10
        self.default = None
        self.iterator = PeekableIterator(range(0, self.N),
                                         default=self.default)

    def test_iterator_last(self) -> None:
        n = next(self.iterator)
        self.assertEqual(n, self.iterator.last)

    def test_iterator_iter_next(self) -> None:
        iterator = iter(self.iterator)
        self.assertEqual(next(iterator), 0)

    def test_iterator_next_after_peek(self) -> None:
        self.iterator.peek()
        self.assertEqual(next(self.iterator), 0)

    def test_iterator_peek(self) -> None:
        self.assertEqual(self.iterator.peek(), 0)
        for i in range(self.N):
            self.assertEqual(self.iterator.peek(i), i)
        self.assertEqual(self.iterator.peek(self.N + 1), self.default)

    def test_iterator_with_context(self) -> None:
        self.assertEqual(next(self.iterator), 0)
        with self.iterator:
            next(self.iterator)
        self.assertEqual(next(self.iterator), 2)

    def test_iterator_with_context_nested(self) -> None:
        self.assertEqual(next(self.iterator), 0)
        with self.iterator:
            with self.iterator:
                next(self.iterator)
            next(self.iterator)
        self.assertEqual(next(self.iterator), 3)

    def test_iterator_with_context_error_raised(self) -> None:
        self.assertEqual(next(self.iterator), 0)
        try:
            with self.iterator:
                next(self.iterator)
                raise Exception
        except Exception:
            pass
        self.assertEqual(next(self.iterator), 1)

    def test_iterator_with_context_error_raised_nested(self) -> None:
        self.assertEqual(0, next(self.iterator))
        with self.iterator:
            try:
                with self.iterator:
                    self.assertEqual(1, next(self.iterator))
                    self.assertEqual(2, next(self.iterator))
                    raise Exception
            except Exception:
                pass
            self.assertEqual(1, next(self.iterator))
            self.assertEqual(2, next(self.iterator))
        self.assertEqual(3, next(self.iterator))

    def test_iterator_simulate(self) -> None:
        self.assertEqual(next(self.iterator), 0)
        with self.iterator.simulate():
            next(self.iterator)
            next(self.iterator)
            next(self.iterator)
        self.assertEqual(next(self.iterator), 1)


if __name__ == "__main__":
    unittest.main()
