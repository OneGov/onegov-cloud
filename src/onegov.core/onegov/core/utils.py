import os.path
import inspect
import magic
import mimetypes
import pydoc
import re

from onegov.core import compat
from unidecode import unidecode
from webob import static

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


class Bunch(object):
    """ A simple but handy "collector of a bunch of named stuff" class.

    See `<http://code.activestate.com/recipes/\
    52308-the-simple-but-handy-collector-of-a-bunch-of-named/>`_.

    For example::

        point = Bunch(x=1, y=2)
        assert point.x == 1
        assert point.y == 2

        point.z = 3
        assert point.z == 3

    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def render_file(file_path, request):
    """ Takes the given file_path (content) and renders it to the browser.
    The file must exist on the local system and be readable by the current
    process.

    """

    # this is a very cachable result - though it's possible that a file
    # changes it's content type, it should usually not, especially since
    # we emphasize the use of random filenames
    @request.app.cache.cache_on_arguments()
    def get_content_type(file_path):
        content_type = mimetypes.guess_type(file_path)[0]

        if not content_type:
            content_type = magic.from_file(file_path, mime=True)
            content_type = content_type.decode('utf-8')

        return content_type

    return request.get_response(
        static.FileApp(file_path, content_type=get_content_type(file_path)))
