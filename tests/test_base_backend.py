import unittest

from time_execution.backends.base import BaseMetricsBackend


class TestBaseBackend(unittest.TestCase):
    def test_write_method(self):
        backend = BaseMetricsBackend()
        with self.assertRaises(NotImplementedError):
            backend.write("test")

    def test_bulk_write(self):
        backend = BaseMetricsBackend()
        with self.assertRaises(NotImplementedError):
            backend.bulk_write([])
