import unittest

from lbaf.Model.lbsMessage import Message


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.msg = Message(1, "something")

    def test_message_initialization_001(self):
        self.assertEqual(self.msg._Message__round, 1)
        self.assertEqual(self.msg._Message__content, "something")

    def test_object_repr(self):
        self.assertEqual(str(self.msg), "Message round: 1, Content: something")

    def test_message_get_round(self):
        self.assertEqual(self.msg.get_round(), 1)

    def test_message_get_content(self):
        self.assertEqual(self.msg.get_content(), "something")


if __name__ == '__main__':
    unittest.main()
