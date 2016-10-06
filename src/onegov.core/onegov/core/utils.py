import bleach
import hashlib
import importlib
import inspect
import json
import magic
import mimetypes
import morepath
import os.path
import re

from collections import Iterable
from contextlib import contextmanager
from cProfile import Profile
from datetime import datetime
from functools import partial
from importlib import import_module
from itertools import groupby, tee
from purl import URL
from sqlalchemy import distinct
from unidecode import unidecode
from uuid import UUID
from webob import static

# XXX keep around for a while for backwards compatibility
from onegov.core.html import sanitize_html  # noqa


# http://stackoverflow.com/a/13500078
_unwanted_url_chars = re.compile(r'[\.\(\)\\/\s<>\[\]{},:;?!@&=+$#@%|\*"\'`]+')
_double_dash = re.compile(r'[-]+')
_number_suffix = re.compile(r'-([0-9]+)$')
_repeated_spaces = re.compile(r'\s\s+')
_uuid = re.compile(
    r'[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}')

# only temporary until bleach has a release > 1.4.1 -
_email_regex = re.compile((
    "([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
    "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
    "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"
))


def normalize_for_url(text):
    """ Takes the given text and makes it fit to be used for an url.

    That means replacing spaces and other unwanted characters with '-',
    lowercasing everything and turning unicode characters into their closest
    ascii equivalent using Unidecode.

    See https://pypi.python.org/pypi/Unidecode

    """

    # German is our main language, so we are extra considerate about it
    # (unidecode turns ü into u)
    text = text.replace("ü", "ue")
    text = text.replace("ä", "ae")
    text = text.replace("ö", "oe")
    clean = _unwanted_url_chars.sub('-', unidecode(text).strip(' ').lower())
    clean = _double_dash.sub('-', clean)
    clean = clean.strip('-')

    return clean


def increment_name(name):
    """ Takes the given name and adds a numbered suffix beginning at 1.

    For example::

        foo => foo-1
        foo-1 => foo-2

    """

    match = _number_suffix.search(name)
    number = (match and int(match.group(1)) or 0) + 1

    if match:
        return _number_suffix.sub('-{}'.format(number), name)
    else:
        return name + '-{}'.format(number)


def lchop(text, beginning):
    """ Removes the beginning from the text if the text starts with it. """

    if text.startswith(beginning):
        return text[len(beginning):]

    return text


def rchop(text, end):
    """ Removes the end from the text if the text ends with it. """

    if text.endswith(end):
        return text[:-len(end)]

    return text


def remove_repeated_spaces(text):
    """ Removes repeated spaces in the text ('a  b' -> 'a b'). """

    return _repeated_spaces.sub(' ', text)


@contextmanager
def profile(filename):
    """ Profiles the wrapped code and stores the result in the profiles folder
    with the given filename.

    """
    profiler = Profile()
    profiler.enable()

    yield

    profiler.disable()
    profiler.create_stats()
    profiler.dump_stats('profiles/{}'.format(filename))


@contextmanager
def timing(name=None):
    """ Runs the wrapped code and prints the time in ms it took to run it.
    The name is printed in front of the time, if given.

    """

    start = datetime.utcnow()

    yield

    duration = datetime.utcnow() - start
    duration = int(round(duration.total_seconds() * 1000, 0))

    if name:
        print('{}: {} ms'.format(name, duration))
    else:
        print('{} ms'.format(duration))


def module_path(module, subpath):
    """ Returns a subdirectory in the given python module.

    :module:
        A python module (actual module or string)

    :subpath:
        Subpath below that python module. Leading slashes ('/') are ignored.
    """

    subpath = subpath.strip('/')

    if isinstance(module, str):
        module = importlib.import_module(module)

    assert module is not None

    parent = os.path.dirname(inspect.getfile(module))
    path = os.path.join(parent, subpath)

    # always be paranoid with path manipulation
    assert is_subpath(parent, path)

    return path


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

        return content_type

    return request.get_response(
        static.FileApp(file_path, content_type=get_content_type(file_path)))


def hash_dictionary(dictionary):
    """ Computes a sha256 hash for the given dictionary. The dictionary
    is expected to only contain values that can be serialized by json.

    That includes int, decimal, string, boolean.

    Note that this function is not meant to be used for hashing secrets. Do
    not include data in this dictionary that is secret!

    """
    dict_as_string = json.dumps(dictionary, sort_keys=True).encode('utf-8')
    return hashlib.sha1(dict_as_string).hexdigest()


def groupbylist(*args, **kwargs):
    """ Works just like Python's ``itertools.groupby`` function, but instead
    of returning generators, it returns lists.

    """
    return [(k, list(g)) for k, g in groupby(*args, **kwargs)]


def linkify(text, escape=True):
    """ Takes plain text and injects html links for urls and email addresses.

    By default the text is html escaped before it is linkified. This accounts
    for the fact that we usually use this for text blocks that we mean to
    extend with email addresses and urls.

    If html is already possible, why linkify it?

    Note: We need to clean the html after we've created it (linkify
    parses escaped html and turns it into real html). As a consequence it
    is possible to have html urls in the text that won't be escaped.

    """

    if not text:
        return text

    # do not parse email until this is fixed:
    # https://github.com/jsocol/bleach/issues/154

    # .. use a simple substitute instead
    text = emailify(text)

    linkified = bleach.linkify(text, parse_email=False)

    if not escape:
        return linkified

    return bleach.clean(
        linkified, tags=['a'], attributes={'a': ['href', 'rel']})


def emailify(text):
    # the link generating code below is not necessarily safe, so we need
    # to clean the result of each generation
    clean = partial(bleach.clean, tags=['a'], attributes={'a': ['href']})

    emails = (
        email[0] for email in re.findall(_email_regex, text)
        if not email[0].startswith('//')
    )

    for email in emails:
        link = '<a href="mailto:{email}">{email}</a>'.format(email=email)
        link = clean(link)

        text = text.replace(email, link)

    return text


def ensure_scheme(url, default='http'):
    """ Makes sure that the given url has a scheme in front, if none
    was provided.

    """

    if not url:
        return url

    # purl (or to be precise urlparse) will parse empty host names ('abc.xyz')
    # wrongly, assuming the abc.xyz is a path. by adding a double slash if
    # there isn't one already, we can circumvent that problem
    if '//' not in url:
        url = '//' + url

    _url = URL(url)

    if _url.scheme():
        return url

    return _url.scheme(default).as_string()


def is_uuid(value):
    """ Returns true if the given value is a uuid. The value may be a string
    or of type UUID. If it's a string, the uuid is checked with a regex.
    """
    if isinstance(value, str):
        return _uuid.match(str(value))

    return isinstance(value, UUID)


def is_non_string_iterable(obj):
    """ Returns true if the given obj is an iterable, but not a string. """
    return not (isinstance(obj, str) or isinstance(obj, bytes))\
        and isinstance(obj, Iterable)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def relative_url(absolute_url):
    """ Removes everything in front of the path, including scheme, host,
    username, password and port.

    """
    url = URL._mutate(
        URL(absolute_url),
        scheme=None,
        username=None,
        password=None,
        host=None,
        port=None
    )

    return url.as_string()


def is_subpath(directory, path):
    """ Returns true if the given path is inside the given directory. """
    directory = os.path.join(os.path.realpath(directory), '')
    path = os.path.realpath(path)

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([path, directory]) == directory


def is_sorted(iterable, key=lambda i: i, reverse=False):
    """ Returns True if the iterable is sorted. """

    i1, i2 = tee(iterable)

    for a, b in zip(i1, sorted(i2, key=key, reverse=reverse)):
        if a is not b:
            return False

    return True


def morepath_modules(cls):
    """ Returns all morepath modules which should be scanned for the given
    morepath application class.

    We can't reliably know the actual morepath modules that
    need to be scanned, which is why we assume that each module has
    one namespace (like 'more.transaction' or 'onegov.core').

    """
    for base in cls.__mro__:
        if not issubclass(base, morepath.App):
            continue

        if base is morepath.App:
            continue

        module = '.'.join(base.__module__.split('.')[:2])

        if module.startswith('test'):
            continue

        yield module


def scan_morepath_modules(cls):
    """ Tries to scann all the morepath modules required for the given
    application class. This is not guaranteed to stay reliable as there is
    no sure way to discover all modules required by the application class.

    """
    for module in sorted(morepath_modules(cls)):
        morepath.scan(import_module(module))


def get_unique_hstore_keys(session, column):
    """ Returns a set of keys found in an hstore column over all records
    of its table.

    """

    return {
        key
        for row in session.query(distinct(column.keys())).all() if row[0]
        for key in row[0]
    }
