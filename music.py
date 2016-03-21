from collections import defaultdict
import random
import time
import subprocess


from helpers import clean

try:
    from pyItunes import *
except ImportError: # Windows
    import os

    class Song(object):
        def __init__(self, name, artist, location, rating=100):
            self.name = name
            self.artist = artist
            self.location = location
            self.rating = rating

        @classmethod
        def from_file(cls, path):
            """
            Return the Song object that corresponds to a file on disk.
            """

            try:
                artist, title = os.path.basename(path).split(' - ')
                title, _ = os.path.splitext(title)
            except ValueError:
                error = 'Could not create song from file: {}...'.format(path)
                raise ValueError(error)

            if not artist or not title:
                error = 'Could not find a metadata for: {}...'.format(path)
                raise ValueError(error)

            return cls(title, artist, path)

        def __eq__(self, other):
            us = (self.name, self.artist)
            them = (other.name, other.artist)
            return us == them

        def __repr__(self):
            """
            Returns the string representation of a Song object.

            We do not include information about the location or rating of
            the song in the interest of brevity and readability, as we are
            usually interested in the song name and artist.
            """
            return 'Song(name={0.name} artist={0.artist})'.format(self)


    class Library(object):
        def __init__(self, path):
            self.songs = self.find_songs(path)

        def find_songs(self, path):
            """
            Return a dict of songs found in :path:
            Key: artist
            Value: Song object
            """
            songs = {}

            for songfile in self.find_audio_files(path):
                song = Song.from_file(songfile)
                songs[song.artist] = song

            return songs


        def find_audio_files(self, path):
            return [songfile for songfile in os.listdir(path) if songfile.endswith('.mp3')]

        def __eq__(self, other):
            return self.songs == other.songs

        def __ne__(self, other):
            return not self == other

        def __repr__(self):
            """
            Returns the string representation of a Library object.

            We do not print the songs dict in the interest of brevity
            and readability, since a library could contain many songs.
            """
            return 'Library()'.format(self)


class MusicPlayer(object):
    currently_playing = None

    def __init__(self):
        import config

        self.library = Library(config.EXPORTED_ITUNES_LIBRARY)
        self.artists = defaultdict(list)

        # FIXME: Since we pop from both sides, we should consider using a
        # collections.deque
        self.queue = []
        for song in self.songs:
            if not song.location:
                continue

            song.location = '/' + song.location if not song.location.startswith('/') else song.location
            self.artists[song.artist].append(song)

    @property
    def songs(self):
        return self.library.values()

    def _play(self, filename):
        try:
            output = subprocess.check_output(['mpg321', filename, '--quiet'])
        except subprocess.CalledProcessError:
            logging.debug('mpg321 killed.')

    def play_song(self, title=None, artist=None,  limit=1000):
        #FIXME: Future Functions for simplicity
        # if title and artist
        # if title and not artist
        # if artist and not title
        # if not title and not artist
        random.seed()

        if artist:
            for key in self.artists.keys():
                # If we match an artist name
                if not key:
                    continue

                if clean(artist.lower()) in clean(key.lower()):
                    # If we match a title
                    if title:
                        title_match = list(filter(lambda x: clean(title.lower()) in clean(x.name.lower()), self.artists[key]))
                        if title_match:
                            self.queue = title_match + self.queue
                            self.stop_music()
                            return True
                    else:
                        songs = self.artists[key]
                        random.shuffle(songs)
                        self.queue = songs[:limit] + self.queue
                        self.stop_music()
                        return True

        if title:
            exact_title_match = list(filter(lambda x: clean(title.lower()) == clean(x.name.lower()), self.songs))
            title_match = list(sorted(filter(lambda x: clean(title.lower()) == clean(x.name.lower()), self.songs), key=lambda x: len(x.name)))
            if exact_title_match:
                self.queue = [exact_title_match[0]]+ self.queue
                self.stop_music()
                return True
            elif title_match:
                self.queue = [random.choice(title_match)]+ self.queue
                self.stop_music()
                return True

        if not title and not artist:
            songs = []
            rated_songs = list(filter(lambda x: x.rating and x.rating >= 60, self.songs))
            random.shuffle(rated_songs)
            self.queue = rated_songs[:limit] + self.queue
            self.stop_music()

        return False

    def play_music_as_available(self):
        while True:
            if not self.queue:
                time.sleep(0.15)
                continue

            next_song = self.queue.pop(0)
            print('Now playing {0.name} by {0.artist}'.format(next_song))
            if self.queue:
                print('Up next: {0.name} by {0.artist}'.format(self.queue[0]))
            self._play(next_song.location)

    def skip(self):
        self.stop_music()

    def stop_music(self):
        try:
             # Kill off mpg321
            subprocess.check_call(['killall', 'mpg321'])
            logging.debug("Stopping mpg321")
        except subprocess.CalledProcessError:
            pass

    def stop_all_music(self):
        self.queue = []
        self.stop_music()

