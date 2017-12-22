import base64
import bleach
import gzip
import hashlib
import importlib
import inspect
import magic
import mimetypes
import morepath
import os.path
import re
import sqlalchemy
import urllib.request

from io import BytesIO, StringIO
from collections import Iterable
from contextlib import contextmanager
from cProfile import Profile
from datetime import datetime
from onegov.core.cache import lru_cache
from onegov.core.custom import json
from importlib import import_module
from itertools import groupby, tee, zip_longest
from onegov.core import log
from purl import URL
from threading import Thread
from unidecode import unidecode
from uuid import UUID
from webob import static


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


@lru_cache(maxsize=32)
def module_path_root(module):
    if isinstance(module, str):
        module = importlib.import_module(module)

    assert module is not None

    return os.path.dirname(inspect.getfile(module))


def module_path(module, subpath):
    """ Returns a subdirectory in the given python module.

    :mod:
        A python module (actual module or string)

    :subpath:
        Subpath below that python module. Leading slashes ('/') are ignored.
    """

    parent = module_path_root(module)
    path = os.path.join(parent, subpath.strip('/'))

    # always be paranoid with path manipulation
    assert is_subpath(parent, path)

    return path


def touch(file_path):
    """ Touches the file on the given path. """
    try:
        os.utime(file_path, None)
    except Exception:
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

    linkified = bleach.linkify(text, parse_email=True)

    if not escape:
        return linkified

    return bleach.clean(
        linkified, tags=['a'], attributes={'a': ['href', 'rel']})


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


def chunks(iterable, n, fillvalue=None):
    """ Iterates through an iterable, returning chunks with the given size.

    For example::

        chunks('ABCDEFG', 3, 'x') --> [
            ('A', 'B', 'C'),
            ('D', 'E', 'F'),
            ('G', 'x', 'x')
        ]

    """

    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


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

    base = session.query(column.keys()).with_entities(
        sqlalchemy.func.skeys(column).label('keys'))

    query = sqlalchemy.select(
        [sqlalchemy.func.array_agg(sqlalchemy.column('keys'))],
        distinct=True
    ).select_from(base.subquery())

    keys = session.execute(query).scalar()
    return set(keys) if keys else set()


def makeopendir(fs, directory):
    """ Creates and opens the given directory in the given PyFilesystem. """

    if not fs.isdir(directory):
        fs.makedir(directory)

    return fs.opendir(directory)


def append_query_param(url, key, value):
    """ Appends a single query parameter to an url. This is faster than
    using Purl, if and only if we only add one query param.

    Also this function assumes that the value is already url encoded.

    """
    template = '?' in url and '{}&{}={}' or '{}?{}={}'
    return template.format(url, key, value)


class PostThread(Thread):

    """ POSTs the given data with the headers to the URL.

    Example::

        data = {'a': 1, 'b': 2}
        data = json.dumps(data).encode('utf-8')
        PostThread(
            'https://example.com/post',
            data,
            (
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Content-Length', len(data))
            )
        ).start()

    This only works for external URLs! If posting to server itself is
    needed, use a process instead of the thread!

    """

    def __init__(self, url, data, headers, timeout=30):
        Thread.__init__(self)
        self.url = url
        self.data = data
        self.headers = headers
        self.timeout = timeout

    def run(self):
        try:
            request = urllib.request.Request(self.url)
            for header in self.headers:
                request.add_header(header[0], header[1])
            urllib.request.urlopen(request, self.data, self.timeout)
        except Exception as e:
            log.error(
                'Error while sending a POST request to {}: {}'.format(
                    self.url, str(e)
                )
            )


def toggle(collection, item):
    """ Toggles an item in a set. """

    if item is None:
        return collection

    if item in collection:
        return collection - {item}
    else:
        return collection | {item}


def binary_to_dictionary(binary, filename=None):
    """ Takes raw binary filedata and stores it in a dictionary together
    with metadata information.

    The data is compressed before it is stored int he dictionary. Use
    :func:`dictionary_to_binary` to get the original binary data back.

    """

    assert isinstance(binary, bytes)

    mimetype = magic.from_buffer(binary, mime=True)
    gzipdata = BytesIO()

    with gzip.GzipFile(fileobj=gzipdata, mode='wb') as f:
        f.write(binary)

    return {
        'data': base64.b64encode(gzipdata.getvalue()).decode('ascii'),
        'filename': filename,
        'mimetype': mimetype,
        'size': len(binary)
    }


def dictionary_to_binary(dictionary):
    """ Takes a dictionary created by :func:`binary_to_dictionary` and returns
    the original binary data.

    """
    data = base64.b64decode(dictionary['data'])

    with gzip.GzipFile(fileobj=BytesIO(data), mode='r') as f:
        return f.read()


def safe_format(format, dictionary, types={int, str, float}, adapt=None,
                raise_on_missing=False):
    """ Takes a user-supplied string with format blocks and returns a string
    where those blocks are replaced by values in a dictionary.

    For example::

        >>> safe_format('[user] has logged in', {'user': 'admin'})
        'admin has logged in'

    :param format:
        The format to use. Square brackets denote dictionary keys. To
        literally print square bracktes, mask them by doubling ('[[' -> '[')

    :param dictionary:
        The dictionary holding the variables to use. If the key is not found
        in the dictionary, the bracket is replaced with an empty string.

    :param types:
        A set of types supported by the dictionary. Limiting this to safe
        types like builtins (str, int, float) ensure that no values are
        accidentally leaked through faulty __str__ representations.

        Note that inheritance is ignored. Supported types need to be
        whitelisted explicitly.

    :param adapt:
        An optional callable that receives the key before it is used. Returns
        the same key or an altered version.

    :param raise_on_missing:
        True if missing keys should result in a runtime error (defaults to
        False).

    This is strictly meant for formats provided by users. Python's string
    formatting options are clearly superior to this, however it is less
    secure!

    """

    output = StringIO()
    buffer = StringIO()
    opened = 0

    for ix, char in enumerate(format):
        if char == '[':
            opened += 1

        if char == ']':
            opened -= 1

        if opened == 1 and char != '[' and char != ']':
            print(char, file=buffer, end='')
            continue

        if opened == 2 or opened == -2:
            if buffer.tell():
                raise RuntimeError("Unexpected bracket inside bracket found")

            print(char, file=output, end='')
            opened = 0
            continue

        if buffer.tell():
            k = adapt(buffer.getvalue()) if adapt else buffer.getvalue()

            if raise_on_missing and k not in dictionary:
                raise RuntimeError("Key '{}' is unknown".format(k))

            v = dictionary.get(k, '')
            t = type(v)

            if t not in types:
                raise RuntimeError("Invalid type for '{}': {}".format(k, t))

            print(v, file=output, end='')
            buffer = StringIO()

        if char != '[' and char != ']':
            print(char, file=output, end='')

    if opened != 0:
        raise RuntimeError("Uneven number of brackets in '{}'".format(format))

    return output.getvalue()


def safe_format_keys(format, adapt=None):
    """ Takes a :func:`safe_format` string and returns the found keys. """

    keys = []

    def adapt_and_record(key):
        key = adapt(key) if adapt else key
        keys.append(key)

        return key

    safe_format(format, {}, adapt=adapt_and_record)

    return keys
