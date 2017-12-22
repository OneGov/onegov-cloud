import onegov.core
import os.path
import pytest
import transaction

from onegov.core import utils
from onegov.core.custom import json
from onegov.core.orm import SessionManager
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from unittest.mock import patch
from uuid import uuid4


def test_normalize_for_url():
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


def test_lchop():
    assert utils.lchop('foobar', 'foo') == 'bar'
    assert utils.lchop('foobar', 'bar') == 'foobar'


def test_rchop():
    assert utils.rchop('foobar', 'foo') == 'foobar'
    assert utils.rchop('foobar', 'bar') == 'foo'
    assert utils.rchop('https://www.example.org/ex/amp/le', '/ex/amp/le') \
        == 'https://www.example.org'


def test_touch(temporary_directory):
    path = os.path.join(temporary_directory, 'test.txt')

    assert not os.path.isfile(path)

    utils.touch(path)

    assert os.path.isfile(path)

    with open(path, 'w') as f:
        f.write('asdf')

    utils.touch(path)

    with open(path, 'r') as f:
        assert f.read() == 'asdf'


def test_module_path():
    path = utils.module_path('onegov.core', 'utils.py')
    assert path == utils.module_path(onegov.core, 'utils.py')
    assert path == utils.module_path(onegov.core, '/utils.py')
    assert os.path.isfile(path)

    with pytest.raises(AssertionError):
        utils.module_path(onegov.core, '../passwd')


def test_linkify():
    # this is really bleach's job, but we want to run the codepath anyway
    assert utils.linkify('info@example.org')\
        == '<a href="mailto:info@example.org">info@example.org</a>'
    assert utils.linkify('https://google.ch')\
        == '<a href="https://google.ch" rel="nofollow">https://google.ch</a>'

    # by default, linkify sanitizes the text before linkifying it
    assert utils.linkify('info@example.org<br>')\
        == '<a href="mailto:info@example.org">info@example.org</a>&lt;br&gt;'

    # we can disable that however
    assert utils.linkify('info@example.org<br>', escape=False)\
        == '<a href="mailto:info@example.org">info@example.org</a><br>'


def test_increment_name():
    assert utils.increment_name('test') == 'test-1'
    assert utils.increment_name('test-2') == 'test-3'
    assert utils.increment_name('test2') == 'test2-1'
    assert utils.increment_name('test-1-1') == 'test-1-2'


def test_ensure_scheme():
    assert utils.ensure_scheme(None) is None
    assert utils.ensure_scheme('seantis.ch') == 'http://seantis.ch'
    assert utils.ensure_scheme('seantis.ch', 'https') == 'https://seantis.ch'

    assert utils.ensure_scheme('google.ch?q=onegov.cloud')\
        == 'http://google.ch?q=onegov.cloud'

    assert utils.ensure_scheme('https://abc.xyz') == 'https://abc.xyz'


def test_is_uuid():
    assert not utils.is_uuid(None)
    assert not utils.is_uuid('')
    assert not utils.is_uuid('asdf')
    assert utils.is_uuid(uuid4())
    assert utils.is_uuid(str(uuid4()))
    assert utils.is_uuid(uuid4().hex)


def test_is_non_string_iterable():
    assert utils.is_non_string_iterable([])
    assert utils.is_non_string_iterable(tuple())
    assert utils.is_non_string_iterable({})
    assert not utils.is_non_string_iterable('abc')
    assert not utils.is_non_string_iterable(b'abc')
    assert not utils.is_non_string_iterable(None)


def test_relative_url():
    assert utils.relative_url('https://www.google.ch/test') == '/test'
    assert utils.relative_url('https://usr:pwd@localhost:443/test') == '/test'
    assert utils.relative_url('/test') == '/test'
    assert utils.relative_url('/test?x=1&y=2') == '/test?x=1&y=2'
    assert utils.relative_url('/test?x=1&y=2#link') == '/test?x=1&y=2#link'


def test_is_subpath():
    assert utils.is_subpath('/', '/test')
    assert utils.is_subpath('/asdf', '/asdf/asdf')
    assert not utils.is_subpath('/asdf/', '/asdf')
    assert not utils.is_subpath('/a', '/b')
    assert not utils.is_subpath('/a', '/a/../b')


def test_is_sorted():
    assert utils.is_sorted('abc')
    assert not utils.is_sorted('aBc')
    assert utils.is_sorted('aBc', key=lambda i: i.lower())
    assert not utils.is_sorted('321')
    assert utils.is_sorted('321', reverse=True)


def test_get_unique_hstore_keys(postgres_dsn):

    Base = declarative_base()

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        _tags = Column(HSTORE, nullable=True)

        @property
        def tags(self):
            return set(self._tags.keys()) if self._tags else set()

        @tags.setter
        def tags(self, value):
            self._tags = {k: '' for k in value} if value else None

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    assert utils.get_unique_hstore_keys(mgr.session(), Document._tags) == set()

    mgr.session().add(Document(tags=None))
    mgr.session().add(Document(tags=['foo', 'bar']))
    mgr.session().add(Document(tags=['foo', 'baz']))

    transaction.commit()

    assert utils.get_unique_hstore_keys(mgr.session(), Document._tags) == {
        'foo', 'bar', 'baz'
    }


def test_remove_repeated_spaces():

    assert utils.remove_repeated_spaces('  ') == ' '
    assert utils.remove_repeated_spaces('a b') == 'a b'
    assert utils.remove_repeated_spaces('a       b') == 'a b'
    assert utils.remove_repeated_spaces((' x  ')) == ' x '


def test_post_thread(session):
    with patch('urllib.request.urlopen') as urlopen:
        url = 'https://example.com/post'
        data = {'key': 'ä$j', 'b': 2}
        data = json.dumps(data).encode('utf-8')
        headers = (
            ('Content-type', 'application/json; charset=utf-8'),
            ('Content-length', len(data))
        )

        thread = utils.PostThread(url, data, headers)
        thread.start()
        thread.join()

        assert urlopen.called
        assert urlopen.call_args[0][0].get_full_url() == url
        assert urlopen.call_args[0][1] == data
        assert urlopen.call_args[0][0].headers == dict(headers)


def test_binary_dictionary():

    d = utils.binary_to_dictionary(b'foobar')
    assert d['filename'] is None
    assert d['mimetype'] == 'text/plain'
    assert d['size'] == 6

    d = utils.binary_to_dictionary(b'foobar', 'readme.txt')
    assert d['filename'] == 'readme.txt'
    assert d['mimetype'] == 'text/plain'
    assert d['size'] == 6

    assert utils.dictionary_to_binary(d) == b'foobar'


def test_safe_format():
    fmt = utils.safe_format

    assert fmt('hello [user]', {'user': 'admin'}) == 'hello admin'
    assert fmt('[ix]: [ix]', {'ix': 1}) == '1: 1'
    assert fmt('[[user]]', {'user': 'admin'}) == '[user]'
    assert fmt('[[[user]]]', {'user': 'admin'}) == '[admin]'
    assert fmt('[asdf]', {}) == ''
    assert fmt('[foo]', {'FOO': 'bar'}, adapt=str.upper) == 'bar'

    with pytest.raises(RuntimeError) as e:
        fmt('[foo[bar]]', {'foo[bar]': 'baz'})

    assert 'bracket inside bracket' in str(e)

    with pytest.raises(RuntimeError) as e:
        fmt('[secret]', {'secret': object()})

    assert 'type' in str(e)

    with pytest.raises(RuntimeError) as e:
        fmt('[asdf', {})

    assert 'Uneven' in str(e)

    with pytest.raises(RuntimeError) as e:
        fmt('[foo]', {}, raise_on_missing=True)

    assert 'is unknown' in str(e)
