import commands

EXPORTED_ITUNES_LIBRARY = '/Users/dean/Documents/Library-New.xml'
NUM_LISTENERS = 15
KODA_TRIGGERS = ['coda', 'koda', 'cota', 'toyota', 'tota', 'kona']
MUSIC_SOMETHING_ARTIST_RE = r'play (?:something|a song) by (.+)'
MUSIC_RE = r'play (.+) by (.+)'
MUSIC_SOMETHING_ELSE_RE = r'play something else'
MUSIC_SOMETHING_RE = r'play something$'
MUSIC_PLAY_TITLE_RE = r'^play (.+)'
DOWNLOAD_RE = r'download (.+) by (.+)'
STOP_MUSIC_RE = r'stop(?: the)? music'
REGEX_FUNC_MAPPINGS = (
    (MUSIC_SOMETHING_ARTIST_RE, '_play_something_by_artist'),
    (MUSIC_RE, '_play_music'),
    (MUSIC_SOMETHING_ELSE_RE, '_play_something_else'),
    (MUSIC_SOMETHING_RE, '_play_something'),
    (MUSIC_PLAY_TITLE_RE, '_play'),
    (DOWNLOAD_RE, '_download'),
    (STOP_MUSIC_RE, '_stop_the_music'),
)
