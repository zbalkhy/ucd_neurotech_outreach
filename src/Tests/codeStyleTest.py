import unittest


class TestStyle(unittest.TestCase):
    def test_clean_style_1(self):
        """Check coding style"""
        with open(r"pycodestyle_report.txt", 'r') as f_open:
            lines = f_open.readlines()
        print('Style checker output for the working folder:')
        print(lines)
        self.assertEqual(len(lines), 0)
