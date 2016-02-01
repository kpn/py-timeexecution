import unittest

from time_execution.backends.base import BaseMetricsBackend


class TestBaseBackend(unittest.TestCase):
    def test_write_method(self):
        backend = BaseMetricsBackend()
        with self.assertRaises(NotImplementedError):
            backend.write('test')
