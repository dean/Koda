def clean(string, chars=list('.()-_')):
    """Cleans a string of all characters we wish to ignore.

    @arg: string: String to clean
    """
    rosetta_stone = {ord(c): None for c in chars}
    return string.translate(rosetta_stone)
