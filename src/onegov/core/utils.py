from __future__ import annotations

import base64
import bleach
from urlextract import URLExtract, CacheFileError
from bleach.linkifier import TLDS
import errno
import fcntl
import gzip
import hashlib
import importlib
import inspect
import magic
import mimetypes
import morepath
import operator
import os.path
import re
import shutil
import sqlalchemy
import urllib.request

from collections.abc import Iterable
from contextlib import contextmanager
from cProfile import Profile
from functools import lru_cache, reduce, cache
from importlib import import_module
from io import BytesIO, StringIO
from itertools import groupby, islice
from markupsafe import escape
from markupsafe import Markup
from onegov.core import log
from onegov.core.custom import json
from onegov.core.errors import AlreadyLockedError
from phonenumbers import (PhoneNumberFormat, format_number,
                          NumberParseException, parse)
from purl import URL
from threading import Thread
from time import perf_counter
from unidecode import unidecode
from uuid import UUID, uuid4
from webob import static
from yubico_client import Yubico  # type:ignore[import-untyped]
from yubico_client.yubico_exceptions import (  # type:ignore[import-untyped]
    SignatureVerificationError, StatusCodeError)


from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable, Collection, Iterator, Mapping
    from fs.base import FS, SubFS
    from re import Match
    from sqlalchemy import ColumnElement
    from sqlalchemy.orm import Session
    from types import ModuleType
    from webob import Response
    from .request import CoreRequest
    from .types import FileDict, LaxFileDict


_T = TypeVar('_T')
_KT = TypeVar('_KT')


# http://stackoverflow.com/a/13500078
_unwanted_url_chars = re.compile(r'[\.\(\)\\/\s<>\[\]{},:;?!@&=+$#@%|\*"\'`]+')
_double_dash = re.compile(r'[-]+')
_number_suffix = re.compile(r'-([0-9]+)$')
_repeated_spaces = re.compile(r'\s\s+')
_repeated_dots = re.compile(r'\.\.+')
_uuid = re.compile(
    r'^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}$')

# only temporary until bleach has a release > 1.4.1 -
_email_regex = re.compile(
    r"([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
    r"{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
    r"\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"
)

# detects multiple successive newlines
_multiple_newlines = re.compile(r'\n{2,}', re.MULTILINE)

# detect starting strings of phone inside a link
_phone_inside_a_tags = r'(\">|href=\"tel:)?'

# regex pattern for swiss phone numbers
_phone_ch_country_code = r'(\+41|0041|0[0-9]{2})'
_phone_ch = re.compile(_phone_ch_country_code + r'([ \r\f\t\d]+)')

# Adds a regex group to capture if a leading a tag is present or if the
# number is part of the href attributes
_phone_ch_html_safe = re.compile(
    _phone_inside_a_tags + _phone_ch_country_code + r'([ \r\f\t\d]+)')

# for yubikeys
ALPHABET = 'cbdefghijklnrtuv'
ALPHABET_RE = re.compile(r'^[cbdefghijklnrtuv]{12,44}$')


@contextmanager
def local_lock(namespace: str, key: str) -> Iterator[None]:
    """ Locks the given namespace/key combination on the current system,
    automatically freeing it after the with statement has been completed or
    once the process is killed.

    Usage::

        with lock('namespace', 'key'):
            pass

    """
    name = f'{namespace}-{key}'.replace('/', '-')

    # NOTE: hardcoding /tmp is a bit piggy, but on the other hand we
    #       don't want different processes to miss each others locks
    #       just because one of them has a different TMPDIR, can we
    #       come up with a more robust way of doing this, e.g. with
    #       named semaphores?
    with open(f'/tmp/{name}', 'w+') as f:  # nosec:B108
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
            fcntl.flock(f, fcntl.LOCK_UN)
        except BlockingIOError as exception:
            raise AlreadyLockedError from exception


def normalize_for_url(text: str) -> str:
    """ Takes the given text and makes it fit to be used for an url.

    That means replacing spaces and other unwanted characters with '-',
    lowercasing everything and turning unicode characters into their closest
    ascii equivalent using Unidecode.

    See https://pypi.python.org/pypi/Unidecode

    """

    # German is our main language, so we are extra considerate about it
    # (unidecode turns ü into u)
    text = text.replace('ü', 'ue')
    text = text.replace('ä', 'ae')
    text = text.replace('ö', 'oe')
    clean = _unwanted_url_chars.sub('-', unidecode(text).strip(' ').lower())
    clean = _double_dash.sub('-', clean)
    clean = clean.strip('-')

    return clean


def normalize_for_path(
    text: str,
    default: str = '_default_path_'
) -> str:
    """
    Takes the given text and makes it fit to be used for a path. It replaces
    invalid characters (for windows and linux systems) with underscores.
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', text).strip()
    return sanitized or default


def normalize_for_filename(
    text: str,
    default: str = '_default_filename_'
) -> str:
    """
    Takes the given text and makes it fit to be used as a filename for windows
    and linux systems. Replaces invalid characters with underscores.
    """
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', text)
    sanitized = sanitized.strip().strip('.')
    sanitized = sanitized or default

    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def increment_name(name: str) -> str:
    """ Takes the given name and adds a numbered suffix beginning at 1.

    For example::

        foo => foo-1
        foo-1 => foo-2

    """

    match = _number_suffix.search(name)
    if match:
        number_str = match.group(1)
        next_number = int(number_str) + 1
        return f'{name[:-len(number_str)]}{next_number}'
    else:
        return f'{name}-1'


def remove_repeated_spaces(text: str) -> str:
    """ Removes repeated spaces in the text ('a  b' -> 'a b'). """

    return _repeated_spaces.sub(' ', text)


def remove_repeated_dots(text: str) -> str:
    """ Removes repeated dots in the text ('a..b' -> 'a.b'). """

    return _repeated_dots.sub('.', text)


@contextmanager
def profile(filename: str) -> Iterator[None]:
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
def timing(name: str | None = None) -> Iterator[None]:
    """ Runs the wrapped code and prints the time in ms it took to run it.
    The name is printed in front of the time, if given.

    """
    start = perf_counter()

    yield

    duration_ms = 1000.0 * (perf_counter() - start)

    if name:
        print(f'{name}: {duration_ms:.0f} ms')  # noqa: T201
    else:
        print(f'{duration_ms:.0f} ms')  # noqa: T201


@lru_cache(maxsize=32)
def module_path_root(module: ModuleType | str) -> str:
    if isinstance(module, str):
        module = importlib.import_module(module)

    assert module is not None

    return os.path.dirname(inspect.getfile(module))


def module_path(module: ModuleType | str, subpath: str) -> str:
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


def touch(file_path: str) -> None:
    """ Touches the file on the given path. """
    try:
        os.utime(file_path, None)
    except Exception:
        open(file_path, 'a').close()


class Bunch:
    """ A simple but handy "collector of a bunch of named stuff" class.

    See `<https://code.activestate.com/recipes/\
    52308-the-simple-but-handy-collector-of-a-bunch-of-named/>`_.

    For example::

        point = Bunch(x=1, y=2)
        assert point.x == 1
        assert point.y == 2

        point.z = 3
        assert point.z == 3

    Allows the creation of simple nested bunches, for example::

        request = Bunch(**{'app.settings.org.my_setting': True})
        assert request.app.settings.org.my_setting is True

    """
    def __init__(self, **kwargs: Any):
        self.__dict__.update(
            (key, value)
            for key, value in kwargs.items()
            if '.' not in key
        )
        for key, value in kwargs.items():
            if '.' in key:
                name, _, key = key.partition('.')
                setattr(self, name, Bunch(**{key: value}))

    if TYPE_CHECKING:
        # let mypy know that any attribute access could be valid
        def __getattr__(self, name: str) -> Any: ...
        def __setattr__(self, name: str, value: Any) -> None: ...
        def __delattr__(self, name: str) -> None: ...

    def __eq__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


def render_file(file_path: str, request: CoreRequest) -> Response:
    """ Takes the given file_path (content) and renders it to the browser.
    The file must exist on the local system and be readable by the current
    process.

    """

    def hash_path(path: str) -> str:
        return hashlib.new(  # nosec:B324
            'sha1',
            path.encode('utf-8'),
            usedforsecurity=False
        ).hexdigest()

    # this is a very cachable result - though it's possible that a file
    # changes it's content type, it should usually not, especially since
    # we emphasize the use of random filenames
    @request.app.cache.cache_on_arguments(to_str=hash_path)
    def get_content_type(file_path: str) -> str:
        content_type = mimetypes.guess_type(file_path)[0]

        if not content_type:
            content_type = magic.from_file(file_path, mime=True)

        return content_type

    return request.get_response(
        static.FileApp(file_path, content_type=get_content_type(file_path)))


def hash_dictionary(dictionary: dict[str, Any]) -> str:
    """ Computes a sha256 hash for the given dictionary. The dictionary
    is expected to only contain values that can be serialized by json.

    That includes int, decimal, string, boolean.

    Note that this function is not meant to be used for hashing secrets. Do
    not include data in this dictionary that is secret!

    """
    # NOTE: For backwards compatibility we use the old json encoder
    #       otherwise our hashes change depending on whether or not
    #       the dictionary contained non-ASCII characters
    dict_as_string = json.dumps(
        dictionary,
        sort_keys=True,
        ensure_ascii=True
    ).encode('ascii')
    return hashlib.new(  # nosec:B324
        'sha1',
        dict_as_string,
        usedforsecurity=False
    ).hexdigest()


@overload
def groupbylist(
    iterable: Iterable[_T],
    key: None = ...
) -> list[tuple[_T, list[_T]]]: ...


@overload
def groupbylist(
    iterable: Iterable[_T],
    key: Callable[[_T], _KT]
) -> list[tuple[_KT, list[_T]]]: ...


def groupbylist(
    iterable: Iterable[_T],
    key: Callable[[_T], Any] | None = None
) -> list[tuple[Any, list[_T]]]:
    """ Works just like Python's ``itertools.groupby`` function, but instead
    of returning generators, it returns lists.

    """
    return [(k, list(g)) for k, g in groupby(iterable, key=key)]


def linkify_phone(text: str) -> Markup:
    """ Takes a string and replaces valid phone numbers with html links. If a
    phone number is matched, it will be replaced by the result of a callback
    function, that does further checks on the regex match. If these checks do
    not pass, the matched number will remain unchanged.

    """

    def strip_whitespace(number: str) -> str:
        return re.sub(r'\s', '', number)

    def is_valid_length(number: str) -> bool:
        if number.startswith('+00'):
            return False
        if number.startswith('00'):
            return len(number) == 13
        elif number.startswith('0'):
            return len(number) == 10
        elif number.startswith('+'):
            return len(number) == 12
        return False

    def handle_match(match: Match[str]) -> str:
        inside_html = match.group(1)
        number = f'{match.group(2)}{match.group(3)}'
        assert not number.endswith('\n')
        if inside_html:
            return match.group(0)
        if is_valid_length(strip_whitespace(number)):
            number = remove_repeated_spaces(number).strip()
            return Markup(
                '<a href="tel:{number}">{number}</a> '
            ).format(number=number)

        return match.group(0)

    # NOTE: re.sub isn't Markup aware, so we need to re-wrap
    return Markup(  # nosec: B704
        _phone_ch_html_safe.sub(handle_match, escape(text)))


@cache
def top_level_domains() -> set[str]:
    try:
        return URLExtract()._load_cached_tlds()
    except CacheFileError:
        pass
    # fallback
    return {'agency', 'ngo', 'swiss', 'gle'}


def linkify(text: str | None) -> Markup:
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
        return Markup('')

    def remove_dots(tlds: set[str]) -> list[str]:
        return [domain[1:] for domain in tlds]

    # bleach.linkify supports only a fairly limited amount of tlds
    additional_tlds = top_level_domains()
    if any(domain in text for domain in additional_tlds):

        all_tlds = list(set(TLDS + remove_dots(additional_tlds)))

        # Longest first, to prevent eager matching, if for example
        # .co is matched before .com
        all_tlds.sort(key=len, reverse=True)

        bleach_linker = bleach.Linker(
            url_re=bleach.linkifier.build_url_re(tlds=all_tlds),
            email_re=bleach.linkifier.build_email_re(tlds=all_tlds),
            parse_email=True if '@' in text else False
        )
        # NOTE: bleach's linkify always returns a plain string
        #       so we need to re-wrap
        linkified = linkify_phone(Markup(  # nosec: B704
            bleach_linker.linkify(escape(text)))
        )

    else:
        # NOTE: bleach's linkify always returns a plain string
        #       so we need to re-wrap
        linkified = linkify_phone(Markup(  # nosec: B704
            bleach.linkify(escape(text), parse_email=True))
        )

    # NOTE: this is already vetted markup, don't clean it
    if isinstance(text, Markup):
        return linkified

    return Markup(bleach.clean(  # nosec: B704
        linkified,
        tags=['a'],
        attributes={'a': ['href', 'rel']},
        protocols=['http', 'https', 'mailto', 'tel']
    ))


def paragraphify(text: str) -> Markup:
    """ Takes a text with newlines groups them into paragraphs according to the
    following rules:

    If there's a single newline between two lines, a <br> will replace that
    newline.

    If there are multiple newlines between two lines, each line will become
    a paragraph and the extra newlines are discarded.

    """
    text = text and text.replace('\r', '').strip('\n')

    if not text:
        return Markup('')

    was_markup = isinstance(text, Markup)

    return Markup('').join(
        Markup('<p>{}</p>').format(
            (
                # NOTE: re.split returns a plain str, so we need to restore
                #       markup based on whether it was markup before
                Markup(p) if was_markup  # nosec: B704
                else escape(p)
            ).replace('\n', Markup('<br>'))
        )
        for p in _multiple_newlines.split(text)
    )


def to_html_ul(
    value: str | None,
    convert_dashes: bool = True,
    with_title: bool = False
) -> Markup:
    """ Linkify and convert to text to one or multiple ul's or paragraphs.
    """
    if not value:
        return Markup('')

    value = value.replace('\r', '').strip('\n')
    value = value.replace('\n\n', '\n \n')

    if not convert_dashes:
        return Markup('<p>{}</p>').format(
            Markup('<br>').join(linkify(value).splitlines())
        )

    elements = []
    temp: list[Markup] = []

    def ul(inner: str) -> Markup:
        return Markup('<ul class="bulleted">{}</ul>').format(inner)

    def li(inner: str) -> Markup:
        return Markup('<li>{}</li>').format(inner)

    def p(inner: str) -> Markup:
        return Markup('<p>{}</p>').format(inner)

    was_list = False

    for i, line in enumerate(value.splitlines()):
        if not line:
            continue

        line = linkify(line)
        is_list = line.startswith('-')
        new_p_or_ul = True if line == ' ' else False

        line = line.lstrip('-').strip()

        if with_title:
            elements.append(p(
                Markup('<span class="title">{}</span>').format(line)))
            with_title = False
        else:
            if new_p_or_ul or (was_list != is_list and i > 0):
                elements.append(
                    ul(Markup('').join(temp)) if was_list
                    else p(Markup('<br>').join(temp))
                )
                temp = []
                was_list = False

            if not new_p_or_ul:
                temp.append(li(line) if is_list else line)

        new_p_or_ul = False
        was_list = is_list

    if temp:
        elements.append(
            ul(Markup('').join(temp)) if was_list
            else p(Markup('<br>').join(temp))
        )

    return Markup('').join(elements)


@overload
def ensure_scheme(url: str, default: str = 'http') -> str: ...
@overload
def ensure_scheme(url: None, default: str = 'http') -> None: ...


def ensure_scheme(url: str | None, default: str = 'http') -> str | None:
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


def is_uuid(value: object) -> bool:
    """ Returns true if the given value is a uuid. The value may be a string
    or of type UUID. If it's a string, the uuid is checked with a regex.
    """
    if isinstance(value, str):
        return _uuid.match(str(value)) and True or False

    return isinstance(value, UUID)


def is_non_string_iterable(obj: object) -> bool:
    """ Returns true if the given obj is an iterable, but not a string. """
    return not isinstance(obj, (str, bytes)) and isinstance(obj, Iterable)


def relative_url(absolute_url: str | None) -> str:
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


def is_subpath(directory: str, path: str) -> bool:
    """ Returns true if the given path is inside the given directory. """
    directory = os.path.join(os.path.realpath(directory), '')
    path = os.path.realpath(path)

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([path, directory]) == directory


@overload
def is_sorted(
    iterable: Iterable[SupportsRichComparison],
    key: Callable[[SupportsRichComparison], SupportsRichComparison] = ...,
    reverse: bool = ...
) -> bool: ...


@overload
def is_sorted(
    iterable: Iterable[_T],
    key: Callable[[_T], SupportsRichComparison],
    reverse: bool = ...
) -> bool: ...


# FIXME: Do we really want to allow any Iterable? This seems like a bad
#        idea to me... Iterators will be consumed and the Iterable might
#        be infinite. This seems like it should be a Container instead,
#        then we also don't need to use tee or list to make a copy
def is_sorted(
    iterable: Iterable[Any],
    key: Callable[[Any], SupportsRichComparison] = lambda i: i,
    reverse: bool = False
) -> bool:
    """ Returns True if the iterable is sorted. """

    # NOTE: we previously used `tee` here, but since `sorted` consumes
    #       the entire iterator, this is the exact case where tee is
    #       slower than just pulling the entire sequence into a list
    seq = list(iterable)

    for a, b in zip(seq, sorted(seq, key=key, reverse=reverse)):
        if a is not b:
            return False

    return True


def morepath_modules(cls: type[morepath.App]) -> Iterator[str]:
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


def scan_morepath_modules(cls: type[morepath.App]) -> None:
    """ Tries to scan all the morepath modules required for the given
    application class. This is not guaranteed to stay reliable as there is
    no sure way to discover all modules required by the application class.

    """
    for module in sorted(morepath_modules(cls)):
        morepath.scan(import_module(module))


def get_unique_hstore_keys(
    session: Session,
    column: ColumnElement[dict[str, Any]]
            | ColumnElement[dict[str, Any] | None]
            | ColumnElement[Mapping[str, Any]]
            | ColumnElement[Mapping[str, Any] | None]
) -> set[str]:
    """ Returns a set of keys found in an hstore column over all records
    of its table.

    """

    base = session.query(column.keys()).with_entities(
        sqlalchemy.func.skeys(column).label('keys'))

    query = sqlalchemy.select(  # type: ignore[var-annotated]
        sqlalchemy.func.array_agg(sqlalchemy.column('keys'))
    ).select_from(base.subquery()).distinct()

    keys = session.execute(query).scalar()
    return set(keys) if keys else set()


def makeopendir(fs: FS, directory: str) -> SubFS[FS]:
    """ Creates and opens the given directory in the given PyFilesystem. """

    if not fs.isdir(directory):
        fs.makedir(directory)

    return fs.opendir(directory)


def append_query_param(url: str, key: str, value: str) -> str:
    """ Appends a single query parameter to an url. This is faster than
    using Purl, if and only if we only add one query param.

    Also this function assumes that the value is already url encoded.

    """
    template = '{}&{}={}' if '?' in url else '{}?{}={}'
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

    def __init__(
        self,
        url: str,
        data: bytes,
        headers: Collection[tuple[str, str]],
        timeout: float = 30
    ):
        Thread.__init__(self)
        self.url = url
        self.data = data
        self.headers = headers
        self.timeout = timeout

    def run(self) -> None:
        try:
            # Validate URL protocol before opening it, since it's possible to
            # open ftp:// and file:// as well.
            if not self.url.lower().startswith('http'):
                raise ValueError from None

            request = urllib.request.Request(self.url)
            for header in self.headers:
                request.add_header(header[0], header[1])
            urllib.request.urlopen(  # nosec B310
                request, self.data, self.timeout
            )
        except Exception as e:
            log.error(
                'Error while sending a POST request to {}: {}'.format(
                    self.url, str(e)
                )
            )


def toggle(collection: set[_T], item: _T | None) -> set[_T]:
    """ Returns a new set where the item has been toggled. """

    if item is None:
        return collection

    if item in collection:
        return collection - {item}
    else:
        return collection | {item}


def binary_to_dictionary(
    binary: bytes,
    filename: str | None = None
) -> FileDict:
    """ Takes raw binary filedata and stores it in a dictionary together
    with metadata information.

    The data is compressed before it is stored int he dictionary. Use
    :func:`dictionary_to_binary` to get the original binary data back.

    """

    assert isinstance(binary, bytes)

    mimetype = magic.from_buffer(binary, mime=True)

    # according to https://tools.ietf.org/html/rfc7111, text/csv should be used
    if mimetype == 'application/csv':
        mimetype = 'text/csv'

    gzipdata = BytesIO()

    with gzip.GzipFile(fileobj=gzipdata, mode='wb') as f:
        f.write(binary)

    return {
        'data': base64.b64encode(gzipdata.getvalue()).decode('ascii'),
        'filename': filename,
        'mimetype': mimetype,
        'size': len(binary)
    }


def dictionary_to_binary(dictionary: LaxFileDict) -> bytes:
    """ Takes a dictionary created by :func:`binary_to_dictionary` and returns
    the original binary data.

    """
    data = base64.b64decode(dictionary['data'])

    with gzip.GzipFile(fileobj=BytesIO(data), mode='r') as f:
        return f.read()


@overload
def safe_format(
    format: str,
    dictionary: dict[str, str | int | float],
    types: None = ...,
    adapt: Callable[[str], str] | None = ...,
    raise_on_missing: bool = ...
) -> str: ...


@overload
def safe_format(
    format: str,
    dictionary: dict[str, _T],
    types: set[type[_T]] = ...,
    adapt: Callable[[str], str] | None = ...,
    raise_on_missing: bool = ...
) -> str: ...


def safe_format(
    format: str,
    dictionary: dict[str, Any],
    types: set[type[Any]] | None = None,
    adapt: Callable[[str], str] | None = None,
    raise_on_missing: bool = False
) -> str:
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

    types = types or {int, str, float}
    output = StringIO()
    buffer = StringIO()
    opened = 0

    for char in format:
        if char == '[':
            opened += 1

        if char == ']':
            opened -= 1

        if opened == 1 and char != '[' and char != ']':
            print(char, file=buffer, end='')
            continue

        if opened == 2 or opened == -2:
            if buffer.tell():
                raise RuntimeError('Unexpected bracket inside bracket found')

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


def safe_format_keys(
    format: str,
    adapt: Callable[[str], str] | None = None
) -> list[str]:
    """ Takes a :func:`safe_format` string and returns the found keys. """

    keys = []

    def adapt_and_record(key: str) -> str:
        key = adapt(key) if adapt else key
        keys.append(key)

        return key

    safe_format(format, {}, adapt=adapt_and_record)

    return keys


def is_valid_yubikey(
    client_id: str,
    secret_key: str,
    expected_yubikey_id: str,
    yubikey: str
) -> bool:
    """ Asks the yubico validation servers if the given yubikey OTP is valid.

    :client_id:
        The yubico API client id.

    :secret_key:
        The yubico API secret key.

    :expected_yubikey_id:
        The expected yubikey id. The yubikey id is defined as the first twelve
        characters of any yubikey value. Each user should have a yubikey
        associated with it's account. If the yubikey value comes from a
        different key, the key is invalid.

    :yubikey:
        The actual yubikey value that should be verified.

    :return: True if yubico confirmed the validity of the key.

    """
    assert client_id and secret_key and expected_yubikey_id and yubikey
    assert len(expected_yubikey_id) == 12

    try:
        return Yubico(client_id, secret_key).verify(yubikey)
    except StatusCodeError as e:
        if e.status_code != 'REPLAYED_OTP':
            raise

        return False
    except SignatureVerificationError:
        return False


def is_valid_yubikey_format(otp: str) -> bool:
    """ Returns True if the given OTP has the correct format. Does not actually
    contact Yubico, so this function may return true, for some invalid keys.

    """

    return ALPHABET_RE.match(otp) and True or False


def yubikey_otp_to_serial(otp: str) -> int | None:
    """ Takes a Yubikey OTP and calculates the serial number of the key.

    The serial key is printed on the yubikey, in decimal and as a QR code.

    Example::

        >>> yubikey_otp_to_serial(
            'ccccccdefghdefghdefghdefghdefghdefghdefghklv')
        2311522

    Adapted from Java::

        https://github.com/Yubico/yubikey-salesforce-client/blob/
        e38e46ee90296a852374a8b744555e99d16b6ca7/src/classes/Modhex.cls

    If the key cannot be calculated, None is returned. This can happen if
    they key is malformed.

    """

    if not is_valid_yubikey_format(otp):
        return None

    token = 'cccc' + otp[:12]

    toggle = False
    keep = 0

    bytesarray = []

    for char in token:
        n = ALPHABET.index(char)

        toggle = not toggle

        if toggle:
            keep = n
        else:
            bytesarray.append((keep << 4) | n)

    value = 0

    # in Java, shifts on integers are masked with 0x1f using AND
    # https://docs.oracle.com/javase/specs/jls/se8/html/jls-15.html#jls-15.19
    mask_value = 0x1f

    for i in range(8):
        shift = (4 - 1 - i) * 8
        value += (bytesarray[i] & 255) << (shift & mask_value)

    return value


def yubikey_public_id(otp: str) -> str:
    """ Returns the yubikey identity given a token. """

    return otp[:12]


def dict_path(dictionary: dict[str, _T], path: str) -> _T:
    """ Gets the value of the given dictionary at the given path.

    For example::

        >>> data = {'foo': {'bar': True}}
        >>> dict_path(data, 'foo.bar')
        True

    """

    if not dictionary:
        raise KeyError()

    return reduce(operator.getitem, path.split('.'), dictionary)  # type:ignore


def safe_move(src: str, dst: str, tmp_dst: str | None = None) -> None:
    """ Rename a file from ``src`` to ``dst``.

    Optionally provide a ``tmp_dst`` where the file will be copied to
    before being renamed. This needs to be on the same filesystem as
    ``tmp``, otherwise this will fail.

    * Moves must be atomic.  ``shutil.move()`` is not atomic.

    * Moves must work across filesystems.  Often temp directories and the
      cache directories live on different filesystems.  ``os.rename()`` can
      throw errors if run across filesystems.

    So we try ``os.rename()``, but if we detect a cross-filesystem copy, we
    switch to ``shutil.move()`` with some wrappers to make it atomic.

    Via https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python

    """
    try:
        os.rename(src, dst)
    except OSError as err:

        if err.errno == errno.EXDEV:
            # Generate a unique ID, and copy `<src>` to the target directory
            # with a temporary name `<dst>.<ID>.tmp`.  Because we're copying
            # across a filesystem boundary, this initial copy may not be
            # atomic.  We intersperse a random UUID so if different processes
            # are copying into `<dst>`, they don't overlap in their tmp copies.
            copy_id = uuid4()
            tmp_dst = f'{tmp_dst or dst}.{copy_id}.tmp'
            shutil.copyfile(src, tmp_dst)

            # Then do an atomic rename onto the new name, and clean up the
            # source file.
            os.rename(tmp_dst, dst)
            os.unlink(src)
        else:
            raise


@overload
def batched(
    iterable: Iterable[_T],
    batch_size: int,
    container_factory: type[tuple] = ...  # type:ignore[type-arg]
) -> Iterator[tuple[_T, ...]]: ...


@overload
def batched(
    iterable: Iterable[_T],
    batch_size: int,
    container_factory: type[list]  # type:ignore[type-arg]
) -> Iterator[list[_T]]: ...


# NOTE: If there were higher order TypeVars, we could properly infer
#       the type of the Container, for now we just add overloads for
#       two of the most common container_factories
@overload
def batched(
    iterable: Iterable[_T],
    batch_size: int,
    container_factory: Callable[[Iterator[_T]], Collection[_T]]
) -> Iterator[Collection[_T]]: ...


def batched(
    iterable: Iterable[_T],
    batch_size: int,
    container_factory: Callable[[Iterator[_T]], Collection[_T]] = tuple
) -> Iterator[Collection[_T]]:
    """ Splits an iterable into batches of batch_size and puts them
    inside a given collection (tuple by default).

    The container_factory is necessary in order to consume the iterator
    returned by islice. Otherwise this function would never return.

    """

    iterator = iter(iterable)
    while True:
        batch = container_factory(islice(iterator, batch_size))
        if len(batch) == 0:
            return

        yield batch


def generate_fts_phonenumbers(numbers: Iterable[str | None]) -> list[str]:
    """
    Generates a list of phonenumbers in various formats for full text search.
    The international, the national and the local format as well as the
    extension.

    """
    result = []

    for number in numbers:
        if not number:
            continue

        try:
            parsed = parse(number, 'CH')
        except NumberParseException:
            # allow invalid phone number
            result.append(number.replace(' ', ''))
            continue

        result.append(format_number(
            parsed, PhoneNumberFormat.E164))

        national = format_number(
            parsed, PhoneNumberFormat.NATIONAL)
        groups = national.split()
        for idx in range(len(groups)):
            partial = ''.join(groups[idx:])
            if len(partial) > 3:
                result.append(partial)

    return result
