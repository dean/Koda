import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import pyItunes
except ImportError:
    from music import Song

    class SongTest(unittest.TestCase):
        """
        Unit tests for the Song class.
        """

        def setUp(self):
            self.title = 'Jessica'
            self.artist = 'The Allman Brothers'
            self.filename = 'The Allman Brothers - Jessica.mp3'
            self.song = Song(self.title, self.artist, self.filename)

        def test_from_file(self):
            song = Song.from_file(self.filename)
            self.assertEqual(song, self.song)

        def test_from_file_in_directory(self):
            song = Song.from_file(self.filename)
            self.assertEqual(song, self.song)

        def test_equality(self):
            other = Song.from_file('music/CCR - Suzie Q.mp3')
            self.assertNotEqual(self.song, other)

        def test_that_equality_ignores_ratings(self):
            other = Song.from_file(self.filename)
            other.rating = 99
            self.assertEqual(self.song, other)

        def test_that_equality_ignores_location(self):
            other = Song.from_file(self.filename)
            other.rating = 99
            self.assertEqual(self.song, other)

        def test_repr(self):
            expected = 'Song(name=Jessica artist=The Allman Brothers)'
            actual = str(self.song)
            self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
