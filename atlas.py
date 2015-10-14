import os
import sys
import time
import logging
import threading
import speech_recognition as sr
from speech_recognition import UnknownValueError

# Initialization
r = sr.Recognizer()
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) {%(funcName)s} %(message)s',)
phrases = ["time to program", "stop the music", "power off"]

# Play programming music
def play_music(fname):
    print(fname)
    logging.debug("Starting mpg321")
    os.system('mpg321 "%s" --quiet' % fname)
    logging.debug("Finished mpg321")


# Stop programming music
def stop_music():
    logging.debug("Killing mpg321")
    os.system("killall mpg321")
    logging.debug("Killed mpg321")


# Speech to text
def listen():
    MAX_WAIT = 5  # seconds
    logging.debug("Listening...")
    with sr.Microphone() as source:  # use the default microphone as the audio source
        r.adjust_for_ambient_noise(source)
        print("Set minimum energy threshold to {}".format(r.energy_threshold))
        try:
            audio = r.listen(source, MAX_WAIT)  # listen for the first phrase and extract it into audio data
        except:  # TODO: catch TimeoutError, a type of OSError
            logging.debug("Timeout exception")
            return None
    try:
        logging.debug("Got it! Now recognizing it...")
        value = r.recognize_google(audio)
        logging.debug("You said {}".format(value))
    except LookupError:  # speech is unintelligible
        logging.debug("Oops! Didn't catch that")
        return False

    return value


# Listen for particular phrases
def listen_for_phrases(timeouts=0):
    while(timeouts < 5):

        logging.debug("Waiting for phrases:")
        for phrase in phrases:
            logging.debug("    '%s'" % phrase)

        # Listen for phrase
        user_said = listen()
        if user_said is None:
            timeouts += 1  # record timeout
            continue

        # PHRASE
        if user_said.lower().startswith("play "):
            value = user_said[4:]
            threading.Thread(name='play_music', target=play_music, args=(get_filename(value),)).start()
            logging.debug("'play_music' thread issued")
        # PHRASE
        elif user_said.lower() == "stop the music":
            threading.Thread(name='stop_music', target=stop_music).start()
            logging.debug("'stop_music' thread issued")

        # PHRASE
        elif user_said.lower() == "power off":
            # Print ATLAS
            bye = open('Goodbye.txt','r')
            for line in bye:
                print(line)
            bye.close()
            sys.exit(-1)

        else:
            continue

        timeouts = 0  # reset timeouts if received response

import glob
import re
import fnmatch
import os
def get_filename(song_info):
    info = song_info.split(' by ')
    if len(info) == 1:
        info = song_info.split(' bye ')
        if len(info) == 1:
            print('Error, could not parse %s' % (song_info))
            return ''
    print(info)
    title, artist = map(lambda item: item.strip(), info)
    print(title, artist)
    init_path = '/Users/dean/Programming/YoutubeDownloaderClient/downloads/'
    songs = os.listdir(init_path)
    songs = filter(lambda song: song.lower().startswith(artist.lower()), songs)
    matches = filter(lambda s: title.lower() in s.lower(), songs)
    x = list(matches)
    print(x)
    if len(x) > 0:
        return os.path.join(init_path, x[0])
    print('Error... unable to parse from songs: {0}'.format(list(songs)))
    return ''


# Await 'Atlas' phrase
def await_commands():
    while(True):
        logging.debug("Waiting for keyword 'Atlas'...")
        try:
            res = listen()
            if res is None or len(res) == 0:
                continue
            res = res.lower()
        except:
            print('Unknonw value error raised from speech_recognition')
        if "atlas" in res or 'alice' in res:
            # threading.Thread(name="say", args=["Yes?"], target=say).start()
            # time.sleep(2)
            # say("Yes?")
            listen_for_phrases()


##########################
#          MAIN          #
##########################
if __name__ == "__main__":
    
    await_commands()
    
    ###############################
    logging.debug("END OF PROGRAM")
    logging.shutdown()
    ###############################



