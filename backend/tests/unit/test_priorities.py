import unittest

from backend.app.scheduling.priorities import get_priority_value


class TestPriorities(unittest.TestCase):

    def test_low_priority(self):
        self.assertEqual(get_priority_value("low"), 1)

    def test_normal_priority(self):
        self.assertEqual(get_priority_value("normal"), 2)

    def test_high_priority(self):
        self.assertEqual(get_priority_value("high"), 3)

    def test_urgent_priority(self):
        self.assertEqual(get_priority_value("urgent"), 4)

    def test_invalid_priority(self):
        with self.assertRaises(ValueError):
            get_priority_value("critical")

    def test_uppercase_priority(self):
        self.assertEqual(get_priority_value("URGENT"), 4)


if __name__ == "__main__":
    unittest.main()