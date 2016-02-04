from functools import defaultdict
import random

from helpers import clean

from pyItunes import *


class MusicPlayer(object):
    currently_playing = None
    queue = []

    def __init__(self):
        library = Library('/Users/dean/Documents/Library-New.xml')
        self.songs = [song for _, song in library.songs.items()]
        self.artists = defaultdict(list)
        for song in self.songs:
            self.artists[song_obj.artist].append(song)

    def _play(self, filename):
        try:
            subprocess.check_call(['mpg321', filename, '--quiet'])
        except subprocess.CalledProcessError:
            logging.debug('mpg321 killed.')
        finally:
            return

    def play_song(self, title=None, artist=None,  limit=1000, front=False, back=False, extras=0):
        if artist:
            for key in self.artists.keys():
                # If we match an artist name
                if clean(artist.lower()) in clean(key.lower()):
                    # If we match a title
                    if title:
                        title_match = list(filter(lambda x: clean(title.lower()) in clean(x.name.lower()), self.artists[key]))
                        if title_match:
                            queue = [title_match.location] + queue
                            self.stop_music()
                            return
                    else:
                        queue = [song.location for song in self.artists[key]][:limit] + queue
                        self.stop_music()
                        return

        if title:
            title_match = list(filter(lambda x: clean(title.lower()) in clean(x.name.lower()), self.songs))
            if title_match:
                queue = [title_match.location][:limit] + queue
                self.stop_music()
                return

        if not title and not artist:
            songs = []
            rated_songs = list(filter(lambda x: x.rating and x.rating >= 60, self.songs))
            for x in xrange(limit):
                songs.append(rated_songs.pop(random.random % len(rated_songs)))
            queue = songs + queue
            self.stop_music()

    def play_music_as_available(self):
        while True:
            if len(queue) == 0:
                time.sleep(0.15)
                continue

            next_song = queue.pop()
            print('Playing {name} by {artist}'.format(next_song.name, next_song.artist)
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
        queue = []
        self.stop_music()
        return
