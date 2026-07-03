import unittest


def add(a, b):
    return a + b


def slugify(text):
    return text.strip().lower().replace(" ", "-")


class CalcTests(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(add(2, 2), 4)

    def test_addition_negative(self):
        self.assertEqual(add(-3, 1), -2)

    def test_slugify(self):
        self.assertEqual(slugify("  BWI Test Hub "), "bwi-test-hub")

    def test_slugify_idempotent(self):
        once = slugify("Hello World")
        self.assertEqual(slugify(once), once)
