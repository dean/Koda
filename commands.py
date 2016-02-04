import logging

from music import MusicPlayer


player = None

def music_player::
    global player
    player = MusicPlayer()
    player.play_music_as_available()
    return


lock = {}
def locked_command(f):
    def wrapped_f(*args, **kwargs):
        global lock
        lock_key = f.__name__
        if not lock.get(lock_key):
            lock[lock_key] = True
            f(*args)
            lock[lock_key] = False
    return wrapped_f


@locked_command()
def _download(title, artist):
    #FIXME: Use YoutubeDownloader API fool
    title = ' '.join(map(capitalize, title.split(' ')))
    artist = ' '.join(map(capitalize, artist.split(' ')))
    with open('../YoutubeDownloaderClient/songs.txt', 'w') as f:
        f.write('{0} --- {1}'.format(title, artist))
    res = os.system('cd ../YoutubeDownloaderClient && python3 download.py --file songs.txt --client-id AIzaSyDs-ONEG30OApiYc8SPNSB2uuqMb9OcX3s')
    if res == 0:
        logging.debug('Attempting to download {0} by {1} to {2}'.format(title, artist, '../YoutubeDownloader/downloads/{0} --- {1}'.format(artist, title)))
    return


@locked_command
def _stop_the_music():
    global player
    player.stop_all_music()
    return


@locked_command()
def _play_music(title, artist):
    global player
    player.play_song(title=title, artist=artist, extras=5)
    return


@locked_command
def _play_something_by_artist(artist):
    global player
    player.play_song(artist=artist)
    return


@locked_command
def _play_something_else():
    global player
    player.skip()
    return


@locked_command
def _play(title):
    global player
    player.play_song(title=title, limit=5)
    return

@locked_command
def _play_something():
    global player
    player.play_song(limit=5)
    return
