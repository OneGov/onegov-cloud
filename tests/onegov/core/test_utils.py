from __future__ import annotations

import onegov.core
import os.path
import pytest
import re
import transaction

from markupsafe import Markup
from onegov.core import utils
from onegov.core.custom import json
from onegov.core.errors import AlreadyLockedError
from onegov.core.orm import SessionManager
from onegov.core.orm.types import HSTORE
from onegov.core.utils import Bunch, linkify_phone, _phone_ch, to_html_ul
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base  # type: ignore[attr-defined]
from unittest.mock import patch
from urlextract import URLExtract
from uuid import uuid4
from yubico_client import Yubico  # type: ignore[import-untyped]

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from onegov.core.orm import Base  # noqa: F401
    from sqlalchemy.orm import Session


def test_normalize_for_url() -> None:
    assert utils.normalize_for_url('asdf') == 'asdf'
    assert utils.normalize_for_url('Asdf') == 'asdf'
    assert utils.normalize_for_url('A S d f') == 'a-s-d-f'
    assert utils.normalize_for_url('far  away') == 'far-away'
    assert utils.normalize_for_url('währung') == 'waehrung'
    assert utils.normalize_for_url('grün') == 'gruen'
    assert utils.normalize_for_url('rötlich') == 'roetlich'
    assert utils.normalize_for_url('one/two') == 'one-two'
    assert utils.normalize_for_url('far / away') == 'far-away'
    assert utils.normalize_for_url('far <away>') == 'far-away'
    assert utils.normalize_for_url('far (away)') == 'far-away'
    assert utils.normalize_for_url('--ok--') == 'ok'
    assert utils.normalize_for_url('a...b..c.d') == 'a-b-c-d'


@pytest.mark.parametrize("input_path, default, expected", [
    ('', None, '_default_path_'),
    ('>', None, '_'),
    ('<:>', None, '___'),
    ('\\/n', None, '__n'),
    (' my path  name is great!  ', None, 'my path  name is great!'),
    ('a/b/c', None, 'a_b_c'),
    ('.-test.', None, '.-test.'),
    ('abc:*?', None, 'abc___'),
    ('\\[hello]|', None, '_[hello]_'),
    ('a/b/c', 'x', 'a_b_c'),
    ('<ll', 'x', '_ll'),
    ('', 'x', 'x'),
])
def test_normalize_for_path(
    input_path: str,
    default: str,
    expected: str
) -> None:
    if default:
        assert utils.normalize_for_path(input_path, default) == expected
    else:
        assert utils.normalize_for_path(input_path) == expected


@pytest.mark.parametrize("input_text, default, expected", [
    ('', None, '_default_filename_'),
    ('invalid<>:"/\\|?*chars.txt', None, 'invalid_________chars.txt'),
    ('  filename  ', None, 'filename'),
    ('.filename.', None, 'filename'),
    ('a' * 300, None, 'a' * 255),
    ('<>:|?*', None, '______'),
    ('', 'custom_default', 'custom_default'),
    ('<>:|?*', 'fallback', '______'),
    ('   ', 'empty_default', 'empty_default'),
    ('.', 'dot_default', 'dot_default'),
    ('valid_name', 'ignored_default', 'valid_name'),
])
def test_normalize_for_filename(
    input_text: str,
    default: str,
    expected: str
) -> None:
    if default:
        assert utils.normalize_for_filename(
            input_text, default=default) == expected
    else:
        assert utils.normalize_for_filename(input_text) == expected


def test_touch(temporary_directory: str) -> None:
    path = os.path.join(temporary_directory, 'test.txt')

    assert not os.path.isfile(path)

    utils.touch(path)

    assert os.path.isfile(path)

    with open(path, 'w') as f:
        f.write('asdf')

    utils.touch(path)

    with open(path, 'r') as f:
        assert f.read() == 'asdf'


def test_module_path() -> None:
    path = utils.module_path('onegov.core', 'utils.py')
    assert path == utils.module_path(onegov.core, 'utils.py')
    assert path == utils.module_path(onegov.core, '/utils.py')
    assert os.path.isfile(path)

    with pytest.raises(AssertionError):
        utils.module_path(onegov.core, '../passwd')


valid_test_phone_numbers = [
    '+41 44 453 45 45',
    '+41 79434 3254',
    '+41     79434     3254',
    '+4179434 3254',
    '004179434 3254',
    '044 302 35 87',
    '079 720 55 03',
    '0797205503',
    '0413025643',
    '041 324 4321',
]

# +041 324 4321 will treat + like a normal text around

invalid_test_phone_numbers = [
    Markup('<a href="tel:061 444 44 44">061 444 44 44</a>'),
    Markup('">+41 44 453 45 45'),
    'some text',
    '+31 654 32 54',
    '+0041 543 44 44',
    '0041-24400321',
    '0043 555 32 43'
]


@pytest.mark.parametrize("number", valid_test_phone_numbers)
def test_phone_regex_groups_valid(number: str) -> None:
    gr = re.search(_phone_ch, number)
    assert gr is not None
    assert gr.group(0)
    assert gr.group(1)
    assert gr.group(2)


@pytest.mark.parametrize("number", valid_test_phone_numbers)
def test_phone_linkify_valid(number: str) -> None:
    r = linkify_phone(number)
    number = utils.remove_repeated_spaces(number)
    wanted = Markup(
        '<a href="tel:{number}">{number}</a> '
    ).format(number=number)
    assert r == wanted
    # Important !
    assert linkify_phone(wanted) == wanted


@pytest.mark.parametrize("number", invalid_test_phone_numbers)
def test_phone_linkify_invalid(number: str) -> None:
    r = linkify_phone(number)
    assert r == number


def test_linkify() -> None:
    # this is really bleach's job, but we want to run the codepath anyway
    assert utils.linkify('info@example.org') == Markup(
        '<a href="mailto:info@example.org">info@example.org</a>'
    )
    assert utils.linkify('https://google.ch') == Markup(
        '<a href="https://google.ch" rel="nofollow">https://google.ch</a>')

    # by default, linkify sanitizes the text before linkifying it
    assert utils.linkify('info@example.org<br>') == Markup(
        '<a href="mailto:info@example.org">info@example.org</a>&lt;br&gt;')

    # we can circumvent that by passing in Markup however
    assert utils.linkify(Markup('info@example.org<br>')) == Markup(
        '<a href="mailto:info@example.org">info@example.org</a><br>')

    # test a longer html string with valid phone number
    tel_nr = valid_test_phone_numbers[0]
    text = Markup('2016/2019<br>{}').format(tel_nr)
    assert utils.linkify(text) == Markup(
        f'2016/2019<br><a href="tel:{tel_nr}">{tel_nr}</a> ')


@pytest.mark.parametrize("tel", [
    ('Tel. +41 41 728 33 11',
     'Tel. <a href="tel:+41 41 728 33 11">+41 41 728 33 11</a> '),
    ('\nTel. +41 41 728 33 11\n',
     '\nTel. <a href="tel:+41 41 728 33 11">+41 41 728 33 11</a> \n'),
])
def test_linkify_with_phone(tel: str) -> None:
    assert utils.linkify(tel[0]) == Markup(tel[1])


def test_linkify_with_phone_newline() -> None:
    assert utils.linkify('Foo\n041 123 45 67') == Markup(
        'Foo\n<a href="tel:041 123 45 67">041 123 45 67</a> '
    )


def test_linkify_with_custom_domains() -> None:
    assert utils.linkify(
        "https://forms.gle/123\nfoo@bar.agency\nfoo@bar.co\nfoo@bar.com\n"
        "https://foobar.agency\n+41 41 511 21 21\nfoo@bar.ngo"
    ) == Markup(
        "<a href=\"https://forms.gle/123\" rel=\"nofollow\">"
        "https://forms.gle/123</a>\n<a href=\"mailto:foo@bar.agency\">"
        "foo@bar.agency</a>\n<a href=\"mailto:foo@bar.co\">foo@bar.co</a>\n"
        "<a href=\"mailto:foo@bar.com\">foo@bar.com</a>\n"
        "<a href=\"https://foobar.agency\" rel=\"nofollow\">"
        "https://foobar.agency</a>\n<a href=\"tel:+41 41 511 21 21\">"
        "+41 41 511 21 21</a> \n<a href=\"mailto:foo@bar.ngo\">foo@bar.ngo</a>"
    )


def test_linkify_with_custom_domain_and_with_email_and_links() -> None:
    assert utils.linkify(
        "foo@bar.agency\nhttps://thismatters.agency\nhttps://google.com"
    ) == Markup(
        "<a href=\"mailto:foo@bar.agency\">foo@bar.agency</a>\n"
        "<a href=\"https://thismatters.agency\" rel=\"nofollow\">"
        "https://thismatters.agency</a>\n<a href=\"https://google.com\" rel"
        "=\"nofollow\">https://google.com</a>")


def test_linkify_with_custom_domain_and_without_email() -> None:
    expected_link = Markup(
        "<a href=\"https://thismatters.agency\" "
        "rel=\"nofollow\">https://thismatters.agency</a>"
    )
    expected_link2 = Markup(
        "<a href=\"https://google.com\" rel=\"nofollow\">"
        "https://google.com</a>"
    )

    # linkify should work even if no email is present
    expected = Markup('\n').join([expected_link, expected_link2])
    assert utils.linkify(
        "https://thismatters.agency\nhttps://google.com"
    ) == expected


def test_load_tlds() -> None:
    def remove_dots(tlds: list[str]) -> list[str]:
        return [domain[1:] for domain in tlds]

    extract = URLExtract()
    tlds = remove_dots(extract._load_cached_tlds())

    assert all("." not in item for item in tlds)
    assert len(tlds) > 1600  # make sure the reading worked

    # if these are not in the list, the list is probably outdated
    additional_tlds = ['agency', 'ngo', 'swiss', 'gle']
    assert all(domain in tlds for domain in additional_tlds)


def test_increment_name() -> None:
    assert utils.increment_name('test') == 'test-1'
    assert utils.increment_name('test-2') == 'test-3'
    assert utils.increment_name('test2') == 'test2-1'
    assert utils.increment_name('test-1-1') == 'test-1-2'


def test_ensure_scheme() -> None:
    assert utils.ensure_scheme(None) is None
    assert utils.ensure_scheme('seantis.ch') == 'http://seantis.ch'
    assert utils.ensure_scheme('seantis.ch', 'https') == 'https://seantis.ch'

    assert utils.ensure_scheme('google.ch?q=onegov.cloud') \
           == 'http://google.ch?q=onegov.cloud'

    assert utils.ensure_scheme('https://abc.xyz') == 'https://abc.xyz'


def test_is_uuid() -> None:
    assert not utils.is_uuid(None)
    assert not utils.is_uuid('')
    assert not utils.is_uuid('asdf')
    assert not utils.is_uuid(uuid4().hex + 'x')
    assert utils.is_uuid(uuid4())
    assert utils.is_uuid(str(uuid4()))
    assert utils.is_uuid(uuid4().hex)


def test_is_non_string_iterable() -> None:
    assert utils.is_non_string_iterable([])
    assert utils.is_non_string_iterable(tuple())
    assert utils.is_non_string_iterable({})
    assert not utils.is_non_string_iterable('abc')
    assert not utils.is_non_string_iterable(b'abc')
    assert not utils.is_non_string_iterable(None)


def test_relative_url() -> None:
    assert utils.relative_url('https://www.google.ch/test') == '/test'
    assert utils.relative_url('https://usr:pwd@localhost:443/test') == '/test'
    assert utils.relative_url('/test') == '/test'
    assert utils.relative_url('/test?x=1&y=2') == '/test?x=1&y=2'
    assert utils.relative_url('/test?x=1&y=2#link') == '/test?x=1&y=2#link'


def test_is_subpath() -> None:
    assert utils.is_subpath('/', '/test')
    assert utils.is_subpath('/asdf', '/asdf/asdf')
    assert not utils.is_subpath('/asdf/', '/asdf')
    assert not utils.is_subpath('/a', '/b')
    assert not utils.is_subpath('/a', '/a/../b')


def test_is_sorted() -> None:
    assert utils.is_sorted('abc')
    assert not utils.is_sorted('aBc')
    assert utils.is_sorted('aBc', key=lambda i: i.lower())
    assert not utils.is_sorted('321')
    assert utils.is_sorted('321', reverse=True)


def test_get_unique_hstore_keys(postgres_dsn: str) -> None:
    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Document(Base):
        __tablename__ = 'documents'

        id: Column[int] = Column(Integer, primary_key=True)
        _tags: Column[Mapping[str, Any] | None] = Column(HSTORE, nullable=True)

        @property
        def tags(self) -> set[str]:
            return set(self._tags.keys()) if self._tags else set()

        @tags.setter
        def tags(self, value: Collection[str]) -> None:
            self._tags = {k: '' for k in value} if value else None

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    assert utils.get_unique_hstore_keys(mgr.session(), Document._tags) == set()

    mgr.session().add(Document(tags=None))  # type: ignore[misc]
    mgr.session().add(Document(tags=['foo', 'bar']))  # type: ignore[misc]
    mgr.session().add(Document(tags=['foo', 'baz']))  # type: ignore[misc]

    transaction.commit()

    assert utils.get_unique_hstore_keys(mgr.session(), Document._tags) == {
        'foo', 'bar', 'baz'
    }


def test_remove_repeated_spaces() -> None:
    assert utils.remove_repeated_spaces('  ') == ' '
    assert utils.remove_repeated_spaces('a b') == 'a b'
    assert utils.remove_repeated_spaces('a       b') == 'a b'
    assert utils.remove_repeated_spaces(' x  ') == ' x '

    assert utils.remove_repeated_spaces('foo  bar') == 'foo bar'
    assert utils.remove_repeated_spaces('  foo  bar  ') == ' foo bar '
    assert utils.remove_repeated_spaces('       foo    bar') == ' foo bar'


def test_post_thread(session: Session) -> None:
    with patch('urllib.request.urlopen') as urlopen:
        url = 'https://example.com/post'
        data = json.dumps({'key': 'ä$j', 'b': 2}).encode('utf-8')
        headers = (
            ('Content-type', 'application/json; charset=utf-8'),
            ('Content-length', str(len(data))),
        )

        thread = utils.PostThread(url, data, headers)
        thread.start()
        thread.join()

        assert urlopen.called
        assert urlopen.call_args[0][0].get_full_url() == url
        assert urlopen.call_args[0][1] == data
        assert urlopen.call_args[0][0].headers == dict(headers)


def test_binary_dictionary() -> None:
    d = utils.binary_to_dictionary(b'foobar')
    assert d['filename'] is None
    assert d['mimetype'] == 'text/plain'
    assert d['size'] == 6

    d = utils.binary_to_dictionary(b'foobar', 'readme.txt')
    assert d['filename'] == 'readme.txt'
    assert d['mimetype'] == 'text/plain'
    assert d['size'] == 6

    assert utils.dictionary_to_binary(d) == b'foobar'  # type: ignore[arg-type]


def test_safe_format() -> None:
    fmt = utils.safe_format

    assert fmt('hello [user]', {'user': 'admin'}) == 'hello admin'
    assert fmt('[ix]: [ix]', {'ix': 1}) == '1: 1'
    assert fmt('[[user]]', {'user': 'admin'}) == '[user]'
    assert fmt('[[[user]]]', {'user': 'admin'}) == '[admin]'
    assert fmt('[asdf]', {}) == ''
    assert fmt('[foo]', {'FOO': 'bar'}, adapt=str.upper) == 'bar'

    with pytest.raises(RuntimeError) as e:
        fmt('[foo[bar]]', {'foo[bar]': 'baz'})

    assert 'bracket inside bracket' in str(e.value)

    with pytest.raises(RuntimeError) as e:
        fmt('[secret]', {'secret': object()})

    assert 'type' in str(e.value)

    with pytest.raises(RuntimeError) as e:
        fmt('[asdf', {})

    assert 'Uneven' in str(e.value)

    with pytest.raises(RuntimeError) as e:
        fmt('[foo]', {}, raise_on_missing=True)

    assert 'is unknown' in str(e.value)


def test_local_lock() -> None:
    with utils.local_lock('foo', 'bar'):
        with pytest.raises(AlreadyLockedError):
            with utils.local_lock('foo', 'bar'):
                pass


def test_is_valid_yubikey_otp() -> None:
    assert not utils.is_valid_yubikey(
        client_id='abc',
        secret_key='dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE=',
        expected_yubikey_id='ccccccbcgujx',
        yubikey='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = True

        assert utils.is_valid_yubikey(
            client_id='abc',
            secret_key='dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE=',
            expected_yubikey_id='ccccccbcgujh',
            yubikey='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )


def test_is_valid_yubikey_format() -> None:
    assert utils.is_valid_yubikey_format('ccccccdefghd')
    assert utils.is_valid_yubikey_format('cccccccdefg' * 4)
    assert not utils.is_valid_yubikey_format('ccccccdefghx')


def test_yubikey_otp_to_serial() -> None:
    assert utils.yubikey_otp_to_serial(
        'ccccccdefghdefghdefghdefghdefghdefghdefghklv') == 2311522
    assert utils.yubikey_otp_to_serial("ceci n'est pas une yubikey") is None


def test_yubikey_public_id() -> None:
    assert utils.yubikey_public_id(
        'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    ) == 'ccccccbcgujh'

    with pytest.raises(TypeError):
        utils.yubikey_public_id(None)  # type: ignore[arg-type]


def test_paragraphify() -> None:
    assert utils.paragraphify('') == ''
    assert utils.paragraphify('\n') == ''
    assert utils.paragraphify('foo') == '<p>foo</p>'
    assert utils.paragraphify('foo\nbar') == '<p>foo<br>bar</p>'
    assert utils.paragraphify('foo\n\nbar') == '<p>foo</p><p>bar</p>'
    assert utils.paragraphify('foo\r\nbar') == '<p>foo<br>bar</p>'
    assert utils.paragraphify('foo\r\n\r\nbar') == '<p>foo</p><p>bar</p>'


def test_bunch() -> None:
    bunch = Bunch(a=1, b=2)
    assert bunch.a == 1
    assert bunch.b == 2

    bunch = Bunch(**{'x.y.z': 3})
    assert bunch.x.y.z == 3

    assert (Bunch() == Bunch()) is True
    assert (Bunch(x=1) == Bunch()) is False
    assert (Bunch(x=1) == Bunch(x=1)) is True
    assert (Bunch(x=1) == Bunch(x=2)) is False
    assert (Bunch(x=1, y=2) == Bunch(x=1, y=2)) is True
    assert (Bunch(x=1, y=2) == Bunch(x=2, y=2)) is False
    assert (Bunch(x=1, y=2) == Bunch(x=1, y=3)) is False

    assert (Bunch() != Bunch()) is False
    assert (Bunch(x=1) != Bunch()) is True
    assert (Bunch(x=1) != Bunch(x=1)) is False
    assert (Bunch(x=1) != Bunch(x=2)) is True
    assert (Bunch(x=1, y=2) != Bunch(x=1, y=2)) is False
    assert (Bunch(x=1, y=2) != Bunch(x=2, y=2)) is True
    assert (Bunch(x=1, y=2) != Bunch(x=1, y=3)) is True


def test_to_html_ul() -> None:
    def li(*args: str) -> str:
        if len(args) > 1:
            return "".join(f'<li>{i}</li>' for i in args)
        return f'<li>{args[0]}</li>'

    text = "\n".join(('Title', 'A'))
    assert to_html_ul(text) == '<p>Title<br>A</p>'

    text = "\n".join(('- Title', '-A', '-B'))
    li_inner = li('Title', 'A', 'B')
    assert to_html_ul(text) == f'<ul class="bulleted">{li_inner}</ul>'

    # list and paragraph combined
    text = "\n".join(('-A', 'B'))
    assert to_html_ul(text) == f'<ul class="bulleted">{li("A")}</ul><p>B</p>'
    text = "\n".join(('A', '-B'))
    assert to_html_ul(text) == f'<p>A</p><ul class="bulleted">{li("B")}</ul>'


def test_batched() -> None:
    iterable = utils.batched(range(12), 5)
    assert next(iterable) == (0, 1, 2, 3, 4)
    assert next(iterable) == (5, 6, 7, 8, 9)
    assert next(iterable) == (10, 11)

    batched_as_list = list(utils.batched(range(12), 5))
    assert batched_as_list == [
        (0, 1, 2, 3, 4),
        (5, 6, 7, 8, 9),
        (10, 11)
    ]


def test_batched_list_container() -> None:
    iterable = utils.batched(range(12), 5, list)
    assert next(iterable) == [0, 1, 2, 3, 4]
    assert next(iterable) == [5, 6, 7, 8, 9]
    assert next(iterable) == [10, 11]

    batched_as_list = list(utils.batched(range(12), 5, list))
    assert batched_as_list == [
        [0, 1, 2, 3, 4],
        [5, 6, 7, 8, 9],
        [10, 11]
    ]
