import datetime
import functools
import logging
import os
import random
import re
import subprocess
import sys
import time
import threading

import speech_recognition as sr

# Initialization
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) {%(funcName)s} %(message)s',)

lock = {}
song_queue = []
triggers = ['coda', 'koda', 'cota', 'toyota', 'tota', 'kona']


def capitalize(string):
    if not string:
        return ''

    f = string[0]
    minimum, maximum = ord('A'), ord('a')
    if minimum <= ord(f) < maximum:
        return string
    return chr(ord(f) - (maximum - minimum)) + string[1:]


def clean(string, chars=list('.()-_')):
    """Cleans a string of all characters we wish to ignore.

    @arg: string: String to clean
    """
    return functools.reduce(lambda original, ignore: original.replace(ignore, ''),
                  [string] + chars)


def _stop_the_music():
    global lock
    global song_queue
    logging.debug("Killing mpg321")
    song_queue = []
    try:
        lock['play music'] = False
        subprocess.check_call(['killall', 'mpg321'])
    except subprocess.CalledProcessError:
        pass
    finally:
        logging.debug("Killed mpg321")
        return


def any_matches(_spoken, triggers):
    matches = []
    for i, s_list in enumerate(_spoken):
        for s in s_list:
            for t in triggers:
                if s.lower().startswith(t):
                    matches.append(i)
    return matches


def clear_matches(_re):
    global spoken
    for i, spoke_list in enumerate(spoken):
        for spoke in spoke_list:
            matches = re.match(_re, spoke, flags=re.I)
            if matches:
                spoken[i] = ''


def parse_title_artist(s):
    s = s.lower()
    split = s.split(' by' )
    if len(split) == 1:
        return None
    return split


def _download(title, artist):
    global lock
    if lock.get('download'):
        return

    lock['download']= True
    title = ' '.join(map(capitalize, title.split(' ')))
    artist = ' '.join(map(capitalize, artist.split(' ')))
    with open('../YoutubeDownloaderClient/songs.txt', 'w') as f:
        f.write('{0} --- {1}'.format(title, artist))
    res = os.system('cd ../YoutubeDownloaderClient && python3 download.py --file songs.txt --client-id AIzaSyDs-ONEG30OApiYc8SPNSB2uuqMb9OcX3s')
    if res == 0:
        logging.debug('Attempting to download {0} by {1} to {2}'.format(title, artist, '../YoutubeDownloader/downloads/{0} --- {1}'.format(artist, title)))
    lock['download']= False
    return


def _play_music(title, artist):
    filenames = get_filename(title=title, artist=artist)
    queue_song(filename)
    return


def queue_song(filename):
    global song_queue
    if filename and not filename in song_queue:
        song_queue.append(filename)
    print('Song queue: {}'.format(song_queue))


def play_song(filename):
    global lock

    # Play the music
    lock['play music'] = True
    logging.debug("Playing {path}".format(path=filename))
    try:
        subprocess.check_call(['mpg321', filename, '--quiet'])
    except subprocess.CalledProcessError:
        logging.debug('mpg321 killed.')

    # Kill off mpg321
    try:
        subprocess.check_call(['killall', 'mpg321'])
        logging.debug("Stopping mpg321")
    except subprocess.CalledProcessError:
        pass
    lock['play music'] = False
    return


def _play_something_music(artist=None):
    global lock

    played_songs = []
    collisions = 0
    filenames = get_filename(artist=artist)
    if filenames:
        for filename in filenames:
            queue_song(filename)

    return


def _play_something_else():
     try:
        subprocess.check_call(['killall', 'mpg321'])
        logging.debug("Stopping mpg321")
     except subprocess.CalledProcessError:
        pass
     lock['play music'] = False
     return


def music_thread():
    global song_queue
    while True:
        while len(song_queue) > 0:
            print(song_queue)
            song = song_queue.pop()
            print('Playing %s' % song)
            play_song(song)

        time.sleep(0.15)
    return


# Listen for particular phrases
def listen_for_phrases():
    global lock
    global spoken
    time_heard = None
    while(True):
        time.sleep(0.15)  # So we don't do millions of iterations in succession...
        matches = any_matches(spoken, triggers)
        if not lock.get('koda') and matches:
            try:
                subprocess.check_call(['mpg321', 'alert.mp3'])
            except subprocess.CalledProcessError:
                print('Error... trying again')
                continue

            for i in matches:
                spoken[i] = ''

            time_heard = datetime.datetime.now()
            lock['koda'] = True

        if lock.get('koda') and (datetime.datetime.now() - time_heard).seconds >= 15:
            matches = any_matches(spoken, triggers)
            for i in matches:
                spoken[i] = ''

            print('Resetting...')
            lock['koda'] = False

        if not lock.get('koda'):
            continue

        phrases = [(re.compile(regex, flags=re.I), func) for regex, func in keyword_expressions]

        for i, user_said_options in enumerate(spoken):
            if not user_said_options:
                continue

            for user_said in user_said_options:
                for _re, func in phrases:
                    match = _re.match(user_said)
                    if match and match.groups():
                        print('Matched %s on %s' %( _re.pattern, user_said))
                        threading.Thread(target=func, args=match.groups()).start()
                        clear_matches(_re.pattern)
                        break
                    elif match:
                        print('Matched on %s' % user_said)
                        threading.Thread(target=func).start()
                        clear_matches(_re.pattern)
                        break


def get_filename(title=None, artist=None):
    init_path = '/Users/dean/Programming/YoutubeDownloaderClient/downloads/'
    songs = os.listdir(init_path)
    if artist:
        artist = artist.lower().strip()
        songs = filter(lambda song: song.lower().startswith(artist), songs)
        songs = list(songs)

        if title:
            matches = list(filter(lambda s: title in clean(s.lower()), songs))
            if not matches:
                print('Error... unable to parse from songs: {0}'.format(list(songs)))
                return None
            return os.path.join(init_path, sorted(matches, key=len)[0])

        if songs:
            print('Choices: \n\t{0}'.format('\n\t'.join(songs)))
            return map(lambda x: os.path.join(init_path, x), songs)
        return None

    if songs:
        return [os.path.join(init_path, random.choice(songs)) for _ in range(5)]

    return None


spoken = [''] * 10
def await_commands():
    threading.Thread(name='Listen for phrases', target=listen_for_phrases).start()
    threading.Thread(name='Music', target=music_thread).start()
    i = 1
    while(True):
        threading.Thread(name='Listener%d' % (i % 7), target=listen, args=(i % 7,)).start()
        time.sleep(2)
        i += 1


# Speech to text
def listen(index):
    global spoken
    MAX_WAIT = index + 5  # seconds
    logging.debug("Listening...")
    with sr.Microphone() as source:  # use the default microphone as the audio source
        try:
            r = sr.Recognizer()
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, MAX_WAIT)  # listen for the first phrase and extract it into audio data
            # print("Set minimum energy threshold to {}".format(r.energy_threshold))
            logging.debug("Got it! Now recognizing it...")
            values = r.recognize_google(audio, show_all=True)
            if values:
                print(values)
                spoken[index] = [x['transcript'] for x in values['alternative']]
        except (sr.UnknownValueError, sr.WaitTimeoutError, LookupError):  # speech is unintelligible
            # logging.debug("Oops! Didn't catch that or timed out.")
            spoken[index] = []
            return
    return


MUSIC_SOMETHING_ELSE_RE = r'play something else'
MUSIC_SOMETHING_ARTIST_RE = r'play (?:something|a song) by (.+)'
MUSIC_RE = r'play (.+) by (.+)'
MUSIC_SOMETHING_RE = r'play something$'
DOWNLOAD_RE = r'download (.+) by (.+)'
STOP_MUSIC_RE = r'stop(?: the)? music'
keyword_expressions = (
    (MUSIC_SOMETHING_ELSE_RE, _play_something_else),
    (MUSIC_SOMETHING_ARTIST_RE, _play_something_music),
    (MUSIC_RE, _play_music),
    (MUSIC_SOMETHING_RE, _play_something_music),
    (DOWNLOAD_RE, _download),
    (STOP_MUSIC_RE, _stop_the_music),
)


if __name__ == "__main__":
    await_commands()
    logging.shutdown()
