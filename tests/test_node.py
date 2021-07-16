import unittest

from kopyt.node import Node, Nodes, Position


class TestNodes(unittest.TestCase):
    def setUp(self) -> None:
        self.position = Position(1, 1)
        self.sequence = [Node(self.position)] * 10
        self.nodes = Nodes(self.position, self.sequence)

    def test_nodes_len(self):
        self.assertEqual(len(self.sequence), len(self.nodes))

    def test_nodes_getitem(self):
        for i in range(len(self.sequence)):
            self.assertEqual(self.sequence[i], self.nodes[i])

    def test_nodes_iter(self):
        for expected, actual in zip(self.sequence, self.nodes):
            self.assertEqual(expected, actual)

    def test_nodes_contains(self):
        for node in self.sequence:
            self.assertIn(node, self.nodes)


if __name__ == "__main__":
    unittest.main()
