from collections import defaultdict
import random
import time
import subprocess

from helpers import clean

from pyItunes import *


class MusicPlayer(object):
    currently_playing = None

    def __init__(self):
        library = Library('/Users/dean/Documents/Library-New.xml')
        self.songs = [song for _, song in library.songs.items()]
        self.artists = defaultdict(list)
        self.queue = []
        for song in self.songs:
            if not song.location:
                continue

            song.location = '/' + song.location
            self.artists[song.artist].append(song)

    def _play(self, filename):
        try:
            output = subprocess.check_output(['mpg321', filename, '--quiet'])
        except subprocess.CalledProcessError:
            logging.debug('mpg321 killed.')
        finally:
            return

    def play_song(self, title=None, artist=None,  limit=1000, front=False, back=False, extras=0):
        #FIXME: Future Functions for simplicity
        # if title and artist
        # if title and not artist
        # if artist and not title
        # if not title and not artist
        random.seed(123456)

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
                        self.queue = self.artists[key][:limit] + self.queue
                        self.stop_music()
                        return True

        if title:
            title_match = list(filter(lambda x: clean(title.lower()) in clean(x.name.lower()), self.songs))
            if title_match:
                self.queue = [random.choice(title_match)]+ self.queue
                self.stop_music()
                return True

        if not title and not artist:
            songs = []
            rated_songs = list(filter(lambda x: x.rating and x.rating >= 60, self.songs))
            for x in range(limit):
                songs.append(rated_songs.pop(int(random.random()) % len(rated_songs)))
            self.queue = songs + self.queue
            self.stop_music()

        return False

    def play_music_as_available(self):
        while True:
            if len(self.queue) == 0:
                time.sleep(0.15)
                continue

            next_song = self.queue.pop()
            print('Playing {0} by {1}'.format(next_song.name, next_song.artist))
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
