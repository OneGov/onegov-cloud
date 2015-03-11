import os.path
import inspect
import pydoc
import re

from onegov.core import compat
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


def module_path(module, subpath):
    """ Returns a subdirectory in the given python module.

    :module:
        A python module (actual module or string)

    :subpath:
        Subpath below that python module. Leading slashes ('/') are ignored.
    """

    subpath = subpath.strip('/')

    if isinstance(module, compat.string_types):
        module = pydoc.locate(module)

    assert module is not None

    path = os.path.dirname(inspect.getfile(module))
    return os.path.join(path, subpath)


def touch(file_path):
    """ Touches the file on the given path. """
    try:
        os.utime(file_path, None)
    except:
        open(file_path, 'a').close()
