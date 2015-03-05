import re
from unidecode import unidecode

_spaces = re.compile(r'\s+')


def normalize_for_url(text):
    """ Takes the given text and makes it fit to be used for an url.

    That means replacing spaces with '-', lowercasing everything and turning
    unicode characters into their closest ascii equivalent using Unidecode.

    See https://pypi.python.org/pypi/Unidecode

    """
    return _spaces.sub('-', unidecode(text).strip(' ').lower())


def lchop(text, beginning):
    """ Removes the beginning from the text if the text starts with it. """

    if text.startswith(beginning):
        return text[len(beginning):]

    return text


def rchop(text, end):
    """ Removes the end from the text if the text ends with it. """

    if text.endswith(end):
        return text[:len(end)]

    return text
