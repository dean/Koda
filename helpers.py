

def parse_title_artist(s):
    s = s.lower()
    split = s.split(' by' )
    if len(split) == 1:
        return None
    return split




def capitalize(string):
    """Capitalizes a string."""
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


