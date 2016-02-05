import functools


def clean(string, chars=list('.()-_')):
    """Cleans a string of all characters we wish to ignore.

    @arg: string: String to clean
    """
    return functools.reduce(lambda original, ignore: original.replace(ignore, ''),
                  [string] + chars)
