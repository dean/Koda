import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from helpers import clean


class TestClean(unittest.TestCase):
    """
    Unit tests for the clean function.
    """

    def test_clean(self):
        self.assertEqual('pyon', clean('python', ['t', 'h']))
        self.assertEqual('pyon', clean('python', 'th'))
        self.assertEqual('python', clean('python'))


if __name__ == '__main__':
    unittest.main()
