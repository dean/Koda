from collections import defaultdict
import random
import time
import subprocess


import config
from helpers import clean

try:
    from pyItunes import *
except ImportError: # Windows
    import os
    import taglib

    class Song(object):
        def __init__(self, name, artist, location, rating=100):
            self.name = name
            self.artist = artist
            self.location = location
            self.rating = rating

    class Library(object):
        def __init__(self, path):
            self.songs = {}
            for file_path in os.listdir(path):
                if not file_path.endswith('.mp3'):
                    continue

                full_file_path = os.path.join(path, file_path)
                name, artist = self.get_name_and_artist(file_path)
                if name and artist:
                    self.songs[artist] = Song(name, artist, full_file_path)

        def get_name_and_artist(self, path):
            try:
                artist, title = path.split(' - ')
                return title.strip(), artist.strip()
            except:
                print('More than one "-" was found in {0} so it was skipped.'.format(path))
                return None, None

class MusicPlayer(object):
    currently_playing = None

    def __init__(self):
        library = Library(config.EXPORTED_ITUNES_LIBRARY)
        self.songs = [song for _, song in library.songs.items()]
        self.artists = defaultdict(list)
        self.queue = []
        for song in self.songs:
            if not song.location:
                continue

            song.location = '/' + song.location if not song.location.startswith('/') else song.location
            self.artists[song.artist].append(song)

    def _play(self, filename):
        try:
            output = subprocess.check_output(['mpg321', filename, '--quiet'])
        except subprocess.CalledProcessError:
            logging.debug('mpg321 killed.')
        finally:
            return

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
            if len(self.queue) == 0:
                time.sleep(0.15)
                continue

            next_song = self.queue.pop(0)
            print('Now playing {0} by {1}'.format(next_song.name, next_song.artist))
            if len(self.queue) > 0:
                print('Up next: {0} by {1}'.format(self.queue[0].name, self.queue[0].artist))
            self._play(next_song.location)
        return

    def skip(self):
        self.stop_music()
        return

    def stop_music(self):
        try:
             # Kill off mpg321
            subprocess.check_call(['killall', 'mpg321'])
            logging.debug("Stopping mpg321")
        except subprocess.CalledProcessError:
            pass
        finally:
            return

    def stop_all_music(self):
        self.queue = []
        self.stop_music()
        return
