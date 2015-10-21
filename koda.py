import datetime
import fnmatch
import functools
import glob
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
triggers = ['atlas', 'alice', 'outlet']


def clean(string, chars=list('.()-_')):
    """Cleans a string of all characters we wish to ignore.

    @arg: string: String to clean
    """
    return functools.reduce(lambda original, ignore: original.replace(ignore, ''),
                  [string] + chars)

# Stop programming music
def stop_the_music():
    clear_matches(STOP_MUSIC_RE)
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
    clear_matches(DOWNLOAD_RE)
    with open('../YoutubeDownloaderClient/songs.txt', 'w') as f:
        f.write('{0} --- {1}'.format(title, artist))
    res = os.system('cd ../YoutubeDownloaderClient && source env/bin/activate && python download.py --file songs.txt --client-id AIzaSyDs-ONEG30OApiYc8SPNSB2uuqMb9OcX3s')
    if res == 0:
        logging.debug('Attempting to download {0} by {1} to {2}'.format(title, artist, '../YoutubeDownloader/downloads/{0} --- {1}'.format(artist, title)))
    lock['download']= False
    return




lock = {}
def _play_music(title, artist):
    global lock

    filename = get_filename(title, artist)
    if not filename or lock.get('play_music'):
        return

    lock['play music'] = True
    clear_matches(MUSIC_RE)
    logging.debug("Playing {path}".format(path=filename))
    try:
        subprocess.check_call(['mpg321', filename, '--quiet'])
        logging.debug("Stopping mpg321")
    except subprocess.CalledProcessError:
        logging.debug('mpg321 killed.')
    finally:
        lock['play music'] = False
        return


atlas = False
download_locked = False
# Listen for particular phrases
def listen_for_phrases():
    global lock
    global spoken
    time_heard = None
    r = 1
    while(True):
        time.sleep(0.15)  # So we don't do millions of iterations in succession...
        matches = any_matches(spoken, triggers)
        if not lock.get('atlas') and matches:
            for i in matches:
                spoken[i] = ''
            print(matches)
            print(spoken)
            print('Triggered!')
            subprocess.check_call(['mpg321', 'alert.mp3'])
            time_heard = datetime.datetime.now()
            lock['atlas'] = True

        if lock.get('atlas') and (datetime.datetime.now() - time_heard).seconds >= 10:
            print('Resetting...')
            lock['atlas'] = False
            # reset()

        # PHRASE
        if not lock.get('atlas'):
            continue

        phrases = {re.compile(regex, flags=re.I): func for regex, func in keyword_expressions.items()}

        for i, user_said in enumerate(spoken):
            for _re, func in phrases.items():
                match = _re.match(user_said)
                if match and match.groups():
                    print('Matched on %s' % user_said)
                    threading.Thread(target=func, args=match.groups()).start()
                elif match:
                    print('Matched on %s' % user_said)
                    threading.Thread(target=func).start()


            #if user_said.lower().startswith("play "):
            #    spoken[i] = ''
            #    value = user_said[4:]
            #    if not music_locked:
            #        filename = get_filename(value)
            #        if not filename:
            #            continue
            #        threading.Thread(name='play_music', target=play_music, args=(filename,)).start()
            #        logging.debug("'play_music' thread issued")
            #    else:
            #        print('Locked from playing music.')

            #if user_said.lower().startswith("download "):
            #    spoken[i] = ''
            #    value = user_said[9:]
            #    title, artist = parse_title_artist(value)
            #    if not download_locked:
            #       threading.Thread(name='Download', target=_download, args=(title, artist)).start()


            ## PHRASE
            #elif user_said.lower() == "stop the music":
            #    spoken[i] = ''
            #    threading.Thread(name='stop_music', target=stop_music).start()
            #    logging.debug("'stop_music' thread issued")
            #    clear_all(['stop the music'])


def get_filename(title, artist):
    title, artist = title.lower().strip(), artist.lower().strip()
    print(title, artist)
    init_path = '/Users/dean/Programming/YoutubeDownloaderClient/downloads/'
    songs = os.listdir(init_path)
    songs = filter(lambda song: song.lower().startswith(artist), songs)
    songs = list(songs)

    if title == 'something':
        if not songs:
            return
        return os.path.join(init_path, random.choice(songs))

    matches = filter(lambda s: title in clean(s.lower()), songs)
    x = list(matches)
    print(x)
    if len(x) > 0:
        return os.path.join(init_path, x[0])
    print('Error... unable to parse from songs: {0}'.format(list(songs)))
    return ''

spoken = [''] * 5
# Await 'Atlas' phrase
def await_commands():
    threading.Thread(name='Listen for phrases', target=listen_for_phrases).start()
    while(True):
        # Spawn 25 threads that each last for 5 seconds (MAX_WAIT) .2 seconds apart from eachother.
        for i in range(5):
            threading.Thread(name='Listener%d' % i, target=listen, args=(i,)).start()
            time.sleep(3)



# Speech to text
def listen(index):
    global spoken
    MAX_WAIT = index + 3  # seconds
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
            pass
            return
    return

MUSIC_RE = r'play (.+) by (.+)'
DOWNLOAD_RE = r'download (.+) by (.+)'
STOP_MUSIC_RE = r'stop(?: the)? music'
keyword_expressions = {
    MUSIC_RE: _play_music,
    DOWNLOAD_RE: _download,
    STOP_MUSIC_RE: stop_the_music,
}

if __name__ == "__main__":
    await_commands()
    logging.debug("END OF PROGRAM")
    logging.shutdown()
