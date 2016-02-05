import datetime
import functools
import itertools
import logging
import os
import random
import re
import subprocess
import time
import threading

import speech_recognition as sr

import commands
import config


# Initialization
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) {%(funcName)s} %(message)s',)
spoken = [''] * config.NUM_LISTENERS


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


def clear_matches_for_func_name(func_name):
    ''' Reverse maps a func name to regex and finds the corresponding match. '''
    for _re, _func_name in config.REGEX_FUNC_MAPPINGS:
        if func_name == _func_name:
            return clear_matches_for_regex(_re)


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
            # FIXME: Helper function here
            match_indices = all_match_indices(spoken, config.KODA_TRIGGERS)
            for i in match_indices:
                spoken[i] = ''

            awake = False
            continue

        compiled_regex_func_mappings = [(re.compile(regex, flags=re.I), func)
                                        for regex, func in config.REGEX_FUNC_MAPPINGS]

        all_user_said = itertools.chain.from_iterable(spoken)
        for user_said in all_user_said:
            if not all_user_said:
                continue

            for _re, func_name in compiled_regex_func_mappings:
                match = _re.match(user_said)
                if match:
                    print('Matched %s on %s' %( _re.pattern, user_said))
                    threading.Thread(target=getattr(commands, func_name), args=match.groups()).start()
                    clear_matches_for_regex(_re.pattern)

                    # Enable ourselves to rapidly give commands to Koda in succession.
                    woken_up_at = datetime.datetime.now()
                    break


def await_commands():
    """ Does our initial thread spawns and spawns listeners periodically. """
    threading.Thread(name='Koda', target=listen_for_phrases).start()
    threading.Thread(name='Music', target=commands.music_player).start()
    i = 1
    while(True):
        n = i % config.NUM_LISTENERS
        threading.Thread(name='Listener%d' % n, target=listen, args=(n,)).start()
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
            spoken[index] = []
            return
    return

if __name__ == "__main__":
    await_commands()
    logging.shutdown()
