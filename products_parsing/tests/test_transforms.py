import unittest

from products_parsing.transforms import apply_transform


class TransformTests(unittest.TestCase):
    def test_parse_bool_accepts_truthy_strings(self):
        self.assertTrue(apply_transform("parse_bool", "yes"))
        self.assertTrue(apply_transform("parse_bool", " TRUE "))

    def test_parse_bool_accepts_falsey_strings(self):
        self.assertFalse(apply_transform("parse_bool", "no"))
        self.assertFalse(apply_transform("parse_bool", "0"))

    def test_parse_bool_accepts_numeric(self):
        self.assertTrue(apply_transform("parse_bool", 1))
        self.assertFalse(apply_transform("parse_bool", 0))

    def test_parse_int_handles_numbers_and_strings(self):
        self.assertEqual(apply_transform("parse_int", 12), 12)
        self.assertEqual(apply_transform("parse_int", 12.7), 12)
        self.assertEqual(apply_transform("parse_int", "1,234"), 1234)
        self.assertIsNone(apply_transform("parse_int", ""))


if __name__ == "__main__":
    unittest.main()
