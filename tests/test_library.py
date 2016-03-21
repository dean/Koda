import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import pyItunes
except ImportError:
    from music import Library

    class MockLibrary(Library):
        """
        Define a MockLibrary class that lets us avoid the filesystem -
        without avoiding classic rap.
        """

        def find_audio_files(self, path):
            return (
                '2pac - California Love.mp3',
                'Wu-Tang Clan - C.R.E.A.M..mp3',
                'Mobb Deep - Shook Ones.mp3',
            )


    class LibraryTest(unittest.TestCase):
        """
        Unit tests for the Library class.
        """

        def setUp(self):
            self.library = MockLibrary('.')

        def test_equality(self):
            other = MockLibrary('.')
            self.assertEqual(self.library, other)

            other.songs['Ludacris'] = 'Act a Fool'
            self.assertNotEqual(self.library, other)

        def test_repr(self):
            expected = 'Library()'
            actual = str(self.library)
            self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
