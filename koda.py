import datetime
import functools
import itertools
import logging
import os
import random
import re
import subprocess
import sys
import time
import threading

import speech_recognition as sr

import commands
import config


# Initialization
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) {%(funcName)s} %(message)s',)

spoken = [''] * 15
MUSIC_SOMETHING_ARTIST_RE = r'play (?:something|a song) by (.+)'
MUSIC_RE = r'play (.+) by (.+)'
MUSIC_SOMETHING_ELSE_RE = r'play something else'
MUSIC_SOMETHING_RE = r'play something$'
MUSIC_PLAY_TITLE_RE = r'^play (.+)'
DOWNLOAD_RE = r'download (.+) by (.+)'
STOP_MUSIC_RE = r'stop(?: the)? music'
REGEX_FUNC_MAPPINGS = (
    (MUSIC_SOMETHING_ARTIST_RE, commands._play_something_by_artist),
    (MUSIC_RE, commands._play_music),
    (MUSIC_SOMETHING_ELSE_RE, commands._play_something_else),
    (MUSIC_SOMETHING_RE, commands._play_something),
    (MUSIC_PLAY_TITLE_RE, commands._play),
    (DOWNLOAD_RE, commands._download),
    (STOP_MUSIC_RE, commands._stop_the_music),
)


def all_match_indices(_spoken, triggers):
    """Returns the indices of matches to triggers from _spoken."""
    match_indices = []
    for i, s_list in enumerate(_spoken):
        for s in s_list:
            for t in triggers:
                if s.lower().startswith(t):
                    match_indices.append(i)
    return match_indices


def clear_matches_for_regex(_re):
    """ Clear all spoken matches for an associated regex. """
    global spoken
    for i, spoke_list in enumerate(spoken):
        for spoke in spoke_list:
            matches = re.match(_re, spoke, flags=re.I)
            if matches:
                print('Clearing match for: {0}'.format(spoke))
                spoken[i] = ''


def play_awake_sound():
    """ PLay the default alert tone for Koda. """
    try:
        subprocess.check_call(['mpg321', 'alert.mp3'])
    except subprocess.CalledProcessError:
        pass


def listen_for_phrases():
    """ Main thread for listening for our key phrases. """
    awake = False
    woken_up_at = None
    while True:
        time.sleep(0.15)
        match_indices = all_match_indices(spoken, config.KODA_TRIGGERS)
        if not awake and len(match_indices) > 0:
            # Waking up!
            play_awake_sound()

            # Clear all matches so we don't repeat later
            for i in match_indices:
                spoken[i] = ''

            woken_up_at = datetime.datetime.now()
            awake = True
        elif not awake:
            continue

        now = datetime.datetime.now()
        seconds_awake = (now - woken_up_at).seconds
        if seconds_awake >= 15:
            awake = False
            continue

        compiled_regex_func_mappings = [(re.compile(regex, flags=re.I), func)
                                        for regex, func in REGEX_FUNC_MAPPINGS]

        all_user_said = itertools.chain.from_iterable(spoken)
        for user_said in all_user_said:
            if not all_user_said:
                continue

            for _re, func in compiled_regex_func_mappings:
                match = _re.match(user_said)
                if match:
                    print('Matched %s on %s' %( _re.pattern, user_said))
                    threading.Thread(target=func, args=match.groups()).start()
                    clear_matches_for_regex(_re.pattern)
                    break


def await_commands():
    """ Does our initial thread spawns and spawns listeners periodically. """
    threading.Thread(name='Koda', target=listen_for_phrases).start()
    threading.Thread(name='Music', target=commands.music_player).start()
    i = 1
    while(True):
        threading.Thread(name='Listener%d' % (i % 7), target=listen, args=(i % 7,)).start()
        time.sleep(2)
        i += 1


# Speech to text
def listen(index):
    """ A general listener. """
    global spoken
    MAX_WAIT = index + 5  # seconds
    logging.debug("Listening...")
    with sr.Microphone() as source:  # use the default microphone as the audio source
        try:
            r = sr.Recognizer()
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, MAX_WAIT)  # listen for the first phrase and extract it into audio data
            logging.debug("Got it! Now recognizing it...")
            values = r.recognize_google(audio, show_all=True)
            if values:
                spoken[index] = [x['transcript'] for x in values['alternative']]
        except (sr.UnknownValueError, sr.WaitTimeoutError, LookupError):  # speech is unintelligible
            # logging.debug("Oops! Didn't catch that or timed out.")
            spoken[index] = []
            return
    return

if __name__ == "__main__":
    await_commands()
    logging.shutdown()
