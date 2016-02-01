import unittest

from tests.conftest import Dummy, fqn_test


class TestFQN(unittest.TestCase):

    def test_fqn(self):
        self.assertEqual(fqn_test.fqn, 'tests.conftest.fqn_test')
        self.assertEqual(Dummy.fqn, 'tests.conftest.Dummy')
        self.assertEqual(Dummy().go.fqn, 'tests.conftest.Dummy.go')
