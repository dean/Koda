import logging
import time

from koda import clear_matches_for_func_name
from music import MusicPlayer


def music_player():
    player = MusicPlayer()
    globals()['player'] = player
    player.play_music_as_available()
    return


def locked_command(f):
    def wrapped_f(*args, **kwargs):
        lock, spoken = kwargs['lock'], kwargs['spoken']
        lock_key = f.__name__
        if not lock.get(lock_key):
            lock[lock_key] = True
            stall = f(*args)
            if stall:
                clear_matches_for_func_name(f.__name__, spoken)
                time.sleep(5)
                clear_matches_for_func_name(f.__name__, spoken)
            lock[lock_key] = False
    return wrapped_f


@locked_command
def _download(title, artist):
    #FIXME: Use YoutubeDownloader API fool
    title = ' '.join(map(capitalize, title.split(' ')))
    artist = ' '.join(map(capitalize, artist.split(' ')))
    with open('../YoutubeDownloaderClient/songs.txt', 'w') as f:
        f.write('{0} --- {1}'.format(title, artist))
    success = os.system('cd ../YoutubeDownloaderClient && python3 download.py --file songs.txt --client-id AIzaSyDs-ONEG30OApiYc8SPNSB2uuqMb9OcX3s')
    if success == 0:
        logging.debug('Attempting to download {0} by {1} to {2}'.format(title, artist, '../YoutubeDownloader/downloads/{0} --- {1}'.format(artist, title)))
    return


@locked_command
def _stop_the_music():
    global player
    player.stop_all_music()
    return


@locked_command
def _play_music(title, artist):
    global player
    success = player.play_song(title=title, artist=artist, extras=5)
    if success:
        return True
    return False


@locked_command
def _play_something_by_artist(artist):
    global player
    success = player.play_song(artist=artist)
    if success:
        return True
    return False


@locked_command
def _play_something_else():
    global player
    if len(player.queue) == 0:
        player.play_song(limit=3)
    else:
        player.skip()
    return True


@locked_command
def _play(title):
    global player
    success = player.play_song(title=title, limit=5)
    if success:
        return True
    return False


@locked_command
def _play_something():
    global player
    player.play_song(limit=5)
    time.sleep(5)
    return True
