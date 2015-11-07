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
r = sr.Recognizer()
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) {%(funcName)s} %(message)s',)
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

# Stop programming music
def stop_the_music():
    logging.debug("Killing mpg321")
    try:
        subprocess.check_call(['killall', 'mpg321'])
    except subprocess.CalledProcessError:
        pass
    finally:
        logging.debug("Killed mpg321")
        return


def any_matches(_spoken, triggers):
    matches = []
    for i, s in enumerate(_spoken):
        for t in triggers:
            if s.lower().startswith(t):
                matches.append(i)
    return matches


def clear_matches(_re):
    global spoken
    for i, spoke in enumerate(spoken):
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


lock = {}
def _play_music(title, artist):
    global lock

    filename = get_filename(title=title, artist=artist)
    if not filename or lock.get('play music'):
        return

    lock['play music'] = True
    logging.debug("Playing {path}".format(path=filename))
    try:
        subprocess.check_call(['mpg321', filename, '--quiet'])
        subprocess.check_call(['killall', 'mpg321'])
        logging.debug("Stopping mpg321")
    except subprocess.CalledProcessError:
        logging.debug('mpg321 killed.')
    finally:
        lock['play music'] = False
        return


def _play_something_music(artist=None):
    global lock

    played_songs = []
    collisions = 0
    while True:
        filename = get_filename(artist=artist)
        if collisions >= 5:
            print('Exhausted all/most options for %s ' % artist)
            return

        if filename in played_songs:
            collisions += 1
            continue

        if not filename or lock.get('play music'):
            return

        played_songs.append(filename)
        lock['play music'] = True
        logging.debug("Playing {path}".format(path=filename))
        try:
            subprocess.check_call(['mpg321', filename, '--quiet'])
        except subprocess.CalledProcessError:
            logging.debug('mpg321 killed.')
            return

        try:
            subprocess.check_call(['killall', 'mpg321'])
            logging.debug("Stopping mpg321")
        except subprocess.CalledProcessError:
            pass
        finally:
            lock['play music'] = False
        print('Continuing after playing "something".')

    return



download_locked = False
# Listen for particular phrases
def listen_for_phrases():
    global lock
    global spoken
    time_heard = None
    while(True):
        time.sleep(0.15)  # So we don't do millions of iterations in succession...
        matches = any_matches(spoken, triggers)
        if not lock.get('koda') and matches:
            for i in matches:
                spoken[i] = ''
            print(matches)
            print(spoken)
            print('Triggered!')
            subprocess.check_call(['mpg321', 'alert.mp3'])
            time_heard = datetime.datetime.now()
            lock['koda'] = True

        if lock.get('koda') and (datetime.datetime.now() - time_heard).seconds >= 10:
            print('Resetting...')
            lock['koda'] = False

        if not lock.get('koda'):
            continue

        phrases = ((re.compile(regex, flags=re.I), func) for regex, func in keyword_expressions)

        for i, user_said in enumerate(spoken):
            if not user_said:
                continue
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
    artist = artist.lower().strip()
    print(title, artist)
    init_path = '/Users/dean/Programming/YoutubeDownloaderClient/downloads/'
    songs = os.listdir(init_path)
    songs = filter(lambda song: song.lower().startswith(artist), songs)
    songs = list(songs)

    if not title:
        print('Choices: \n\t{0}'.format('\n\t'.join(songs)))
        if not songs:
            return ''
        return os.path.join(init_path, random.choice(songs))
    title = title.lower().strip()
    matches = filter(lambda s: title in clean(s.lower()), songs)
    x = list(matches)
    print(x)
    if len(x) > 0:
        return os.path.join(init_path, x[0])
    print('Error... unable to parse from songs: {0}'.format(list(songs)))
    return ''

spoken = ['t'] * 25
def await_commands():
    threading.Thread(name='Listen for phrases', target=listen_for_phrases).start()
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
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, MAX_WAIT)  # listen for the first phrase and extract it into audio data
            # print("Set minimum energy threshold to {}".format(r.energy_threshold))
            logging.debug("Got it! Now recognizing it...")
            value = r.recognize_google(audio)
            if value and len(value) > 0:
                logging.debug("You said {}".format(value))
                spoken[index] = value
        except (sr.UnknownValueError, sr.WaitTimeoutError, LookupError):  # speech is unintelligible
            # logging.debug("Oops! Didn't catch that or timed out.")
            spoken[index] = ''
            return
    return

MUSIC_SOMETHING_RE = r'play something'
MUSIC_RE = r'play (.+) by (.+)'
MUSIC_SOMETHING_ARTIST_RE = r'play (?:something|a song) by (.+)'
DOWNLOAD_RE = r'download (.+) by (.+)'
STOP_MUSIC_RE = r'stop(?: the)? music'
keyword_expressions = (
    (MUSIC_SOMETHING_ARTIST_RE, _play_something_music),
    (MUSIC_RE, _play_music),
    (DOWNLOAD_RE, _download),
    (STOP_MUSIC_RE, stop_the_music),
    (MUSIC_SOMETHING_RE, _play_something_music),
)

if __name__ == "__main__":
    await_commands()
    logging.debug("END OF PROGRAM")
    logging.shutdown()
