import unittest

class TestConfig(unittest.TestCase):
    def test_force_fail(self):
        self.assertEqual(False, True)